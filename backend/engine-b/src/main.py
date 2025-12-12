import os
import sys
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from io import StringIO

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from dhanhq import dhanhq
import uvicorn
from google.cloud import secretmanager

# ML/AI Libraries - Gradient Boosting Focus
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
import joblib

# Performance Optimization Imports (optional - graceful degradation)
# These will be initialized after logger is available
PERFORMANCE_MODULES_AVAILABLE = False

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

# NLP for Sentiment
try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

# Google Cloud Integrations (Official SDKs)
try:
    from src.google_integrations import (
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
    print(f"⚠️ Google integrations not available: {e}")

# Enhanced GenAI with Function Calling (v3.7.7)
try:
    from src.google_integrations import (
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
    print(f"⚠️ Enhanced GenAI not available: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("InfinityAI.EngineB")

# Now try to import performance modules (after logger is available)
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from performance import CacheManager, ConnectionPoolManager, HealthMonitor, CircuitBreaker
    PERFORMANCE_MODULES_AVAILABLE = True
    logger.info("✅ Performance modules loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Performance modules not available (optional): {e}")
    # Define placeholders when not available
    CacheManager = None
    ConnectionPoolManager = None
    HealthMonitor = None
    CircuitBreaker = None

# Import Indian Market Knowledge Base (after logger is defined)
try:
    from services.market_knowledge import IndianMarketKnowledge
    MARKET_KNOWLEDGE = IndianMarketKnowledge()
    HAS_MARKET_KNOWLEDGE = True
    logger.info("✅ Indian Market Knowledge Base loaded successfully")
except ImportError as e:
    HAS_MARKET_KNOWLEDGE = False
    MARKET_KNOWLEDGE = None
    logger.warning(f"⚠️ Market Knowledge module not available: {e}")

# --- Google Cloud Integrations ---
TRADING_LOGGER_B = None
MODEL_STORAGE_B = None
GENAI_CLIENT_B = None
SIGNAL_AGENT = None
RISK_AGENT = None
MARKET_AGENT = None

if HAS_GOOGLE_INTEGRATIONS:
    try:
        PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0779271931")

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
        logger.warning(f"⚠️ Error initializing Google integrations: {e}")

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
    logger.warning(f"⚠️ Enhanced Trading AI not available: {e}")

# --- Enhanced GenAI Client with Function Calling (v3.7.7) ---
ENHANCED_GENAI_CLIENT = None
NEWS_AGGREGATOR = None

if HAS_ENHANCED_GENAI:
    try:
        PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0779271931")

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
        logger.warning(f"⚠️ Error initializing Enhanced GenAI: {e}")

# Initialize Enhanced Trading AI with GenAI client
if HAS_ENHANCED_TRADING_AI and GENAI_CLIENT_B:
    try:
        ENHANCED_TRADING_AI = create_enhanced_trading_ai(GENAI_CLIENT_B)
        logger.info("✅ Enhanced Trading AI v4.0 initialized with Gemini")
    except Exception as e:
        logger.warning(f"⚠️ Error initializing Enhanced Trading AI: {e}")

app = FastAPI(
    title="InfinityAI.Pro - Engine B (Production)",
    description="SEBI 2025 Compliant Algorithmic Trading Engine with Real-Time ML Inference and Vertex AI",
    version="3.7.7-vertexai"
)

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

# Add CORS middleware
# CORS allowed origins for production
ALLOWED_ORIGINS = [
    "https://infinityai.pro",
    "https://www.infinityai.pro",
    "https://app.infinityai.pro",
    "https://engine-a.infinityai.pro",
    "https://engine-b.infinityai.pro",
    "https://engine-c.infinityai.pro",
    "https://gen-lang-client-0779271931.web.app",
    "https://gen-lang-client-0779271931.firebaseapp.com",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# SEBI 2025 MARKET CONFIGURATION
# =====================================================================
MARKET_CONFIG = {
    "LOT_SIZES": {
        "NIFTY": 75,           # Updated Nov 2024
        "BANKNIFTY": 30,       # Updated Nov 2024
        "FINNIFTY": 65,        # Updated Nov 2024
        "MIDCPNIFTY": 120,     # Updated Nov 2024
        "NIFTYNXT50": 25,
        "SENSEX": 20,
        "BANKEX": 30
    },
    "EXPIRY_DAYS": {
        "MIDCPNIFTY": 0,       # Monday
        "FINNIFTY": 1,         # Tuesday
        "BANKNIFTY": 2,        # Wednesday
        "NIFTY": 3,            # Thursday
        "SENSEX": 4,           # Friday
        "BANKEX": 4            # Friday
    },
    "MARGIN_RULES_2025": {
        "OPTION_BUY_PREMIUM": 1.0,  # 100% Upfront
        "INTRADAY_EQUITY": 0.20,    # 20% Upfront (VaR + ELM)
        "NO_SPREAD_BENEFIT_EXPIRY": True  # Effective Feb 10, 2025
    },
    "HOLIDAYS_2025": [
        "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10",
        "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15",
        "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22",
        "2025-11-05", "2025-12-25"
    ],
    "TRADING_SESSIONS": {
        "pre_open": {"start": "09:00", "end": "09:08"},
        "normal": {"start": "09:15", "end": "15:30"},
        "post_close": {"start": "15:40", "end": "16:00"}
    }
}

# --- Secret Manager Helper ---
def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0779271931")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        # Strip any trailing whitespace/newlines from the secret
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.warning(f"Secret fetch failed for {secret_id}: {e}")
        return ""

# =====================================================================
# DYNAMIC SYMBOL MAPPER (Production Grade)
# =====================================================================
class SymbolMapper:
    """
    Dynamic Symbol Mapping Service.
    Fetches the daily Master Scrip List from DhanHQ to ensure accurate mapping.
    """
    MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"

    def __init__(self):
        self.symbol_map: Dict[str, str] = {}  # Symbol -> Security ID
        self.id_map: Dict[int, str] = {}      # Security ID -> Symbol
        self.meta_map: Dict[int, Dict] = {}   # Security ID -> Metadata
        self.last_updated: Optional[datetime] = None
        self._load_fallback_mapping()

    def _load_fallback_mapping(self):
        """Load fallback mapping for critical symbols"""
        fallback = {
            # NSE Indices
            "NIFTY": "13", "NIFTY50": "13", "BANKNIFTY": "25", "FINNIFTY": "26",
            # NSE Equities
            "RELIANCE": "1333", "TCS": "2968", "HDFCBANK": "1394", "INFY": "1594",
            "ICICIBANK": "1270", "HINDUNILVR": "1552", "ITC": "1663", "SBIN": "2837",
            "BHARTIARTL": "411", "KOTAKBANK": "1922", "LT": "2031", "AXISBANK": "152",
            "ASIANPAINT": "102", "MARUTI": "2170", "SUNPHARMA": "2936", "TITAN": "3003",
            "TATAMOTORS": "2975", "WIPRO": "3145", "ULTRACEMCO": "3073", "POWERGRID": "2640",
            "NTPC": "2379", "M&M": "2142", "TATASTEEL": "3012", "JSWSTEEL": "1828",
            "INDUSINDBK": "1600", "BAJFINANCE": "163", "BAJAJFINSV": "164",
            "HCLTECH": "1391", "DRREDDY": "1165", "ADANIENT": "25", "ADANIPORTS": "26",
            # MCX Commodities (Security IDs from Dhan MCX Master)
            "CRUDEOIL": "428416", "CRUDEOILM": "428424",
            "GOLD": "428219", "GOLDM": "428226", "GOLDPETAL": "428281",
            "SILVER": "428359", "SILVERM": "428366", "SILVERMIC": "428371",
            "NATURALGAS": "428431", "COPPER": "428439", "ZINC": "428456",
            "LEAD": "428463", "ALUMINIUM": "428478", "NICKEL": "428485"
        }
        self.symbol_map = fallback
        self.id_map = {int(v): k for k, v in fallback.items()}

    async def refresh(self):
        """Downloads and parses the master scrip CSV from DhanHQ (optimized with connection pooling)"""
        global aiohttp_session

        if not HAS_AIOHTTP:
            logger.warning("aiohttp not available, using fallback symbol map")
            return

        try:
            logger.info("🔄 Refreshing Master Scrip List from DhanHQ...")

            # Use shared session if available, otherwise create temp session
            session = aiohttp_session
            should_close = False
            if session is None or session.closed:
                session = aiohttp.ClientSession()
                should_close = True

            try:
                async with session.get(self.MASTER_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to fetch CSV: {resp.status}")
                    csv_text = await resp.text()
            finally:
                if should_close:
                    await session.close()

            # Parse CSV
            df = pd.read_csv(
                StringIO(csv_text),
                usecols=['SEM_TRADING_SYMBOL', 'SEM_SMST_SECURITY_ID', 'SEM_EXM_EXCH_ID', 'SEM_SERIES', 'SEM_LOT_UNITS'],
                low_memory=False
            )

            # Filter for NSE Equity, Derivatives & MCX Commodities
            df = df[df['SEM_EXM_EXCH_ID'].isin(['NSE', 'NSE_FNO', 'MCX'])]

            # Build Maps
            self.symbol_map = pd.Series(
                df.SEM_SMST_SECURITY_ID.astype(str).values,
                index=df.SEM_TRADING_SYMBOL
            ).to_dict()

            self.id_map = pd.Series(
                df.SEM_TRADING_SYMBOL.values,
                index=df.SEM_SMST_SECURITY_ID.astype(int)
            ).to_dict()

            # Handle duplicate security IDs by keeping first occurrence
            df_unique = df.drop_duplicates(subset=['SEM_SMST_SECURITY_ID'], keep='first')
            self.meta_map = df_unique.set_index('SEM_SMST_SECURITY_ID')[['SEM_SERIES', 'SEM_LOT_UNITS']].to_dict('index')

            # Merge fallback critical symbols (MCX commodities use expiry-based names in CSV)
            fallback_critical = {
                "CRUDEOIL": "428416", "CRUDEOILM": "428424",
                "GOLD": "428219", "GOLDM": "428226", "GOLDPETAL": "428281",
                "SILVER": "428359", "SILVERM": "428366", "SILVERMIC": "428371",
                "NATURALGAS": "428431", "COPPER": "428439", "ZINC": "428456",
                "LEAD": "428463", "ALUMINIUM": "428478", "NICKEL": "428485",
                "NIFTY": "13", "NIFTY50": "13", "BANKNIFTY": "25", "FINNIFTY": "26"
            }
            for sym, sec_id in fallback_critical.items():
                if sym not in self.symbol_map:
                    self.symbol_map[sym] = sec_id
                    logger.info(f"📌 Added fallback mapping: {sym} -> {sec_id}")

            self.last_updated = datetime.now()
            logger.info(f"✅ Symbol Map Updated: {len(self.symbol_map)} symbols loaded (incl. fallback)")

        except Exception as e:
            logger.error(f"❌ Symbol Map Refresh Failed: {e}, reloading fallback")
            self._load_fallback_mapping()  # Restore fallback mappings on failure

    def get_id(self, symbol: str) -> Optional[str]:
        return self.symbol_map.get(symbol.upper())

    def get_symbol(self, sec_id: str) -> Optional[str]:
        try:
            return self.id_map.get(int(sec_id))
        except:
            return None

    def get_metadata(self, sec_id: str) -> Dict:
        try:
            return self.meta_map.get(int(sec_id), {})
        except:
            return {}

SYMBOL_MAPPER = SymbolMapper()

# =====================================================================
# API MODELS
# =====================================================================
class SignalRequest(BaseModel):
    symbol: str
    fast: bool = False
    news_headlines: Optional[List[str]] = None  # For sentiment-enhanced signals
    timeframe: str = "1d"

class SignalResponse(BaseModel):
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: float
    predicted_price: float
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    timestamp: str
    model_version: str
    sentiment_score: Optional[float] = None
    data_source: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None

class TrainingRequest(BaseModel):
    symbol: str
    historical_days: int = 365
    lookahead_days: int = 5
    n_estimators: int = 100
    max_depth: int = 6
    learning_rate: float = 0.1
    use_sentiment: bool = False

class TrainingResponse(BaseModel):
    status: str
    symbol: str
    historical_days: int
    samples_used: int
    features_count: int
    model_accuracies: Dict[str, float]
    training_time_seconds: float
    data_source: str
    timestamp: str

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    timestamp: str

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
        self.trained_symbols: set = set()
        self.version = "v3.6-instrument-signals"
        self.capabilities = {
            "xgboost": True,
            "lightgbm": True,
            "catboost": HAS_CATBOOST,
            "random_forest": True,
            "transformers": HAS_TRANSFORMERS,
            "nltk_sentiment": HAS_NLTK,
            "ta_lib": HAS_TA_LIB,
            "yfinance": HAS_YFINANCE,
            "weighted_voting": True
        }
        self._initialize_models()

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

            if HAS_NLTK:
                try:
                    self.models['nltk_sentiment'] = SentimentIntensityAnalyzer()
                    logger.info("✅ NLTK VADER sentiment initialized")
                except Exception as e:
                    logger.warning(f"⚠️ NLTK sentiment init failed: {e}")

            if HAS_TRANSFORMERS:
                try:
                    self.models['transformer_sentiment'] = pipeline(
                        "sentiment-analysis",
                        model="distilbert-base-uncased-finetuned-sst-2-english"
                    )
                    logger.info("✅ Transformer sentiment model loaded")
                except Exception as e:
                    logger.warning(f"⚠️ Transformer sentiment init failed: {e}")

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

    def weighted_ensemble_predict(self, X_scaled: np.ndarray) -> tuple:
        """
        Make weighted ensemble prediction.
        Returns (predicted_class, confidence, votes_detail)
        """
        weights = self.get_ensemble_weights()
        class_votes = {0: 0.0, 1: 0.0, 2: 0.0}  # SELL, HOLD, BUY
        votes_detail = {}

        for model_name, weight in weights.items():
            model = self.get_model(model_name)
            if model is not None:
                try:
                    # Get probability predictions if available
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X_scaled)[0]
                        for cls_idx, prob in enumerate(proba):
                            if cls_idx < 3:  # Ensure we only use valid classes
                                class_votes[cls_idx] += prob * weight
                        votes_detail[model_name] = {
                            'prediction': int(np.argmax(proba)),
                            'weight': weight,
                            'probabilities': proba.tolist()
                        }
                    else:
                        pred = model.predict(X_scaled)[0]
                        class_votes[int(pred)] += weight
                        votes_detail[model_name] = {
                            'prediction': int(pred),
                            'weight': weight
                        }
                except Exception as e:
                    logger.warning(f"Ensemble prediction failed for {model_name}: {e}")

        # Get final prediction
        final_class = max(class_votes.items(), key=lambda x: x[1])[0]
        total_weight = sum(class_votes.values())
        confidence = class_votes[final_class] / total_weight if total_weight > 0 else 0.5

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
        "NIFTYBANK": "^NSEBANK", "FINNIFTY": "NIFTY_FIN_SERVICE.NS"
    }

    def __init__(self):
        self.dhan = None
        self.cache: Dict[str, tuple] = {}
        self.data_source_stats = {"dhan": 0, "yahoo": 0, "synthetic": 0}
        self._init_dhan_client()

    def _init_dhan_client(self):
        """Initialize DhanHQ client with GCP secrets"""
        try:
            client_id = os.getenv("DHAN_CLIENT_ID") or get_secret("dhan-client-id")
            access_token = os.getenv("DHAN_ACCESS_TOKEN") or get_secret("dhan-access-token")

            if client_id and access_token and client_id != "":
                self.dhan = dhanhq(client_id, access_token)
                logger.info("✅ DhanHQ client initialized with credentials")
            else:
                logger.warning("⚠️ DhanHQ credentials not found, will use Yahoo Finance")
        except Exception as e:
            logger.warning(f"⚠️ DhanHQ init failed: {e}")

    async def fetch_data(self, symbol: str, days: int = 365) -> tuple:
        """
        Smart Fetch with source tracking:
        1. Try DhanHQ Historical API
        2. Fallback to Yahoo Finance
        3. Generate synthetic data as last resort
        Returns: (DataFrame, source_name)
        """
        symbol = symbol.upper()
        cache_key = f"{symbol}_{days}"

        # Check cache (5 min TTL)
        if cache_key in self.cache:
            cached_data, cached_time, source = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < 300:
                return cached_data, source

        df = pd.DataFrame()
        source = "synthetic"

        # Method 1: DhanHQ API
        if self.dhan:
            try:
                sec_id = SYMBOL_MAPPER.get_id(symbol)
                if sec_id:
                    to_date = datetime.now().strftime("%Y-%m-%d")
                    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

                    # Determine exchange segment and instrument type
                    # MCX Commodities (Crude Oil, Gold, Silver)
                    if symbol in ["CRUDEOIL", "CRUDEOILM", "GOLD", "GOLDM", "GOLDPETAL", "SILVER", "SILVERM", "SILVERMIC",
                                  "NATURALGAS", "COPPER", "ZINC", "LEAD", "ALUMINIUM", "NICKEL", "COTTON"]:
                        exchange_segment = "MCX_COMM"
                        instrument_type = "FUTCOM"  # Futures of Commodity
                        logger.info(f"🏭 MCX Commodity detected: {symbol} (sec_id={sec_id}) using MCX_COMM/FUTCOM")
                    # NSE/BSE Indices
                    elif symbol in ["NIFTY", "NIFTY50", "BANKNIFTY", "NIFTYBANK", "FINNIFTY"]:
                        exchange_segment = "IDX_I"
                        instrument_type = "INDEX"
                    # Default: NSE Equity
                    else:
                        exchange_segment = "NSE_EQ"
                        instrument_type = "EQUITY"

                    logger.info(f"📡 Calling DhanHQ historical_daily_data for {symbol}: sec_id={sec_id}, segment={exchange_segment}")
                    resp = self.dhan.historical_daily_data(
                        security_id=sec_id,
                        exchange_segment=exchange_segment,
                        instrument_type=instrument_type,
                        from_date=from_date,
                        to_date=to_date
                    )

                    logger.info(f"📡 DhanHQ response for {symbol}: status={resp.get('status') if resp else 'None'}, has_data={bool(resp.get('data') if resp else False)}")

                    if resp and resp.get('status') == 'success' and resp.get('data'):
                        data = resp['data']
                        df = pd.DataFrame(data)

                        # Normalize columns
                        col_map = {
                            'start_Time': 'Date', 'timestamp': 'Date',
                            'open': 'Open', 'high': 'High', 'low': 'Low',
                            'close': 'Close', 'volume': 'Volume'
                        }
                        df.rename(columns=col_map, inplace=True)

                        if 'Date' in df.columns:
                            df['Date'] = pd.to_datetime(df['Date'])
                            df.set_index('Date', inplace=True)

                        if len(df) >= 50:
                            source = "dhan"
                            self.data_source_stats["dhan"] += 1
                            logger.info(f"📊 Fetched {len(df)} days from DhanHQ for {symbol}")
                        else:
                            logger.warning(f"⚠️ DhanHQ returned only {len(df)} rows for {symbol}, need at least 50")
                    else:
                        logger.warning(f"⚠️ DhanHQ returned non-success for {symbol}: {resp}")
                else:
                    logger.warning(f"⚠️ No security ID found for {symbol} in SymbolMapper")
            except Exception as e:
                logger.warning(f"DhanHQ fetch failed for {symbol}: {e}")

        # Method 2: Yahoo Finance Fallback
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

        # Method 3: Synthetic Data (Last Resort)
        if df.empty or len(df) < 50:
            logger.warning(f"⚠️ Using synthetic data for {symbol}")
            df = self._generate_synthetic_data(symbol, days)
            source = "synthetic"
            self.data_source_stats["synthetic"] += 1

        # Cache result
        self.cache[cache_key] = (df, datetime.now(), source)
        return df, source

    def _generate_synthetic_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Generate realistic synthetic OHLCV data"""
        np.random.seed(hash(symbol) % 2**32)

        base_prices = {
            "NIFTY": 24500, "BANKNIFTY": 52000, "FINNIFTY": 23500,
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

                # MACD
                macd = ta_lib.trend.MACD(df['close'])
                df['MACD_12_26_9'] = macd.macd()
                df['MACDh_12_26_9'] = macd.macd_diff()
                df['MACDs_12_26_9'] = macd.macd_signal()

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

                # Volatility - Bollinger Bands
                bb = ta_lib.volatility.BollingerBands(df['close'], window=20, window_dev=2)
                df['BBL_20_2.0'] = bb.bollinger_lband()
                df['BBM_20_2.0'] = bb.bollinger_mavg()
                df['BBU_20_2.0'] = bb.bollinger_hband()
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

        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD_12_26_9'] = ema12 - ema26
        df['MACDs_12_26_9'] = df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()
        df['MACDh_12_26_9'] = df['MACD_12_26_9'] - df['MACDs_12_26_9']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df['BBM_20_2.0'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BBU_20_2.0'] = df['BBM_20_2.0'] + (bb_std * 2)
        df['BBL_20_2.0'] = df['BBM_20_2.0'] - (bb_std * 2)
        df['BBB_20_2.0'] = (df['BBU_20_2.0'] - df['BBL_20_2.0']) / df['BBM_20_2.0']

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

        # Create labels based on future returns
        df['Future_Return'] = (df['Close'].shift(-lookahead) - df['Close']) / df['Close']
        df['Label'] = 1  # Default: HOLD
        df.loc[df['Future_Return'] > 0.01, 'Label'] = 2  # BUY
        df.loc[df['Future_Return'] < -0.01, 'Label'] = 0  # SELL

        df = df.dropna()

        if len(df) < 100:
            raise ValueError("Insufficient data for training (need at least 100 samples)")

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

# =====================================================================
# PERFORMANCE OPTIMIZATION - Global Instances for 24/7 Operation
# =====================================================================
# Using Any type to avoid NameError when performance modules not available
perf_cache: Optional[Any] = None
connection_manager: Optional[Any] = None
health_monitor: Optional[Any] = None
aiohttp_session: Optional[aiohttp.ClientSession] = None

# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.on_event("startup")
async def startup_event():
    """Bootstrap application state with performance optimizations"""
    global perf_cache, connection_manager, health_monitor, aiohttp_session

    # Initialize performance modules
    if PERFORMANCE_MODULES_AVAILABLE and CacheManager is not None:
        try:
            perf_cache = CacheManager(max_size=5000, default_ttl=60.0, name="engine_b")
            await perf_cache.initialize()
            connection_manager = ConnectionPoolManager()
            await connection_manager.initialize()
            health_monitor = HealthMonitor()
            logger.info("✅ Performance modules initialized for Engine B")
        except Exception as e:
            logger.warning(f"⚠️ Performance modules init failed: {e}")

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

    await SYMBOL_MAPPER.refresh()
    logger.info("🚀 InfinityAI Engine B Started (Performance Optimized)")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown with cleanup"""
    global aiohttp_session, connection_manager, health_monitor, perf_cache

    logger.info("🛑 Engine B shutting down...")

    if aiohttp_session:
        await aiohttp_session.close()
    if connection_manager:
        await connection_manager.shutdown()
    if health_monitor:
        await health_monitor.stop_monitoring()
    if perf_cache:
        await perf_cache.shutdown()

    logger.info("✅ Engine B cleanup complete")

@app.get("/healthz")
@app.get("/health")
@app.get("/api/health")
async def healthz():
    return {
        "status": "healthy",
        "service": "engine-b-ai-ml-prod",
        "version": "4.0-enhanced-trading-ai",
        "capabilities": MODEL_STORE.capabilities,
        "dhan_connected": MARKET_ENGINE.dhan is not None,
        "google_integrations": {
            "genai": GENAI_CLIENT_B is not None,
            "cloud_logging": TRADING_LOGGER_B is not None,
            "cloud_storage": MODEL_STORAGE_B is not None,
            "signal_agent": SIGNAL_AGENT is not None,
            "risk_agent": RISK_AGENT is not None,
            "market_agent": MARKET_AGENT is not None,
            "enhanced_trading_ai": ENHANCED_TRADING_AI is not None
        },
        "enhanced_features": {
            "indian_market_knowledge": HAS_ENHANCED_TRADING_AI,
            "sebi_2025_compliance": HAS_ENHANCED_TRADING_AI,
            "smart_entry_exit": HAS_ENHANCED_TRADING_AI,
            "position_sizing": HAS_ENHANCED_TRADING_AI,
            "risk_management": HAS_ENHANCED_TRADING_AI
        },
        "timestamp": datetime.utcnow().isoformat()
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
    """Returns current market status based on 2025 calendar"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    is_holiday = date_str in MARKET_CONFIG["HOLIDAYS_2025"]
    is_weekend = now.weekday() >= 5

    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    is_open_time = market_open <= now <= market_close

    status = "CLOSED"
    if not is_holiday and not is_weekend and is_open_time:
        status = "OPEN"

    next_holiday = next((h for h in MARKET_CONFIG["HOLIDAYS_2025"] if h > date_str), "2026-01-01")

    return {
        "status": status,
        "is_holiday": is_holiday,
        "is_weekend": is_weekend,
        "server_time": now.isoformat(),
        "next_holiday": next_holiday,
        "trading_sessions": MARKET_CONFIG["TRADING_SESSIONS"]
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

    # Initialize scoring
    score = 0
    reasons = []

    # RSI Analysis
    rsi = latest.get('RSI_14')
    if rsi is not None:
        if rsi < 30:
            score += 2
            reasons.append("RSI Oversold")
        elif rsi > 70:
            score -= 2
            reasons.append("RSI Overbought")

    # EMA Trend
    ema_50 = latest.get('EMA_50')
    if ema_50 is not None:
        if current_price > ema_50:
            score += 1
            reasons.append("Above EMA 50")
        else:
            score -= 1
            reasons.append("Below EMA 50")

    # MACD
    macd = latest.get('MACD_12_26_9')
    macd_signal = latest.get('MACDs_12_26_9')
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            score += 1
            reasons.append("MACD Bullish")
        else:
            score -= 1
            reasons.append("MACD Bearish")

    # ADX Trend Strength
    adx = latest.get('ADX_14')
    if adx is not None and adx > 25:
        score = int(score * 1.5)
        reasons.append(f"Strong Trend (ADX: {adx:.1f})")

    # Sentiment Analysis (if headlines provided)
    sentiment_score = None
    if req.news_headlines:
        sentiment_score = SENTIMENT_ANALYZER.aggregate_headlines(req.news_headlines)
        if sentiment_score > 0.3:
            score += 2
            reasons.append(f"Positive Sentiment ({sentiment_score:.2f})")
        elif sentiment_score < -0.3:
            score -= 2
            reasons.append(f"Negative Sentiment ({sentiment_score:.2f})")

    # ML Model Enhancement (if trained) - Using Weighted Ensemble
    ml_used = False
    ensemble_detail = None
    if symbol in MODEL_STORE.trained_symbols:
        try:
            feature_cols = [c for c in MARKET_ENGINE.get_feature_columns() if c in df_features.columns]
            X = df_features[feature_cols].iloc[-1:].values
            X_scaled = MODEL_STORE.scalers['standard'].transform(X)

            # Use weighted ensemble prediction
            ml_class, ml_confidence, ensemble_detail = MODEL_STORE.weighted_ensemble_predict(X_scaled)

            if ml_class == 2:  # BUY
                score += 3
                reasons.append(f"ML Ensemble: BUY ({ml_confidence:.1%} confidence)")
            elif ml_class == 0:  # SELL
                score -= 3
                reasons.append(f"ML Ensemble: SELL ({ml_confidence:.1%} confidence)")
            else:  # HOLD
                reasons.append(f"ML Ensemble: HOLD ({ml_confidence:.1%} confidence)")

            ml_used = True
        except Exception as e:
            logger.warning(f"ML inference failed: {e}")

    # Determine final signal
    if score >= 3:
        signal = "BUY"
    elif score <= -3:
        signal = "SELL"
    else:
        signal = "HOLD"

    # Calculate confidence
    confidence = min(95, max(30, 50 + abs(score) * 8))

    # Risk calculations
    atr = latest.get('ATRr_14', current_price * 0.02)
    stop_loss, target = RISK_ENGINE.get_stop_loss_target(current_price, atr, signal)

    # Predicted price
    if signal == "BUY":
        predicted_price = round(current_price * 1.02, 2)
    elif signal == "SELL":
        predicted_price = round(current_price * 0.98, 2)
    else:
        predicted_price = round(current_price, 2)

    return SignalResponse(
        symbol=symbol,
        signal=signal,
        confidence=confidence,
        predicted_price=predicted_price,
        current_price=round(current_price, 2),
        stop_loss=stop_loss,
        target=target,
        timestamp=datetime.utcnow().isoformat(),
        model_version=MODEL_STORE.version + ("-ml" if ml_used else "-rules"),
        sentiment_score=sentiment_score,
        data_source=data_source,
        analysis={
            "rsi": round(rsi, 2) if rsi else None,
            "adx": round(adx, 2) if adx else None,
            "trend": "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral",
            "key_factors": reasons,
            "score": score
        }
    )

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
                "trading_hours": "09:15 - 15:30 IST"
            },
            "bse": {
                "name": "Bombay Stock Exchange",
                "indices": ["SENSEX", "BSE 100", "BSE 200"],
                "trading_hours": "09:15 - 15:30 IST"
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


class BatchSignalsRequest(BaseModel):
    """Request model for batch signals"""
    symbols: List[str]
    fast: bool = True


@app.post("/api/v1/signal/batch")
@app.post("/api/v1/signals/batch")  # Alias for frontend compatibility
async def generate_batch_signals(request: BatchSignalsRequest):
    """Generate signals for multiple symbols"""
    if len(request.symbols) > 50:
        raise HTTPException(status_code=422, detail="Maximum 50 symbols per batch")

    signals = []
    for symbol in request.symbols:
        try:
            signal = await generate_signal(SignalRequest(symbol=symbol, fast=request.fast))
            signals.append(signal)
        except Exception as e:
            logger.error(f"Batch signal error for {symbol}: {e}")

    return {
        "signals": signals,
        "total": len(signals),
        "timestamp": datetime.utcnow().isoformat()
    }


class InstrumentSignalsRequest(BaseModel):
    """Request model for instrument-specific signals"""
    instruments: List[str]  # e.g., ['equities', 'nifty-options', 'banknifty-options']
    min_confidence: float = 0.75
    strategy: Optional[str] = "ai-signals"
    max_signals: int = 10


@app.post("/api/v1/signals/instruments")
async def generate_instrument_signals(req: InstrumentSignalsRequest):
    """
    Generate AI signals filtered by trading instruments.

    Supported instruments:
    - equities: NSE/BSE stocks
    - nifty-options: NIFTY 50 Index Options
    - banknifty-options: Bank NIFTY Index Options
    - sensex-options: BSE SENSEX Options
    - finnifty-options: Financial Services NIFTY Options
    - crude-options: MCX Crude Oil Options
    - gold-options: MCX Gold Options
    - silver-options: MCX Silver Options
    """
    # Map instruments to symbols to analyze
    instrument_symbols = {
        "equities": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "WIPRO", "ITC", "BHARTIARTL", "LT"],
        "nifty-options": ["NIFTY"],
        "banknifty-options": ["BANKNIFTY"],
        "sensex-options": ["SENSEX"],
        "finnifty-options": ["FINNIFTY"],
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

    logger.info(f"📊 Generating signals for instruments: {req.instruments}")
    logger.info(f"📈 Analyzing symbols: {symbols_to_analyze}")

    # Generate signals for each symbol
    all_signals = []
    for symbol in symbols_to_analyze:
        try:
            signal = await generate_signal(SignalRequest(symbol=symbol, fast=True))

            # Determine which instrument this symbol belongs to
            instrument_type = None
            for instrument, syms in instrument_symbols.items():
                if symbol in syms:
                    instrument_type = instrument
                    break

            signal_dict = signal.dict() if hasattr(signal, 'dict') else signal
            signal_dict["instrument_type"] = instrument_type
            signal_dict["security_id"] = get_security_id(symbol)  # Add security ID for execution

            # Only include signals meeting confidence threshold
            if signal_dict.get("confidence", 0) >= req.min_confidence:
                all_signals.append(signal_dict)

        except Exception as e:
            logger.warning(f"Signal generation failed for {symbol}: {e}")

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
        "SENSEX": "1",
        "FINNIFTY": "26009",
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
async def train_batch_models(symbols: List[str] = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK"]):
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
                "status": 'loaded' if MODEL_STORE.get_model(name) else 'not_available'
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
class PositionAnalysisRequest(BaseModel):
    """Request model for position analysis"""
    symbol: str
    trading_symbol: str
    security_id: str
    position_type: str  # LONG or SHORT
    exchange_segment: str
    product_type: str
    buy_avg: float
    cost_price: float
    buy_qty: int
    sell_qty: int = 0
    net_qty: int
    realized_profit: float = 0.0
    unrealized_profit: float = 0.0
    expiry_date: Optional[str] = None
    option_type: Optional[str] = None  # CALL or PUT
    strike_price: Optional[float] = None
    current_price: Optional[float] = None

class PositionAnalysisResponse(BaseModel):
    """Response model for position analysis"""
    symbol: str
    analysis: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    ai_recommendation: Dict[str, Any]
    market_context: Dict[str, Any]
    timestamp: str

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

class GeminiSignalRequest(BaseModel):
    """Request model for Gemini-powered signal generation"""
    symbol: str
    current_price: float
    historical_data: Optional[Dict[str, Any]] = None
    technical_indicators: Optional[Dict[str, float]] = None
    news_context: Optional[str] = None


class AgentAnalysisRequest(BaseModel):
    """Request model for agent-based analysis"""
    symbol: str
    market_data: Dict[str, Any]
    analysis_type: str = "comprehensive"  # signal, risk, market, comprehensive


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
        from src.google_integrations import TradingPrompt
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

class EnhancedSignalRequest(BaseModel):
    """Request for enhanced AI trading signal with comprehensive context."""
    symbol: str
    current_price: float
    technical_data: Optional[Dict[str, Any]] = None
    market_context: Optional[Dict[str, Any]] = None
    news_sentiment: Optional[str] = None
    portfolio_context: Optional[Dict[str, Any]] = None


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
            from src.google_integrations import TradingPrompt
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
            "reasoning": signal.reasoning,
            "version": "infinityai-enhanced-v4.0",
            "model": "gemini-2.0-flash",
            "timestamp": signal.timestamp
        }

    except Exception as e:
        logger.error(f"Error generating enhanced signal: {e}")
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

class EnhancedSignalRequest(BaseModel):
    """Request for enhanced trading signal with function calling"""
    symbol: str
    analysis_type: str = "comprehensive"  # intraday, swing, options, comprehensive
    auto_execute: bool = False
    fetch_live_data: bool = True


class MarketDataRequest(BaseModel):
    """Request for market data"""
    symbol: str
    exchange: str = "NSE"
    data_type: str = "quote"  # quote, technicals, options, all


@app.post("/api/v1/gemini/enhanced-signal")
async def generate_enhanced_signal(req: EnhancedSignalRequest):
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


class GeminiChatRequest(BaseModel):
    """Request model for Gemini chat."""
    question: str
    context: Optional[str] = None


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


class FinanceAIRequest(BaseModel):
    """Request model for Finance AI analysis."""
    symbol: str
    current_price: float
    technical_indicators: Optional[Dict[str, Any]] = None
    news_items: Optional[List[str]] = None
    model_type: str = "stock_analyst"


class OptionsStrategyRequest(BaseModel):
    """Request model for options strategy."""
    index: str = "NIFTY"
    spot_price: float
    outlook: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    capital: float = 100000
    risk_appetite: str = "MODERATE"  # LOW, MODERATE, HIGH


class RiskAnalysisRequest(BaseModel):
    """Request model for portfolio risk analysis."""
    positions: List[Dict[str, Any]]
    account_value: float


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
async def get_finance_ai_options_strategy(request: OptionsStrategyRequest):
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
async def get_finance_ai_risk_analysis(request: RiskAnalysisRequest):
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

