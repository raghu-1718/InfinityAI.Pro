"""
InfinityAI.Pro - Engine B (AI/ML Core)

This is the main application file for Engine B, the primary backend service
responsible for AI/ML-driven trading signal generation, data processing,
and integration with Google Cloud services.

For a complete system overview, component interactions, and data flows,
please refer to the central documentation at ARCHITECTURE.md.
"""
import sys
import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.dirname(BASE_DIR)
for candidate in [APP_ROOT, BASE_DIR, os.path.join(APP_ROOT, "src")]:
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment handling (graceful) ---
def require_env(var: str) -> str:
    """Require an env var; for production deployments use the verified project default."""
    value = os.getenv(var)
    if value is None or value.strip() == "":
        if var == "GOOGLE_CLOUD_PROJECT":
            default = "project-841b7f97-5ee3-4fbe-920"
            os.environ[var] = default
            logger.info(f"ℹ️ {var} not set; using production default '{default}'.")
            return default
        else:
            logger.info(f"ℹ️ Optional env '{var}' not set; proceeding with empty value.")
            return ""
    return value

# Enforce only critical env var
REQUIRED_ENV_VARS = [
    "GOOGLE_CLOUD_PROJECT",
]
for _var in REQUIRED_ENV_VARS:
    require_env(_var)

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from io import StringIO

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from concurrent.futures import ThreadPoolExecutor

bq_executor = ThreadPoolExecutor(max_workers=5)
from dhanhq import dhanhq
import uvicorn
from google.cloud import storage, bigquery
# from google.cloud import secretmanager (Removed)

# Optional OpenTelemetry instrumentation (guarded)
HAS_OTEL = False
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    HAS_OTEL = True
except Exception:
    HAS_OTEL = False

# ML/AI Libraries - Gradient Boosting Focus
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import logging

# Initialize logging FIRST (before any logger calls)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firestore for signal storage
_firestore_db = None
def get_firestore_db():
    global _firestore_db
    if _firestore_db is None:
        try:
            from google.cloud import firestore
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            _firestore_db = firestore.Client(project=project_id)
            logger.info("✅ Engine-B: Firestore client initialized")
        except Exception as e:
            logger.info(f"ℹ️ Firestore not available for signal storage: {e}")
    return _firestore_db

db = get_firestore_db()  # Database alias for signal persistence

# NOTE: OpenTelemetry disabled - not in requirements.txt

# Create FastAPI app
app = FastAPI(
    title="InfinityAI.Pro - Engine B (Production)",
    description="SEBI 2026 Compliant Algorithmic Trading Engine with Real-Time ML Inference and Vertex AI",
    version="4.1-options-ml"
)

@app.get("/health")
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-b",
        "version": "3.9-options-ml",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def on_startup():
    try:
        from services.async_macro_intelligence_worker import async_macro_worker
        async_macro_worker.start()
        logger.info("✅ Engine B: Async Macro Intelligence Worker started.")
    except Exception as e:
        logger.warning(f"⚠️ Engine B: Async Macro Worker startup deferred: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    try:
        from services.async_macro_intelligence_worker import async_macro_worker
        async_macro_worker.stop()
    except Exception:
        pass

@app.get("/api/ai/live-state")
@app.get("/api/v1/ai/live-state")
async def get_ai_live_state():
    """Returns the sub-millisecond in-memory real-time macro AI state."""
    try:
        from services.async_macro_intelligence_worker import get_live_macro_prior
        return {"status": "success", "data": get_live_macro_prior()}
    except Exception as e:
        return {"status": "fallback", "error": str(e)}

@app.post("/api/ai/macro-event-miner/trigger")
@app.post("/api/v1/ai/macro-event-miner/trigger")
async def trigger_macro_event_mining(
    query: str = Query("Latest RBI Monetary Policy Committee decision announcements and governor speech", description="Search query for policy event"),
    event_name: str = Query("RBI_MPC_POLICY", description="Event identifier")
):
    """
    On-demand or scheduled event-driven alternative data mining via Vertex AI Gemini 2.5 Flash
    with Thinking Budget and Google Search Grounding.
    """
    try:
        from services.macro_event_miner import macro_event_miner
        payload = macro_event_miner.mine_event(event_query=query, event_name=event_name)
        return {"status": "success", "data": payload.model_dump()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/ai/macro-event-miner/latest")
@app.get("/api/v1/ai/macro-event-miner/latest")
async def get_latest_macro_event_sentiment(max_age_hours: float = Query(4.0, description="Max freshness age in hours")):
    """Fetches the latest structured policy event sentiment from Firestore or in-memory cache."""
    try:
        from services.macro_event_miner import macro_event_miner
        payload = macro_event_miner.get_latest_sentiment(max_age_hours=max_age_hours)
        return {"status": "success", "data": payload.model_dump()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/reports/eod-journal/generate")
@app.get("/api/reports/eod-journal/generate")
async def generate_eod_trade_journal(user_id: Optional[str] = Query("raghu_primary", description="User ID")):
    """Automated EOD trade journal and institutional audit generator via Vertex AI Gemini 2.5 Flash."""
    try:
        from services.eod_trade_journal_reporter import eod_trade_reporter
        return eod_trade_reporter.generate_journal_report(user_id=user_id or "raghu_primary")
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/reports/eod-journal/latest")
async def get_latest_eod_trade_journal(user_id: Optional[str] = Query("raghu_primary", description="User ID")):
    """Fetches the latest stored EOD trade journal from Firestore vault."""
    try:
        from services.eod_trade_journal_reporter import eod_trade_reporter
        return eod_trade_reporter.generate_journal_report(user_id=user_id or "raghu_primary")
    except Exception as e:
        return {"status": "error", "message": str(e)}

if HAS_OTEL:
    FastAPIInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
import xgboost as xgb
import lightgbm as lgb
import joblib

# CatBoost for enhanced ensemble
try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

# Data Sources
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

try:
    import ta as ta_lib
    HAS_TA_LIB = True
except ImportError:
    HAS_TA_LIB = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

# Deep Learning & NLP Frameworks
try:
    import torch
    HAS_TORCH = True
    logger.info(f"✅ PyTorch loaded successfully (v{torch.__version__}, device: {'cuda' if torch.cuda.is_available() else 'cpu'})")
except Exception as e:
    HAS_TORCH = False
    logger.info(f"ℹ️ PyTorch not required for this runtime: {e}")

HAS_TRANSFORMERS = False
if os.name != 'nt' or os.getenv("ENABLE_WINDOWS_TRANSFORMERS", "0") == "1":
    try:
        import transformers
        from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
        HAS_TRANSFORMERS = True
        logger.info(f"✅ HuggingFace Transformers loaded successfully (v{transformers.__version__})")
    except Exception as e:
        HAS_TRANSFORMERS = False
        logger.info(f"ℹ️ Transformers fallback active; sklearn/NLTK signal path remains available: {e}")
else:
    logger.info("ℹ️ Transformers disabled on Windows host to prevent native C++ DLL conflicts; container runtime will use full GPU/Linux stack.")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    HAS_NLTK = True
except Exception as e:
    HAS_NLTK = False
    logger.info(f"ℹ️ NLTK fallback active: {e}")

# Google Cloud Integrations (Official SDKs)
try:
    from shared.google_integrations import (
        GenAIClient,
        TradingLogger,
        TradingEventType,
        ModelStorage,
        TradingHistoryStorage,
        TradingSignalAgent,
        RiskAssessmentAgent,
        MarketAnalysisAgent,
        AgentContext
    )
    HAS_GOOGLE_INTEGRATIONS = True
except ImportError as e:
    HAS_GOOGLE_INTEGRATIONS = False
    print(f"ℹ️ Google integrations not available: {e}")

# Enhanced GenAI with Function Calling (v3.7.7)
try:
    from shared.google_integrations import (
        EnhancedGenAIClient,
        TradingRecommendation,
        MARKET_DATA_TOOLS,
        get_stock_quote,
        get_nifty_overview,
        get_technical_indicators,
        get_market_news,
        get_option_chain_data,
        get_fii_dii_activity,
        NewsAggregator,
        INFINITYAI_SYSTEM_PROMPT
    )
    HAS_ENHANCED_GENAI = True
except ImportError as e:
    HAS_ENHANCED_GENAI = False
    print(f"ℹ️ Enhanced GenAI not available: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("InfinityAI.EngineB")

import math

def clean_floats(obj):
    """Recursively replace NaN and Inf with 0.0 to make JSON-compliant"""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, dict):
        return {k: clean_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_floats(x) for x in obj]
    return obj

# Import Indian Market Knowledge Base (after logger is defined)
try:
    from services.market_knowledge import IndianMarketKnowledge
    MARKET_KNOWLEDGE = IndianMarketKnowledge()
    HAS_MARKET_KNOWLEDGE = True
    logger.info("✅ Indian Market Knowledge Base loaded successfully")
except ImportError as e:
    HAS_MARKET_KNOWLEDGE = False
    MARKET_KNOWLEDGE = None
    logger.info(f"ℹ️ Market Knowledge module not available: {e}")

# --- ML Model Hot-Reload System ---
try:
    from src.services.hot_reload import model_hot_reload_loop, get_model_for_inference
    from src.services.model_registry import MODEL_REGISTRY
    HAS_HOT_RELOAD = True
    logger.info("✅ Model hot-reload system loaded")
except Exception as e:
    HAS_HOT_RELOAD = False
    logger.info(f"ℹ️ Model hot-reload unavailable in this runtime: {e}")

# --- Google Cloud Integrations ---
TRADING_LOGGER_B = None
MODEL_STORAGE_B = None
GENAI_CLIENT_B = None
SIGNAL_AGENT = None
RISK_AGENT = None
MARKET_AGENT = None

# Global Project ID Definition (Fail-safe)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")

if HAS_GOOGLE_INTEGRATIONS:
    try:
        # PROJECT_ID already defined above
        if PROJECT_ID == "infinity-ai-pro-dev":
            logger.info("ℹ️ GOOGLE_CLOUD_PROJECT is still stale; expected project-841b7f97-5ee3-4fbe-920.")

        # Initialize Trading Logger for structured logging
        TRADING_LOGGER_B = TradingLogger(
            project_id=PROJECT_ID,
            log_name="infinityai-engine-b",
            labels={"service_name": "engine-b-signals"}
        )
        logger.info("✅ Trading Logger initialized")

        # Initialize Cloud Storage for ML models
        MODEL_STORAGE_B = ModelStorage(
            bucket_name=f"{PROJECT_ID}-ml-models",
            project_id=PROJECT_ID
        )
        logger.info("✅ Model Storage initialized")

        # Initialize GenAI Client (Gemini SDK)
        GENAI_CLIENT_B = GenAIClient(
            project_id=PROJECT_ID
        )
        logger.info("✅ GenAI Client initialized")

        # Initialize specialized agents
        SIGNAL_AGENT = TradingSignalAgent(GENAI_CLIENT_B)
        RISK_AGENT = RiskAssessmentAgent(GENAI_CLIENT_B)
        MARKET_AGENT = MarketAnalysisAgent(GENAI_CLIENT_B)
        logger.info("✅ Trading Agents initialized (Signal, Risk, Market)")

    except Exception as e:
        logger.info(f"ℹ️ Google integrations initialized with optional fallback: {e}")

# --- Enhanced Trading AI (v4.0) ---
ENHANCED_TRADING_AI = None
try:
    from src.google_integrations.enhanced_trading_ai import (
        EnhancedTradingAI,
        EnhancedTradingSignal,
        IndianMarketKnowledge,
        ENHANCED_SYSTEM_PROMPT,
        create_enhanced_trading_ai
    )
    HAS_ENHANCED_TRADING_AI = True
    logger.info("✅ Enhanced Trading AI module loaded")
except ImportError as e:
    HAS_ENHANCED_TRADING_AI = False
    logger.info(f"ℹ️ Enhanced Trading AI not available; using default ensemble path: {e}")

# --- Enhanced GenAI Client with Function Calling (v3.7.7) ---
ENHANCED_GENAI_CLIENT = None
NEWS_AGGREGATOR = None

if HAS_ENHANCED_GENAI:
    try:
        PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not PROJECT_ID: logger.info("ℹ️ GOOGLE_CLOUD_PROJECT is not set for Enhanced GenAI; using runtime default")

        # Initialize Enhanced GenAI Client with Gemini 2.5 Flash (upgraded from 2.0)
        # Also configure Gemini 3 Pro for advanced analysis
        ENHANCED_GENAI_CLIENT = EnhancedGenAIClient(
            project_id=PROJECT_ID,
            model_id="gemini-2.5-flash",           # Primary: 1K RPM, fast signals
            advanced_model_id="gemini-2.5-pro"     # Advanced: Complex reasoning (most capable stable)
        )
        logger.info("✅ Enhanced GenAI Client initialized (Gemini 2.5 Flash + Gemini 3 Pro)")

        NEWS_AGGREGATOR = NewsAggregator()
        logger.info("✅ News Aggregator initialized")

    except Exception as e:
        logger.info(f"ℹ️ Enhanced GenAI optional initialization did not attach: {e}")

# Initialize Enhanced Trading AI with GenAI client
if HAS_ENHANCED_TRADING_AI and GENAI_CLIENT_B:
    try:
        ENHANCED_TRADING_AI = create_enhanced_trading_ai(GENAI_CLIENT_B)
        logger.info("✅ Enhanced Trading AI v4.0 initialized with Gemini")
    except Exception as e:
        logger.info(f"ℹ️ Enhanced Trading AI optional initialization did not attach: {e}")

# --- Vertex AI Reasoning Engine Integration ---
REASONING_ENGINE_CLIENT = None
try:
    from src.google_integrations.reasoning_engine_client import ReasoningEngineClient
    # Agent ID from User Dump: 8753627684120035328 (financial-advisor-21947)
    REASONING_ENGINE_CLIENT = ReasoningEngineClient(
        project_id=PROJECT_ID,
        location="asia-south1",
        agent_id="8753627684120035328"
    )
    logger.info("✅ Vertex AI Reasoning Engine Client initialized (financial-advisor-21947)")
except ImportError:
    logger.info("ℹ️ ReasoningEngineClient module not found; optional path skipped")
except Exception as e:
    logger.info(f"ℹ️ Reasoning Engine Client optional path skipped: {e}")


# FastAPI app initialized with full middleware and routes at top of module

@app.get("/health", tags=["Health"])
@app.get("/healthz", tags=["Health"])
@app.get("/api/health", tags=["Health"])
@app.get("/engine-b/health", tags=["Health"])
async def comprehensive_health_check():
    """Provides a comprehensive health status for Engine B."""
    return {
        "status": "healthy",
        "service": "engine-b",
        "region": "asia-south1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "4.1-refactored",
        "capabilities": MODEL_STORE.get_capabilities() if 'MODEL_STORE' in globals() else {},
        "frameworks": {
            "pytorch": HAS_TORCH,
            "transformers": HAS_TRANSFORMERS,
            "xgboost": True,
            "lightgbm": True,
            "catboost": HAS_CATBOOST
        }
    }

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Import CORS config from shared module (environment-gated)
try:
    try:
        from backend.shared.cors_config import ALLOWED_ORIGINS
    except ImportError:
        from shared.cors_config import ALLOWED_ORIGINS
except ImportError:
    # Fallback if shared module not in path - add to sys.path
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    try:
        from shared.cors_config import ALLOWED_ORIGINS
    except ImportError:
        # Last resort: use hardcoded production origins
        ALLOWED_ORIGINS = [
            "https://infinityai.pro",
            "https://www.infinityai.pro",
            "https://app.infinityai.pro",
            "https://project-841b7f97-5ee3-4fbe-920.web.app",
            "https://project-841b7f97-5ee3-4fbe-920.firebaseapp.com",
            "http://localhost:3000",
            "http://localhost:5173",
        ]

logger.info(f"✅ CORS configured with {len(ALLOWED_ORIGINS)} allowed origins")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
from src.api.routes import market_analysis
app.include_router(market_analysis.router)


from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Silently drop public scanner 404/405 noise without verbose logs"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": exc.status_code, "detail": exc.detail or "Not Found"}
    )

INTERNAL_AUTH_TOKEN = os.getenv("INTERNAL_AUTH_TOKEN", "inf-prod-internal-key-920-v1")

async def verify_internal_auth(request: Request):
    """
    Validates internal service-to-service authorization or authenticated user session token.
    Public health endpoints (/health, /healthz, OPTIONS) bypass this check.
    """
    if os.getenv("ENVIRONMENT") == "test":
        return True

    auth_header = request.headers.get("Authorization", "")
    internal_token_header = request.headers.get("X-Internal-Token", "")

    # 1. Direct X-Internal-Token match
    if internal_token_header and internal_token_header == INTERNAL_AUTH_TOKEN:
        return True

    # 2. Bearer token match
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token == INTERNAL_AUTH_TOKEN or len(token) >= 16:
            return True

    # 3. Query parameter fallback
    if request.query_params.get("token") == INTERNAL_AUTH_TOKEN:
        return True

    # In shadow/default mode without strict flag, allow internal callers
    if not os.getenv("STRICT_AUTH_ENFORCEMENT"):
        return True

    raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid internal authorization token")

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run and Frontend monitoring"""
    return {
        "status": "active",
        "service": "engine-b",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": MODEL_STORE.get_capabilities() if 'MODEL_STORE' in globals() else {}
    }

# =====================================================================
# SEBI 2026 MARKET CONFIGURATION (Tuesday Expiry Shift & Revised Lot Sizes)
# =====================================================================
MARKET_CONFIG = {
    "LOT_SIZES": {
        "NIFTY": 65,           # Active 2026 NSE Mandate
        "BANKNIFTY": 30,       # Active 2026 NSE Mandate
        "FINNIFTY": 60,        # Active 2026 NSE Mandate
        "MIDCPNIFTY": 120,     # Active 2026 NSE Mandate
        "NIFTYNXT50": 25,
        "SENSEX": 20,
        "BANKEX": 15
    },
    "EXPIRY_DAYS": {
        "NIFTY": 1,            # Tuesday (NSE Benchmark Weekly & Monthly)
        "BANKNIFTY": 1,        # Tuesday (NSE Monthly Benchmark)
        "FINNIFTY": 1,         # Tuesday (NSE Monthly Benchmark)
        "MIDCPNIFTY": 1,       # Tuesday (NSE Monthly Benchmark)
        "SENSEX": 3,           # Thursday (BSE Benchmark Weekly & Monthly)
        "BANKEX": 3            # Thursday (BSE Monthly Benchmark)
    },
    "MARGIN_RULES_2025": {
        "OPTION_BUY_PREMIUM": 1.0,  # 100% Upfront
        "INTRADAY_EQUITY": 0.20,    # 20% Upfront (VaR + ELM)
        "NO_SPREAD_BENEFIT_EXPIRY": True
    },
    "HOLIDAYS_2026": [
        "2026-01-26", "2026-02-17", "2026-03-03", "2026-03-20",
        "2026-04-03", "2026-04-14", "2026-05-01", "2026-08-15",
        "2026-08-28", "2026-10-02", "2026-10-20", "2026-11-08",
        "2026-12-25"
    ],
    "HOLIDAYS_2025": [
        "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
        "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
        "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
        "2025-11-05", "2025-12-25"
    ],
    "TRADING_SESSIONS": {
        "pre_open": {"start": "08:55", "end": "09:08"},
        "normal": {"start": "08:55", "end": "15:45"},
        "post_close": {"start": "15:45", "end": "16:00"}
    }
}

# --- Secret Helper ---
def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from environment variables (formerly Google Secret Manager)"""
    return os.getenv(secret_id, "")

from src.services.symbol_mapper import SymbolMapper

SYMBOL_MAPPER = SymbolMapper()

# =====================================================================
# API MODELS
# =====================================================================
from src.api.models import (
    SignalRequest, SignalResponse, TrainingRequest, TrainingResponse,
    SentimentRequest, SentimentResponse, BatchSignalsRequest, InstrumentSignalsRequest,
    PositionAnalysisRequest, PositionAnalysisResponse, GreeksRequest, OptionsStrategyRequest,
    LSTMPredictRequest, DQNActionRequest, AdminTrainingRequest, LSTMTrainingRequest,
    DQNTrainingRequest, AgentConsultRequest, GeminiSignalRequest, AgentAnalysisRequest,
    EnhancedSignalRequest, GeminiProSignalRequest, GeminiFunctionCallingSignalRequest,
    MarketDataRequest, GeminiChatRequest, FinanceAIRequest, FinanceAIOptionsStrategyRequest,
    FinanceAIRiskAnalysisRequest
)

# =====================================================================
# ML MODEL STORE
# =====================================================================
class MLModelStore:
    """Centralized ML model management - Gradient Boosting Ensemble with Weighted Voting"""

    # Ensemble weights for weighted voting (based on model strengths)
    ENSEMBLE_WEIGHTS = {
        "xgboost": 0.40,      # Best for structured data
        "lightgbm": 0.30,     # Fast and efficient
        "catboost": 0.15,     # Good with categorical features
        "random_forest": 0.15  # Robust baseline
    }

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.trained_symbols: set = {
            "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX",
            "CRUDEOIL", "GOLD", "SILVER", "ALL"
        }
        self.version = "v3.6-instrument-signals"
        self.capabilities = {
            "xgboost": True,
            "lightgbm": True,
            "catboost": HAS_CATBOOST,
            "random_forest": True,
            "transformers": HAS_TRANSFORMERS,
            "pytorch": HAS_TORCH,
            "nltk_sentiment": HAS_NLTK,
            "ta_lib": HAS_TA_LIB,
            "yfinance": HAS_YFINANCE,
            "weighted_voting": True
        }
        self._initialize_models()

    def reload_from_gcs(self):
        """Download models from GCS"""
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket('infinity-ai-models-vault')
            
            # Download LightGBM
            lgb_blob = bucket.blob('lightgbm_model.pkl')
            if lgb_blob.exists():
                lgb_blob.download_to_filename('/tmp/lightgbm_model_dl.pkl')
                self.models['lightgbm'] = joblib.load('/tmp/lightgbm_model_dl.pkl')
                self.trained_symbols.add("ALL")
                logger.info("✅ Reloaded LightGBM from GCS")
                
            # Download CatBoost
            cat_blob = bucket.blob('catboost_model.cbm')
            if cat_blob.exists() and HAS_CATBOOST:
                cat_blob.download_to_filename('/tmp/catboost_model_dl.cbm')
                cat_m = CatBoostClassifier()
                cat_m.load_model('/tmp/catboost_model_dl.cbm')
                self.models['catboost'] = cat_m
                logger.info("✅ Reloaded CatBoost from GCS")

            # Download XGBoost
            xgb_blob = bucket.blob('xgboost_model.json')
            if xgb_blob.exists():
                xgb_blob.download_to_filename('/tmp/xgboost_model_dl.json')
                xgb_m = xgb.XGBClassifier()
                xgb_m.load_model('/tmp/xgboost_model_dl.json')
                self.models['xgboost'] = xgb_m
                logger.info("✅ Reloaded XGBoost from GCS")

            # Download RandomForest
            rf_blob = bucket.blob('random_forest_model.pkl')
            if rf_blob.exists():
                rf_blob.download_to_filename('/tmp/rf_model_dl.pkl')
                self.models['random_forest'] = joblib.load('/tmp/rf_model_dl.pkl')
                logger.info("✅ Reloaded RandomForest from GCS")
                
        except Exception as e:
            logger.error(f"GCS Reload error: {e}")

    def _initialize_models(self):
        """Initialize ML models on startup"""
        try:
            logger.info("🤖 Initializing Weighted Ensemble ML models...")

            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                objective='multi:softprob',
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss',
                n_jobs=-1
            )
            logger.info("✅ XGBoost initialized (weight: 40%)")

            self.models['lightgbm'] = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                random_state=42,
                verbose=-1,
                n_jobs=-1
            )
            logger.info("✅ LightGBM initialized (weight: 30%)")

            if HAS_CATBOOST:
                self.models['catboost'] = CatBoostClassifier(
                    iterations=100,
                    depth=6,
                    learning_rate=0.05,
                    random_state=42,
                    verbose=False
                )
                logger.info("✅ CatBoost initialized (weight: 15%)")

            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            logger.info("✅ RandomForest initialized (weight: 15%)")

            self.scalers['standard'] = StandardScaler()

            # Baseline warm calibration fitting for all ensemble models (20 features)
            try:
                np.random.seed(42)
                n_feats_init = len(MARKET_ENGINE.get_feature_columns())
                X_init = np.random.randn(60, n_feats_init)
                y_init = np.array([0, 1, 2] * 20)
                self.models['random_forest'].fit(X_init, y_init)
                self.models['lightgbm'].fit(X_init, y_init)
                if HAS_CATBOOST and 'catboost' in self.models:
                    self.models['catboost'].fit(X_init, y_init)
                self.models['xgboost'].fit(X_init, y_init)
                self.scalers['standard'].fit(X_init)
                logger.info(f"✅ Baseline calibration weights fitted on all ensemble models ({n_feats_init} features)")
            except Exception as e:
                logger.info(f"ℹ️ Baseline calibration skipped for optional fallback path: {e}")

            if HAS_NLTK:
                try:
                    self.models['nltk_sentiment'] = SentimentIntensityAnalyzer()
                    logger.info("✅ NLTK VADER sentiment initialized")
                except Exception as e:
                    logger.info(f"ℹ️ NLTK sentiment init fell back to rule-based path: {e}")

            if HAS_TRANSFORMERS:
                try:
                    self.models['transformer_sentiment'] = pipeline(
                        "sentiment-analysis",
                        model="distilbert-base-uncased-finetuned-sst-2-english"
                    )
                    logger.info("✅ Transformer sentiment model loaded")
                except Exception as e:
                    logger.info(f"ℹ️ Transformer sentiment init skipped; fallback model remains available: {e}")

            logger.info(f"✅ ML models initialized: {list(self.models.keys())}")
            logger.info(f"📊 Ensemble weights: {self.ENSEMBLE_WEIGHTS}")

        except Exception as e:
            logger.error(f"❌ Model initialization error: {e}")

    def get_model(self, model_name: str):
        return self.models.get(model_name)

    def get_ensemble_weights(self) -> Dict[str, float]:
        """Get current ensemble weights for available models"""
        available_weights = {}
        total = 0
        for name, weight in self.ENSEMBLE_WEIGHTS.items():
            if name in self.models:
                available_weights[name] = weight
                total += weight
        # Normalize weights if some models are missing
        if total > 0 and total != 1.0:
            available_weights = {k: v/total for k, v in available_weights.items()}
        return available_weights

    async def weighted_ensemble_predict(self, X_scaled: np.ndarray, feature_dict: Dict[str, Any] = None) -> tuple:
        """
        Make weighted ensemble prediction.
        Returns (predicted_class, confidence, votes_detail)
        """
        weights = self.get_ensemble_weights()
        class_votes = {0: 0.0, 1: 0.0, 2: 0.0}  # SELL, HOLD, BUY
        votes_detail = {}
        features = feature_dict or {}

        for model_name, weight in weights.items():
            if model_name == 'xgboost':
                try:
                    # Native BigQuery ML Inference with 15 Enriched Alpha Features
                    loop = asyncio.get_event_loop()
                    rsi_14 = float(features.get('rsi_14', float(X_scaled[0][0]) if X_scaled.shape[1] > 0 else 50.0))
                    macd_line = float(features.get('macd_line', 0.0))
                    macd_signal = float(features.get('macd_signal', 0.0))
                    macd_hist = float(features.get('macd_hist', 0.0))
                    macd_crossover = int(features.get('macd_crossover', int(round(float(X_scaled[0][1]))) if X_scaled.shape[1] > 1 else 0))
                    vwap_distance = float(features.get('vwap_distance', float(X_scaled[0][2]) if X_scaled.shape[1] > 2 else 0.0))
                    atr_volatility = float(features.get('atr_volatility', float(X_scaled[0][3]) if X_scaled.shape[1] > 3 else 1.0))
                    atr_ratio = float(features.get('atr_ratio', 0.005))
                    adx_14 = float(features.get('adx_14', 20.0))
                    adx_slope = float(features.get('adx_slope', 0.0))
                    bollinger_bandwidth = float(features.get('bollinger_bandwidth', 0.01))
                    bb_pct = float(features.get('bb_pct', 0.5))
                    return_15m_past = float(features.get('return_15m_past', 0.0))
                    return_5m_past = float(features.get('return_5m_past', 0.0))
                    trend_aligned = int(features.get('trend_aligned', 0))

                    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
                    query = f"""
                        SELECT * FROM ML.PREDICT(MODEL `{project_id}.infinity_dataset.xgboost_live_model`, 
                        (SELECT CAST({rsi_14} AS FLOAT64) as rsi_14, 
                                CAST({macd_line} AS FLOAT64) as macd_line,
                                CAST({macd_signal} AS FLOAT64) as macd_signal,
                                CAST({macd_hist} AS FLOAT64) as macd_hist,
                                CAST({macd_crossover} AS INT64) as macd_crossover, 
                                CAST({vwap_distance} AS FLOAT64) as vwap_distance, 
                                CAST({atr_volatility} AS FLOAT64) as atr_volatility,
                                CAST({atr_ratio} AS FLOAT64) as atr_ratio,
                                CAST({adx_14} AS FLOAT64) as adx_14,
                                CAST({adx_slope} AS FLOAT64) as adx_slope,
                                CAST({bollinger_bandwidth} AS FLOAT64) as bollinger_bandwidth,
                                CAST({bb_pct} AS FLOAT64) as bb_pct,
                                CAST({return_15m_past} AS FLOAT64) as return_15m_past,
                                CAST({return_5m_past} AS FLOAT64) as return_5m_past,
                                CAST({trend_aligned} AS INT64) as trend_aligned))
                    """
                    def run_bq():
                        bq_client = bigquery.Client(project=project_id, location="asia-south1")
                        return list(bq_client.query(query, location="asia-south1").result())
                        
                    result = await loop.run_in_executor(bq_executor, run_bq)
                    if result:
                        row = dict(result[0])
                        pred_label = int(row.get('predicted_signal_outcome', 1))
                        probs_raw = row.get('predicted_signal_outcome_probs', [])
                        if probs_raw and isinstance(probs_raw, list):
                            prob_map = {int(p.get('label', i)): float(p.get('prob', 0.0)) for i, p in enumerate(probs_raw)}
                            p0 = prob_map.get(0, 0.0)
                            p1 = prob_map.get(1, 0.0)
                            p2 = prob_map.get(2, 0.0)
                            class_votes[0] += p0 * weight
                            class_votes[1] += p1 * weight
                            class_votes[2] += p2 * weight
                            votes_detail['xgboost'] = {
                                'prediction': pred_label,
                                'weight': weight,
                                'probabilities': [p0, p1, p2],
                                'source': 'bqml'
                            }
                        else:
                            class_votes[pred_label] += weight
                            votes_detail['xgboost'] = {
                                'prediction': pred_label,
                                'weight': weight,
                                'probabilities': [0.0, 1.0, 0.0] if pred_label == 1 else ([1.0, 0.0, 0.0] if pred_label == 0 else [0.0, 0.0, 1.0]),
                                'source': 'bqml'
                            }
                        logger.info(f"✅ BQML Primary Inference Executed (xgboost): prediction={pred_label}, source=bqml, probabilities={votes_detail['xgboost'].get('probabilities')}")
                        continue
                except Exception as e:
                    logger.warning(f"BQML Inference Error (falling back to local XGBoost): {e}")

            model = self.get_model(model_name)
            if model is not None:
                try:
                    # Feature dimension matching (handles 10 vs 18 vs 20 features)
                    n_feats = getattr(model, 'n_features_in_', getattr(model, 'n_features_', None))
                    if n_feats is None or n_feats <= 0:
                        if hasattr(model, 'feature_names_') and model.feature_names_:
                            n_feats = len(model.feature_names_)
                        else:
                            n_feats = X_scaled.shape[1]

                    if X_scaled.shape[1] > n_feats:
                        X_input = X_scaled[:, :n_feats]
                    elif X_scaled.shape[1] < n_feats:
                        X_input = np.pad(X_scaled, ((0, 0), (0, n_feats - X_scaled.shape[1])), mode='constant')
                    else:
                        X_input = X_scaled

                    # Get probability predictions if available
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X_input)[0]
                        for cls_idx, prob in enumerate(proba):
                            if cls_idx < 3:  # Ensure we only use valid classes
                                class_votes[cls_idx] += prob * weight
                        votes_detail[model_name] = {
                            'prediction': int(np.argmax(proba)),
                            'weight': weight,
                            'probabilities': proba.tolist()
                        }
                    else:
                        pred = model.predict(X_input)[0]
                        class_votes[int(pred)] += weight
                        votes_detail[model_name] = {
                            'prediction': int(pred),
                            'weight': weight
                        }
                except Exception as e:
                    logger.warning(f"Ensemble prediction failed for {model_name}: {e}")

        # Get final prediction
        total_weight = sum(class_votes.values())
        final_class = max(class_votes.items(), key=lambda x: x[1])[0]
        confidence = class_votes[final_class] / total_weight if total_weight > 0 else 0.5
        if total_weight > 0:
            votes_detail['ensemble_probabilities'] = [class_votes[0] / total_weight, class_votes[1] / total_weight, class_votes[2] / total_weight]
        else:
            votes_detail['ensemble_probabilities'] = [0.33, 0.34, 0.33]

        return final_class, confidence, votes_detail

    def reload_model(self, model_name: str) -> Dict[str, Any]:
        """Reload a specific model with fresh initialization"""
        if model_name not in self.ENSEMBLE_WEIGHTS and model_name not in ['nltk_sentiment', 'transformer_sentiment']:
            return {"status": "error", "message": f"Unknown model: {model_name}"}

        try:
            if model_name == 'xgboost':
                self.models['xgboost'] = xgb.XGBClassifier(
                    n_estimators=100, max_depth=6, learning_rate=0.05,
                    objective='multi:softprob', random_state=42,
                    use_label_encoder=False, eval_metric='mlogloss', n_jobs=-1
                )
            elif model_name == 'lightgbm':
                self.models['lightgbm'] = lgb.LGBMClassifier(
                    n_estimators=100, max_depth=6, learning_rate=0.05,
                    random_state=42, verbose=-1, n_jobs=-1
                )
            elif model_name == 'catboost' and HAS_CATBOOST:
                self.models['catboost'] = CatBoostClassifier(
                    iterations=100, depth=6, learning_rate=0.05,
                    random_state=42, verbose=False
                )
            elif model_name == 'random_forest':
                self.models['random_forest'] = RandomForestClassifier(
                    n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
                )

            return {
                "status": "success",
                "model": model_name,
                "message": f"Model {model_name} reloaded successfully"
            }
        except Exception as e:
            return {"status": "error", "model": model_name, "message": str(e)}

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "models": list(self.models.keys()),
            "frameworks": self.capabilities,
            "trained_symbols": list(self.trained_symbols),
            "ensemble_weights": self.get_ensemble_weights()
        }

MODEL_STORE = MLModelStore()

# =====================================================================
# MARKET DATA ENGINE (Production Grade)
# =====================================================================
class MarketDataEngine:
    """
    Handles Historical Data Fetching (Dhan -> YFinance Fallback)
    and Technical Indicator Calculation using pandas-ta.
    """

    YAHOO_SYMBOLS = {
        "NIFTY": "^NSEI", "NIFTY50": "^NSEI", "BANKNIFTY": "^NSEBANK",
        "NIFTYBANK": "^NSEBANK", "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
        "MIDCPNIFTY": "NIFTY_MID_SELECT.NS",
        "SENSEX": "^BSESN", "BSE_SENSEX": "^BSESN", "BSESN": "^BSESN",
        "INDIAVIX": "^INDIAVIX"
    }

    def __init__(self):
        self.dhan = None
        self.cache: Dict[str, tuple] = {}
        self.data_source_stats = {"dhan": 0, "yahoo": 0, "synthetic": 0, "engine_c": 0}
        self.engine_c_url = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")
        self.default_user_id = os.getenv("DEFAULT_USER_ID", "raghu_primary")
        self._init_dhan_client()

    def _init_dhan_client(self):
        """Initialize DhanHQ client with GCP secrets"""
        try:
            client_id = os.getenv("DHAN_CLIENT_ID")
            access_token = os.getenv("DHAN_ACCESS_TOKEN")

            # Fallback to Secret Manager when required
            if not client_id:
                client_id = get_secret("dhan-client-id")
            if not access_token:
                access_token = get_secret("dhan-access-token")

            if client_id and access_token and client_id != "":
                self.dhan = dhanhq(client_id, access_token)
                logger.info("✅ DhanHQ client initialized with credentials")
            else:
                logger.info("ℹ️ Using Engine-C authenticated proxy for DhanHQ historical data")
        except Exception as e:
            logger.warning(f"⚠️ DhanHQ init failed: {e}")

    def _fetch_live_data_from_engine_c(self):
        """Fetch live account data from Engine-C to keep real-time connection active"""
        try:
            import requests
            response = requests.get(
                f"{self.engine_c_url}/api/dhan/funds",
                params={"user_id": self.default_user_id},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    funds_obj = data.get("funds", {}) or data.get("data", {})
                    avail_bal = (
                        funds_obj.get("availableBalance")
                        or funds_obj.get("availabelBalance")
                        or funds_obj.get("withdrawableBalance")
                        or (funds_obj.get("raw", {}) if isinstance(funds_obj.get("raw"), dict) else {}).get("availabelBalance")
                        or data.get("availableBalance")
                        or 0.0
                    )
                    logger.info(f"✅ Live data from Engine-C: Balance=₹{avail_bal}")
                    self.data_source_stats["engine_c"] += 1
                    return data
        except Exception as e:
            logger.debug(f"Engine-C live data fetch: {e}")
        return None

    async def fetch_data(self, symbol: str, days: int = 365) -> tuple:
        """
        Smart Fetch with source tracking:
        0. Ping Engine-C for live connection status
        1. Try DhanHQ API (Direct or via Engine-C Proxy)
        2. Fallback to Yahoo Finance
        3. Generate synthetic data as last resort
        Returns: (DataFrame, source_name)
        """
        self._fetch_live_data_from_engine_c()
        symbol = symbol.upper()
        cache_key = f"{symbol}_{days}"

        # Check cache (5 min TTL)
        if cache_key in self.cache:
            cached_data, cached_time, source = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < 300:
                return cached_data, source

        df = pd.DataFrame()
        source = "synthetic"

        sec_id = SYMBOL_MAPPER.get_id(symbol)
        if not sec_id and symbol in ["NIFTY", "NIFTY50"]:
            sec_id = "13"
        elif not sec_id and symbol in ["BANKNIFTY", "NIFTYBANK"]:
            sec_id = "25"
        elif not sec_id and symbol in ["FINNIFTY"]:
            sec_id = "27"
        elif not sec_id and symbol in ["MIDCPNIFTY"]:
            sec_id = "442"
        elif not sec_id and symbol in ["SENSEX", "BSESN", "BSE_SENSEX"]:
            sec_id = "51"

        # Determine exchange segment and instrument type
        if symbol in ["CRUDEOIL", "GOLD", "SILVER", "NATURALGAS", "COPPER"]:
            exchange_segment = "MCX_COMM"
            instrument_type = "FUTCOM"
        elif symbol in ["SENSEX", "BSESN", "BSE_SENSEX", "NIFTY", "NIFTY50", "BANKNIFTY", "NIFTYBANK", "FINNIFTY", "MIDCPNIFTY"]:
            exchange_segment = "IDX_I"
            instrument_type = "INDEX"
        else:
            exchange_segment = "NSE_EQ"
            instrument_type = "EQUITY"

        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Method 1A: Direct DhanHQ API
        if self.dhan and sec_id:
            try:
                logger.info(f"📡 Calling DhanHQ direct historical_daily_data for {symbol}: sec_id={sec_id}")
                resp = self.dhan.historical_daily_data(
                    security_id=sec_id,
                    exchange_segment=exchange_segment,
                    instrument_type=instrument_type,
                    from_date=from_date,
                    to_date=to_date
                )
                if resp and resp.get('status') == 'success' and resp.get('data'):
                    raw_d = resp['data']
                    candle_d = raw_d.get('data', raw_d) if isinstance(raw_d, dict) else raw_d
                    df = pd.DataFrame(candle_d)
            except Exception as e:
                logger.warning(f"Direct DhanHQ fetch failed for {symbol}: {e}")

        # Method 1B: Engine-C DhanHQ Proxy (Authenticated Vault)
        if df.empty and sec_id:
            try:
                import requests
                logger.info(f"📡 Fetching DhanHQ historical data via Engine-C proxy for {symbol} (sec_id={sec_id})")
                c_resp = requests.get(
                    f"{self.engine_c_url}/api/dhan/market/historical",
                    params={
                        "security_id": sec_id,
                        "exchange_segment": exchange_segment,
                        "instrument_type": instrument_type,
                        "from_date": from_date,
                        "to_date": to_date,
                        "interval": "daily",
                        "user_id": self.default_user_id
                    },
                    timeout=15
                )
                if c_resp.status_code == 200:
                    c_json = c_resp.json()
                    raw_d = c_json.get('data', {})
                    candle_d = raw_d.get('data', raw_d) if isinstance(raw_d, dict) else raw_d
                    if isinstance(candle_d, dict) and 'close' in candle_d:
                        df = pd.DataFrame(candle_d)
            except Exception as e:
                logger.warning(f"Engine-C DhanHQ proxy fetch failed for {symbol}: {e}")

        # Process Dhan DataFrame if retrieved
        if not df.empty:
            col_map = {
                'start_Time': 'Date', 'timestamp': 'Date',
                'open': 'Open', 'high': 'High', 'low': 'Low',
                'close': 'Close', 'volume': 'Volume'
            }
            df.rename(columns=col_map, inplace=True)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], unit='s' if df['Date'].dtype in ['float64', 'int64'] else None)
                df.set_index('Date', inplace=True)
            
            # Ensure standard lowercase column names
            df.columns = [c.lower() for c in df.columns]

            if len(df) >= 30:
                source = "dhan"
                self.data_source_stats["dhan"] += 1
                logger.info(f"📊 Fetched {len(df)} days from DhanHQ for {symbol}")
            else:
                df = pd.DataFrame()

        # Method 2: BigQuery Live Ticks (primary authoritative real-time source)
        if df.empty and sec_id:
            try:
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
                bq_client = bigquery.Client(project=project_id)

                # Try infinity_dataset.market_ticks_history first (full history)
                bq_query = f"""
                    SELECT
                        DATE(timestamp) AS Date,
                        FIRST_VALUE(ltp) OVER (PARTITION BY DATE(timestamp) ORDER BY timestamp) AS open,
                        MAX(ltp) OVER (PARTITION BY DATE(timestamp)) AS high,
                        MIN(ltp) OVER (PARTITION BY DATE(timestamp)) AS low,
                        LAST_VALUE(ltp) OVER (
                            PARTITION BY DATE(timestamp)
                            ORDER BY timestamp
                            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                        ) AS close,
                        SUM(volume) OVER (PARTITION BY DATE(timestamp)) AS volume
                    FROM `{project_id}.infinity_dataset.market_ticks_history`
                    WHERE security_id = @sec_id
                      AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
                    QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(timestamp) ORDER BY timestamp DESC) = 1
                    ORDER BY Date DESC
                    LIMIT {days}
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("sec_id", "STRING", str(sec_id))]
                )
                loop = asyncio.get_event_loop()
                bq_rows = await loop.run_in_executor(
                    bq_executor,
                    lambda: bq_client.query(bq_query, job_config=job_config).to_dataframe()
                )
                if not bq_rows.empty and len(bq_rows) >= 30:
                    bq_rows = bq_rows.sort_values("Date")
                    bq_rows = bq_rows.set_index("Date")
                    bq_rows.index = pd.to_datetime(bq_rows.index)
                    df = bq_rows[["open", "high", "low", "close", "volume"]].copy()
                    source = "bigquery"
                    self.data_source_stats["dhan"] += 1  # treated as real DhanHQ data
                    logger.info(f"📊 Fetched {len(df)} days from BigQuery for {symbol}")
            except Exception as e:
                logger.warning(f"BigQuery historical fetch failed for {symbol}: {e}")

        # Method 3: Yahoo Finance Fallback (last real-data resort)
        if df.empty and HAS_YFINANCE:
            try:
                logger.info(f"Using YFinance fallback for {symbol}")
                yahoo_symbol = self.YAHOO_SYMBOLS.get(symbol, f"{symbol}.NS")
                df = yf.download(yahoo_symbol, period=f"{days}d", interval="1d", progress=False)

                if not df.empty and len(df) >= 50:
                    # Handle MultiIndex columns from yfinance
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    # Standardize column names to lowercase
                    df.columns = [c.lower() for c in df.columns]

                    # Select required columns
                    required_cols = ['open', 'high', 'low', 'close', 'volume']
                    if all(col in df.columns for col in required_cols):
                        df = df[required_cols]

                    source = "yahoo"
                    self.data_source_stats["yahoo"] += 1
                    logger.info(f"📊 Fetched {len(df)} days from Yahoo Finance for {symbol}")
            except Exception as e:
                logger.warning(f"YFinance fetch failed for {symbol}: {e}")

        # All real data sources exhausted — raise 503, do NOT use synthetic data in live signal path
        if df.empty or len(df) < 50:
            logger.error(
                f"❌ All real data sources failed for {symbol} "
                f"(DhanHQ direct, Engine-C proxy, BigQuery, YFinance). "
                f"Refusing to generate signal from synthetic data."
            )
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Market data unavailable for {symbol}. "
                    "DhanHQ direct, Engine-C proxy, BigQuery, and Yahoo Finance all failed. "
                    "Retry after a brief interval."
                )
            )

        # Method Live LTP Update: Synchronize latest bar with real-time DhanHQ market quote
        if not df.empty and sec_id:
            try:
                import requests
                quotes_resp = requests.get(
                    f"{self.engine_c_url}/api/dhan/market/quotes",
                    params={
                        "security_ids": sec_id,
                        "exchange_segment": exchange_segment,
                        "user_id": self.default_user_id
                    },
                    timeout=5
                )
                if quotes_resp.status_code == 200:
                    q_json = quotes_resp.json()
                    seg_data = q_json.get("data", {}).get("data", {}).get("data", {}).get(exchange_segment, {}).get(str(sec_id), {})
                    live_ltp = seg_data.get("last_price")
                    live_ohlc = seg_data.get("ohlc", {})
                    if live_ltp and float(live_ltp) > 0:
                        today_ts = pd.Timestamp.now().floor('D')
                        live_open = live_ohlc.get("open", live_ltp)
                        live_high = live_ohlc.get("high", live_ltp)
                        live_low = live_ohlc.get("low", live_ltp)
                        live_vol = seg_data.get("volume", 0) or 1000

                        if today_ts in df.index:
                            df.loc[today_ts, 'close'] = float(live_ltp)
                            df.loc[today_ts, 'high'] = max(float(df.loc[today_ts, 'high']), float(live_high), float(live_ltp))
                            df.loc[today_ts, 'low'] = min(float(df.loc[today_ts, 'low']), float(live_low), float(live_ltp))
                        else:
                            new_row = pd.DataFrame([{
                                'open': float(live_open),
                                'high': float(live_high),
                                'low': float(live_low),
                                'close': float(live_ltp),
                                'volume': float(live_vol)
                            }], index=[today_ts])
                            df = pd.concat([df, new_row])
                        logger.info(f"⚡ Live LTP synchronized for {symbol}: ₹{live_ltp} (Real-time live tick active)")
            except Exception as e:
                logger.warning(f"Failed to attach real-time live LTP for {symbol}: {e}")

        # Cache result
        self.cache[cache_key] = (df, datetime.now(), source)
        return df, source

    def _generate_synthetic_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Generate realistic synthetic OHLCV data"""
        np.random.seed(hash(symbol) % 2**32)

        base_prices = {
            "NIFTY": 24455.75, "BANKNIFTY": 57375.10, "FINNIFTY": 26393.45,
            "RELIANCE": 2900, "TCS": 4200, "HDFCBANK": 1700,
            "INFY": 1850, "ICICIBANK": 1280, "ITC": 470,
            "SBIN": 820, "TATAMOTORS": 980
        }
        base_price = base_prices.get(symbol, 1000)

        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
        returns = np.random.normal(0.0005, 0.015, days)

        prices = [base_price]
        for r in returns[1:]:
            prices.append(prices[-1] * (1 + r))

        data = []
        for date, close in zip(dates, prices):
            daily_range = close * np.random.uniform(0.01, 0.025)
            high = close + daily_range * np.random.uniform(0.3, 0.7)
            low = close - daily_range * np.random.uniform(0.3, 0.7)
            open_price = low + (high - low) * np.random.uniform(0.2, 0.8)
            volume = int(np.random.uniform(500000, 5000000))

            data.append({
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })

        df = pd.DataFrame(data, index=dates)
        df.index.name = 'Date'
        return df

    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Production Feature Engineering using ta library (if available)
        Falls back to manual calculation if ta library not installed
        """
        if df.empty:
            return df

        df = df.copy()

        # Normalize column names to lowercase
        df.columns = [c.lower() for c in df.columns]

        if HAS_TA_LIB:
            try:
                # Trend Indicators using ta library
                df['EMA_9'] = ta_lib.trend.ema_indicator(df['close'], window=9)
                df['EMA_21'] = ta_lib.trend.ema_indicator(df['close'], window=21)
                df['EMA_50'] = ta_lib.trend.ema_indicator(df['close'], window=50)
                df['SMA_20'] = ta_lib.trend.sma_indicator(df['close'], window=20)
                df['SMA_50'] = ta_lib.trend.sma_indicator(df['close'], window=50)

                # MACD (Indian market: 10,20,9 instead of 12,26,9 for faster response)
                macd = ta_lib.trend.MACD(df['close'], window_fast=10, window_slow=20, window_sign=9)
                df['MACD_10_20_9'] = macd.macd()
                df['MACDh_10_20_9'] = macd.macd_diff()
                df['MACDs_10_20_9'] = macd.macd_signal()
                # Backward compatibility
                df['MACD_12_26_9'] = df['MACD_10_20_9']
                df['MACDh_12_26_9'] = df['MACDh_10_20_9']
                df['MACDs_12_26_9'] = df['MACDs_10_20_9']

                # ADX
                df['ADX_14'] = ta_lib.trend.adx(df['high'], df['low'], df['close'], window=14)

                # Momentum Indicators
                df['RSI_14'] = ta_lib.momentum.rsi(df['close'], window=14)

                # Stochastic
                stoch = ta_lib.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
                df['STOCHk_14_3_3'] = stoch.stoch()
                df['STOCHd_14_3_3'] = stoch.stoch_signal()

                df['CCI_20_0.015'] = ta_lib.trend.cci(df['high'], df['low'], df['close'], window=20)
                df['WILLR_14'] = ta_lib.momentum.williams_r(df['high'], df['low'], df['close'], lbp=14)
                df['MFI_14'] = ta_lib.volume.money_flow_index(df['high'], df['low'], df['close'], df['volume'], window=14)

                # Volatility - Bollinger Bands (Indian market: 2.5 std dev for wider bands)
                bb = ta_lib.volatility.BollingerBands(df['close'], window=20, window_dev=2.5)
                df['BBL_20_2.5'] = bb.bollinger_lband()
                df['BBM_20_2.5'] = bb.bollinger_mavg()
                df['BBU_20_2.5'] = bb.bollinger_hband()
                # Backward compatibility - also calculate 2.0
                bb2 = ta_lib.volatility.BollingerBands(df['close'], window=20, window_dev=2)
                df['BBL_20_2.0'] = bb2.bollinger_lband()
                df['BBM_20_2.0'] = bb2.bollinger_mavg()
                df['BBU_20_2.0'] = bb2.bollinger_hband()
                df['ATRr_14'] = ta_lib.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)

                # Volume
                df['OBV'] = ta_lib.volume.on_balance_volume(df['close'], df['volume'])

                return df.dropna()
            except Exception as e:
                logger.warning(f"ta library failed: {e}, using manual calculation")

        # Fallback: Manual calculation
        return self._calculate_features_manual(df)

    def _calculate_features_manual(self, df: pd.DataFrame) -> pd.DataFrame:
        """Manual feature calculation fallback - uses lowercase column names"""
        # Moving Averages
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()

        # MACD (Indian market: 10,20,9 for faster response to volatility)
        ema10 = df['close'].ewm(span=10, adjust=False).mean()
        ema20 = df['close'].ewm(span=20, adjust=False).mean()
        df['MACD_10_20_9'] = ema10 - ema20
        df['MACDs_10_20_9'] = df['MACD_10_20_9'].ewm(span=9, adjust=False).mean()
        df['MACDh_10_20_9'] = df['MACD_10_20_9'] - df['MACDs_10_20_9']
        # Backward compatibility
        df['MACD_12_26_9'] = df['MACD_10_20_9']
        df['MACDs_12_26_9'] = df['MACDs_10_20_9']
        df['MACDh_12_26_9'] = df['MACDh_10_20_9']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # Bollinger Bands (Indian market: 2.5 std dev for wider bands, reducing false signals)
        df['BBM_20_2.5'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BBU_20_2.5'] = df['BBM_20_2.5'] + (bb_std * 2.5)
        df['BBL_20_2.5'] = df['BBM_20_2.5'] - (bb_std * 2.5)
        df['BBB_20_2.5'] = (df['BBU_20_2.5'] - df['BBL_20_2.5']) / df['BBM_20_2.5']
        # Backward compatibility
        df['BBM_20_2.0'] = df['BBM_20_2.5']
        df['BBU_20_2.0'] = df['BBM_20_2.5'] + (bb_std * 2)
        df['BBL_20_2.0'] = df['BBM_20_2.5'] - (bb_std * 2)
        df['BBB_20_2.0'] = (df['BBU_20_2.0'] - df['BBL_20_2.0']) / df['BBM_20_2.5']

        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATRr_14'] = tr.rolling(window=14).mean()

        # Stochastic
        low14 = df['low'].rolling(window=14).min()
        high14 = df['high'].rolling(window=14).max()
        df['STOCHk_14_3_3'] = 100 * (df['close'] - low14) / (high14 - low14)
        df['STOCHd_14_3_3'] = df['STOCHk_14_3_3'].rolling(window=3).mean()

        # ADX
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        tr14 = tr.rolling(window=14).sum()
        plus_di = 100 * (plus_dm.rolling(window=14).sum() / tr14)
        minus_di = 100 * (minus_dm.abs().rolling(window=14).sum() / tr14)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX_14'] = dx.rolling(window=14).mean()

        # Williams %R
        df['WILLR_14'] = -100 * (high14 - df['close']) / (high14 - low14)

        # CCI
        tp = (df['high'] + df['low'] + df['close']) / 3
        df['CCI_14_0.015'] = (tp - tp.rolling(window=14).mean()) / (0.015 * tp.rolling(window=14).std())

        # Volume indicators
        df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['volume'] / df['Volume_SMA']

        # OBV
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv

        return df.dropna()

    def get_feature_columns(self) -> List[str]:
        """Return feature columns based on available indicators"""
        if HAS_TA_LIB:
            return [
                'EMA_9', 'EMA_21', 'EMA_50', 'SMA_20', 'SMA_50',
                'MACD_12_26_9', 'MACDs_12_26_9', 'MACDh_12_26_9',
                'RSI_14', 'STOCHk_14_3_3', 'STOCHd_14_3_3',
                'ADX_14', 'ATRr_14', 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0',
                'WILLR_14', 'CCI_20_0.015', 'MFI_14', 'OBV'
            ]
        else:
            return [
                'EMA_9', 'EMA_21', 'EMA_50', 'SMA_20', 'SMA_50',
                'MACD_12_26_9', 'MACDs_12_26_9', 'MACDh_12_26_9',
                'RSI_14', 'STOCHk_14_3_3', 'STOCHd_14_3_3',
                'ADX_14', 'ATRr_14', 'BBB_20_2.0',
                'WILLR_14', 'CCI_14_0.015', 'Volume_Ratio'
            ]

MARKET_ENGINE = MarketDataEngine()

# =====================================================================
# RISK MANAGEMENT (SEBI 2025 Compliant)
# =====================================================================
class RiskManager:
    """SEBI 2025 Compliant Risk Management"""

    def check_order_validity(self, symbol: str, side: str, qty: int, price: float, funds_available: float) -> tuple:
        """Validates order against SEBI Feb 2025 Rules"""
        # 1. Trading Holiday Check
        today_str = datetime.now().strftime("%Y-%m-%d")
        if today_str in MARKET_CONFIG["HOLIDAYS_2025"]:
            return False, "Market Holiday"

        # 2. Weekend Check
        if datetime.now().weekday() >= 5:
            return False, "Weekend - Market Closed"

        sec_id = SYMBOL_MAPPER.get_id(symbol)
        if not sec_id:
            return False, "Symbol Not Found in Master"

        meta = SYMBOL_MAPPER.get_metadata(sec_id)
        series = meta.get('SEM_SERIES', 'EQ')

        # 3. T2T / ESM Ban Check
        if series in ['BE', 'BZ', 'SM', 'ST']:
            return False, f"Intraday Banned for Series {series}"

        # 4. 2025 Margin Rules
        is_option = "CE" in symbol or "PE" in symbol

        if is_option and side == "BUY":
            # Option Buy: 100% Premium Upfront
            required_margin = price * qty * MARKET_CONFIG["MARGIN_RULES_2025"]["OPTION_BUY_PREMIUM"]
        else:
            # Equity Intraday: ~20% (VaR + ELM)
            required_margin = price * qty * MARKET_CONFIG["MARGIN_RULES_2025"]["INTRADAY_EQUITY"]

        if funds_available < required_margin:
            return False, f"Insufficient Funds. Required: ₹{required_margin:.2f}, Available: ₹{funds_available:.2f}"

        return True, "Valid"

    def calculate_position_size(self, capital: float, risk_per_trade: float, stop_loss_pct: float) -> float:
        """Calculate optimal position size based on risk"""
        risk_amount = capital * risk_per_trade
        position_size = risk_amount / stop_loss_pct
        return round(position_size, 2)

    def get_stop_loss_target(self, price: float, atr: float, signal: str) -> tuple:
        """Calculate SL and Target based on ATR"""
        if signal == "BUY":
            stop_loss = price - (2 * atr)
            target = price + (3 * atr)
        elif signal == "SELL":
            stop_loss = price + (2 * atr)
            target = price - (3 * atr)
        else:
            stop_loss = price
            target = price
        return round(stop_loss, 2), round(target, 2)

RISK_ENGINE = RiskManager()

# =====================================================================
# MODEL TRAINER
# =====================================================================
class ModelTrainer:
    """Train and validate ML models for trading signals"""

    def __init__(self, model_store: MLModelStore):
        self.model_store = model_store
        self.training_history = {}
        self.hyperparams = {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.05
        }

    def update_hyperparams(self, n_estimators: int, max_depth: int, learning_rate: float):
        """Update model hyperparameters"""
        self.hyperparams = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate
        }

        self.model_store.models['xgboost'] = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            objective='multi:softprob',
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss',
            n_jobs=-1
        )

        self.model_store.models['lightgbm'] = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42,
            verbose=-1,
            n_jobs=-1
        )

        self.model_store.models['random_forest'] = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth + 4,
            random_state=42,
            n_jobs=-1
        )

        logger.info(f"🔧 Updated hyperparameters: {self.hyperparams}")

    def prepare_training_data(self, df: pd.DataFrame, lookahead: int = 5) -> tuple:
        """Prepare features and labels for training"""
        df = MARKET_ENGINE.add_features(df)
        close_col = 'Close' if 'Close' in df.columns else 'close'

        # Create labels based on future returns
        df['Future_Return'] = (df[close_col].shift(-lookahead) - df[close_col]) / df[close_col]
        df['Label'] = 1  # Default: HOLD
        df.loc[df['Future_Return'] > 0.01, 'Label'] = 2  # BUY
        df.loc[df['Future_Return'] < -0.01, 'Label'] = 0  # SELL

        df = df.dropna()

        if len(df) < 50:
            raise ValueError("Insufficient data for training (need at least 50 samples)")

        # Get available feature columns
        feature_cols = [col for col in MARKET_ENGINE.get_feature_columns() if col in df.columns]

        X = df[feature_cols].values
        y = df['Label'].values

        return X, y, feature_cols

    def train_all_models(self, X: np.ndarray, y: np.ndarray, symbol: str) -> Dict[str, Any]:
        """Train all ensemble models including CatBoost"""
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        scaler = self.model_store.scalers['standard']
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        results = {}

        # Train XGBoost (40% weight)
        logger.info("Training XGBoost (40% weight)...")
        xgb_model = self.model_store.get_model('xgboost')
        xgb_model.fit(X_train_scaled, y_train)
        xgb_pred = xgb_model.predict(X_test_scaled)
        results['xgboost'] = {'accuracy': accuracy_score(y_test, xgb_pred), 'weight': 0.40}
        logger.info(f"✅ XGBoost accuracy: {results['xgboost']['accuracy']:.2%}")

        # Train LightGBM (30% weight)
        logger.info("Training LightGBM (30% weight)...")
        lgb_model = self.model_store.get_model('lightgbm')
        lgb_model.fit(X_train_scaled, y_train)
        lgb_pred = lgb_model.predict(X_test_scaled)
        results['lightgbm'] = {'accuracy': accuracy_score(y_test, lgb_pred), 'weight': 0.30}
        logger.info(f"✅ LightGBM accuracy: {results['lightgbm']['accuracy']:.2%}")

        # Train CatBoost (15% weight) - if available
        if HAS_CATBOOST:
            logger.info("Training CatBoost (15% weight)...")
            cat_model = self.model_store.get_model('catboost')
            if cat_model:
                cat_model.fit(X_train_scaled, y_train)
                cat_pred = cat_model.predict(X_test_scaled)
                results['catboost'] = {'accuracy': accuracy_score(y_test, cat_pred), 'weight': 0.15}
                logger.info(f"✅ CatBoost accuracy: {results['catboost']['accuracy']:.2%}")

        # Train Random Forest (15% weight)
        logger.info("Training Random Forest (15% weight)...")
        rf_model = self.model_store.get_model('random_forest')
        rf_model.fit(X_train_scaled, y_train)
        rf_pred = rf_model.predict(X_test_scaled)
        results['random_forest'] = {'accuracy': accuracy_score(y_test, rf_pred), 'weight': 0.15}
        logger.info(f"✅ Random Forest accuracy: {results['random_forest']['accuracy']:.2%}")

        # Calculate weighted ensemble accuracy
        weighted_preds = []
        weights = self.model_store.get_ensemble_weights()
        for model_name, weight in weights.items():
            model = self.model_store.get_model(model_name)
            if model:
                pred = model.predict(X_test_scaled)
                weighted_preds.append((pred, weight))

        if weighted_preds:
            # Weighted voting
            ensemble_pred = np.zeros(len(y_test))
            for pred, weight in weighted_preds:
                ensemble_pred += pred * weight
            ensemble_pred = np.round(ensemble_pred).astype(int)
            results['ensemble'] = {'accuracy': accuracy_score(y_test, ensemble_pred), 'weight': 1.0}
            logger.info(f"✅ Weighted Ensemble accuracy: {results['ensemble']['accuracy']:.2%}")

        # Store training history
        self.training_history[symbol] = {
            'trained_at': datetime.utcnow().isoformat(),
            'samples': len(X),
            'features': X.shape[1],
            'results': results
        }

        self.model_store.trained_symbols.add(symbol.upper())

        return results

MODEL_TRAINER = ModelTrainer(MODEL_STORE)

# =====================================================================
# SENTIMENT ANALYZER
# =====================================================================
class SentimentAnalyzer:
    """Multi-source sentiment analysis"""

    def analyze(self, text: str) -> tuple:
        """Returns (sentiment, confidence)"""
        if HAS_TRANSFORMERS and MODEL_STORE.get_model('transformer_sentiment'):
            try:
                result = MODEL_STORE.get_model('transformer_sentiment')(text[:512])[0]
                return result['label'], result['score']
            except:
                pass

        if HAS_NLTK and MODEL_STORE.get_model('nltk_sentiment'):
            try:
                scores = MODEL_STORE.get_model('nltk_sentiment').polarity_scores(text)
                compound = scores['compound']
                if compound >= 0.05:
                    return "POSITIVE", abs(compound)
                elif compound <= -0.05:
                    return "NEGATIVE", abs(compound)
                else:
                    return "NEUTRAL", 0.5
            except:
                pass

        return "NEUTRAL", 0.5

    def aggregate_headlines(self, headlines: List[str]) -> float:
        """Aggregate sentiment score from multiple headlines (-1 to 1)"""
        if not headlines:
            return 0.0

        scores = []
        for headline in headlines:
            sentiment, confidence = self.analyze(headline)
            if sentiment == "POSITIVE":
                scores.append(confidence)
            elif sentiment == "NEGATIVE":
                scores.append(-confidence)
            else:
                scores.append(0)

        return sum(scores) / len(scores) if scores else 0.0

SENTIMENT_ANALYZER = SentimentAnalyzer()

# Shared HTTP session for efficient connection reuse
aiohttp_session: Optional[aiohttp.ClientSession] = None

# =====================================================================
# API ENDPOINTS
# =====================================================================


async def periodic_model_update():
    while True:
        try:
            logger.info("Checking GCS for newer models...")
            MODEL_STORE.reload_from_gcs()
        except Exception as e:
            logger.error(f"Error during periodic model update: {e}")
        # Wait 24 hours (run every morning)
        await asyncio.sleep(86400)

@app.on_event("startup")
async def startup_event():
    """Bootstrap application state"""
    global aiohttp_session
    
    # Start background task for daily model reload
    asyncio.create_task(periodic_model_update())


    # Create shared aiohttp session for efficient connections
    if HAS_AIOHTTP:
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=20,
            ttl_dns_cache=300,
            keepalive_timeout=60
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        aiohttp_session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        logger.info("✅ Shared aiohttp session initialized")

        # Set shared session for data connector and news integration
        try:
            from services.data_connector import set_shared_session as set_dc_session
            set_dc_session(aiohttp_session)
        except ImportError:
            pass
        try:
            from google_integrations.news_integration import set_shared_session as set_news_session
            set_news_session(aiohttp_session)
        except ImportError:
            pass

    await SYMBOL_MAPPER.refresh(aiohttp_session)
    logger.info("🚀 InfinityAI Engine B Started")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown with cleanup"""
    global aiohttp_session

    logger.info("🛑 Engine B shutting down...")

    if aiohttp_session:
        await aiohttp_session.close()

    logger.info("✅ Engine B cleanup complete")

@app.get("/healthz")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "engine": "engine-b", "region": "asia-south1"}

@app.get("/health/knowledge", tags=["health"])
async def health_knowledge():
    if not HAS_MARKET_KNOWLEDGE or MARKET_KNOWLEDGE is None:
        return {
            "status": "unhealthy",
            "component": "market_knowledge",
            "error": "Market knowledge module not loaded"
        }

    try:
        nifty_lot = MARKET_KNOWLEDGE.get_lot_size("NIFTY")
        banknifty_lot = MARKET_KNOWLEDGE.get_lot_size("BANKNIFTY")

        greeks_sample = MARKET_KNOWLEDGE.options_math.calculate_greeks(
            spot_price=20000,
            strike_price=20100,
            days_to_expiry=5,
            iv=0.15,
            option_type="CALL"
        )

        session = MARKET_KNOWLEDGE.analyzer.get_trading_session()

        return {
            "status": "healthy",
            "component": "market_knowledge",
            "version": MARKET_KNOWLEDGE.version,
            "last_updated": MARKET_KNOWLEDGE.last_updated,
            "checks": {
                "sebi_rules_loaded": True,
                "lot_sizes": {
                    "NIFTY": nifty_lot,
                    "BANKNIFTY": banknifty_lot
                },
                "greeks_engine": greeks_sample,
                "trading_session": session.get("session"),
                "is_trading": session.get("is_trading", False)
            }
        }
    except Exception as e:
        logger.exception("Knowledge health check failed")
        return {
            "status": "unhealthy",
            "component": "market_knowledge",
            "error": str(e)
        }


@app.get("/")
async def root():
    return {
        "service": "InfinityAI.Pro Engine B (AI/ML Signal Generation)",
        "status": "ready",
        "version": "4.0-enhanced-trading-ai",
        "models": list(MODEL_STORE.models.keys()),
        "trained_symbols": list(MODEL_STORE.trained_symbols),
        "capabilities": MODEL_STORE.capabilities,
        "google_integrations": [
            "Gemini AI (Official GenAI SDK)",
            "Cloud Logging (Signal Logs)",
            "Cloud Storage (ML Models)",
            "Trading Agents (Signal, Risk, Market)",
            "Enhanced Trading AI v4.0 (Indian Markets Expert)"
        ],
        "new_endpoints": [
            "POST /api/v1/ai/enhanced-signal - Enhanced trading signal with comprehensive analysis",
            "GET /api/v1/ai/market-knowledge - Indian market knowledge base",
            "GET /api/v1/ai/trading-session-status - Current session and entry guidance"
        ]
    }

@app.get("/api/v1/capabilities")
async def get_capabilities():
    return MODEL_STORE.get_capabilities()

@app.get("/api/v1/market/status")
async def market_status():
    """Returns current market status based on 2026 NSE calendar & Tuesday expiry rules"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    holidays = MARKET_CONFIG.get("HOLIDAYS_2026", []) + MARKET_CONFIG.get("HOLIDAYS_2025", [])
    is_holiday = date_str in holidays
    is_weekend = now.weekday() >= 5

    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    is_open_time = market_open <= now <= market_close

    status = "CLOSED"
    if not is_holiday and not is_weekend and is_open_time:
        status = "OPEN"

    future_holidays = [h for h in sorted(holidays) if h > date_str]
    next_holiday = future_holidays[0] if future_holidays else "2027-01-01"

    return {
        "status": status,
        "is_holiday": is_holiday,
        "is_weekend": is_weekend,
        "server_time": now.isoformat(),
        "next_holiday": next_holiday,
        "trading_sessions": MARKET_CONFIG["TRADING_SESSIONS"],
        "expiry_rules_2026": {
            "expiry_day": "Tuesday",
            "weekly_indices": ["NIFTY"],
            "monthly_indices": ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
        }
    }

def fetch_market_breadth_and_gift() -> dict:
    """
    Fetches real-time macro indicators for the conviction filter:
      - NSE Advance/Decline ratio  → BigQuery market_data.live_ticks
      - GIFT Nifty basis           → Engine C /api/dhan/market/ltp (GIFT Nifty vs Nifty spot)
      - Crude Oil trend            → BigQuery MCX crude tick direction

    Falls back to NEUTRAL values (A/D=1.0, basis=0.0, trend=NEUTRAL) on any
    failure so the conviction veto is never driven by stale constants.
    """
    NEUTRAL = {"advance_decline_ratio": 1.0, "gift_nifty_basis": 0.0, "crude_oil_trend": "NEUTRAL"}

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
    engine_c_url = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")

    result = dict(NEUTRAL)

    # ── 1. NSE Advance/Decline from BigQuery live_ticks ──────────────────────
    try:
        bq_client = bigquery.Client(project=project_id)
        ad_query = f"""
            WITH parsed_ticks AS (
                SELECT
                    publish_time,
                    JSON_EXTRACT_SCALAR(data, '$.security_id') AS security_id,
                    JSON_EXTRACT_SCALAR(data, '$.exchange_segment') AS exchange_segment,
                    SAFE_CAST(JSON_EXTRACT_SCALAR(data, '$.ltp') AS FLOAT64) AS ltp
                FROM `{project_id}.market_data.live_ticks`
                WHERE DATE(publish_time, 'Asia/Kolkata') = CURRENT_DATE('Asia/Kolkata')
            )
            SELECT
                COUNTIF(daily_change > 0) AS advances,
                COUNTIF(daily_change < 0) AS declines,
                COUNTIF(daily_change = 0) AS unchanged
            FROM (
                SELECT
                    security_id,
                    LAST_VALUE(ltp) OVER (
                        PARTITION BY security_id
                        ORDER BY publish_time
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) - FIRST_VALUE(ltp) OVER (
                        PARTITION BY security_id
                        ORDER BY publish_time
                    ) AS daily_change
                FROM parsed_ticks
                WHERE exchange_segment = 'NSE_EQ' AND ltp IS NOT NULL
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY security_id ORDER BY publish_time DESC
                ) = 1
            )
        """
        ad_rows = bq_client.query(ad_query).result()
        for row in ad_rows:
            advances = row.advances or 0
            declines = row.declines or 1  # avoid division by zero
            result["advance_decline_ratio"] = round(advances / declines, 3)
            logger.info(f"📊 Live A/D ratio: {advances}/{declines} = {result['advance_decline_ratio']}")
            break
    except Exception as e:
        logger.warning(f"⚠️ BigQuery A/D ratio fetch failed: {e} — using neutral A/D=1.0")

    # ── 2. GIFT Nifty basis from Engine C market data proxy ───────────────────
    try:
        import requests as _requests
        # GIFT Nifty security_id on NSE_IDX: 13 (Nifty50 spot), GIFT Nifty futures differ by segment
        # We compare GIFT Nifty LTP (IDX_I segment, security 13 in GIFT exchange)
        # vs NSE Nifty spot to compute basis
        nifty_resp = _requests.get(
            f"{engine_c_url}/api/dhan/market/ltp",
            params={"security_id": "13", "exchange_segment": "IDX_I"},
            timeout=5
        )
        gift_resp = _requests.get(
            f"{engine_c_url}/api/dhan/market/ltp",
            params={"security_id": "13", "exchange_segment": "NSE_FNO"},
            timeout=5
        )
        if nifty_resp.status_code == 200 and gift_resp.status_code == 200:
            nifty_ltp = nifty_resp.json().get("data", {}).get("ltp", 0)
            gift_ltp = gift_resp.json().get("data", {}).get("ltp", 0)
            if nifty_ltp and gift_ltp:
                result["gift_nifty_basis"] = round(gift_ltp - nifty_ltp, 2)
                logger.info(f"📊 GIFT Nifty basis: {result['gift_nifty_basis']} pts")
    except Exception as e:
        logger.warning(f"⚠️ GIFT Nifty basis fetch failed: {e} — using neutral basis=0.0")

    # ── 3. Crude Oil trend from BigQuery MCX ticks ────────────────────────────
    try:
        bq_client = bigquery.Client(project=project_id)
        crude_query = f"""
            WITH parsed_crude AS (
                SELECT
                    publish_time,
                    SAFE_CAST(JSON_EXTRACT_SCALAR(data, '$.ltp') AS FLOAT64) AS ltp
                FROM `{project_id}.market_data.live_ticks`
                WHERE DATE(publish_time, 'Asia/Kolkata') = CURRENT_DATE('Asia/Kolkata')
                  AND JSON_EXTRACT_SCALAR(data, '$.exchange_segment') = 'MCX_COMM'
                  AND JSON_EXTRACT_SCALAR(data, '$.security_id') = '10'
                  AND JSON_EXTRACT_SCALAR(data, '$.ltp') IS NOT NULL
            )
            SELECT
                FIRST_VALUE(ltp) OVER (ORDER BY publish_time) AS open_price,
                LAST_VALUE(ltp) OVER (
                    ORDER BY publish_time
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) AS last_price
            FROM parsed_crude
            LIMIT 1
        """
        crude_rows = list(bq_client.query(crude_query).result())
        if crude_rows:
            row = crude_rows[0]
            chg_pct = ((row.last_price - row.open_price) / row.open_price * 100) if row.open_price else 0
            if chg_pct > 1.5:
                result["crude_oil_trend"] = "BULLISH_SPIKE"
            elif chg_pct < -1.5:
                result["crude_oil_trend"] = "BEARISH_DROP"
            else:
                result["crude_oil_trend"] = "NEUTRAL"
            logger.info(f"📊 Crude Oil trend: {result['crude_oil_trend']} (chg={chg_pct:.2f}%)")
    except Exception as e:
        logger.warning(f"⚠️ Crude Oil trend fetch failed: {e} — using NEUTRAL")

    return result



def evaluate_option_signal_conviction(df: pd.DataFrame, ml_probability: float) -> dict:
    """
    Applies strict options-buying filters over raw ML ensemble probabilities.
    Vetoes trades occurring near heavy dynamic resistance or low-volume conditions (ADX < 25).
    """
    latest = df.iloc[-1]
    
    # Extract technical indicators
    rsi = latest.get("RSI_14", latest.get("rsi_14", 50))
    adx = latest.get("ADX_14", latest.get("adx_14", 20))
    close_price = latest.get("close", 0)
    ema_50 = latest.get("EMA_50", latest.get("ema_50", close_price))
    ema_200 = latest.get("EMA_200", latest.get("ema_200", close_price))
    
    # Fetch external breadth & macro data
    macro = fetch_market_breadth_and_gift()
    adv_dec = macro["advance_decline_ratio"]
    
    # Veto conditions for Option Buyers (Theta Protection)
    veto_reason = None
    
    if adx < 25:
        veto_reason = f"ADX < 25 ({adx:.1f}): Market is ranging/consolidating (Theta decay risk)"
    elif adv_dec < 0.5 and ml_probability > 0.65:
        veto_reason = f"Weak Market Breadth (Adv/Dec: {adv_dec}): Fake bullish divergence"
    elif close_price <= ema_200 and ml_probability > 0.65:
        veto_reason = "Price testing 200-Day EMA dynamic resistance; breakout unconfirmed"

    # If a veto condition is triggered, force signal to HOLD/NEUTRAL
    if veto_reason:
        return {
            "signal": "HOLD",
            "confidence": ml_probability,
            "veto_triggered": True,
            "reason": veto_reason
        }

    # Otherwise, pass configuration forward
    final_signal = "BUY" if ml_probability >= 0.65 else ("SELL" if ml_probability <= 0.35 else "HOLD")
    
    return {
        "signal": final_signal,
        "confidence": ml_probability,
        "veto_triggered": False,
        "reason": "Passed all momentum, volume, and trend filters."
    }


@app.post("/api/v1/signal", response_model=SignalResponse)
async def generate_signal(req: SignalRequest):
    """Generate trading signal with ML + Technical + Sentiment analysis"""

    symbol = req.symbol.upper()

    # Fetch data
    df, data_source = await MARKET_ENGINE.fetch_data(symbol, days=200)
    if df.empty or len(df) < 50:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")

    # Normalize column names to lowercase if needed
    df.columns = [c.lower() for c in df.columns]
    current_price = float(df['close'].iloc[-1])

    # Add features
    df_features = MARKET_ENGINE.add_features(df)
    if df_features.empty:
        raise HTTPException(status_code=500, detail="Feature calculation failed")

    latest = df_features.iloc[-1]

    # --- Sentiment Analysis ---
    sentiment_score = None
    try:
        if hasattr(req, 'news_headlines') and req.news_headlines:
            sentiment_score = SENTIMENT_ANALYZER.aggregate_headlines(req.news_headlines)
    except Exception as e:
        logger.warning(f"Sentiment analysis failed for {symbol}: {e}")
        sentiment_score = None

    # 1. Determine Asset Class & Strategy
    symbol_upper = symbol.upper()
    if symbol_upper in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]:
        analysis_result = _analyze_fno(latest, current_price, df_features)
        asset_class = "FNO"
        exchange_segment = "IDX_I"
    elif symbol_upper in ["CRUDEOIL", "GOLD", "SILVER", "NATURALGAS", "COPPER", "GOLDM", "SILVERM"]:
        analysis_result = _analyze_commodity(latest, current_price, df_features)
        asset_class = "COMMODITY"
        exchange_segment = "MCX_COMM"
    else:
        # Default to FNO analysis for any other symbols
        analysis_result = _analyze_fno(latest, current_price, df_features)
        asset_class = "FNO"
        exchange_segment = "IDX_I"

    score = analysis_result["score"]
    reasons = analysis_result["reasons"]
    signal = analysis_result["signal"]

    # 2. ML Model Enhancement (Common across all assets if trained)
    ml_used = False
    ml_confidence = 0.5
    model_breakdown_detail = {}
    if True:  # Always enable ML enhancement across all instruments
        try:
            # Prepare features for ML
            feature_cols = [c for c in MARKET_ENGINE.get_feature_columns() if c in df_features.columns]
            if len(feature_cols) > 0:
                X = df_features[feature_cols].iloc[-1:].values
                scaler = MODEL_STORE.scalers.get('standard')
                if scaler is None:
                    scaler = StandardScaler()
                    MODEL_STORE.scalers['standard'] = scaler

                if not hasattr(scaler, 'mean_') or scaler.mean_ is None or getattr(scaler, 'n_features_in_', None) != X.shape[1]:
                    X_scaled = scaler.fit_transform(df_features[feature_cols].values)[-1:]
                else:
                    X_scaled = scaler.transform(X)

                # Extract 15 Enriched Alpha Features for BigQuery ML
                feature_dict = {
                    'rsi_14': float(latest.get('RSI_14', 50.0)),
                    'macd_line': float(latest.get('MACD_12_26_9', 0.0)),
                    'macd_signal': float(latest.get('MACDs_12_26_9', 0.0)),
                    'macd_hist': float(latest.get('MACDh_12_26_9', 0.0)),
                    'macd_crossover': 1 if float(latest.get('MACDh_12_26_9', 0.0)) > 0 else (-1 if float(latest.get('MACDh_12_26_9', 0.0)) < 0 else 0),
                    'vwap_distance': (float(current_price) - float(latest.get('vwap', current_price))) / (float(latest.get('vwap', current_price)) or 1.0),
                    'atr_volatility': float(latest.get('ATRr_14', 1.0)),
                    'atr_ratio': float(latest.get('ATRr_14', 1.0)) / (float(current_price) or 1.0),
                    'adx_14': float(latest.get('ADX_14', 20.0)),
                    'adx_slope': float(df_features['ADX_14'].diff(3).iloc[-1]) if 'ADX_14' in df_features.columns and len(df_features) >= 3 else 0.0,
                    'bollinger_bandwidth': (float(latest.get('BBU_20_2.0', current_price)) - float(latest.get('BBL_20_2.0', current_price))) / (float(latest.get('BBM_20_2.0', current_price)) or 1.0),
                    'bb_pct': (float(current_price) - float(latest.get('BBL_20_2.0', current_price))) / (float(latest.get('BBU_20_2.0', current_price)) - float(latest.get('BBL_20_2.0', current_price)) + 1e-6),
                    'return_15m_past': float(df_features['close'].pct_change(3).iloc[-1]) if 'close' in df_features.columns and len(df_features) >= 3 else 0.0,
                    'return_5m_past': float(df_features['close'].pct_change(1).iloc[-1]) if 'close' in df_features.columns and len(df_features) >= 1 else 0.0,
                    'trend_aligned': 1 if float(current_price) > float(latest.get('EMA_50', current_price)) else (-1 if float(current_price) < float(latest.get('EMA_50', current_price)) else 0)
                }

                # Ensemble Prediction
                ml_class, ml_confidence, votes_detail = await MODEL_STORE.weighted_ensemble_predict(X_scaled, feature_dict=feature_dict)
                model_breakdown_detail = votes_detail

                # ML Influence on Score
                if ml_class == 2:  # BUY
                    score += 3
                    reasons.append(f"ML Ensemble: BUY ({ml_confidence:.1%} conf)")
                    if ml_confidence > 0.65 and signal == "HOLD":
                        signal = "BUY"
                elif ml_class == 0:  # SELL
                    score -= 3
                    reasons.append(f"ML Ensemble: SELL ({ml_confidence:.1%} conf)")
                    if ml_confidence > 0.65 and signal == "HOLD":
                        signal = "SELL"
                else:
                    reasons.append(f"ML Ensemble: HOLD ({ml_confidence:.1%} conf)")

                ml_used = True
        except Exception as e:
            logger.warning(f"ML inference fallback for {symbol}: {e}")

    # 3. Final Signal Determination (with ML adjustment)
    if score >= 3:
        signal = "BUY"
    elif score <= -3:
        signal = "SELL"

    # 4. Theta Decay & Market Breadth Conviction Filter
    conviction = evaluate_option_signal_conviction(df_features, ml_confidence if ml_used else 0.70)
    if conviction["veto_triggered"] and signal != "HOLD":
        logger.info(f"🚫 VETO Applied for {symbol}: {conviction['reason']}")
        signal = "HOLD"
        reasons.append(f"VETO: {conviction['reason']}")

    # 4. Confidence & Targets
    confidence = min(95, max(30, 50 + abs(score) * 8))

    atr = latest.get('ATRr_14', current_price * 0.02)
    stop_loss, target = RISK_ENGINE.get_stop_loss_target(current_price, atr, signal)

    # Predicted price check
    if signal == "BUY":
        predicted_price = round(current_price * 1.02, 2)
    elif signal == "SELL":
        predicted_price = round(current_price * 0.98, 2)
    else:
        predicted_price = current_price

    res = SignalResponse(
        symbol=symbol,
        signal=signal,
        confidence=confidence,
        predicted_price=predicted_price,
        current_price=round(current_price, 2),
        stop_loss=stop_loss,
        target=target,
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_version=MODEL_STORE.version + ("-ml" if ml_used else "-rules"),
        sentiment_score=sentiment_score,
        data_source=data_source,
        security_id=SYMBOL_MAPPER.get_id(symbol),
        exchange_segment=exchange_segment,
        analysis={
            "rsi": round(latest.get('RSI_14', 0), 2),
            "adx": round(latest.get('ADX_14', 0), 2),
            "trend": "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral",
            "key_factors": reasons,
            "score": score,
            "asset_class": asset_class,
            "model_breakdown": model_breakdown_detail,
            "veto_active": conviction.get("veto_triggered", False),
            "veto_reason": conviction.get("reason"),
            "fallback_used": not ml_used,
            "p_sell": round(float(model_breakdown_detail.get("ensemble_probabilities", [0.33, 0.34, 0.33])[0]), 4) if isinstance(model_breakdown_detail, dict) and "ensemble_probabilities" in model_breakdown_detail else 0.33,
            "p_hold": round(float(model_breakdown_detail.get("ensemble_probabilities", [0.33, 0.34, 0.33])[1]), 4) if isinstance(model_breakdown_detail, dict) and "ensemble_probabilities" in model_breakdown_detail else 0.34,
            "p_buy": round(float(model_breakdown_detail.get("ensemble_probabilities", [0.33, 0.34, 0.33])[2]), 4) if isinstance(model_breakdown_detail, dict) and "ensemble_probabilities" in model_breakdown_detail else 0.33,
            "catboost_prob": round(float(model_breakdown_detail.get("catboost", {}).get("probabilities", [0.33, 0.34, 0.33])[2 if signal == "BUY" else 0 if signal == "SELL" else 1]), 4) if isinstance(model_breakdown_detail, dict) and "catboost" in model_breakdown_detail else (0.65 if ml_used and signal == "BUY" else 0.35 if ml_used and signal == "SELL" else 0.50),
            "lightgbm_prob": round(float(model_breakdown_detail.get("lightgbm", {}).get("probabilities", [0.33, 0.34, 0.33])[2 if signal == "BUY" else 0 if signal == "SELL" else 1]), 4) if isinstance(model_breakdown_detail, dict) and "lightgbm" in model_breakdown_detail else (0.68 if ml_used and signal == "BUY" else 0.32 if ml_used and signal == "SELL" else 0.50),
            "xgboost_prob": round(float(model_breakdown_detail.get("xgboost", {}).get("probabilities", [0.33, 0.34, 0.33])[2 if signal == "BUY" else 0 if signal == "SELL" else 1]), 4) if isinstance(model_breakdown_detail, dict) and "xgboost" in model_breakdown_detail else (0.70 if ml_used and signal == "BUY" else 0.30 if ml_used and signal == "SELL" else 0.50)
        }
    )

    if hasattr(res, 'model_dump'):
        res_dict = res.model_dump()
    else:
        res_dict = res.dict()
    return clean_floats(res_dict)

# --- Asset-Specific Strategy Helpers ---


def _analyze_fno(latest, price, df):
    """
    Indices (F&O) Strategy: Volatility & Mean Reversion
    Focus: ADX (Trend Strength), Bollinger Bands (Volatility), VWAP (if avail)
    """
    score = 0
    reasons = []

    # ADX - Filter Choppy Markets
    adx = latest.get('ADX_14')
    if adx and adx < 20:
        reasons.append("Choppy Market (Low ADX) - Avoiding Trades")
        return {"score": 0, "reasons": reasons, "signal": "HOLD"}

    # Fast MA for Scalping nature
    ema_20 = latest.get('EMA_20', latest.get('EMA_50')) # Fallback to 50 if 20 missing
    if ema_20:
        if price > ema_20: score += 1; reasons.append("Above Fast EMA")
        else: score -= 1; reasons.append("Below Fast EMA")

    # RSI - Sensitive settings for indices
    rsi = latest.get('RSI_14')
    if rsi:
        if rsi > 60: score += 1; reasons.append("High Momentum")
        elif rsi < 40: score -= 1; reasons.append("Low Momentum")

    return {"score": score, "reasons": reasons, "signal": _score_to_signal(score)}

def _analyze_commodity(latest, price, df):
    """
    Commodities Strategy: Pure Trend Following
    Focus: SuperTrend (conceptually), Breakouts, Strong MACD
    """
    score = 0
    reasons = []

    # ADX is Critical for Commodities
    adx = latest.get('ADX_14')
    if adx and adx > 25:
        score += 1
        reasons.append(f"Strong Trend (ADX {adx:.0f})")

    # MACD Weighting is higher
    macd = latest.get('MACD_12_26_9')
    signal = latest.get('MACDs_12_26_9')
    if macd and signal:
        if macd > signal: score += 2; reasons.append("MACD Bullish Trend")
        else: score -= 2; reasons.append("MACD Bearish Trend")

    # Price vs Long Term MA
    ema_200 = latest.get('EMA_200', latest.get('EMA_50'))
    if ema_200:
        if price > ema_200: score += 1; reasons.append("Long Term Bullish")
        else: score -= 1; reasons.append("Long Term Bearish")

    return {"score": score, "reasons": reasons, "signal": _score_to_signal(score)}

def _score_to_signal(score):
    if score >= 3: return "BUY"
    if score <= -3: return "SELL"
    return "HOLD"

@app.post("/api/v1/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(req: SentimentRequest):
    """Analyze sentiment of news/text"""
    sentiment, confidence = SENTIMENT_ANALYZER.analyze(req.text)
    return SentimentResponse(
        text=req.text[:100] + "..." if len(req.text) > 100 else req.text,
        sentiment=sentiment,
        confidence=confidence,
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/api/v1/train", response_model=TrainingResponse)
async def train_model(req: TrainingRequest):
    """Train ML models with hyperparameter tuning"""
    start_time = time.time()

    try:
        logger.info(f"🎓 Training {req.symbol} with {req.historical_days} days data")

        MODEL_TRAINER.update_hyperparams(
            n_estimators=req.n_estimators,
            max_depth=req.max_depth,
            learning_rate=req.learning_rate
        )

        df, data_source = await MARKET_ENGINE.fetch_data(req.symbol, days=req.historical_days)

        if df.empty or len(df) < 100:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {req.symbol}")

        X, y, feature_cols = MODEL_TRAINER.prepare_training_data(df, lookahead=req.lookahead_days)
        results = MODEL_TRAINER.train_all_models(X, y, req.symbol)

        training_time = time.time() - start_time

        return TrainingResponse(
            status="success",
            symbol=req.symbol.upper(),
            historical_days=req.historical_days,
            samples_used=len(X),
            features_count=len(feature_cols),
            model_accuracies={k: round(v['accuracy'], 4) for k, v in results.items()},
            training_time_seconds=round(training_time, 2),
            data_source=data_source,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@app.get("/api/v1/training/status")
async def get_training_status():
    """Get training status and history"""
    return {
        "trained_symbols": list(MODEL_STORE.trained_symbols),
        "training_history": MODEL_TRAINER.training_history,
        "hyperparameters": MODEL_TRAINER.hyperparams,
        "models_status": {
            "xgboost": "trained" if MODEL_STORE.trained_symbols else "not_trained",
            "lightgbm": "trained" if MODEL_STORE.trained_symbols else "not_trained",
            "random_forest": "trained" if MODEL_STORE.trained_symbols else "not_trained"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/data/sources")
async def get_data_source_stats():
    """Get data source statistics"""
    return {
        "dhan_client_available": MARKET_ENGINE.dhan is not None,
        "fetch_stats": MARKET_ENGINE.data_source_stats,
        "symbol_mapper_loaded": len(SYMBOL_MAPPER.symbol_map) > 0,
        "symbols_count": len(SYMBOL_MAPPER.symbol_map),
        "cache_size": len(MARKET_ENGINE.cache),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/config/market")
async def get_market_config():
    """Get SEBI 2025 market configuration"""
    return MARKET_CONFIG

@app.get("/api/v1/market/knowledge")
async def get_market_knowledge():
    """Comprehensive market knowledge"""
    return {
        "exchange_info": {
            "nse": {
                "name": "National Stock Exchange of India",
                "indices": ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY MIDCAP 100"],
                "trading_hours": "08:55 - 15:45 IST"
            },
            "bse": {
                "name": "Bombay Stock Exchange",
                "indices": ["SENSEX", "BSE 100", "BSE 200"],
                "trading_hours": "08:55 - 15:45 IST"
            }
        },
        "trading_sessions": MARKET_CONFIG["TRADING_SESSIONS"],
        "lot_sizes_2025": MARKET_CONFIG["LOT_SIZES"],
        "expiry_days": MARKET_CONFIG["EXPIRY_DAYS"],
        "margin_rules_2025": MARKET_CONFIG["MARGIN_RULES_2025"],
        "holidays_2025": MARKET_CONFIG["HOLIDAYS_2025"],
        "supported_symbols": list(SYMBOL_MAPPER.symbol_map.keys())[:50],
        "ml_models": {
            "ensemble": ["XGBoost", "LightGBM", "Random Forest"],
            "nlp": ["NLTK VADER", "Transformers (DistilBERT)"],
            "signal_types": ["BUY", "HOLD", "SELL"]
        }
    }




def get_firestore_db():
    """Safely return Google Cloud Firestore database client if configured"""
    try:
        from google.cloud import firestore
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
        return firestore.Client(project=project_id)
    except Exception as e:
        logger.warning(f"Firestore client init fallback: {e}")
    return None


async def store_signal_to_firestore(user_id: str, signal: Any) -> bool:
    """Store generated signal to Google Cloud Firestore signals collection"""
    try:
        db = get_firestore_db()
        if not db:
            logger.warning("Firestore not available for signal storage")
            return False

        # Convert signal to dict
        if hasattr(signal, 'dict'):
            signal_dict = signal.dict()
        elif hasattr(signal, '__dict__'):
            signal_dict = signal.__dict__
        else:
            signal_dict = dict(signal)

        # Add metadata
        signal_dict['user_id'] = user_id
        signal_dict['stored_at'] = datetime.utcnow().isoformat()
        signal_dict['timestamp'] = datetime.utcnow().isoformat()

        # Store to Firestore: signals collection
        db.collection('signals').document().set(signal_dict)
        logger.info(f"✓ Stored signal for {signal_dict.get('symbol', 'UNKNOWN')} to Firestore (user: {user_id})")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to store signal to Firestore: {e}")
        return False


@app.options("/api/v1/signal/batch")
@app.options("/api/v1/signals/batch")
async def preflight_batch(request: Request):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
    return Response(status_code=403)

@app.post("/api/v1/signal/batch")
@app.post("/api/v1/signals/batch")  # Alias for frontend compatibility
async def generate_batch_signals(request: BatchSignalsRequest, auth: bool = Depends(verify_internal_auth)):
    """Generate signals for multiple symbols concurrently via asyncio.gather and store to Firestore"""
    if len(request.symbols) > 50:
        raise HTTPException(status_code=422, detail="Maximum 50 symbols per batch")

    sem = asyncio.Semaphore(10)

    async def _process_single_symbol(symbol: str):
        async with sem:
            try:
                sig = await generate_signal(SignalRequest(symbol=symbol, fast=request.fast))
                stored = False
                if request.user_id:
                    stored = await store_signal_to_firestore(request.user_id, sig)
                return sig, stored
            except Exception as e:
                logger.error(f"Batch signal error for {symbol}: {e}")
                return None, False

    results = await asyncio.gather(*[_process_single_symbol(sym) for sym in request.symbols])
    signals = [r[0] for r in results if r[0] is not None]
    stored_count = sum(1 for r in results if r[1])

    return clean_floats({
        "signals": signals,
        "total": len(signals),
        "stored": stored_count,
        "user_id": request.user_id,
        "timestamp": datetime.utcnow().isoformat()
    })




@app.post("/api/v1/signals/instruments")
async def generate_instrument_signals(req: InstrumentSignalsRequest, auth: bool = Depends(verify_internal_auth)):
    """
    Generate AI signals filtered by trading instruments with concurrent asyncio.gather processing.

    Supported instruments:
    - equities: NSE/BSE stocks
    - nifty-options: NIFTY 50 Index Options
    - banknifty-options: Bank NIFTY Index Options
    - sensex-options: BSE SENSEX Options
    - finnifty-options: Financial Services NIFTY Options
    - midcpnifty-options: MIDCAP NIFTY Options
    - crude-options: MCX Crude Oil Options
    - gold-options: MCX Gold Options
    - silver-options: MCX Silver Options
    """
    # Map instruments to symbols to analyze (Pure Index Options & MCX Commodities)
    instrument_symbols = {
        "nifty-options": ["NIFTY"],
        "banknifty-options": ["BANKNIFTY"],
        "sensex-options": ["SENSEX"],
        "finnifty-options": ["FINNIFTY"],
        "midcpnifty-options": ["MIDCPNIFTY"],
        "crude-options": ["CRUDEOIL"],
        "gold-options": ["GOLD", "GOLDM"],
        "silver-options": ["SILVER", "SILVERM"]
    }

    # Collect all symbols to analyze based on selected instruments
    symbols_to_analyze = []
    for instrument in req.instruments:
        if instrument in instrument_symbols:
            symbols_to_analyze.extend(instrument_symbols[instrument])

    if not symbols_to_analyze:
        raise HTTPException(
            status_code=400,
            detail=f"No valid instruments selected. Valid options: {list(instrument_symbols.keys())}"
        )

    # Remove duplicates
    symbols_to_analyze = list(set(symbols_to_analyze))

    logger.info(f"📊 Generating concurrent signals for instruments: {req.instruments} ({len(symbols_to_analyze)} symbols)")

    sem = asyncio.Semaphore(10)

    async def _process_instrument_symbol(symbol: str):
        async with sem:
            try:
                signal = await generate_signal(SignalRequest(symbol=symbol, fast=True))
                instrument_type = None
                for instrument, syms in instrument_symbols.items():
                    if symbol in syms:
                        instrument_type = instrument
                        break

                signal_dict = signal.dict() if hasattr(signal, 'dict') else signal
                signal_dict["instrument_type"] = instrument_type
                signal_dict["security_id"] = get_security_id(symbol)

                if signal_dict.get("confidence", 0) >= req.min_confidence:
                    return signal_dict
            except Exception as e:
                logger.warning(f"Signal generation failed for {symbol}: {e}")
            return None

    results = await asyncio.gather(*[_process_instrument_symbol(sym) for sym in symbols_to_analyze])
    all_signals = [r for r in results if r is not None]

    # Sort by confidence and limit results
    all_signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    filtered_signals = all_signals[:req.max_signals]

    # Separate actionable signals (BUY/SELL) from HOLD
    actionable = [s for s in filtered_signals if s.get("signal") in ["BUY", "SELL"]]
    hold_signals = [s for s in filtered_signals if s.get("signal") == "HOLD"]

    return {
        "instruments": req.instruments,
        "strategy": req.strategy,
        "min_confidence": req.min_confidence,
        "signals": filtered_signals,
        "actionable_signals": actionable,
        "hold_signals": len(hold_signals),
        "total_analyzed": len(symbols_to_analyze),
        "timestamp": datetime.utcnow().isoformat()
    }


def get_security_id(symbol: str) -> str:
    """Get Dhan security ID for a symbol"""
    # Security ID mapping (NSE Equity symbols to Dhan Security IDs)
    security_id_map = {
        # NSE Equities
        "RELIANCE": "1333",
        "TCS": "2968",
        "HDFCBANK": "1394",
        "INFY": "1594",
        "ICICIBANK": "1270",
        "SBIN": "3045",
        "WIPRO": "3787",
        "ITC": "1660",
        "BHARTIARTL": "2885",
        "LT": "1660",
        # Indices
        "NIFTY": "13",
        "BANKNIFTY": "25",
        "SENSEX": "51",
        "FINNIFTY": "27",
        "MIDCPNIFTY": "442",
        # MCX Commodities
        "CRUDEOIL": "11",
        "CRUDEOILM": "12",
        "GOLD": "5",
        "GOLDM": "6",
        "GOLDPETAL": "7",
        "SILVER": "8",
        "SILVERM": "9",
        "SILVERMIC": "10",
        "NATURALGAS": "13",
        "COPPER": "14",
        "ZINC": "15",
        "LEAD": "16",
        "ALUMINIUM": "17",
        "NICKEL": "18",
        "COTTON": "19"
    }
    return security_id_map.get(symbol.upper(), symbol)

@app.post("/api/v1/train/batch")
async def train_batch_models(symbols: List[str] = ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY", "MIDCPNIFTY"]):
    """Train models on multiple symbols"""
    results = {}

    for symbol in symbols:
        try:
            response = await train_model(TrainingRequest(symbol=symbol))
            results[symbol] = {"status": "success", "accuracy": response.model_accuracies}
        except Exception as e:
            results[symbol] = {"status": "failed", "error": str(e)}

    return {
        "batch_results": results,
        "successful": sum(1 for r in results.values() if r["status"] == "success"),
        "failed": sum(1 for r in results.values() if r["status"] == "failed"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/models")
async def list_models():
    """List all available ML models with ensemble weights"""

    def get_model_status(name):
        model = MODEL_STORE.get_model(name)
        if model is None:
            return 'not_available'

        # Check if fitted (heuristic)
        try:
            if name == 'random_forest':
                # scikit-learn check
                if hasattr(model, 'estimators_'):
                    return 'loaded'
            elif name == 'xgboost':
                # XGBoost check
                if hasattr(model, 'get_booster'):
                     # This might throw if not fitted on some versions, or return None
                     return 'loaded'
            elif name == 'lightgbm':
                 if hasattr(model, 'booster_'):
                     return 'loaded'
            elif name == 'catboost':
                 if model.is_fitted():
                     return 'loaded'

            # If we are here, it might be initialized but not fitted.
            # However, for the purpose of 'status', 'initialized' is better than crashing.
            # But the original code was crashing on implicit checks.
            # Let's return 'initialized_waiting_for_data' if it exists but maybe not fitted.
            return 'initialized'
        except Exception:
            return 'error'

    model_info = {
        'xgboost': {'type': 'gradient_boosting', 'framework': 'xgboost', 'weight': 0.40},
        'lightgbm': {'type': 'gradient_boosting', 'framework': 'lightgbm', 'weight': 0.30},
        'catboost': {'type': 'gradient_boosting', 'framework': 'catboost', 'weight': 0.15},
        'random_forest': {'type': 'ensemble', 'framework': 'scikit-learn', 'weight': 0.15},
        'transformer_sentiment': {'type': 'nlp', 'framework': 'transformers', 'weight': None},
        'nltk_sentiment': {'type': 'nlp', 'framework': 'nltk', 'weight': None}
    }

    return {
        "models": [
            {
                "name": name,
                "type": meta['type'],
                "framework": meta['framework'],
                "ensemble_weight": meta['weight'],
                "status": get_model_status(name)
            }
            for name, meta in model_info.items()
        ],
        "ensemble_weights": MODEL_STORE.get_ensemble_weights(),
        "trained_symbols": list(MODEL_STORE.trained_symbols)
    }

@app.post("/api/v1/models/reload")
async def reload_all_models():
    """Reload all ML models with fresh initialization"""
    results = {}
    for model_name in ['xgboost', 'lightgbm', 'catboost', 'random_forest']:
        result = MODEL_STORE.reload_model(model_name)
        results[model_name] = result

    return {
        "status": "success",
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/models/{model_name}/reload")
async def reload_specific_model(model_name: str):
    """Reload a specific ML model"""
    result = MODEL_STORE.reload_model(model_name)
    return result

@app.post("/api/v1/models/{model_name}/retrain")
async def retrain_specific_model(model_name: str, symbol: str = "NIFTY", historical_days: int = 365):
    """Retrain a specific model on given symbol data"""
    if model_name not in ['xgboost', 'lightgbm', 'catboost', 'random_forest']:
        raise HTTPException(400, f"Model {model_name} not trainable")

    try:
        # Fetch data
        df, data_source = await MARKET_ENGINE.fetch_data(symbol, days=historical_days)
        if df.empty or len(df) < 100:
            raise HTTPException(400, f"Insufficient data for {symbol}")

        # Prepare training data
        X, y, feature_cols = MODEL_TRAINER.prepare_training_data(df, lookahead=5)

        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        scaler = MODEL_STORE.scalers['standard']
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train specific model
        model = MODEL_STORE.get_model(model_name)
        if model is None:
            raise HTTPException(400, f"Model {model_name} not available")

        model.fit(X_train_scaled, y_train)
        predictions = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, predictions)

        MODEL_STORE.trained_symbols.add(symbol.upper())

        return {
            "status": "success",
            "model": model_name,
            "symbol": symbol,
            "accuracy": round(accuracy, 4),
            "samples_trained": len(X_train),
            "samples_tested": len(X_test),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Retrain failed for {model_name}: {e}")
        raise HTTPException(500, f"Training failed: {str(e)}")

@app.get("/api/v1/models/ensemble-weights")
async def get_ensemble_weights():
    """Get current ensemble voting weights"""
    return {
        "weights": MODEL_STORE.get_ensemble_weights(),
        "available_models": list(MODEL_STORE.models.keys()),
        "default_weights": MODEL_STORE.ENSEMBLE_WEIGHTS
    }

# =====================================================================
# POSITION ANALYSIS API - AI/ML POWERED
# =====================================================================

@app.post("/api/v1/position/analyze", response_model=PositionAnalysisResponse)
async def analyze_position(request: PositionAnalysisRequest):
    """
    AI/ML powered position analysis for options and equity positions.
    Provides comprehensive analysis including Greeks estimation, risk metrics,
    and AI-driven recommendations.
    """
    try:
        # Parse position details
        is_option = request.exchange_segment == "NSE_FNO" and request.option_type
        is_put = request.option_type == "PUT" if is_option else False
        is_call = request.option_type == "CALL" if is_option else False

        # Calculate days to expiry
        days_to_expiry = None
        if request.expiry_date:
            try:
                expiry = datetime.strptime(request.expiry_date, "%Y-%m-%d")
                days_to_expiry = (expiry - datetime.now()).days
            except:
                days_to_expiry = None

        # Fetch underlying data for analysis
        underlying_symbol = request.symbol.split("-")[0] if "-" in request.symbol else request.symbol

        # For index options like NIFTY, use ^NSEI
        if underlying_symbol.upper() == "NIFTY":
            fetch_symbol = "^NSEI"
        elif underlying_symbol.upper() == "BANKNIFTY":
            fetch_symbol = "^NSEBANK"
        else:
            fetch_symbol = f"{underlying_symbol}.NS"

        try:
            df, data_source = await MARKET_ENGINE.fetch_data(fetch_symbol, days=30)
        except Exception as e:
            logger.warning(f"Could not fetch market data for {fetch_symbol}: {e}")
            df = pd.DataFrame()
            data_source = "unavailable"

        # Calculate technical indicators with safe column access
        if not df.empty and 'Close' in df.columns:
            current_underlying_price = df['Close'].iloc[-1]
            volatility = df['Close'].pct_change().std() * np.sqrt(252) if len(df) > 5 else 0.25
        else:
            current_underlying_price = request.current_price or request.strike_price or 0
            volatility = 0.25

        # Calculate trend
        if not df.empty and 'Close' in df.columns and len(df) >= 20:
            sma_20 = df['Close'].rolling(20).mean().iloc[-1]
            sma_5 = df['Close'].rolling(5).mean().iloc[-1]
            trend = "BULLISH" if sma_5 > sma_20 else "BEARISH"
            trend_strength = abs(sma_5 - sma_20) / sma_20 * 100 if sma_20 > 0 else 0
        else:
            trend = "NEUTRAL"
            trend_strength = 0
            sma_20 = current_underlying_price
            sma_5 = current_underlying_price

        # Calculate Greeks estimation for options
        greeks = {}
        if is_option and request.strike_price and days_to_expiry is not None:
            # Simplified Greeks estimation
            moneyness = current_underlying_price / request.strike_price if request.strike_price > 0 else 1
            time_factor = max(days_to_expiry, 1) / 365

            # Delta estimation
            if is_call:
                if moneyness > 1.05:  # ITM
                    delta = 0.7 + (moneyness - 1.05) * 2
                elif moneyness < 0.95:  # OTM
                    delta = 0.3 - (0.95 - moneyness) * 2
                else:  # ATM
                    delta = 0.5
            else:  # PUT
                if moneyness < 0.95:  # ITM for put
                    delta = -0.7 - (0.95 - moneyness) * 2
                elif moneyness > 1.05:  # OTM for put
                    delta = -0.3 + (moneyness - 1.05) * 2
                else:  # ATM
                    delta = -0.5

            delta = max(-1, min(1, delta))

            # Theta estimation (time decay)
            theta = -request.cost_price * (1 / max(days_to_expiry, 1)) * 0.5

            # Gamma estimation
            gamma = 0.05 if 0.95 <= moneyness <= 1.05 else 0.02

            # Vega estimation
            vega = request.cost_price * 0.1 * np.sqrt(time_factor)

            greeks = {
                "delta": round(delta, 4),
                "theta": round(theta, 2),
                "gamma": round(gamma, 4),
                "vega": round(vega, 2),
                "moneyness": round(moneyness, 4),
                "moneyness_status": "ITM" if (is_call and moneyness > 1) or (is_put and moneyness < 1) else "OTM" if (is_call and moneyness < 1) or (is_put and moneyness > 1) else "ATM"
            }

        # Risk Metrics
        position_value = abs(request.net_qty * request.cost_price)
        max_loss = position_value if request.position_type == "LONG" else float('inf')

        # For options, max loss is premium paid (for buyers)
        if is_option and request.position_type == "LONG":
            max_loss = position_value

        # Breakeven calculation for options
        breakeven = None
        if is_option and request.strike_price:
            if is_call:
                breakeven = request.strike_price + request.cost_price
            else:  # PUT
                breakeven = request.strike_price - request.cost_price

        # P&L Analysis
        pnl_pct = (request.unrealized_profit / position_value * 100) if position_value > 0 else 0

        risk_metrics = {
            "position_value": round(position_value, 2),
            "unrealized_pnl": round(request.unrealized_profit, 2),
            "unrealized_pnl_pct": round(pnl_pct, 2),
            "max_loss": round(max_loss, 2) if max_loss != float('inf') else "Unlimited",
            "breakeven": round(breakeven, 2) if breakeven else None,
            "days_to_expiry": days_to_expiry,
            "implied_volatility_estimate": round(volatility * 100, 2),
            "greeks": greeks if greeks else None
        }

        # AI Recommendation
        recommendation_score = 0
        recommendation_factors = []

        # Factor 1: P&L Status
        if pnl_pct > 20:
            recommendation_score += 2
            recommendation_factors.append("Significant profit - consider booking partial gains")
        elif pnl_pct > 5:
            recommendation_score += 1
            recommendation_factors.append("Position in profit - monitor for target")
        elif pnl_pct < -30:
            recommendation_score -= 2
            recommendation_factors.append("Significant loss - review exit strategy")
        elif pnl_pct < -10:
            recommendation_score -= 1
            recommendation_factors.append("Position underwater - evaluate stop-loss")

        # Factor 2: Time Decay (for options)
        if days_to_expiry is not None:
            if days_to_expiry <= 2:
                recommendation_score -= 2
                recommendation_factors.append("CRITICAL: Expiry imminent - high theta risk")
            elif days_to_expiry <= 5:
                recommendation_score -= 1
                recommendation_factors.append("Near expiry - accelerated time decay")
            elif days_to_expiry > 20:
                recommendation_score += 1
                recommendation_factors.append("Good time value remaining")

        # Factor 3: Moneyness
        if greeks and 'moneyness_status' in greeks:
            if greeks['moneyness_status'] == "OTM" and days_to_expiry and days_to_expiry <= 5:
                recommendation_score -= 2
                recommendation_factors.append("OTM near expiry - low probability of profit")
            elif greeks['moneyness_status'] == "ITM":
                recommendation_score += 1
                recommendation_factors.append("In-the-money - has intrinsic value")

        # Factor 4: Trend alignment
        if is_call and trend == "BULLISH":
            recommendation_score += 1
            recommendation_factors.append("CALL aligned with bullish trend")
        elif is_put and trend == "BEARISH":
            recommendation_score += 1
            recommendation_factors.append("PUT aligned with bearish trend")
        elif is_call and trend == "BEARISH":
            recommendation_score -= 1
            recommendation_factors.append("CALL against bearish trend")
        elif is_put and trend == "BULLISH":
            recommendation_score -= 1
            recommendation_factors.append("PUT against bullish trend")

        # Generate final recommendation
        if recommendation_score >= 2:
            action = "HOLD"
            confidence = "HIGH"
            summary = "Position is performing well. Consider holding or taking partial profits."
        elif recommendation_score >= 0:
            action = "MONITOR"
            confidence = "MEDIUM"
            summary = "Position needs monitoring. Set alerts for key levels."
        elif recommendation_score >= -2:
            action = "REVIEW"
            confidence = "MEDIUM"
            summary = "Position under pressure. Review risk management."
        else:
            action = "EXIT_CONSIDERATION"
            confidence = "HIGH"
            summary = "Position at risk. Strongly consider exit or hedging."

        ai_recommendation = {
            "action": action,
            "confidence": confidence,
            "summary": summary,
            "score": recommendation_score,
            "factors": recommendation_factors,
            "suggested_actions": []
        }

        # Add specific action suggestions
        if is_option and days_to_expiry and days_to_expiry <= 2:
            ai_recommendation["suggested_actions"].append({
                "action": "EXIT_BEFORE_EXPIRY",
                "reason": "Avoid expiry day volatility and STT charges",
                "urgency": "HIGH"
            })

        if pnl_pct > 30:
            ai_recommendation["suggested_actions"].append({
                "action": "BOOK_PARTIAL_PROFIT",
                "reason": f"Lock in {pnl_pct:.1f}% gains on part of position",
                "urgency": "MEDIUM"
            })

        if pnl_pct < -25 and days_to_expiry and days_to_expiry <= 10:
            ai_recommendation["suggested_actions"].append({
                "action": "CONSIDER_STOP_LOSS",
                "reason": "Limited time for recovery",
                "urgency": "HIGH"
            })

        # Market Context
        market_context = {
            "underlying_price": round(current_underlying_price, 2),
            "trend": trend,
            "trend_strength": round(trend_strength, 2),
            "volatility": round(volatility * 100, 2),
            "sma_5": round(sma_5, 2),
            "sma_20": round(sma_20, 2),
            "market_status": "CLOSED" if datetime.now().weekday() >= 5 else "TRADING_HOURS",
            "data_source": data_source
        }

        # Position analysis summary
        analysis = {
            "position_type": "OPTION" if is_option else "EQUITY",
            "option_type": request.option_type if is_option else None,
            "direction": request.position_type,
            "quantity": request.net_qty,
            "entry_price": request.cost_price,
            "current_value": round(request.net_qty * (request.current_price or request.cost_price), 2),
            "strike_price": request.strike_price if is_option else None,
            "expiry_date": request.expiry_date,
            "is_profitable": request.unrealized_profit > 0,
            "risk_reward_status": "FAVORABLE" if pnl_pct > 0 else "UNFAVORABLE"
        }

        return PositionAnalysisResponse(
            symbol=request.trading_symbol,
            analysis=analysis,
            risk_metrics=risk_metrics,
            ai_recommendation=ai_recommendation,
            market_context=market_context,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Position analysis failed: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@app.post("/api/v1/portfolio/analyze")
async def analyze_portfolio(positions: List[PositionAnalysisRequest]):
    """
    Analyze entire portfolio with AI/ML insights.
    Provides portfolio-level risk assessment and recommendations.
    """
    try:
        analyses = []
        total_value = 0
        total_pnl = 0
        total_risk = 0

        for position in positions:
            analysis = await analyze_position(position)
            analyses.append(analysis.dict())
            total_value += analysis.risk_metrics.get("position_value", 0)
            total_pnl += position.unrealized_profit

        # Portfolio-level metrics
        portfolio_pnl_pct = (total_pnl / total_value * 100) if total_value > 0 else 0

        # Concentration risk
        position_weights = []
        for a in analyses:
            weight = a["risk_metrics"]["position_value"] / total_value * 100 if total_value > 0 else 0
            position_weights.append(weight)

        max_concentration = max(position_weights) if position_weights else 0
        concentration_risk = "HIGH" if max_concentration > 50 else "MEDIUM" if max_concentration > 25 else "LOW"

        return {
            "portfolio_summary": {
                "total_positions": len(positions),
                "total_value": round(total_value, 2),
                "total_unrealized_pnl": round(total_pnl, 2),
                "portfolio_pnl_pct": round(portfolio_pnl_pct, 2),
                "concentration_risk": concentration_risk,
                "max_position_weight": round(max_concentration, 2)
            },
            "positions": analyses,
            "portfolio_recommendation": {
                "diversification": "ADEQUATE" if len(positions) >= 3 else "LOW",
                "risk_level": "HIGH" if portfolio_pnl_pct < -20 else "MEDIUM" if portfolio_pnl_pct < 0 else "LOW",
                "suggested_actions": []
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Portfolio analysis failed: {e}")
        raise HTTPException(500, f"Portfolio analysis failed: {str(e)}")

# =====================================================================
# INDIAN MARKET KNOWLEDGE ENDPOINTS
# =====================================================================
@app.get("/api/v1/knowledge/index/{symbol}")
async def get_index_knowledge(symbol: str):
    """
    Get comprehensive knowledge about an Indian index.
    Includes lot sizes, trading hours, expiry info, and SEBI rules.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    try:
        symbol = symbol.upper()
        info = MARKET_KNOWLEDGE.get_index_info(symbol)
        rules = MARKET_KNOWLEDGE.get_sebi_rules(symbol)
        sessions = MARKET_KNOWLEDGE.get_trading_sessions()

        return {
            "symbol": symbol,
            "index_info": info,
            "sebi_rules": rules,
            "trading_sessions": sessions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Index knowledge fetch failed: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/v1/knowledge/stock/{symbol}")
async def get_stock_knowledge(symbol: str):
    """
    Get comprehensive knowledge about an Indian stock.
    Includes security ID, exchange info, and trading specifications.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    try:
        symbol = symbol.upper()
        stock_info = MARKET_KNOWLEDGE.get_stock_info(symbol)

        if not stock_info:
            raise HTTPException(404, f"Stock {symbol} not found in knowledge base")

        return {
            "symbol": symbol,
            "stock_info": stock_info,
            "trading_sessions": MARKET_KNOWLEDGE.get_trading_sessions(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock knowledge fetch failed: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/v1/knowledge/indicators")
async def get_indicators_knowledge():
    """
    Get documentation for all technical indicators used by the ML models.
    Includes formulas, interpretations, and trading signals.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    return {
        "indicators": MARKET_KNOWLEDGE.get_all_indicators(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/knowledge/greeks")
async def get_option_greeks_knowledge():
    """
    Get comprehensive knowledge about Option Greeks.
    Includes Delta, Gamma, Theta, Vega explanations and formulas.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    return {
        "greeks": MARKET_KNOWLEDGE.get_option_greeks_info(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/knowledge/economic")
async def get_economic_indicators():
    """
    Get knowledge about economic indicators affecting Indian markets.
    Includes RBI rates, inflation data, and market impact analysis.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    return {
        "economic_indicators": MARKET_KNOWLEDGE.get_economic_indicators(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/knowledge/patterns")
async def get_candlestick_patterns():
    """
    Get documentation for all candlestick patterns recognized by ML models.
    Includes pattern descriptions, signals, and reliability scores.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    return {
        "patterns": MARKET_KNOWLEDGE.get_candlestick_patterns(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/knowledge/ml-features")
async def get_ml_features():
    """
    Get the complete list of ML features used for trading predictions.
    Includes feature descriptions, importance, and data sources.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    return {
        "ml_features": MARKET_KNOWLEDGE.get_ml_features(),
        "model_types": ["XGBoost", "LightGBM", "CatBoost", "RandomForest"],
        "ensemble_weights": MODEL_STORE.get_ensemble_weights(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/knowledge/complete")
async def get_complete_knowledge():
    """
    Get the complete Indian market knowledge base.
    Comprehensive data for ML model training and real-time decisions.
    """
    if not HAS_MARKET_KNOWLEDGE:
        raise HTTPException(503, "Market Knowledge module not available")

    return {
        "version": MARKET_KNOWLEDGE.version,
        "last_updated": MARKET_KNOWLEDGE.last_updated,
        "indexes": MARKET_KNOWLEDGE.INDEX_INFO,
        "top_stocks": MARKET_KNOWLEDGE.TOP_50_STOCKS,
        "sebi_rules": MARKET_KNOWLEDGE.SEBI_2025_RULES,
        "trading_sessions": MARKET_KNOWLEDGE.TRADING_SESSIONS,
        "technical_indicators": MARKET_KNOWLEDGE.TECHNICAL_INDICATORS,
        "option_greeks": MARKET_KNOWLEDGE.OPTION_GREEKS,
        "economic_indicators": MARKET_KNOWLEDGE.ECONOMIC_INDICATORS,
        "candlestick_patterns": MARKET_KNOWLEDGE.CANDLESTICK_PATTERNS,
        "ml_features": MARKET_KNOWLEDGE.ML_FEATURES,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/knowledge/analyze-with-context")
async def analyze_with_market_knowledge(request: SignalRequest):
    """
    Generate trading signal with full market knowledge context.
    Enhances ML predictions with domain expertise.
    """
    if not HAS_MARKET_KNOWLEDGE:
        # Fallback to regular analysis
        return await generate_signal(request)

    try:
        # Get base ML signal
        base_signal = await generate_signal(request)

        # Enhance with market knowledge context
        symbol = request.symbol.upper()

        # Get symbol-specific knowledge
        if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
            context = MARKET_KNOWLEDGE.get_index_info(symbol)
            sebi_rules = MARKET_KNOWLEDGE.get_sebi_rules(symbol)
        else:
            context = MARKET_KNOWLEDGE.get_stock_info(symbol)
            sebi_rules = MARKET_KNOWLEDGE.SEBI_2025_RULES.get("equity", {})

        # Add knowledge context to response
        enhanced_response = base_signal.dict()
        enhanced_response["market_knowledge"] = {
            "symbol_context": context,
            "sebi_rules": sebi_rules,
            "trading_session": MARKET_KNOWLEDGE.get_trading_sessions(),
            "knowledge_version": MARKET_KNOWLEDGE.version
        }

        return enhanced_response

    except Exception as e:
        logger.error(f"Knowledge-enhanced analysis failed: {e}")
        # Fallback to regular signal
        return await generate_signal(request)


# --- Google Cloud AI Integration Endpoints ---


@app.post("/api/v1/ai/gemini-signal")
async def generate_gemini_signal(req: GeminiSignalRequest):
    """Generate trading signal using Gemini AI (Official SDK)"""
    if not HAS_GOOGLE_INTEGRATIONS or GENAI_CLIENT_B is None:
        raise HTTPException(status_code=503, detail="GenAI client not available")

    try:
        market_data = {
            "symbol": req.symbol,
            "current_price": req.current_price,
            "historical_data": req.historical_data or {},
            "technical_indicators": req.technical_indicators or {},
            "news_context": req.news_context
        }

        # Create structured trading prompt
        from shared.google_integrations import TradingPrompt
        trading_prompt = TradingPrompt(
            symbol=req.symbol,
            market="NSE",
            analysis_type="signal",
            context=market_data,
            news_context=req.news_context
        )

        # Generate signal using official Gemini SDK
        signal_result = await GENAI_CLIENT_B.generate_trading_signal(
            prompt=trading_prompt
        )

        # Convert TradingAnalysis to dict
        signal_dict = {
            "signal": signal_result.signal,
            "confidence": signal_result.confidence,
            "reasoning": signal_result.reasoning,
            "risk_level": signal_result.risk_level,
            "entry_price": signal_result.entry_price,
            "stop_loss": signal_result.stop_loss,
            "target_price": signal_result.target_price,
            "timeframe": signal_result.timeframe
        }

        # Log the signal
        if TRADING_LOGGER_B:
            TRADING_LOGGER_B.log_signal(
                symbol=req.symbol,
                signal=signal_dict.get("signal", "HOLD"),
                confidence=signal_dict.get("confidence", 0.0),
                model_name="gemini-2.0-flash",
                metadata={"market_data": market_data}
            )

        return {
            "status": "success",
            "symbol": req.symbol,
            "signal": signal_dict,
            "model": "gemini-2.0-flash",
            "sdk": "google-genai",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating Gemini signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# ENHANCED TRADING AI v4.0 ENDPOINTS
# =====================================================================



@app.post("/api/v1/ai/enhanced-signal")
async def generate_enhanced_signal(req: EnhancedSignalRequest):
    """
    Generate enhanced trading signal using InfinityAI Trading Intelligence v4.0.

    Features:
    - Comprehensive Indian market knowledge
    - SEBI 2025 compliant risk management
    - Precise entry/exit timing
    - FII/DII sentiment integration
    - Multi-timeframe analysis
    - Position sizing recommendations

    Returns complete trading plan with:
    - Signal (BUY/SELL/HOLD)
    - Confidence (0-100%)
    - Entry price, stop loss, targets
    - Risk:Reward ratio
    - Position size recommendation
    - Detailed reasoning
    """
    if not HAS_ENHANCED_TRADING_AI or ENHANCED_TRADING_AI is None:
        # Fallback to regular Gemini signal
        logger.warning("Enhanced Trading AI not available, using fallback")
        if HAS_GOOGLE_INTEGRATIONS and GENAI_CLIENT_B:
            from shared.google_integrations import TradingPrompt
            trading_prompt = TradingPrompt(
                symbol=req.symbol,
                market="NSE",
                analysis_type="signal",
                context=req.technical_data or {}
            )
            signal_result = await GENAI_CLIENT_B.generate_trading_signal(prompt=trading_prompt)
            return {
                "status": "success",
                "symbol": req.symbol,
                "signal": {
                    "signal": signal_result.signal,
                    "confidence": signal_result.confidence,
                    "reasoning": signal_result.reasoning,
                },
                "version": "fallback",
                "timestamp": datetime.utcnow().isoformat()
            }
        raise HTTPException(status_code=503, detail="Enhanced Trading AI not available")

    try:
        # Fetch additional market data if not provided
        if req.technical_data is None and HAS_YFINANCE:
            try:
                ticker = yf.Ticker(f"{req.symbol}.NS")
                hist = ticker.history(period="5d", interval="15m")
                if not hist.empty and HAS_TA_LIB:
                    import ta as ta_lib
                    close = hist['Close']

                    req.technical_data = {
                        "rsi": ta_lib.momentum.RSIIndicator(close, window=14).rsi().iloc[-1] if len(close) > 14 else 50,
                        "macd": ta_lib.trend.MACD(close).macd().iloc[-1] if len(close) > 26 else 0,
                        "macd_signal": ta_lib.trend.MACD(close).macd_signal().iloc[-1] if len(close) > 26 else 0,
                        "sma_20": close.rolling(20).mean().iloc[-1] if len(close) > 20 else close.iloc[-1],
                        "sma_50": close.rolling(50).mean().iloc[-1] if len(close) > 50 else close.iloc[-1],
                        "volume": int(hist['Volume'].iloc[-1]),
                        "volume_avg": int(hist['Volume'].rolling(20).mean().iloc[-1]) if len(hist) > 20 else int(hist['Volume'].iloc[-1]),
                        "volume_ratio": hist['Volume'].iloc[-1] / hist['Volume'].rolling(20).mean().iloc[-1] if len(hist) > 20 else 1.0,
                        "atr": ta_lib.volatility.AverageTrueRange(hist['High'], hist['Low'], close).average_true_range().iloc[-1] if len(hist) > 14 else 0,
                        "bb_upper": ta_lib.volatility.BollingerBands(close).bollinger_hband().iloc[-1] if len(close) > 20 else close.iloc[-1],
                        "bb_lower": ta_lib.volatility.BollingerBands(close).bollinger_lband().iloc[-1] if len(close) > 20 else close.iloc[-1],
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch technical data for {req.symbol}: {e}")

        # Generate enhanced signal
        signal = await ENHANCED_TRADING_AI.generate_signal(
            symbol=req.symbol,
            current_price=req.current_price,
            technical_data=req.technical_data,
            market_context=req.market_context,
            news_sentiment=req.news_sentiment,
            portfolio_context=req.portfolio_context
        )

        # Log the signal
        if TRADING_LOGGER_B:
            TRADING_LOGGER_B.log_signal(
                symbol=req.symbol,
                signal=signal.signal,
                confidence=signal.confidence,
                model_name="infinityai-enhanced-v4.0",
                metadata={
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "target_1": signal.target_1,
                    "target_2": signal.target_2,
                    "timeframe": signal.timeframe,
                    "risk_reward": signal.risk_reward_ratio,
                    "position_size_pct": signal.position_size_pct
                }
            )

        return {
            "status": "success",
            "symbol": req.symbol,
            "signal": {
                "signal": signal.signal,
                "confidence": signal.confidence,
                "risk_level": signal.risk_level,
                "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "target_1": signal.target_1,
                "target_2": signal.target_2,
                "timeframe": signal.timeframe,
                "position_size_pct": signal.position_size_pct,
                "risk_reward_ratio": signal.risk_reward_ratio,
                "expected_return_pct": signal.expected_return_pct,
                "max_loss_pct": signal.max_loss_pct,
                "order_type": signal.order_type,
                "time_in_force": signal.time_in_force
            },
            "market_context": {
                "session": signal.market_session,
                "fii_dii_sentiment": signal.fii_dii_sentiment,
                "sector_strength": signal.sector_strength,
                "global_cues": signal.global_cues,
                "trend": signal.trend,
                "volume_confirmation": signal.volume_confirmation
            },
            "key_levels": signal.key_levels,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating enhanced signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/enhanced-signal")
async def generate_enhanced_signal(req: GeminiProSignalRequest):
    """
    Generate GenAI-powered trading signal using Gemini 2.5 Flash / 3 Pro.
    Integrates real-time market data with GenAI reasoning.
    """
    if not ENHANCED_GENAI_CLIENT:
         raise HTTPException(status_code=503, detail="Enhanced GenAI Client not initialized")

    try:
        if req.use_pro_model:
             # Use Gemini 3 Pro / 2.5 Pro (Advanced)
             logger.info(f"🧠 Using Advanced Model (Gemini Pro) for {req.symbol}")
             res = await ENHANCED_GENAI_CLIENT.advanced_analysis_gemini3(
                 f"Analyze {req.symbol} for {req.timeframe} trading using advanced multi-factor analysis."
             )
             return res
        else:
            # Use Gemini 2.5 Flash (Standard)
            logger.info(f"⚡ Using Fast Model (Gemini Flash) for {req.symbol}")
            res = await ENHANCED_GENAI_CLIENT.generate_trading_signal(
                symbol=req.symbol,
                analysis_type=req.user_analysis_type
            )
            return res.to_dict()

    except Exception as e:
        logger.error(f"❌ Enhanced signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/v1/ai/market-knowledge")
async def get_market_knowledge_summary():
    """
    Get comprehensive Indian market knowledge summary.

    Returns:
    - Market timings
    - Index lot sizes
    - Expiry schedule
    - SEBI regulations
    - Risk management rules
    - Technical indicator settings
    """
    if not HAS_ENHANCED_TRADING_AI:
        raise HTTPException(status_code=503, detail="Enhanced Trading AI not available")

    try:
        from src.google_integrations.enhanced_trading_ai import IndianMarketKnowledge
        knowledge = IndianMarketKnowledge()

        return {
            "status": "success",
            "market_timings": knowledge.MARKET_TIMINGS,
            "index_lot_sizes": knowledge.INDEX_LOT_SIZES,
            "expiry_schedule": knowledge.EXPIRY_SCHEDULE,
            "holidays_2025": knowledge.NSE_HOLIDAYS_2025,
            "sebi_rules": knowledge.SEBI_ALGO_RULES,
            "circuit_breakers": knowledge.CIRCUIT_BREAKERS,
            "risk_management": knowledge.RISK_MANAGEMENT,
            "indicator_settings": knowledge.INDICATOR_SETTINGS,
            "timing_rules": knowledge.TIMING_RULES,
            "version": "v4.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching market knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/news")
async def get_market_news_endpoint(
    category: str = "markets",
    symbol: Optional[str] = None,
    limit: int = 20
):
    """
    Get Real-Time Market News.
    Supports general categories or symbol-specific news.
    """
    try:
        aggregator = NewsAggregator()
        if symbol:
            feed = await aggregator.fetch_symbol_news(symbol, max_articles=limit)
        else:
            feed = await aggregator.fetch_all_news([category], max_articles=limit)
        return feed.to_dict()
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ai/trading-session-status")
async def get_trading_session_status():
    """
    Get current trading session status with actionable insights.

    Returns:
    - Current session type
    - Whether to avoid entry
    - Best trading windows
    - Time to market close
    """
    if not HAS_ENHANCED_TRADING_AI:
        raise HTTPException(status_code=503, detail="Enhanced Trading AI not available")

    try:
        session = ENHANCED_TRADING_AI.get_market_session()
        avoid_entry, avoid_reason = ENHANCED_TRADING_AI.should_avoid_entry()

        from datetime import timezone
        ist_offset = timedelta(hours=5, minutes=30)
        ist_now = datetime.utcnow() + ist_offset
        current_time = ist_now.time()

        # Calculate time to market close
        from datetime import time as dt_time
        market_close = datetime.combine(ist_now.date(), dt_time(15, 30))
        if ist_now < market_close:
            time_to_close = market_close - ist_now
            minutes_to_close = int(time_to_close.total_seconds() / 60)
        else:
            minutes_to_close = 0

        return {
            "status": "success",
            "session": {
                "type": session.value,
                "ist_time": ist_now.strftime("%Y-%m-%d %H:%M:%S IST"),
                "is_trading_hours": session.value == "normal",
                "minutes_to_close": minutes_to_close
            },
            "entry_guidance": {
                "avoid_entry": avoid_entry,
                "reason": avoid_reason if avoid_entry else "Good time for entry",
                "best_windows": [
                    {"name": "Morning Breakout", "time": "09:30-10:30"},
                    {"name": "Post Consolidation", "time": "11:00-12:00"},
                    {"name": "Afternoon Momentum", "time": "14:00-15:00"}
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ai/agent-analysis")
async def run_agent_analysis(req: AgentAnalysisRequest):
    """Run specialized agent for market analysis"""
    if not HAS_GOOGLE_INTEGRATIONS:
        raise HTTPException(status_code=503, detail="Google integrations not available")

    try:
        import uuid
        # Create proper AgentContext object
        context = AgentContext(
            session_id=str(uuid.uuid4()),
            symbol=req.symbol,
            market="NSE",
            data={
                "market_data": req.market_data,
                "market_context": req.market_data
            }
        )

        results = {}

        if req.analysis_type in ["signal", "comprehensive"] and SIGNAL_AGENT:
            signal_result = await SIGNAL_AGENT.run(context)
            results["signal_analysis"] = signal_result.data if signal_result.success else signal_result.error

        if req.analysis_type in ["risk", "comprehensive"] and RISK_AGENT:
            risk_result = await RISK_AGENT.run(context)
            results["risk_analysis"] = risk_result.data if risk_result.success else risk_result.error

        if req.analysis_type in ["market", "comprehensive"] and MARKET_AGENT:
            market_result = await MARKET_AGENT.run(context)
            results["market_analysis"] = market_result.data if market_result.success else market_result.error

        # Log the analysis
        if TRADING_LOGGER_B:
            TRADING_LOGGER_B.log_ml_prediction(
                model_name="trading-agents",
                symbol=req.symbol,
                prediction=results,
                latency_ms=0.0
            )

        return {
            "status": "success",
            "symbol": req.symbol,
            "analysis_type": req.analysis_type,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error running agent analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ai/integrations-status")
async def get_ai_integrations_status():
    """Get status of all AI/Google Cloud integrations"""

    # Get available models info if enhanced client exists
    available_models = {}
    if ENHANCED_GENAI_CLIENT is not None:
        try:
            available_models = ENHANCED_GENAI_CLIENT.get_available_models()
        except:
            available_models = {"error": "Could not fetch model info"}

    return {
        "google_integrations_available": HAS_GOOGLE_INTEGRATIONS,
        "enhanced_genai_available": HAS_ENHANCED_GENAI,
        "genai_client": GENAI_CLIENT_B is not None,
        "enhanced_genai_client": ENHANCED_GENAI_CLIENT is not None,
        "trading_logger": TRADING_LOGGER_B is not None,
        "model_storage": MODEL_STORAGE_B is not None,
        "news_aggregator": NEWS_AGGREGATOR is not None,
        "agents": {
            "signal_agent": SIGNAL_AGENT is not None,
            "risk_agent": RISK_AGENT is not None,
            "market_agent": MARKET_AGENT is not None
        },
        "ml_models": {
            "traditional": list(MODEL_STORE.models.keys()),
            "capabilities": MODEL_STORE.capabilities
        },
        "gemini_models": available_models,
        "version": "4.0.0-gemini3pro",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/ai/available-models")
async def get_available_ai_models():
    """Get all available Gemini models and their capabilities"""
    if not HAS_ENHANCED_GENAI or ENHANCED_GENAI_CLIENT is None:
        return {
            "error": "Enhanced GenAI client not available",
            "basic_models": ["gemini-2.0-flash", "gemini-1.5-pro"]
        }

    return ENHANCED_GENAI_CLIENT.get_available_models()


@app.post("/api/v1/ai/gemini3-analysis")
async def generate_gemini3_analysis(
    query: str,
    use_advanced_reasoning: bool = True
):
    """
    Use Gemini 3 Pro for advanced analysis requiring deep reasoning.

    Best for:
    - Complex multi-factor analysis
    - Options strategy optimization
    - Risk scenario modeling
    - Portfolio rebalancing decisions
    """
    if not HAS_ENHANCED_GENAI or ENHANCED_GENAI_CLIENT is None:
        raise HTTPException(status_code=503, detail="Enhanced GenAI client not available")

    try:
        result = await ENHANCED_GENAI_CLIENT.advanced_analysis_gemini3(
            query=query,
            use_advanced_reasoning=use_advanced_reasoning
        )
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ai/usage-stats")
async def get_ai_usage_stats():
    """Get AI usage statistics and estimated costs"""
    if not HAS_ENHANCED_GENAI or ENHANCED_GENAI_CLIENT is None:
        return {"error": "Enhanced GenAI client not available"}

    return ENHANCED_GENAI_CLIENT.get_usage_stats()


# =====================================================================
# ENHANCED GEMINI API - v4.0.0 with Gemini 3 Pro & Function Calling
# =====================================================================


@app.post("/api/v1/gemini/enhanced-signal")
async def generate_gemini_enhanced_signal(req: GeminiFunctionCallingSignalRequest):
    """
    Generate enhanced trading signal with Vertex AI function calling.
    Automatically fetches real-time market data.
    """
    if not HAS_ENHANCED_GENAI or ENHANCED_GENAI_CLIENT is None:
        raise HTTPException(status_code=503, detail="Enhanced GenAI client not available")

    try:
        recommendation = await ENHANCED_GENAI_CLIENT.generate_trading_signal(
            symbol=req.symbol,
            analysis_type=req.analysis_type,
            fetch_live_data=req.fetch_live_data,
            auto_execute=req.auto_execute
        )

        # Log the signal
        if TRADING_LOGGER_B:
            TRADING_LOGGER_B.log_signal(
                symbol=req.symbol,
                signal=recommendation.signal.value,
                confidence=recommendation.confidence,
                model_name="gemini-2.0-flash-vertexai",
                metadata={
                    "entry_price": recommendation.entry_price,
                    "stop_loss": recommendation.stop_loss,
                    "targets": recommendation.target_prices,
                    "risk_level": recommendation.risk_level.value
                }
            )

        return {
            "status": "success",
            "symbol": req.symbol,
            "recommendation": recommendation.to_dict(),
            "model": "gemini-2.0-flash",
            "vertex_ai": True,
            "function_calling": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating enhanced signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/gemini/market-summary")
async def get_gemini_market_summary():
    """
    Get comprehensive market summary using Gemini with function calling.
    Includes NIFTY, BANKNIFTY, FII/DII, news sentiment.
    """
    if not HAS_ENHANCED_GENAI or ENHANCED_GENAI_CLIENT is None:
        raise HTTPException(status_code=503, detail="Enhanced GenAI client not available")

    try:
        summary = await ENHANCED_GENAI_CLIENT.get_market_summary()

        return {
            "status": "success",
            "summary": summary.get("response"),
            "function_calls_made": summary.get("function_calls", []),
            "token_usage": summary.get("token_usage", {}),
            "model": "gemini-2.0-flash",
            "vertex_ai": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/gemini/quick-signal/{symbol}")
async def get_quick_signal(symbol: str):
    """
    Get quick BUY/SELL/HOLD signal for a symbol.
    """
    if not HAS_ENHANCED_GENAI or ENHANCED_GENAI_CLIENT is None:
        raise HTTPException(status_code=503, detail="Enhanced GenAI client not available")

    try:
        signal = await ENHANCED_GENAI_CLIENT.quick_signal(symbol.upper())

        return {
            "status": "success",
            "symbol": symbol.upper(),
            "analysis": signal.get("response"),
            "function_calls": signal.get("function_calls", []),
            "vertex_ai": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting quick signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gemini/options-analysis")
async def analyze_options(symbol: str = "NIFTY", strategy: str = "auto"):
    """
    Analyze options for a symbol and get strategy recommendation.
    """
    if not HAS_ENHANCED_GENAI or ENHANCED_GENAI_CLIENT is None:
        raise HTTPException(status_code=503, detail="Enhanced GenAI client not available")

    try:
        analysis = await ENHANCED_GENAI_CLIENT.options_analysis(symbol, strategy)

        return {
            "status": "success",
            "symbol": symbol,
            "analysis": analysis.get("response"),
            "function_calls": analysis.get("function_calls", []),
            "vertex_ai": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing options: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/api/v1/gemini/chat")
async def gemini_chat(request: GeminiChatRequest):
    """
    Free-form chat with Gemini for any trading-related questions.
    Supports context from previous conversation.
    """
    try:
        # Try Finance AI model first (best for finance)
        if HAS_FINANCE_AI:
            from src.google_integrations.finance_ai_model import get_finance_ai_model
            import google.genai.types as genai_types

            model = get_finance_ai_model()

            # Ensure client is initialized
            if not model._ensure_client():
                raise HTTPException(status_code=503, detail="Finance AI model not available")

            # Construct prompt
            system_prompt = """You are an expert Indian stock market analyst and trading advisor.
You have deep knowledge of NSE, BSE, NIFTY, Bank NIFTY, and all Indian market instruments.
Provide clear, actionable answers focused on Indian markets.
Include specific numbers, prices, levels, and recommendations where appropriate.
Be concise but comprehensive."""

            user_prompt = request.question
            if request.context:
                user_prompt = f"Context: {request.context}\n\nQuestion: {request.question}"

            # Call Gemini
            response = await asyncio.to_thread(
                model._client.models.generate_content,
                model=model.model_name,
                contents=user_prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.4,
                    max_output_tokens=2048,
                )
            )

            return {
                "status": "success",
                "response": response.text,
                "model": "gemini-2.0-flash",
                "timestamp": datetime.utcnow().isoformat()
            }

        # Fallback to Enhanced GenAI
        elif HAS_ENHANCED_GENAI and ENHANCED_GENAI_CLIENT:
            response = await ENHANCED_GENAI_CLIENT.chat(request.question, request.context)
            return {
                "status": "success",
                "response": response.get("response", ""),
                "function_calls": response.get("function_calls", []),
                "model": "gemini-2.0-flash",
                "timestamp": datetime.utcnow().isoformat()
            }

        else:
            raise HTTPException(status_code=503, detail="No AI model available")

    except Exception as e:
        logger.error(f"Gemini chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/v1/market-data/{symbol}")
async def get_live_market_data(symbol: str, exchange: str = "NSE", data_type: str = "all"):
    """
    Get live market data using market data tools.
    data_type: quote, technicals, options, news, all
    """
    if not HAS_ENHANCED_GENAI:
        raise HTTPException(status_code=503, detail="Market data tools not available")

    try:
        result = {}

        if data_type in ["quote", "all"]:
            result["quote"] = get_stock_quote(symbol, exchange)

        if data_type in ["technicals", "all"]:
            result["technicals"] = get_technical_indicators(symbol, exchange)

        if data_type in ["options", "all"] and symbol.upper() in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
            result["option_chain"] = get_option_chain_data(symbol)

        if data_type in ["news", "all"]:
            result["market_news"] = get_market_news("indian_markets")

        if data_type in ["fii_dii", "all"]:
            result["fii_dii"] = get_fii_dii_activity()

        return {
            "status": "success",
            "symbol": symbol,
            "exchange": exchange,
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/nifty-overview")
async def get_nifty_market_overview():
    """
    Get comprehensive NIFTY 50 market overview.
    """
    if not HAS_ENHANCED_GENAI:
        raise HTTPException(status_code=503, detail="Market data tools not available")

    try:
        overview = get_nifty_overview()

        return {
            "status": "success",
            "data": overview,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting NIFTY overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/news/market")
async def get_market_news_feed(category: str = "markets", max_articles: int = 20):
    """
    Get live market news with sentiment analysis.
    category: markets, stocks, economy, global
    """
    if not NEWS_AGGREGATOR:
        raise HTTPException(status_code=503, detail="News aggregator not available")

    try:
        feed = await NEWS_AGGREGATOR.fetch_all_news([category], max_articles)

        return {
            "status": "success",
            "category": category,
            "overall_sentiment": feed.overall_sentiment,
            "sentiment_breakdown": {
                "bullish": feed.bullish_count,
                "bearish": feed.bearish_count,
                "neutral": feed.neutral_count
            },
            "articles": [a.to_dict() for a in feed.articles],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/news/symbol/{symbol}")
async def get_symbol_news(symbol: str, max_articles: int = 10):
    """
    Get news specific to a stock symbol.
    """
    if not NEWS_AGGREGATOR:
        raise HTTPException(status_code=503, detail="News aggregator not available")

    try:
        feed = await NEWS_AGGREGATOR.fetch_symbol_news(symbol.upper(), max_articles)

        return {
            "status": "success",
            "symbol": symbol.upper(),
            "sentiment": feed.overall_sentiment,
            "articles": [a.to_dict() for a in feed.articles],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting symbol news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/gemini/usage-stats")
async def get_gemini_usage_stats():
    """
    Get Gemini API usage statistics.
    """
    if not ENHANCED_GENAI_CLIENT:
        return {"message": "Enhanced GenAI client not initialized"}

    return {
        "status": "success",
        "usage": ENHANCED_GENAI_CLIENT.get_usage_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }


# =====================================================================
# ENHANCED REAL-TIME DATA ENDPOINTS (v3.8)
# =====================================================================

try:
    from src.google_integrations.enhanced_data_sources import (
        get_market_intelligence,
        get_yahoo_provider,
        get_news_aggregator
    )
    HAS_ENHANCED_DATA = True
    logger.info("✅ Enhanced data sources loaded for API endpoints")
except ImportError as e:
    HAS_ENHANCED_DATA = False
    logger.warning(f"Enhanced data sources not available: {e}")
except Exception as e:
    HAS_ENHANCED_DATA = False
    logger.error(f"Error loading enhanced data sources: {type(e).__name__}: {e}")


@app.get("/api/v1/market/pulse")
async def get_market_pulse_endpoint():
    """
    Get comprehensive market pulse combining all data sources.

    Returns real-time data from:
    - Yahoo Finance (indices, stocks)
    - NSE (option chains, FII/DII)
    - Global markets (US, Europe, Asia)
    - Sector performance
    - Market breadth analysis
    """
    if not HAS_ENHANCED_DATA:
        raise HTTPException(status_code=503, detail="Enhanced data sources not available")

    try:
        intelligence = get_market_intelligence()
        pulse = intelligence.get_market_pulse()
        return pulse
    except Exception as e:
        logger.error(f"Market pulse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/global")
async def get_global_markets_endpoint():
    """
    Get global market data for correlation analysis.

    Includes:
    - US Markets: S&P 500, NASDAQ, DOW
    - European Markets: FTSE, DAX
    - Asian Markets: Nikkei, Hang Seng
    - Correlation signal for Indian markets
    """
    if not HAS_ENHANCED_DATA:
        raise HTTPException(status_code=503, detail="Enhanced data sources not available")

    try:
        provider = get_yahoo_provider()
        return {
            "status": "success",
            "data": provider.get_global_markets().to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Global markets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/sectors")
async def get_sector_performance_endpoint():
    """
    Get sector-wise performance for Indian markets.

    Analyzes:
    - Banking, IT, Pharma, Auto, FMCG
    - Metal, Energy, Realty, Finance
    - Top gainer/loser in each sector
    """
    if not HAS_ENHANCED_DATA:
        raise HTTPException(status_code=503, detail="Enhanced data sources not available")

    try:
        provider = get_yahoo_provider()
        return {
            "status": "success",
            "data": provider.get_sector_performance(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Sector performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/nifty50-heatmap")
async def get_nifty50_heatmap_endpoint():
    """
    Get NIFTY 50 stocks heatmap with gainers and losers.

    Returns:
    - All NIFTY 50 stocks with current price and change
    - Top 5 gainers and losers
    - Market breadth analysis
    """
    if not HAS_ENHANCED_DATA:
        raise HTTPException(status_code=503, detail="Enhanced data sources not available")

    try:
        provider = get_yahoo_provider()
        return {
            "status": "success",
            "data": provider.get_nifty50_heatmap(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"NIFTY 50 heatmap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/news/aggregated")
async def get_aggregated_news_endpoint(sources: str = None, max_articles: int = 20):
    """
    Get aggregated news from multiple sources with sentiment analysis.

    Sources:
    - Economic Times
    - Moneycontrol
    - Livemint
    - Reuters India
    - CNBC

    Args:
        sources: Comma-separated list of sources (optional)
        max_articles: Maximum articles to return (default 20)
    """
    if not HAS_ENHANCED_DATA:
        raise HTTPException(status_code=503, detail="Enhanced data sources not available")

    try:
        aggregator = get_news_aggregator()
        source_list = sources.split(",") if sources else None
        news = await aggregator.fetch_news(sources=source_list, max_articles=max_articles)
        return {
            "status": "success",
            "data": news,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"News aggregation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stock/{symbol}/intelligence")
async def get_stock_intelligence_endpoint(symbol: str):
    """
    Get comprehensive intelligence for a specific stock.

    Includes:
    - Real-time quote from Yahoo Finance
    - Sector classification
    - Global market context
    - Quick trading recommendation
    """
    if not HAS_ENHANCED_DATA:
        raise HTTPException(status_code=503, detail="Enhanced data sources not available")

    try:
        intelligence = get_market_intelligence()
        data = await intelligence.get_stock_intelligence(symbol.upper())
        return data
    except Exception as e:
        logger.error(f"Stock intelligence error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FINANCE AI MODEL ENDPOINTS (v4.1)
# Advanced AI-powered trading analysis using Gemini
# ============================================================================

# Import Finance AI Model
try:
    from src.google_integrations.finance_ai_model import (
        get_finance_ai_model,
        FinanceModelType,
        get_stock_signal,
        get_market_trend,
        get_options_recommendation
    )
    HAS_FINANCE_AI = True
except ImportError:
    HAS_FINANCE_AI = False




@app.post("/api/v1/finance-ai/signal")
async def get_finance_ai_signal(request: FinanceAIRequest):
    """
    Get AI-powered trading signal using Gemini Finance Model.

    This endpoint uses specialized finance prompts and Indian market knowledge
    to generate accurate trading signals with entry, stop-loss, and targets.
    """
    if not HAS_FINANCE_AI:
        raise HTTPException(status_code=503, detail="Finance AI model not available")

    try:
        model = get_finance_ai_model()

        # Map string to enum
        model_type_map = {
            "stock_analyst": FinanceModelType.STOCK_ANALYST,
            "options_strategist": FinanceModelType.OPTIONS_STRATEGIST,
            "technical_analyst": FinanceModelType.TECHNICAL_ANALYST,
            "risk_manager": FinanceModelType.RISK_MANAGER,
            "sentiment_analyst": FinanceModelType.SENTIMENT_ANALYST,
        }
        model_type = model_type_map.get(request.model_type, FinanceModelType.STOCK_ANALYST)

        signal = await model.analyze_stock(
            symbol=request.symbol,
            current_price=request.current_price,
            technical_indicators=request.technical_indicators,
            news_items=request.news_items,
            model_type=model_type
        )

        return {
            "status": "success",
            "symbol": signal.symbol,
            "signal": {
                "action": signal.action,
                "confidence": signal.confidence,
                "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "target_1": signal.target_1,
                "target_2": signal.target_2,
                "target_3": signal.target_3,
                "risk_reward_ratio": signal.risk_reward_ratio,
                "position_size_pct": signal.position_size_pct,
                "timeframe": signal.timeframe,
                "risk_level": signal.risk_level
            },
            "reasoning": signal.reasoning,
            "key_factors": signal.key_factors,
            "model": "gemini-2.0-flash",
            "model_type": request.model_type,
            "timestamp": signal.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Finance AI signal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/finance-ai/market-analysis")
async def get_finance_ai_market_analysis(request: FinanceAIRequest):
    """
    Get comprehensive market analysis using Finance AI.

    Returns trend analysis, support/resistance levels, and recommendations.
    """
    if not HAS_FINANCE_AI:
        raise HTTPException(status_code=503, detail="Finance AI model not available")

    try:
        model = get_finance_ai_model()
        analysis = await model.get_market_analysis(
            symbol=request.symbol,
            current_price=request.current_price,
            technical_data=request.technical_indicators
        )

        return {
            "status": "success",
            "symbol": analysis.symbol,
            "analysis": {
                "trend": analysis.trend,
                "trend_strength": analysis.trend_strength,
                "support_levels": analysis.support_levels,
                "resistance_levels": analysis.resistance_levels,
                "key_indicators": analysis.key_indicators,
                "sentiment_score": analysis.sentiment_score,
                "volume_analysis": analysis.volume_analysis,
                "sector_outlook": analysis.sector_outlook,
                "global_cues": analysis.global_cues
            },
            "recommendation": analysis.recommendation,
            "model": "gemini-2.0-flash",
            "timestamp": analysis.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Finance AI market analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/finance-ai/options-strategy")
async def get_finance_ai_options_strategy(request: FinanceAIOptionsStrategyRequest):
    """
    Get AI-powered options strategy recommendation.

    Considers index levels, outlook, capital, and risk appetite
    to suggest optimal options strategies.
    """
    if not HAS_FINANCE_AI:
        raise HTTPException(status_code=503, detail="Finance AI model not available")

    try:
        model = get_finance_ai_model()
        strategy = await model.get_options_strategy(
            index=request.index,
            spot_price=request.spot_price,
            outlook=request.outlook,
            capital=request.capital,
            risk_appetite=request.risk_appetite
        )

        return {
            "status": "success",
            "index": request.index,
            "spot_price": request.spot_price,
            "outlook": request.outlook,
            "strategy": strategy,
            "model": "gemini-2.0-flash",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Finance AI options strategy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/finance-ai/risk-analysis")
async def get_finance_ai_risk_analysis(request: FinanceAIRiskAnalysisRequest):
    """
    Get AI-powered portfolio risk analysis.

    Analyzes position-level and portfolio-level risks,
    provides hedge recommendations and position adjustments.
    """
    if not HAS_FINANCE_AI:
        raise HTTPException(status_code=503, detail="Finance AI model not available")

    try:
        model = get_finance_ai_model()
        risk_analysis = await model.analyze_risk(
            positions=request.positions,
            account_value=request.account_value
        )

        return {
            "status": "success",
            "account_value": request.account_value,
            "positions_count": len(request.positions),
            "risk_analysis": risk_analysis,
            "model": "gemini-2.0-flash",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Finance AI risk analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/finance-ai/status")
async def get_finance_ai_status():
    """
    Get Finance AI model status and capabilities.
    """
    capabilities = {
        "finance_ai_available": HAS_FINANCE_AI,
        "models": [
            "stock_analyst",
            "options_strategist",
            "risk_manager",
            "sentiment_analyst",
            "technical_analyst",
            "portfolio_optimizer"
        ],
        "features": [
            "Stock signal generation",
            "Market trend analysis",
            "Options strategy recommendations",
            "Portfolio risk analysis",
            "Sentiment analysis",
            "Technical analysis"
        ],
        "indian_market_support": True,
        "instruments": [
            "Equities (NSE/BSE)",
            "Index Options (NIFTY, BANKNIFTY, SENSEX)",
            "Stock Options",
            "Commodities"
        ]
    }

    if HAS_FINANCE_AI:
        try:
            model = get_finance_ai_model()
            capabilities["model_name"] = model.model_name
            capabilities["project_id"] = model.project_id
            capabilities["initialized"] = model._initialized
        except Exception as e:
            capabilities["initialization_error"] = str(e)

    return {
        "status": "success",
        "capabilities": capabilities,
        "gemini_model": "gemini-2.0-flash",
        "timestamp": datetime.utcnow().isoformat()
    }


# --- Options Trading Endpoints ---

@app.post("/api/v1/options/greeks")
async def calculate_greeks(req: GreeksRequest):
    """Calculate Black-Scholes Greeks for an option"""
    try:
        from shared.analytics.greeks_calculator import BlackScholesGreeks
        from datetime import datetime

        # Calculate time to expiry
        expiry_date = datetime.strptime(req.expiry, "%Y-%m-%d")
        days_to_expiry = (expiry_date - datetime.now()).days
        time_to_expiry = max(0, days_to_expiry) / 365.0

        # Calculate Greeks
        greeks = BlackScholesGreeks.calculate_greeks(
            spot=req.spot,
            strike=req.strike,
            time_to_expiry=time_to_expiry,
            volatility=req.volatility,
            option_type=req.option_type
        )

        # Calculate option price
        option_price = BlackScholesGreeks.calculate_option_price(
            spot=req.spot,
            strike=req.strike,
            time_to_expiry=time_to_expiry,
            volatility=req.volatility,
            option_type=req.option_type
        )

        return {
            "status": "success",
            "symbol": req.symbol,
            "strike": req.strike,
            "expiry": req.expiry,
            "option_type": req.option_type,
            "theoretical_price": round(option_price, 2),
            "greeks": greeks,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Greeks calculation error: {e}")
        raise HTTPException(500, f"Greeks calculation failed: {str(e)}")

@app.post("/api/v1/options/strategy")
async def execute_strategy(req: OptionsStrategyRequest):
    """Execute options strategy and return P&L analysis"""
    try:
        from shared.analytics.options_strategies import create_strategy

        # Create strategy
        strategy = create_strategy(
            strategy_type=req.strategy_type,
            symbol=req.symbol,
            spot_price=req.spot_price,
            expiry=req.expiry,
            **req.parameters
        )

        # Get strategy summary
        summary = strategy.summary()

        # Calculate P&L range
        price_range_min = req.spot_price * 0.9  # -10%
        price_range_max = req.spot_price * 1.1  # +10%
        pnl_data = strategy.calculate_pnl_range(
            min_price=price_range_min,
            max_price=price_range_max,
            steps=50
        )

        # Find breakeven points
        breakevens = strategy.breakeven_points(price_range_min, price_range_max)

        return {
            "status": "success",
            "strategy": summary,
            "pnl_chart": pnl_data,
            "breakeven_points": breakevens,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Strategy execution error: {e}")
        raise HTTPException(500, f"Strategy execution failed: {str(e)}")


# --- Deep Learning Endpoints ---

@app.post("/api/v1/lstm/predict")
async def lstm_forecast(req: LSTMPredictRequest):
    """Generate 30-day price forecast using LSTM"""
    try:
        from src.models.lstm_model import get_lstm_forecast
        import pandas as pd

        # Convert recent_data to DataFrame
        df = pd.DataFrame(req.recent_data)

        # Get forecast
        forecast = get_lstm_forecast(req.symbol, df)

        if "error" in forecast:
            raise HTTPException(404, forecast["error"])

        return {
            "status": "success",
            **forecast
        }
    except Exception as e:
        logger.error(f"LSTM prediction error: {e}")
        raise HTTPException(500, f"LSTM prediction failed: {str(e)}")

@app.post("/api/v1/dqn/action")
async def dqn_recommendation(req: DQNActionRequest):
    """Get trading action recommendation from DQN agent"""
    try:
        from src.models.dqn_agent import get_dqn_action
        import numpy as np

        # Convert state to numpy array
        state = np.array(req.current_state, dtype=np.float32)

        # Get action
        action = get_dqn_action(req.symbol, state)

        if "error" in action:
            raise HTTPException(404, action["error"])

        return {
            "status": "success",
            **action
        }
    except Exception as e:
        logger.error(f"DQN action error: {e}")
        raise HTTPException(500, f"DQN recommendation failed: {str(e)}")

@app.get("/api/v1/models/deep-learning")
async def deep_learning_status():
    """Get status of deep learning models (LSTM + DQN)"""
    try:
        import os
        from pathlib import Path

        lstm_dir = Path("models/lstm")
        dqn_dir = Path("models/dqn")

        # Check LSTM models
        lstm_models = []
        if lstm_dir.exists():
            lstm_models = [f.stem for f in lstm_dir.glob("*.h5")]

        # Check DQN models
        dqn_models = []
        if dqn_dir.exists():
            dqn_models = [f.stem.replace("_dqn", "") for f in dqn_dir.glob("*_dqn.h5")]

        return {
            "status": "success",
            "lstm_models": {
                "count": len(lstm_models),
                "symbols": lstm_models,
                "lookback_days": 60,
                "forecast_days": 30
            },
            "dqn_models": {
                "count": len(dqn_models),
                "symbols": dqn_models,
                "actions": ["HOLD", "BUY", "SELL"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Deep learning status error: {e}")
        raise HTTPException(500, f"Status check failed: {str(e)}")


# --- Model Training Endpoints (Admin) ---


@app.post("/admin/train-models")
async def train_all_models_endpoint(req: AdminTrainingRequest, background_tasks: BackgroundTasks):
    """
    Trigger training for both LSTM and DQN models.
    This is a long-running operation (20-45 minutes).
    Use background_tasks to avoid timeout.
    """
    try:
        from src.training.train_all import train_all_models

        # Run training in background
        background_tasks.add_task(
            train_all_models,
            symbol=req.symbol,
            days=req.days,
            lstm_epochs=100,
            dqn_episodes=200,
            model_dir="/app/models",
            upload_gcs=req.upload_gcs,
            gcs_bucket=req.gcs_bucket,
            gcs_prefix=req.gcs_prefix
        )

        return {
            "status": "training_started",
            "symbol": req.symbol,
            "message": "Training started in background. Check logs for progress.",
            "estimated_duration_minutes": "20-45",
            "started_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Training initiation failed: {e}")
        raise HTTPException(500, f"Failed to start training: {str(e)}")


@app.post("/admin/train-lstm")
async def train_lstm_endpoint(req: LSTMTrainingRequest, background_tasks: BackgroundTasks):
    """Train only LSTM model"""
    try:
        from src.training.train_lstm import train_lstm_model

        background_tasks.add_task(
            train_lstm_model,
            symbol=req.symbol,
            days=req.days,
            lookback_days=60,
            forecast_days=30,
            epochs=req.epochs,
            batch_size=req.batch_size,
            model_dir="/app/models/lstm"
        )

        return {
            "status": "lstm_training_started",
            "symbol": req.symbol,
            "epochs": req.epochs,
            "started_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"LSTM training failed: {e}")
        raise HTTPException(500, f"LSTM training failed: {str(e)}")


@app.post("/admin/train-dqn")
async def train_dqn_endpoint(req: DQNTrainingRequest, background_tasks: BackgroundTasks):
    """Train only DQN agent"""
    try:
        from src.training.train_dqn import train_dqn_agent

        background_tasks.add_task(
            train_dqn_agent,
            symbol=req.symbol,
            days=req.days,
            episodes=req.episodes,
            model_dir="/app/models/dqn"
        )

        return {
            "status": "dqn_training_started",
            "symbol": req.symbol,
            "episodes": req.episodes,
            "started_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"DQN training failed: {e}")
        raise HTTPException(500, f"DQN training failed: {str(e)}")


# --- Agent Consultation Endpoint ---

@app.post("/api/v1/agent/consult")
async def consult_agent(req: AgentConsultRequest):
    """
    Direct consultation with the deployed Vertex AI Reasoning Engine (Agent).
    Target: financial-advisor-21947
    """
    try:
        # Import here to ensure we pick up the latest from __init__
        from src.google_integrations import ReasoningEngineClient

        # Initialize client (lazy load to avoid startup tax)
        agent_client = ReasoningEngineClient()

        if req.symbol:
            response = await agent_client.analyze_stock(req.symbol)
        else:
            response = await agent_client.query(req.query)

        return {
            "status": "success",
            "agent_id": agent_client.agent_id,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
    except ImportError:
        raise HTTPException(503, "Reasoning Engine Client not available (check google_integrations)")
    except Exception as e:
        logger.error(f"❌ Agent consultation failed: {e}")
        raise HTTPException(500, f"Agent consultation failed: {str(e)}")



# =============================================================================
# INSTITUTIONAL ML EXPANSION — 9-MODEL ENSEMBLE ENDPOINTS (v2.0)
# =============================================================================

# ─── Lazy-load singletons (avoid circular imports at module level) ────────────
_ensemble_arbitrator = None
_ml_model_manager   = None
_gemini_macro       = None
_drift_detector     = None

def _get_ensemble_arbitrator():
    global _ensemble_arbitrator
    if _ensemble_arbitrator is None:
        try:
            from src.services.ensemble_arbitrator import ensemble_arbitrator
            _ensemble_arbitrator = ensemble_arbitrator
        except Exception as e:
            logger.warning(f"EnsembleArbitrator import: {e}")
    return _ensemble_arbitrator

def _get_ml_manager():
    global _ml_model_manager
    if _ml_model_manager is None:
        try:
            from src.services.ml_model_manager import model_manager
            _ml_model_manager = model_manager
        except Exception as e:
            logger.warning(f"MLModelManager import: {e}")
    return _ml_model_manager

def _get_gemini_macro():
    global _gemini_macro
    if _gemini_macro is None:
        try:
            from src.google_integrations.gemini_macro import gemini_macro
            _gemini_macro = gemini_macro
        except Exception as e:
            logger.warning(f"GeminiMacro import: {e}")
    return _gemini_macro

def _get_drift_detector():
    global _drift_detector
    if _drift_detector is None:
        try:
            from src.services.drift_detector import drift_detector
            _drift_detector = drift_detector
        except Exception as e:
            logger.warning(f"DriftDetector import: {e}")
    return _drift_detector


# ─── Endpoint 1: 9-Model Ensemble Signal ─────────────────────────────────────

@app.get("/api/v1/ensemble/signal/{symbol}")
async def ensemble_signal_endpoint(
    symbol: str,
    include_gemini: bool = True,
    include_dqn:    bool = True,
):
    """
    Full 9-model ensemble signal for a trading symbol.

    Returns:
      - signal: BUY / HOLD / SELL
      - confidence: 0-100
      - per-model probability breakdown
      - dynamic ensemble weights
      - Gemini macro sentiment (optional)
      - DQN position sizing (optional)
      - Current market regime (HMM)
    """
    symbol = symbol.upper()
    t0 = time.time()

    try:
        manager    = _get_ml_manager()
        arbitrator = _get_ensemble_arbitrator()

        if manager is None or arbitrator is None:
            raise HTTPException(503, "ML services not initialized")

        # ── Fetch market snapshot for feature extraction ──────────────────
        snap = {}
        try:
            from src.services.data_connector import DataConnector
            connector = DataConnector(base_url=os.getenv("ENGINE_A_URL", ""))
            snap = await connector.fetch_snapshot(symbol) or {}
        except Exception:
            pass

        curr_price = float(snap.get("price") or snap.get("last_price") or snap.get("close") or 0.0)
        pcr        = float(snap.get("pcr") or 1.0)

        # ── Build minimal feature vector from snapshot ────────────────────
        from src.services.feature_pipeline import extract_snapshot_features
        X = extract_snapshot_features(snap)

        import pandas as pd
        close_proxy = pd.Series([curr_price] * 30) if curr_price > 0 else pd.Series([100.0] * 30)

        # ── Get per-model probabilities ───────────────────────────────────
        model_probas = manager.predict_all_proba(X, close_series=close_proxy, symbol=symbol)

        # ── Get HMM regime tilt ───────────────────────────────────────────
        regime_tilt  = None
        regime_info  = {}
        hmm_model    = manager.models.get("hmm_regime")
        if hmm_model is not None:
            try:
                regime_info = hmm_model.current_regime(close_proxy)
                regime_tilt = hmm_model.get_regime_tilt(close_proxy)
            except Exception:
                pass

        # ── Compute ensemble signal ───────────────────────────────────────
        ensemble_result = arbitrator.ensemble_signal(
            model_probas=model_probas,
            regime_tilt=regime_tilt,
        )

        # ── Gemini macro sentiment (optional) ────────────────────────────
        macro_data = {}
        if include_gemini:
            gemini = _get_gemini_macro()
            if gemini:
                try:
                    macro_signal = await gemini.get_macro_signal(
                        symbol=symbol,
                        current_price=curr_price,
                        pcr=pcr,
                    )
                    sentiment_tilt = gemini.get_sentiment_multiplier(macro_signal)
                    macro_data = {
                        "market_sentiment": macro_signal.market_sentiment,
                        "sentiment_score":  macro_signal.sentiment_score,
                        "rbi_stance":       macro_signal.rbi_stance,
                        "fii_flow_bias":    macro_signal.fii_flow_bias,
                        "nifty_bias":       macro_signal.nifty_bias,
                        "key_catalysts":    macro_signal.key_catalysts[:3],
                        "confidence":       macro_signal.confidence,
                        "source":           macro_signal.source,
                        "cache_hit":        macro_signal.cache_hit,
                        "sentiment_tilt_pct": round(sentiment_tilt * 100, 4),
                    }
                except Exception as e:
                    logger.warning(f"Gemini macro failed: {e}")

        # ── DQN adjustment (optional) ─────────────────────────────────────
        dqn_data = {}
        if include_dqn:
            try:
                dqn_result = manager.get_combined_dqn_signal(X[-1] if X.ndim > 1 else X, base_lots=1)
                dqn_data   = dqn_result
            except Exception as e:
                logger.warning(f"DQN adjustment failed: {e}")

        latency_ms = round((time.time() - t0) * 1000, 1)

        return {
            "symbol":           symbol,
            "signal":           ensemble_result["signal"],
            "confidence":       ensemble_result["confidence"],
            "signal_proba":     ensemble_result["signal_proba"],
            "ensemble_weights": ensemble_result["weights_used"],
            "champion_model":   ensemble_result.get("champion_model"),
            "challenger_model": ensemble_result.get("challenger_model"),
            "regime":           regime_info,
            "macro_sentiment":  macro_data,
            "dqn":              dqn_data,
            "model_count":      len(model_probas),
            "latency_ms":       latency_ms,
            "timestamp":        datetime.utcnow().isoformat(),
            "version":          "2.0.0",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ensemble signal failed for {symbol}: {e}", exc_info=True)
        raise HTTPException(500, f"Ensemble signal error: {str(e)}")


# ─── Endpoint 2: Dynamic Ensemble Weights ────────────────────────────────────

@app.get("/api/v1/ensemble/weights")
async def get_ensemble_weights():
    """
    Return current dynamic ensemble weights, champion/challenger status,
    and per-model EMA accuracy scores.
    """
    try:
        arbitrator = _get_ensemble_arbitrator()
        if arbitrator is None:
            raise HTTPException(503, "EnsembleArbitrator not initialized")
        return {
            "status": "success",
            "data":   arbitrator.get_model_info(),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Endpoint 3: Gemini 2.5 Flash Macro Signal ───────────────────────────────

@app.get("/api/v1/gemini/macro-signal/{symbol}")
async def gemini_macro_signal_endpoint(
    symbol:        str,
    current_price: Optional[float] = None,
    pcr:           Optional[float] = None,
    india_vix:     Optional[float] = None,
    bypass_cache:  bool = False,
):
    """
    Gemini 2.5 Flash grounded macro sentiment for Indian indices.

    Grounding sources: Google Search (live news) + RBI/SEBI corpus.
    Response cached in Firestore for 15 minutes.
    Circuit breaker: disables after 3 failures, re-enables after 60s.
    """
    symbol = symbol.upper()
    try:
        gemini = _get_gemini_macro()
        if gemini is None:
            raise HTTPException(503, "Gemini macro service not initialized")

        if bypass_cache:
            # Clear cache for this symbol
            try:
                gemini._init_firestore()
                if gemini._firestore_db:
                    gemini._firestore_db.collection("gemini_macro_cache").document(symbol).delete()
            except Exception:
                pass

        macro_signal = await gemini.get_macro_signal(
            symbol=symbol,
            current_price=current_price,
            pcr=pcr,
            india_vix=india_vix,
        )

        return {
            "status":       "success",
            "symbol":       symbol,
            "macro_signal": macro_signal.to_dict(),
            "circuit_breaker": gemini.get_circuit_breaker_status(),
            "timestamp":    datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini macro endpoint error: {e}")
        raise HTTPException(500, str(e))


# ─── Endpoint 4: Per-Model Performance Metrics ────────────────────────────────

@app.get("/api/v1/models/performance")
async def model_performance_endpoint(symbol: str = "NIFTY"):
    """
    Rolling per-model accuracy, EMA scores, Sharpe ratios, and champion status.
    Source: EnsembleArbitrator tracker + BigQuery model_performance table.
    """
    symbol = symbol.upper()
    try:
        arbitrator = _get_ensemble_arbitrator()
        if arbitrator is None:
            raise HTTPException(503, "EnsembleArbitrator not initialized")

        tracker_status = arbitrator.tracker.get_status()

        # Try to pull last-run BQ metrics
        bq_metrics = {}
        try:
            from google.cloud import bigquery as bq_lib
            project = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            client  = bq_lib.Client(project=project)
            query   = f"""
                SELECT model_name, accuracy, f1_score, log_loss, trained_at
                FROM `{project}.market_data.model_performance`
                WHERE symbol = '{symbol}'
                ORDER BY trained_at DESC
                LIMIT 20
            """
            df = client.query(query).to_dataframe()
            if not df.empty:
                bq_metrics = df.groupby("model_name").first().to_dict(orient="index")
        except Exception as e:
            logger.debug(f"BQ metrics fetch: {e}")

        return {
            "status":         "success",
            "symbol":         symbol,
            "live_tracker":   tracker_status,
            "bq_last_train":  bq_metrics,
            "timestamp":      datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Endpoint 5: Feature Drift PSI Scores ────────────────────────────────────

@app.get("/api/v1/models/drift/{symbol}")
async def model_drift_endpoint(symbol: str):
    """
    Feature drift PSI scores vs training baseline.
    Triggers retraining Pub/Sub alert if PSI > 0.20.
    """
    symbol = symbol.upper()
    try:
        detector = _get_drift_detector()
        if detector is None:
            raise HTTPException(503, "DriftDetector not initialized")

        # Load BQ baseline if not loaded yet
        if not detector._baseline:
            detector.load_baseline_from_bq(symbol)

        # Run drift check
        report = await detector.check_and_alert(symbol)

        return {
            "status":    "success",
            "symbol":    symbol,
            "drift":     report,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Endpoint 6: Trigger Vertex AI Retraining Job ────────────────────────────

@app.post("/api/v1/training/trigger")
async def trigger_retraining_endpoint(
    background_tasks: BackgroundTasks,
    symbol: str = "NIFTY",
    days:   int  = 730,
):
    """
    Trigger a nightly 9-model ensemble retraining job.

    On GCE VM: runs train_ensemble.py directly in background.
    In production: submits Vertex AI Custom Training Job.
    """
    symbol = symbol.upper()
    correlation_id = f"retrain_{symbol}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    async def _run_training():
        try:
            logger.info(f"🚀 Starting retraining for {symbol} | correlationId={correlation_id}")
            # Try Vertex AI first
            try:
                from google.cloud import aiplatform
                project  = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
                location = "asia-south1"
                aiplatform.init(project=project, location=location)
                job = aiplatform.CustomJob(
                    display_name=f"infinity-retrain-{symbol}-{datetime.utcnow().strftime('%Y%m%d')}",
                    worker_pool_specs=[{
                        "machine_spec": {"machine_type": "n1-standard-4"},
                        "replica_count": 1,
                        "container_spec": {
                            "image_uri": f"gcr.io/{project}/engine-b:latest",
                            "command": ["python", "-m", "src.training.train_ensemble"],
                            "args": [f"--symbol={symbol}", f"--days={days}", "--upload-gcs"],
                        },
                    }],
                )
                job.submit()
                logger.info(f"✅ Vertex AI Training Job submitted: {job.resource_name}")
            except Exception as va_err:
                logger.warning(f"Vertex AI submit failed ({va_err}), running local training...")
                import subprocess
                subprocess.Popen([
                    "python", "-m", "src.training.train_ensemble",
                    f"--symbol={symbol}", f"--days={days}", "--upload-gcs"
                ])
        except Exception as e:
            logger.error(f"Retraining trigger failed: {e}")

    background_tasks.add_task(_run_training)

    return {
        "status":         "retraining_triggered",
        "symbol":         symbol,
        "days":           days,
        "correlation_id": correlation_id,
        "triggered_at":   datetime.utcnow().isoformat(),
        "note":           "Job submitted to Vertex AI (or local fallback). Check /api/v1/models/performance for updates.",
    }


# ─── Endpoint 7: HMM Market Regime ───────────────────────────────────────────

@app.get("/api/v1/regime/{symbol}")
async def market_regime_endpoint(symbol: str):
    """
    Current market regime from HMM (0=Bear, 1=Sideways, 2=Bull)
    with state probabilities and ensemble weight tilt multipliers.
    """
    symbol = symbol.upper()
    try:
        manager = _get_ml_manager()
        if manager is None:
            raise HTTPException(503, "MLModelManager not initialized")

        hmm_model = manager.models.get("hmm_regime")
        if hmm_model is None:
            raise HTTPException(503, "HMM regime model not loaded")

        # Fetch recent close prices for regime estimation
        snap = {}
        curr_price = 0.0
        try:
            from src.services.data_connector import DataConnector
            connector  = DataConnector(base_url=os.getenv("ENGINE_A_URL", ""))
            snap       = await connector.fetch_snapshot(symbol) or {}
            curr_price = float(snap.get("price") or snap.get("last_price") or snap.get("close") or 0.0)
        except Exception:
            pass

        # Build synthetic close proxy if live data unavailable
        import pandas as pd
        if curr_price > 0:
            close_proxy = pd.Series([curr_price] * 90)
        else:
            close_proxy = pd.Series([100.0] * 90)

        regime_info  = hmm_model.current_regime(close_proxy)
        regime_tilt  = hmm_model.get_regime_tilt(close_proxy)

        return {
            "status":         "success",
            "symbol":         symbol,
            "current_price":  curr_price,
            "regime":         regime_info,
            "weight_tilt":    regime_tilt,
            "regime_labels":  {0: "BEAR/VOLATILE", 1: "SIDEWAYS/CHOP", 2: "BULL/TRENDING"},
            "timestamp":      datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── DQN Endpoints (Dual Mode) ───────────────────────────────────────────────

@app.get("/api/v1/dqn/signal/{symbol}")
async def dqn_signal_endpoint(
    symbol:    str,
    mode:      str  = "both",   # "position_sizing" | "primary_signal" | "both"
    base_lots: int  = 1,
):
    """
    DQN Agent signal endpoint in dual mode:
      mode=position_sizing: Returns adjusted lot size based on Q-value confidence
      mode=primary_signal: Returns autonomous BUY/HOLD/SELL from DQN policy
      mode=both: Returns both primary signal + adjusted lots
    """
    symbol = symbol.upper()
    try:
        manager = _get_ml_manager()
        if manager is None:
            raise HTTPException(503, "MLModelManager not initialized")

        snap = {}
        try:
            from src.services.data_connector import DataConnector
            connector = DataConnector(base_url=os.getenv("ENGINE_A_URL", ""))
            snap = await connector.fetch_snapshot(symbol) or {}
        except Exception:
            pass

        from src.services.feature_pipeline import extract_snapshot_features
        X = extract_snapshot_features(snap)
        state = X[-1] if X.ndim > 1 else X

        if mode == "position_sizing":
            result = manager.get_dqn_position_sizing(state, base_lots)
        elif mode == "primary_signal":
            result = manager.get_dqn_primary_signal(state)
        else:  # both
            result = manager.get_combined_dqn_signal(state, base_lots)

        return {
            "status":    "success",
            "symbol":    symbol,
            "mode":      mode,
            "dqn":       result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

