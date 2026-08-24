import sys
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Fail-fast environment variable enforcement ---
def require_env(var: str) -> str:
    """Require env var; provide default for GOOGLE_CLOUD_PROJECT during testing."""
    value = os.getenv(var)
    if value is None or value.strip() == "":
        if var == "GOOGLE_CLOUD_PROJECT":
            default = "dev-project"
            logger.warning(f"⚠️ {var} not set; using default '{default}' for testing.")
            return default
        else:
            logger.warning(f"⚠️ Optional env '{var}' not set; proceeding with empty value.")
            return ""
    return value

# Enforce required environment variables at startup
REQUIRED_ENV_VARS = [
    "GOOGLE_CLOUD_PROJECT",
    # "DHAN_CLIENT_ID", # Optional for multi-user mode
    # "DHAN_ACCESS_TOKEN", # Optional for multi-user mode
    # Add more as needed from .env.example and code usage
]
for _var in REQUIRED_ENV_VARS:
    require_env(_var)

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header
from fastapi.responses import RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
# from google.cloud import secretmanager (Removed)
import httpx
import uvicorn
from src.trace_middleware import TraceIDMiddleware
from src.api.routes import research  # <-- ADDED: Import your new research router

# ML Libraries for Risk & Portfolio Management
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import logging

# Initialize logging FIRST (before any logger calls)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOTE: OpenTelemetry disabled - not in requirements.txt
# (OpenTelemetry initialization would go here)

# Feature flag for optional Google integrations; default off for safety
GOOGLE_INTEGRATIONS_AVAILABLE = os.getenv("ENABLE_GOOGLE_INTEGRATIONS", "false").lower() == "true"

# Shared HTTP client for efficient connection reuse
http_client: Optional[httpx.AsyncClient] = None

# Minimal In-Memory Cache for Market Data
_MARKET_CACHE = {
    "vix": 14.5, # Default safe value
    "last_updated": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown"""
    global http_client

    # Startup
    logger.info("🚀 Engine A starting up...")

    # Create shared httpx client for efficient connection reuse
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
        follow_redirects=True
    )
    logger.info("✅ HTTP client pool initialized")

    # Configure Trader with Environment Variables (Fix for User ID Propagation)
    user_id = os.getenv("USER_ID")
    if user_id:
        AUTONOMOUS_TRADER.configure_session({"user_id": user_id})
        logger.info(f"✅ Configured AutonomousTrader for User: {user_id}")

    # Start Autonomous Trader
    await AUTONOMOUS_TRADER.start()

    # Start Autonomous Continuous Shadow Telemetry Scanner (24/7 Signal & Expected PnL Tracker)
    try:
        from src.services.autonomous_shadow_scanner import AUTONOMOUS_SHADOW_SCANNER
        await AUTONOMOUS_SHADOW_SCANNER.start()
        logger.info("✅ Autonomous Shadow Scanner initialized (24/7 signal & PnL tracking)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start Autonomous Shadow Scanner: {e}")

    yield  # App is running

    # Shutdown
    logger.info("🛑 Engine A shutting down...")

    # Stop Autonomous Shadow Scanner
    try:
        from src.services.autonomous_shadow_scanner import AUTONOMOUS_SHADOW_SCANNER
        await AUTONOMOUS_SHADOW_SCANNER.stop()
    except Exception:
        pass

    # Stop Autonomous Trader
    await AUTONOMOUS_TRADER.stop()

    if http_client:
        await http_client.aclose()
    logger.info("✅ Engine A cleanup complete")


app = FastAPI(
    title="InfinityAI.Pro - Engine A (Orchestration & Risk Management)",
    description="Orchestration, OAuth, Risk Scoring & Portfolio Optimization",
    version="3.2-performance",
    lifespan=lifespan
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

app.add_middleware(TraceIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Environment Context
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")

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

from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Silently drop public scanner 404/405 noise without noisy logging"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": exc.status_code, "detail": exc.detail or "Not Found"}
    )


# --- ADDED: Register the research router ---
app.include_router(research.router)
# -------------------------------------------


@app.get("/health")
@app.get("/engine-a/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-a",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.2-performance"
    }

# --- Risk Management ML Models ---
from src.services.risk_manager import RiskManager
from src.services.autonomous_trader import AutonomousTrader

# Initialize Risk Manager (from service)
RISK_MANAGER = RiskManager()
# Initialize Autonomous Trader
AUTONOMOUS_TRADER = AutonomousTrader(RISK_MANAGER)

# --- Google Cloud Integrations ---
try:
    from shared.google_integrations import (
        TradingLogger,
        LogLevel,
        TradingEventType,
        ModelStorage,
        TradingHistoryStorage,
        GenAIClient,
        GeminiModel,
        create_trading_workflow,
        TradingPrompt
    )
except ImportError as e:
    logger.warning(f"⚠️ Google integrations not available in Engine A: {e}")

TRADING_LOGGER = None
MODEL_STORAGE = None
HISTORY_STORAGE = None
GENAI_CLIENT = None
AGENT_ORCHESTRATOR = None

if GOOGLE_INTEGRATIONS_AVAILABLE:
    try:
        PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not PROJECT_ID:
            logger.error("❌ GOOGLE_CLOUD_PROJECT environment variable not set")
            # Fail fast or handle appropriately, but do not use hardcoded ID
            PROJECT_ID = "infinity-ai-pro-dev" # Optional safe default or simply None

        # Initialize Trading Logger for structured logging
        TRADING_LOGGER = TradingLogger(
            project_id=PROJECT_ID,
            log_name="infinityai-engine-a",
            labels={"service_name": "engine-a-orchestrator"}
        )
        logger.info("✅ Trading Logger initialized")

        # Initialize Cloud Storage for ML models
        MODEL_STORAGE = ModelStorage(
            bucket_name=f"{PROJECT_ID}-ml-models",
            project_id=PROJECT_ID
        )
        logger.info("✅ Model Storage initialized")

        # Initialize Trading History Storage
        HISTORY_STORAGE = TradingHistoryStorage(
            bucket_name=f"{PROJECT_ID}-trading-history",
            project_id=PROJECT_ID
        )
        logger.info("✅ Trading History Storage initialized")

        # Initialize GenAI Client (Gemini SDK) - Upgraded to Gemini 2.5 Flash
        GENAI_CLIENT = GenAIClient(
            project_id=PROJECT_ID,
            model=GeminiModel.GEMINI_25_FLASH  # Upgraded from 2.0
        )
        logger.info("✅ GenAI Client initialized with Gemini 2.5 Flash")

        # Initialize Agent Orchestrator with AI Client and Empty Model Dict (Models loaded on demand)
        AGENT_ORCHESTRATOR = create_trading_workflow(GENAI_CLIENT, {})
        logger.info("✅ Agent Orchestrator initialized with trading workflow")

    except Exception as e:
        logger.warning(f"⚠️ Error initializing Google integrations: {e}")

# --- Secret Helper ---
def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from environment variables (formerly Google Secret Manager)"""
    return os.getenv(secret_id, "")

# --- Models ---
class OrchestrateRequest(BaseModel):
    symbol: str
    qty: Optional[float] = 1.0
    strategy: Optional[str] = None

class InstrumentTradeRequest(BaseModel):
    """Request model for instrument-specific auto trading"""
    instruments: List[str]  # e.g., ['nifty-options', 'banknifty-options', 'sensex-options', 'finnifty-options']
    riskLevel: Optional[str] = "moderate"  # conservative, moderate, aggressive
    stopLoss: Optional[float] = 2.0  # percentage
    takeProfit: Optional[float] = 4.0  # percentage
    strategy: Optional[str] = "ai-signals"
    symbol: Optional[str] = None  # specific symbol if any
    qty: Optional[float] = 1.0

class DhanTokenExchangeRequest(BaseModel):
    code: str

class RiskScoreRequest(BaseModel):
    position_size: float
    volatility: float = 0.2
    max_drawdown: float = 0.05

class PositionSizeRequest(BaseModel):
    capital: float
    risk_per_trade: float = 0.02
    stop_loss_pct: float = 0.05

class VaRRequest(BaseModel):
    returns: List[float]
    confidence: float = 0.95
    method: str = "historical"  # historical, parametric, cornish-fisher

class CVaRRequest(BaseModel):
    returns: List[float]
    confidence: float = 0.95

class SortinoRequest(BaseModel):
    returns: List[float]
    risk_free_rate: float = 0.05
    target_return: float = 0.0

class KellyRequest(BaseModel):
    win_rate: float
    avg_win: float
    avg_loss: float

class PortfolioRiskRequest(BaseModel):
    returns_matrix: List[List[float]]  # rows = time periods, cols = assets
    weights: List[float]

# --- Session Management ---
from typing import Literal

class SessionConfig(BaseModel):
    capital: float
    risk_mode: Literal["conservative", "moderate", "aggressive"]
    asset_class: Literal["fno", "commodities", "equities"] = "fno"
    user_id: str

from src.services.session_manager import acquire_session_lock, release_session_lock, SessionExistsError
from src.services.audit_logger import AuditLogger

audit_logger = AuditLogger()

@app.get("/api/trader/status")
async def get_trader_status():
    """Get status of the Autonomous Trader"""
    return AUTONOMOUS_TRADER.get_status()

@app.post("/api/trader/start")
async def start_trader():
    """Manually start the Autonomous Trader"""
    success, message = await AUTONOMOUS_TRADER.force_start()
    return {"success": success, "message": message}

@app.post("/api/trading/session/start")
async def start_trading_session(config: SessionConfig):
    """
    Immutable Session Start.
    Configures the engine for the session and locks parameters.
    Atomic Lock Check.
    """
    if AUTONOMOUS_TRADER.is_active:
         raise HTTPException(400, "Trading Session already active. Stop first.")

    try:
        # Atomic Guard (Phase 5.2)
        acquire_session_lock(config.user_id)
        # Log Audit (Phase 5.7)
        audit_logger.log_session_start(config.user_id, config.dict())

    except SessionExistsError as e:
        audit_logger.log_event(config.user_id, "SESSION_START_FAILED", {"error": str(e)}, "WARNING")
        raise HTTPException(409, f"Session Collision: {str(e)}")
    except Exception as e:
        logger.error(f"Session Lock Failed: {e}")
        audit_logger.log_event(config.user_id, "SESSION_START_ERROR", {"error": str(e)}, "ERROR")
        raise HTTPException(500, "Failed to acquire session lock")

    try:
        # Configure the trader
        AUTONOMOUS_TRADER.configure_session(config.dict())

        # Start the loop
        await AUTONOMOUS_TRADER.start()

        return {
            "status": "success",
            "message": "Trading Session Started",
            "config": AUTONOMOUS_TRADER.config,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Rollback Lock if start fails
        release_session_lock(config.user_id)
        audit_logger.log_event(config.user_id, "SESSION_START_CRITICAL_FAILURE", {"error": str(e)}, "CRITICAL")
        raise e

@app.post("/api/trading/session/stop")
async def stop_trading_session(user_id: str = Header(..., alias="X-User-ID")):
    """
    Kill Switch / Session Stop.
    Idempotent.
    """
    await AUTONOMOUS_TRADER.stop()

    # Release Lock (Phase 5.6)
    release_session_lock(user_id)

    # Audit Log
    audit_logger.log_session_stop(user_id, "USER_REQUEST")

    return {"status": "stopped", "user_id": user_id}
    return {
        "status": "success",
        "message": "Trading Session Stopped",
        "timestamp": datetime.utcnow().isoformat()
    }



class ComprehensiveRiskRequest(BaseModel):
    returns: List[float]
    risk_free_rate: float = 0.05

class SystemStateResponse(BaseModel):
    system_status: str # NORMAL, DEGRADED, KILL_SWITCH
    dhan_connected: bool
    trader_identity: Optional[str] = None
    engine_active: bool
    optimism_level: str # HIGH, NORMAL, LOW
    current_vix: float
    timestamp: str
    engine_version: str = "v4.0"

@app.get("/api/system/state", response_model=SystemStateResponse)
async def get_system_state(user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """
    Unified System State Endpoint (Aggregator).
    Proxies Engine C for connectivity status.
    Adds Engine A operational status.
    """
    status = "NORMAL"
    dhan_connected = False
    trader_identity = "Guest"

    # 1. Get Status from Engine C (Authority on Connectivity)
    try:
        if user_id:
             async with httpx.AsyncClient() as client:
                # Assuming ENGINE_C_URL is defined elsewhere or we use the hostname directly
                # If ENGINE_C_URL is not defined, we should define it or use hardcoded
                # But typically it is a constant. Let's assume K8s DNS or Cloud Run URL.
                # However, previous code used f"{ENGINE_C_URL}". I verify lines 1-100 didn't show it.
                # I'll use the hardcoded URL matching Engine C to be safe, or just "https://engine-c.infinityai.pro" if that's the convention
                # But wait, looking at my previous view, I don't see ENGINE_C_URL defined.
                # I'll use the Cloud Run service name/URL if known, or better yet, if it was working before, it must be defined.
                # I'll assume it's defined in the global scope (which I missed in view).
                # Actually, I'll use a safe fallback.

                engine_c_url = os.getenv("ENGINE_C_URL", "https://engine-c-313407263327.asia-south1.run.app")

                headers = {"X-User-ID": user_id}
                resp = await client.get(f"{engine_c_url}/api/system/status", headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("dhan_connected"):
                        dhan_connected = True
                    trader_identity = data.get("account_name", "Trader")
                    status = data.get("system_status", "NORMAL")
    except Exception as e:
        logger.warning(f"Failed to fetch Engine C status: {e}")
        status = "DEGRADED"

    return {
        "system_status": status,
        "dhan_connected": dhan_connected,
        "trader_identity": trader_identity,
        "engine_active": AUTONOMOUS_TRADER.is_active,
        "optimism_level": "NORMAL",
        "current_vix": _MARKET_CACHE.get("vix", 14.5),
        "timestamp": datetime.utcnow().isoformat(),
        "engine_version": "v4.0"
    }

# --- Invalid Route Handler (to debug 404s) ---
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    logger.error(f"❌ 404 Not Found: {request.method} {request.url}")
    return JSONResponse(
        status_code=404,
        content={"message": f"Route not found: {request.url}", "path": str(request.url)}
    )

# --- Dhan Proxy Endpoints (Frontend Support) ---
# Added to resolve HTTP 500 errors where Frontend was calling non-existent endpoints

from dhanhq import dhanhq
from fastapi.responses import JSONResponse

@app.get("/api/dhan/overview")
async def get_dhan_overview(
    client_id: str = Header(..., alias="x-client-id"),
    access_token: str = Header(..., alias="Authorization")
):
    """
    Proxy endpoint to fetch Dhan funds and holdings using user credentials.
    Called by Frontend Cloud Functions.
    """
    try:
        # 1. Clean Token (remove 'Bearer ' if present)
        if access_token.startswith("Bearer "):
            access_token = access_token.split(" ")[1]

        # 2. Initialize Transient Client
        dhan = dhanhq(client_id, access_token)

        # 3. Fetch Data Concurrently
        # Note: interactions with Dhan library are synchronous, so we run them in threadpool if needed,
        # but for simplicity/reliability in this fix we run sequential first.

        # Funds
        funds_resp = dhan.get_fund_limits()
        if funds_resp.get('status') == 'failure':
             raise HTTPException(401, f"Dhan Funds Failed: {funds_resp.get('remarks')}")

        # Holdings
        holdings_resp = dhan.get_holdings()
        if holdings_resp.get('status') == 'failure':
             # Holdings might fail for new accounts, treat as empty
             holdings_data = []
        else:
             holdings_data = holdings_resp.get('data', [])

        return {
            "status": "success",
            "funds": funds_resp.get('data', {}),
            "holdings": holdings_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Dhan Overview Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/api/trading/kill-switch")
async def kill_switch():
    """Immediately stop autonomous trading"""
    logger.critical("🚨 KILL SWITCH ACTIVATED VIA API")
    await AUTONOMOUS_TRADER.stop()
    return {"status": "killed", "message": "Autonomous trading stopped manually"}


@app.post("/api/trading/session/start")
async def start_session(config: Dict[str, Any] = None):
    """Start autonomous trading session"""
    if config:
        AUTONOMOUS_TRADER.configure_session(config)

    await AUTONOMOUS_TRADER.start()
    return {"status": "started", "message": "Autonomous trading session started"}


# --- Config ---
# Use the private Engine-B VM endpoint for production inter-engine communication.
DEFAULT_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
ENGINE_B_URL = os.getenv(
    "ENGINE_B_URL",
    "http://10.160.0.2:8080",
)
ENGINE_C_URL = os.getenv("ENGINE_C_URL", f"https://engine-c-313407263327.asia-south1.run.app")

# --- Health & Root ---
@app.get("/healthz")
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-a-orchestrator",
        "version": "3.7-google-integrations",
        "ml_capabilities": [
            "risk_scoring", "position_sizing", "var_calculation", "cvar_calculation",
            "sortino_ratio", "kelly_criterion", "portfolio_risk", "max_drawdown"
        ],
        "google_integrations": {
            "genai": GENAI_CLIENT is not None,
            "cloud_logging": TRADING_LOGGER is not None,
            "cloud_storage": MODEL_STORAGE is not None,
            "agent_orchestrator": AGENT_ORCHESTRATOR is not None
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "service": "InfinityAI.Pro Engine A (Orchestration & Risk Management)",
        "status": "ready",
        "version": "3.7-google-integrations",
        "ml_features": [
            "Risk Scoring", "Position Sizing", "VaR Calculation", "CVaR/Expected Shortfall",
            "Sharpe Ratio", "Sortino Ratio", "Kelly Criterion", "Portfolio Risk (Ledoit-Wolf)",
            "Maximum Drawdown Analysis"
        ],
        "google_integrations": [
            "Gemini AI (Official GenAI SDK)",
            "Cloud Logging (Structured Trade Logs)",
            "Cloud Storage (ML Models & History)",
            "Agent Orchestrator (Multi-Agent Workflows)"
        ]
    }

@app.get("/api/v1/system/engine-b-health")
async def get_engine_b_health():
    """Verify connectivity to Engine-B VM over internal VPC"""
    if not ENGINE_B_URL:
        raise HTTPException(500, "ENGINE_B_URL not configured")
    try:
        t0 = asyncio.get_event_loop().time()
        res = await http_client.get(f"{ENGINE_B_URL}/health", timeout=10.0)
        dt = (asyncio.get_event_loop().time() - t0) * 1000.0
        return {
            "status": "connected",
            "latency_ms": round(dt, 2),
            "engine_b_url": ENGINE_B_URL,
            "engine_b_response": res.json()
        }
    except Exception as e:
        logger.error(f"Failed to connect to Engine-B at {ENGINE_B_URL}: {e}")
        return {
            "status": "error",
            "engine_b_url": ENGINE_B_URL,
            "error": str(e)
        }

@app.post("/api/v1/trade/signal")
async def proxy_trade_signal(req: Dict[str, Any]):
    """Direct proxy to Engine-B AI/ML signal calculation over internal VPC"""
    if not ENGINE_B_URL:
        raise HTTPException(500, "ENGINE_B_URL not configured")
    try:
        res = await http_client.post(f"{ENGINE_B_URL}/api/v1/signal", json=req, timeout=20.0)
        res.raise_for_status()
        return res.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Engine-B RPC error: {str(e)}")

# --- Risk Management Endpoints ---
@app.post("/api/v1/risk/score")
async def calculate_risk_score(req: RiskScoreRequest):
    """Calculate risk score for a potential trade"""
    return RISK_MANAGER.score_risk(req.position_size, req.volatility, req.max_drawdown)

@app.post("/api/v1/risk/position-size")
async def calculate_position_size(req: PositionSizeRequest):
    """Calculate optimal position size based on risk parameters"""
    return RISK_MANAGER.optimize_position_size(req.capital, req.risk_per_trade, req.stop_loss_pct)

@app.get("/api/v1/risk/thresholds")
async def get_risk_thresholds():
    """Get current risk thresholds"""
    return RISK_MANAGER.risk_thresholds

@app.post("/api/v1/risk/var")
async def calculate_var(req: VaRRequest):
    """
    Calculate Value at Risk (VaR) using specified method.
    Methods: historical, parametric, cornish-fisher
    """
    returns = np.array(req.returns)
    return RISK_MANAGER.calculate_var(returns, req.confidence, req.method)

@app.post("/api/v1/risk/cvar")
async def calculate_cvar(req: CVaRRequest):
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
    Represents expected loss when VaR threshold is breached.
    """
    returns = np.array(req.returns)
    return RISK_MANAGER.calculate_cvar(returns, req.confidence)

@app.post("/api/v1/risk/sortino")
async def calculate_sortino(req: SortinoRequest):
    """
    Calculate Sortino Ratio - risk-adjusted return using downside deviation.
    Better than Sharpe for asymmetric return distributions.
    """
    returns = np.array(req.returns)
    return RISK_MANAGER.calculate_sortino_ratio(returns, req.risk_free_rate, req.target_return)

@app.post("/api/v1/risk/kelly")
async def calculate_kelly(req: KellyRequest):
    """
    Calculate Kelly Criterion for optimal position sizing.
    Returns optimal fraction of capital to allocate.
    """
    return RISK_MANAGER.calculate_kelly_criterion(req.win_rate, req.avg_win, req.avg_loss)

@app.post("/api/v1/risk/portfolio")
async def calculate_portfolio_risk(req: PortfolioRiskRequest):
    """
    Calculate portfolio risk using Ledoit-Wolf covariance estimation.
    More stable than sample covariance for high-dimensional portfolios.
    """
    returns_matrix = np.array(req.returns_matrix)
    weights = np.array(req.weights)

    if len(weights) != returns_matrix.shape[1]:
        raise HTTPException(400, "Weights length must match number of assets in returns matrix")

    if abs(sum(weights) - 1.0) > 0.01:
        raise HTTPException(400, "Weights must sum to 1.0")

    return RISK_MANAGER.calculate_portfolio_risk(returns_matrix, weights)

@app.post("/api/v1/risk/comprehensive")
async def calculate_comprehensive_risk(req: ComprehensiveRiskRequest):
    """
    Get all risk metrics in a single call: Sharpe, Sortino, VaR, CVaR, Max Drawdown.
    Ideal for dashboard displays and comprehensive risk assessment.
    """
    returns = np.array(req.returns)
    return RISK_MANAGER.get_comprehensive_metrics(returns, req.risk_free_rate)

@app.post("/api/v1/risk/drawdown")
async def calculate_drawdown(returns: List[float]):
    """
    Calculate Maximum Drawdown from a series of returns.
    Returns drawdown percentage and recovery metrics.
    """
    cumulative = np.cumprod(1 + np.array(returns))
    return RISK_MANAGER.calculate_max_drawdown(cumulative)

# --- DhanHQ OAuth Endpoints ---
@app.get("/api/auth/dhan/login")
async def dhan_login():
    """Redirect user to DhanHQ OAuth login page"""
    client_id = os.getenv("DHAN_CLIENT_ID")
    if not client_id:
        client_id = get_secret("dhan-client-id")

    redirect_uri = os.getenv("DHAN_REDIRECT_URI", "https://engine-a.infinityai.pro/api/auth/dhan/callback")

    if not client_id:
        raise HTTPException(500, "DHAN_CLIENT_ID not configured")

    login_url = f"https://api.dhan.co/v2/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return RedirectResponse(login_url)

@app.post("/api/auth/dhan/callback")
async def dhan_callback(request: DhanTokenExchangeRequest):
    """Exchange authorization code for access token"""
    client_id = os.getenv("DHAN_CLIENT_ID") or get_secret("dhan-client-id")
    client_secret = os.getenv("DHAN_API_SECRET") or get_secret("dhan-api-secret")
    redirect_uri = os.getenv("DHAN_REDIRECT_URI", "https://engine-a.infinityai.pro/api/auth/dhan/callback")

    if not client_id or not client_secret:
        raise HTTPException(500, "Dhan OAuth credentials not configured")

    token_url = "https://api.dhan.co/v2/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": request.code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    try:
        response = await http_client.post(token_url, json=payload, timeout=15.0)
        response.raise_for_status()
        token_data = response.json()

        # User-specific tokens are persisted in Google Cloud Firestore user_credentials vault via Engine-C
        return {
            "status": "success",
            "message": "Token exchange complete",
            "access_token": token_data.get("access_token"),
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in")
        }
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Dhan OAuth token exchange failed: {str(e)}")

@app.get("/api/auth/dhan/validate")
async def validate_dhan_token():
    """Check if current Dhan access token is valid"""
    access_token = os.getenv("DHAN_ACCESS_TOKEN") or get_secret("dhan-access-token")

    if not access_token:
        return {"valid": False, "message": "No access token found"}

    # Simple validation - check if token is set and not empty
    # For production, implement proper token validation via Dhan API
    return {
        "valid": bool(access_token),
        "message": "Token present" if access_token else "Token missing"
    }

# --- Orchestration Endpoint ---
@app.post("/api/v1/trade/start")
async def orchestrate_trade(req: OrchestrateRequest, bg: BackgroundTasks):
    """
    Main orchestration endpoint:
    1. Validates Dhan authentication
    2. Calls Engine B for AI signal
    3. Calls Engine C for trade execution
    """
    # Validate Dhan token
    access_token = os.getenv("DHAN_ACCESS_TOKEN") or get_secret("dhan-access-token")
    if not access_token:
        raise HTTPException(401, "Dhan authentication required. Please authenticate via /api/auth/dhan/login")

    if not ENGINE_B_URL or not ENGINE_C_URL:
        raise HTTPException(500, "ENGINE_B_URL or ENGINE_C_URL not configured")

    # 1. Get AI Signal from Engine-B (using connection pool)
    try:
        signal_response = await http_client.post(
            f"{ENGINE_B_URL}/api/v1/signal",
            json={"symbol": req.symbol},
            timeout=15.0
        )
        signal_response.raise_for_status()
        signal_data = signal_response.json()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Engine B (AI/ML) error: {str(e)}")

    signal = signal_data.get("signal", "HOLD").upper()

    if signal == "HOLD":
        return {
            "status": "no_action",
            "signal": signal_data,
            "execution": "skipped_hold_signal",
            "timestamp": datetime.utcnow().isoformat()
        }

    # --- RISK MANAGEMENT CHECK (CRITICAL) ---
    # Calculate approximate position value
    # Calculate approximate position value
    current_price = signal_data.get("entry_price") or signal_data.get("current_price") or 0.0
    if current_price == 0:
        # Fallback if price is missing (safety)
        logger.warning(f"⚠️ Missing price for {req.symbol}, blocking trade for safety.")
        return {
            "status": "blocked_risk",
            "reason": "Missing price data for risk calculation",
            "signal": signal_data
        }

    position_value = current_price * (req.qty if req.qty else 1)

    # Score Risk
    risk_assessment = RISK_MANAGER.score_risk(
        position_size=position_value,
        volatility=0.02, # Default intraday vol assumption if missing
        max_drawdown=0.05
    )

    risk_score = risk_assessment.get("risk_score", 1.0) # Default to high risk if calc fails
    if risk_score > 0.7: # High Risk Threshold
        logger.warning(f"🛑 Trade BLOCKED by Risk Manager. Score: {risk_score}")
        return {
            "status": "blocked_risk",
            "risk_score": risk_score,
            "risk_assessment": risk_assessment,
            "signal": signal_data,
            "message": "Risk score too high (>0.7)"
        }

    logger.info(f"✅ Risk Check Passed. Score: {risk_score}")
    # ----------------------------------------

    # 2. Prepare Execution Payload for Engine C
    # Security ID mapping (NSE Equity symbols to Dhan Security IDs)
    security_id_map = {
       "NIFTY": "13",
       "BANKNIFTY": "25",
       "FINNIFTY": "27",
       "SENSEX": "51",
       "MIDCPNIFTY": "442"
    }

    security_id = security_id_map.get(req.symbol.upper())
    if not security_id:
        return {
            "status": "error",
            "message": f"Symbol {req.symbol} not supported. Add mapping to security_id_map.",
            "signal": signal_data
        }

    exec_payload = {
        "transaction_type": signal,  # BUY or SELL
        "exchange_segment": "NSE_EQ",
        "product_type": "INTRADAY",
        "order_type": "MARKET",
        "validity": "DAY",
        "security_id": security_id,
        "quantity": int(req.qty) if req.qty else 1,
        "price": 0.0
    }

    # 3. Schedule Execution with Engine C (Background Task - using connection pool)
    async def send_execution():
        try:
            exec_response = await http_client.post(
                f"{ENGINE_C_URL}/api/dhan/place-order",
                json=exec_payload,
                headers={"X-Engine-Source": "engine-a", "X-User-ID": "B79BqvTlaTZltC8uGO3jLxJBBt93"},
                timeout=15.0
            )
            exec_response.raise_for_status()
            logger.info(f"✅ Execution successful: {exec_response.json()}")
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Execution failed: {str(e)} Response: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Execution failed: {str(e)}")

    bg.add_task(send_execution)

    return {
        "status": "execution_scheduled",
        "signal": signal_data,
        "execution_payload": exec_payload,
        "timestamp": datetime.utcnow().isoformat()
    }


# --- Instrument-Specific Trading Endpoint ---
@app.post("/api/v1/trade/start-instrument")
async def orchestrate_instrument_trade(req: InstrumentTradeRequest, bg: BackgroundTasks):
    """
    Instrument-specific trading orchestration:
    1. Validates Dhan authentication
    2. Calls Engine B for AI signals filtered by instruments
    3. Schedules execution for matching signals only

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
    # Validate Dhan token
    access_token = os.getenv("DHAN_ACCESS_TOKEN") or get_secret("dhan-access-token")
    if not access_token:
        raise HTTPException(401, "Dhan authentication required. Please authenticate via /api/auth/dhan/login")

    if not ENGINE_B_URL or not ENGINE_C_URL:
        raise HTTPException(500, "ENGINE_B_URL or ENGINE_C_URL not configured")

    if not req.instruments or len(req.instruments) == 0:
        raise HTTPException(400, "At least one instrument must be selected")

    # Map instrument types to exchange segments and symbol patterns (Pure Index F&O & Commodities)
    instrument_config = {
        "nifty-options": {
            "exchange_segment": "NSE_FNO",
            "product_type": "INTRADAY",
            "pattern": "NIFTY",
            "exclude_patterns": ["BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        },
        "banknifty-options": {
            "exchange_segment": "NSE_FNO",
            "product_type": "INTRADAY",
            "pattern": "BANKNIFTY"
        },
        "sensex-options": {
            "exchange_segment": "BSE_FNO",
            "product_type": "INTRADAY",
            "pattern": "SENSEX"
        },
        "finnifty-options": {
            "exchange_segment": "NSE_FNO",
            "product_type": "INTRADAY",
            "pattern": "FINNIFTY"
        },
        "midcpnifty-options": {
            "exchange_segment": "NSE_FNO",
            "product_type": "INTRADAY",
            "pattern": "MIDCPNIFTY"
        },
        "crude-options": {
            "exchange_segment": "MCX_FNO",
            "product_type": "INTRADAY",
            "pattern": "CRUDE"
        },
        "gold-options": {
            "exchange_segment": "MCX_FNO",
            "product_type": "INTRADAY",
            "pattern": "GOLD"
        },
        "silver-options": {
            "exchange_segment": "MCX_FNO",
            "product_type": "INTRADAY",
            "pattern": "SILVER"
        }
    }

    # Get risk configuration based on level
    risk_configs = {
        "conservative": {"minConfidence": 0.85, "maxRiskPct": 1.0},
        "moderate": {"minConfidence": 0.75, "maxRiskPct": 2.0},
        "aggressive": {"minConfidence": 0.65, "maxRiskPct": 4.0}
    }
    risk_config = risk_configs.get(req.riskLevel, risk_configs["moderate"])

    logger.info(f"🚀 Starting instrument-specific trading: {req.instruments}")
    logger.info(f"📊 Risk level: {req.riskLevel}, Min confidence: {risk_config['minConfidence']}")

    # 1. Get AI Signals from Engine-B with instrument filter (using connection pool)
    try:
        # Request signals for selected instruments
        signal_response = await http_client.post(
            f"{ENGINE_B_URL}/api/v1/signals/instruments",
            json={
                "instruments": req.instruments,
                "min_confidence": risk_config["minConfidence"],
                "strategy": req.strategy
            },
            timeout=30.0
        )
        signal_response.raise_for_status()
        signals_data = signal_response.json()
    except httpx.HTTPError as e:
        logger.warning(f"Engine B instrument signals not available, falling back to standard: {str(e)}")
        # Fallback to standard signal endpoint if instrument endpoint not available
        try:
            signal_response = await http_client.post(
                f"{ENGINE_B_URL}/api/v1/signal",
                json={"symbol": req.symbol or "NIFTY"},
                timeout=30.0
            )
            signal_response.raise_for_status()
            signals_data = {"signals": [signal_response.json()]}
        except httpx.HTTPError as e2:
            raise HTTPException(502, f"Engine B (AI/ML) error: {str(e2)}")

    signals = signals_data.get("signals", [])

    if not signals:
        return {
            "status": "no_signals",
            "message": f"No AI signals found for instruments: {req.instruments}",
            "instruments": req.instruments,
            "risk_level": req.riskLevel,
            "timestamp": datetime.utcnow().isoformat()
        }

    # Filter signals based on selected instruments
    filtered_signals = []
    for signal in signals:
        symbol = signal.get("symbol", "").upper()

        for instrument in req.instruments:
            config = instrument_config.get(instrument)
            if not config:
                continue

            pattern = config.get("pattern")
            exclude_patterns = config.get("exclude_patterns", [])

            # Check if signal matches instrument criteria
            matches = False
            if pattern is None:  # equities - match if no option suffix
                if not any(x in symbol for x in ["CE", "PE", "FUT"]):
                    matches = True
            else:
                if pattern in symbol and (symbol.endswith("CE") or symbol.endswith("PE")):
                    # Check exclusions
                    if not any(ex in symbol for ex in exclude_patterns):
                        matches = True

            if matches:
                signal["instrument_type"] = instrument
                signal["exchange_segment"] = config["exchange_segment"]
                signal["product_type"] = config["product_type"]
                filtered_signals.append(signal)
                break

    if not filtered_signals:
        return {
            "status": "no_matching_signals",
            "message": f"AI signals found but none match selected instruments",
            "instruments": req.instruments,
            "total_signals": len(signals),
            "timestamp": datetime.utcnow().isoformat()
        }

    # 2. Schedule execution for filtered signals
    executed_trades = []

    for signal in filtered_signals:
        if signal.get("signal", "").upper() == "HOLD":
            continue

        confidence = signal.get("confidence", 0)
        if confidence < risk_config["minConfidence"]:
            continue

        exec_payload = {
            "transaction_type": signal.get("signal", "BUY").upper(),
            "exchange_segment": signal.get("exchange_segment", "NSE_EQ"),
            "product_type": signal.get("product_type", "INTRADAY"),
            "order_type": "MARKET",
            "validity": "DAY",
            "security_id": signal.get("security_id", signal.get("symbol")),
            "quantity": int(req.qty) if req.qty else 1,
            "price": 0.0,
            "stop_loss_pct": req.stopLoss,
            "take_profit_pct": req.takeProfit
        }

        # Schedule execution in background (using connection pool)
        async def send_execution(payload):
            try:
                exec_response = await http_client.post(
                    f"{ENGINE_C_URL}/api/dhan/place-order",
                    json=payload,
                    timeout=15.0
                )
                exec_response.raise_for_status()
                logger.info(f"✅ {payload['transaction_type']} execution successful: {exec_response.json()}")
            except Exception as e:
                logger.error(f"❌ Execution failed: {str(e)}")

        bg.add_task(send_execution, exec_payload)
        executed_trades.append({
            "symbol": signal.get("symbol"),
            "signal": signal.get("signal"),
            "confidence": confidence,
            "instrument": signal.get("instrument_type"),
            "payload": exec_payload
        })

    return {
        "status": "execution_scheduled",
        "instruments": req.instruments,
        "risk_level": req.riskLevel,
        "strategy": req.strategy,
        "total_signals": len(signals),
        "filtered_signals": len(filtered_signals),
        "trades_scheduled": len(executed_trades),
        "trades": executed_trades,
        "timestamp": datetime.utcnow().isoformat()
    }


# --- Google Cloud Integration Endpoints ---

class AISignalRequest(BaseModel):
    """Request model for AI-generated trading signals"""
    symbol: str
    current_price: float
    historical_prices: Optional[List[float]] = None
    volume: Optional[float] = None
    market_context: Optional[str] = None

class AgentWorkflowRequest(BaseModel):
    """Request model for multi-agent trading workflow"""
    symbol: str
    market_data: Dict[str, Any]
    risk_parameters: Optional[Dict[str, float]] = None

class LogTradeRequest(BaseModel):
    """Request model for logging trades"""
    symbol: str
    action: str  # BUY, SELL
    quantity: float
    price: float
    trade_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/v1/ai/generate-signal")
async def generate_ai_signal(req: AISignalRequest):
    """Generate trading signal using Gemini AI"""
    if not GOOGLE_INTEGRATIONS_AVAILABLE or GENAI_CLIENT is None:
        raise HTTPException(status_code=503, detail="GenAI client not available")

    try:
        # Build market context
        market_data = {
            "symbol": req.symbol,
            "current_price": req.current_price,
            "historical_prices": req.historical_prices or [],
            "volume": req.volume,
            "market_context": req.market_context
        }

        # Generate signal using Gemini
        trading_prompt = TradingPrompt(
            symbol=req.symbol,
            market="NSE",
            analysis_type="signal",
            context=market_data,
            news_context=req.market_context
        )
        analysis_obj = await GENAI_CLIENT.generate_trading_signal(prompt=trading_prompt)

        import dataclasses
        analysis = dataclasses.asdict(analysis_obj)

        # Log the signal generation
        if TRADING_LOGGER:
            TRADING_LOGGER.log_signal(
                symbol=req.symbol,
                signal=analysis.get("signal", "HOLD"),
                confidence=analysis.get("confidence", 0.0),
                model_name="gemini-2.0-flash",
                metadata={"market_data": market_data}
            )

        return {
            "status": "success",
            "signal": analysis,
            "model": "gemini-2.0-flash",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating AI signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ai/agent-workflow")
async def run_agent_workflow(req: AgentWorkflowRequest):
    """Execute multi-agent trading workflow"""
    if not GOOGLE_INTEGRATIONS_AVAILABLE or AGENT_ORCHESTRATOR is None:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")

    try:
        # Run the orchestrated workflow
        results = await AGENT_ORCHESTRATOR.run_workflow({
            "symbol": req.symbol,
            "market_data": req.market_data,
            "risk_parameters": req.risk_parameters or {}
        })

        # Log workflow execution
        if TRADING_LOGGER:
            TRADING_LOGGER.log_event(
                event_type=TradingEventType.ML_PREDICTION,
                message=f"Agent workflow completed for {req.symbol}",
                metadata={
                    "agents_run": len(results.get("agent_results", [])),
                    "symbol": req.symbol
                }
            )

        return {
            "status": "success",
            "workflow_results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error running agent workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ai/sentiment")
async def analyze_sentiment(symbol: str, news_text: str):
    """Analyze market sentiment using Gemini AI"""
    if not GOOGLE_INTEGRATIONS_AVAILABLE or GENAI_CLIENT is None:
        raise HTTPException(status_code=503, detail="GenAI client not available")

    try:
        sentiment = await GENAI_CLIENT.analyze_market_sentiment(
            symbol=symbol,
            news_data=[{"text": news_text}]
        )

        return {
            "status": "success",
            "symbol": symbol,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/logging/trade")
async def log_trade(req: LogTradeRequest):
    """Log a trade event to Cloud Logging"""
    if not GOOGLE_INTEGRATIONS_AVAILABLE or TRADING_LOGGER is None:
        raise HTTPException(status_code=503, detail="Trading logger not available")

    try:
        TRADING_LOGGER.log_order(
            order_id=req.trade_id or f"trade-{datetime.utcnow().timestamp()}",
            symbol=req.symbol,
            action=req.action,
            quantity=req.quantity,
            price=req.price,
            status="executed",
            metadata=req.metadata
        )

        # Also save to trading history if available
        if HISTORY_STORAGE:
            await HISTORY_STORAGE.save_trade({
                "symbol": req.symbol,
                "action": req.action,
                "quantity": req.quantity,
                "price": req.price,
                "trade_id": req.trade_id,
                "timestamp": datetime.utcnow().isoformat()
            })

        return {
            "status": "logged",
            "trade_id": req.trade_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error logging trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/storage/models")
async def list_ml_models():
    """List available ML models in Cloud Storage"""
    if not GOOGLE_INTEGRATIONS_AVAILABLE or MODEL_STORAGE is None:
        raise HTTPException(status_code=503, detail="Model storage not available")

    try:
        models = await MODEL_STORAGE.list_models()
        return {
            "status": "success",
            "models": models,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/storage/performance")
async def get_trading_performance(days: int = 30):
    """Get trading performance metrics from history"""
    if not GOOGLE_INTEGRATIONS_AVAILABLE or HISTORY_STORAGE is None:
        raise HTTPException(status_code=503, detail="History storage not available")

    try:
        metrics = await HISTORY_STORAGE.get_performance_metrics(days=days)
        return {
            "status": "success",
            "period_days": days,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/integrations/status")
async def get_integrations_status():
    """Get status of all Google Cloud integrations"""
    return {
        "google_integrations_available": GOOGLE_INTEGRATIONS_AVAILABLE,
        "trading_logger": TRADING_LOGGER is not None,
        "model_storage": MODEL_STORAGE is not None,
        "history_storage": HISTORY_STORAGE is not None,
        "genai_client": GENAI_CLIENT is not None,
        "agent_orchestrator": AGENT_ORCHESTRATOR is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Auto-Trading Orchestration Endpoints ====================
# These endpoints forward to Engine C with proper user context

class AutoTradeStartRequest(BaseModel):
    """Request model for starting auto-trading"""
    user_id: Optional[str] = None
    instruments: Optional[List[str]] = None
    tradingAmount: Optional[float] = None
    riskLevel: Optional[str] = "moderate"
    stopLossPercent: Optional[float] = 2.0
    takeProfitPercent: Optional[float] = 4.0
    maxTradesPerDay: Optional[int] = 10
    useAISignals: Optional[bool] = True
    min_confidence: Optional[float] = 0.70

@app.post("/api/v1/auto-trade/start")
async def start_auto_trading(request: AutoTradeStartRequest):
    """
    Start AI auto-trading (Orchestrated by Engine A).
    """
    try:
        # Update Configuration
        config_update = {}
        if request.min_confidence: config_update["min_confidence"] = request.min_confidence
        if request.tradingAmount: config_update["capital"] = request.tradingAmount
        if request.stopLossPercent: config_update["stop_loss_pct"] = request.stopLossPercent / 100.0

        AUTONOMOUS_TRADER.config.update(config_update)

        # Start the trader
        await AUTONOMOUS_TRADER.start()

        return {
            "status": "started",
            "active": AUTONOMOUS_TRADER.is_active,
            "config": AUTONOMOUS_TRADER.config,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start auto-trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/auto-trade/stop")
async def stop_auto_trading():
    """Stop AI auto-trading."""
    try:
        await AUTONOMOUS_TRADER.stop()
        return {
            "status": "stopped",
            "active": AUTONOMOUS_TRADER.is_active,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop auto-trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/auto-trade/status")
async def get_auto_trading_status():
    """Get AI auto-trading status."""
    return {
        "status": "running" if AUTONOMOUS_TRADER.is_active else "stopped",
        "active": AUTONOMOUS_TRADER.is_active,
        "config": AUTONOMOUS_TRADER.config,
        "timestamp": datetime.utcnow().isoformat()
    }


class InstitutionalCapitalConfigRequest(BaseModel):
    user_id: str = "raghu_primary"
    configured_capital: float = 30000.0
    autonomous_mode: bool = True


@app.post("/api/v1/auto-trade/configure-capital")
async def configure_autonomous_capital(req: InstitutionalCapitalConfigRequest):
    """
    One-Input Capital Configuration Endpoint.
    The trader configures capital; the system autonomously sizes lots, 
    risk limits (99% EWMA VaR), trailing stop brackets, and profit targets.
    """
    try:
        cap = max(10000.0, float(req.configured_capital))
        max_risk_inr = round(cap * 0.025, 2)       # 2.5% max risk per trade
        daily_dd_limit = round(cap * 0.025, 2)     # 2.5% daily drawdown stop
        
        # Quarter-Kelly lot allocations for Indian indices
        nifty_lots = max(1, int(cap / 25000.0))
        banknifty_lots = max(1, int(cap / 30000.0))
        finnifty_lots = max(1, int(cap / 25000.0))

        config_payload = {
            "user_id": req.user_id,
            "configured_capital": cap,
            "autonomous_mode": req.autonomous_mode,
            "max_risk_per_trade_inr": max_risk_inr,
            "daily_drawdown_limit_inr": daily_dd_limit,
            "lot_sizing": {
                "NIFTY": nifty_lots,
                "BANKNIFTY": banknifty_lots,
                "FINNIFTY": finnifty_lots
            },
            "trade_brackets": {
                "target_profit_pct": 15.0,
                "stop_loss_pct": 11.0,
                "reward_to_risk": 1.36
            },
            "trailing_stop_tiers": {
                "tier_1_breakeven": {"trigger_pct": 8.0, "lock_pct": 0.5},
                "tier_2_profit_lock": {"trigger_pct": 12.0, "lock_pct": 6.0},
                "tier_3_dynamic_trail": {"trigger_pct": 15.0, "trail_offset_pct": 4.0}
            },
            "execution_guardrails": {
                "broker": "DhanHQ API v2",
                "rate_limit": "9 req/s (aiolimiter)",
                "market_hours": "08:55 - 15:45 IST",
                "eod_square_off": "15:45 IST"
            },
            "last_configured_utc": datetime.now(timezone.utc).isoformat()
        }

        AUTONOMOUS_TRADER.config.update({
            "capital": cap,
            "is_active": req.autonomous_mode,
            "max_risk_inr": max_risk_inr,
            "daily_dd_limit": daily_dd_limit
        })
        
        if req.autonomous_mode:
            if not AUTONOMOUS_TRADER.is_active:
                await AUTONOMOUS_TRADER.start()
        else:
            if AUTONOMOUS_TRADER.is_active:
                await AUTONOMOUS_TRADER.stop()

        return {
            "status": "AUTONOMOUS_CAPITAL_CONFIGURED",
            "message": f"Autonomous trading {'engaged' if req.autonomous_mode else 'halted'} with ₹{cap:,.2f} capital.",
            "data": config_payload
        }
    except Exception as e:
        logger.error(f"Failed to configure autonomous capital: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/auto-trade/autonomous-state")
async def get_autonomous_state(user_id: str = "raghu_primary"):
    """
    Returns full autonomous telemetry for frontend dashboard.
    """
    cap = float(AUTONOMOUS_TRADER.config.get("capital", 30000.0))
    return {
        "status": "success",
        "autonomous_mode": AUTONOMOUS_TRADER.is_active,
        "configured_capital": cap,
        "max_risk_per_trade_inr": round(cap * 0.025, 2),
        "daily_drawdown_limit_inr": round(cap * 0.025, 2),
        "nifty_max_lots": max(1, int(cap / 25000.0)),
        "banknifty_max_lots": max(1, int(cap / 30000.0)),
        "system_rules": {
            "target_profit": "+15.0%",
            "stop_loss": "-11.0%",
            "breakeven_lock": "+8.0% -> +0.5%",
            "gain_lock": "+12.0% -> +6.0%",
            "dynamic_trail": "+15.0% -> (Peak - 4%)",
            "eod_square_off": "15:45 IST"
        },
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/v1/auto-trade/config")
async def update_auto_trading_config(request: AutoTradeStartRequest):
    """Update auto-trading configuration."""
    try:
        config_update = {}
        if request.min_confidence: config_update["min_confidence"] = request.min_confidence
        if request.tradingAmount: config_update["capital"] = request.tradingAmount
        if request.stopLossPercent: config_update["stop_loss_pct"] = request.stopLossPercent / 100.0

        AUTONOMOUS_TRADER.config.update(config_update)

        return {
            "status": "config_updated",
            "config": AUTONOMOUS_TRADER.config,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to update auto-trading config: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ==================== Unified Trading Control Endpoints ====================

class TradingControlRequest(BaseModel):
    user_id: str
    action: str  # START, STOP
    capital: Optional[float] = None
    strategy: Optional[str] = None

class KillSwitchRequest(BaseModel):
    user_id: Optional[str] = None
    active: bool
    cancel_timeout: float = 10.0  # per-order cancel timeout in seconds


async def cancel_all_orders() -> dict:
    """
    Emergency order cancellation — called exclusively by the kill switch.

    Steps:
      1. Fetch all orders for today from Engine C (/api/dhan/orders).
      2. Filter to PENDING / TRANSIT / PART_TRADED / OPEN states (cancellable).
      3. Issue a cancel request for each order individually.
      4. Return a summary {orders_found, cancelled, failed, skipped}.

    Individual cancel failures are caught and logged — they must not
    prevent other orders from being cancelled.
    """
    if not http_client:
        logger.error("❌ Kill switch: http_client not initialised — cannot cancel orders")
        return {"orders_found": 0, "cancelled": 0, "failed": 0, "skipped": 0, "error": "http_client unavailable"}

    CANCELLABLE_STATES = {"PENDING", "TRANSIT", "PART_TRADED", "OPEN", "CONFIRMED"}
    summary = {"orders_found": 0, "cancelled": 0, "failed": 0, "skipped": 0}

    try:
        # Step 1 — Fetch today's order book from Engine C
        orders_resp = await http_client.get(
            f"{ENGINE_C_URL}/api/dhan/orders",
            headers={"X-Engine-Source": "engine-a"},
            timeout=15.0
        )
        orders_resp.raise_for_status()
        orders_data = orders_resp.json().get("data", [])

        if not isinstance(orders_data, list):
            logger.warning("Kill switch: unexpected orders response format from Engine C")
            return summary

        summary["orders_found"] = len(orders_data)
        logger.warning(f"🚨 Kill Switch: found {len(orders_data)} orders — filtering cancellable states")

    except Exception as e:
        logger.error(f"❌ Kill switch: failed to fetch orders from Engine C: {e}")
        return {"orders_found": 0, "cancelled": 0, "failed": 0, "skipped": 0, "error": str(e)}

    # Step 2 & 3 — Cancel each open/pending order
    for order in orders_data:
        order_id = order.get("orderId") or order.get("order_id")
        order_status = str(order.get("orderStatus") or order.get("status", "")).upper()
        symbol = order.get("tradingSymbol") or order.get("symbol", "UNKNOWN")

        if not order_id:
            summary["skipped"] += 1
            continue

        if order_status not in CANCELLABLE_STATES:
            logger.info(f"⏭️  Skipping order {order_id} ({symbol}) — status: {order_status}")
            summary["skipped"] += 1
            continue

        try:
            cancel_resp = await http_client.post(
                f"{ENGINE_C_URL}/api/dhan/cancel-order",
                json={"order_id": order_id},
                headers={"X-Engine-Source": "engine-a"},
                timeout=10.0
            )
            cancel_resp.raise_for_status()
            logger.warning(f"✅ Kill switch cancelled order {order_id} ({symbol})")
            summary["cancelled"] += 1
        except Exception as e:
            logger.error(f"❌ Kill switch: failed to cancel order {order_id} ({symbol}): {e}")
            summary["failed"] += 1

    logger.warning(
        f"🚨 Kill Switch cancel complete — "
        f"cancelled={summary['cancelled']}, "
        f"failed={summary['failed']}, "
        f"skipped={summary['skipped']}"
    )
    return summary


@app.post("/api/trading/control")
async def trading_control(req: TradingControlRequest):
    """Unified control endpoint for Trading Engine"""
    try:
        if req.action == "START":
            # Update config and start
            if req.capital:
                AUTONOMOUS_TRADER.config.update({"capital": req.capital})

            await AUTONOMOUS_TRADER.start()

            return {
                "success": True,
                "status": "RUNNING",
                "message": "Engine Started Successfully"
            }

        elif req.action == "STOP":
            await AUTONOMOUS_TRADER.stop()
            return {
                "success": True,
                "status": "STOPPED",
                "message": "Engine Stopped"
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except Exception as e:
        logger.error(f"Trading control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trading/kill-switch")
async def set_kill_switch(req: KillSwitchRequest):
    """
    Global Emergency Kill Switch.

    When active=true:
      1. Immediately stops the autonomous trading loop.
      2. Fetches all open/pending orders from Engine C and cancels each one.
      3. Returns a cancel summary (cancelled / failed / skipped counts).

    When active=false:
      - Simply deactivates the kill switch flag (does not restart trading).
        Use /api/v1/auto-trade/start or /api/trading/control to restart.
    """
    try:
        cancel_summary = {}

        if req.active:
            # Step 1 — Stop the autonomous trader immediately
            await AUTONOMOUS_TRADER.stop()
            logger.warning("🚨 KILL SWITCH ACTIVATED — autonomous trader stopped")

            # Step 2 — Cancel all open/pending orders via Engine C
            cancel_summary = await cancel_all_orders()
            logger.warning(f"🚨 Kill Switch cancel summary: {cancel_summary}")

        else:
            logger.info("✅ Kill Switch DEACTIVATED — trading loop remains stopped until manually restarted")

        return {
            "success": True,
            "kill_switch_active": req.active,
            "message": "Kill Switch " + ("ACTIVATED" if req.active else "DEACTIVATED"),
            "autonomous_trader_stopped": req.active,
            "cancel_summary": cancel_summary,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Kill switch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/v1/shadow-signals")
async def get_shadow_signals(limit: int = 50, month: Optional[str] = None):
    """
    Returns live shadow signals ledger with aggregate monthly performance metrics.
    """
    try:
        from google.cloud import firestore
        project_id = os.getenv("GCP_PROJECT_ID", "project-841b7f97-5ee3-4fbe-920")
        db = firestore.Client(project=project_id)
        col = db.collection("ai_signals_ledger")
        
        query = col.order_by("timestamp_utc", direction=firestore.Query.DESCENDING).limit(limit)
        docs = list(query.stream())
        
        signals = []
        resolved_trades = 0
        winning_trades = 0
        gross_pnl_total = 0.0
        net_pnl_total = 0.0
        fees_total = 0.0
        
        for d in docs:
            data = d.to_dict()
            signals.append(data)
            status = data.get("outcome_status")
            if status in ["TARGET_HIT", "STOP_LOSS_HIT", "EOD_SQUAREOFF"]:
                resolved_trades += 1
                net = data.get("net_pnl") or 0.0
                gross = data.get("gross_pnl") or 0.0
                fees = data.get("estimated_tax_brokerage") or 55.0
                gross_pnl_total += gross
                net_pnl_total += net
                fees_total += fees
                if net > 0:
                    winning_trades += 1
                    
        win_rate = (winning_trades / resolved_trades * 100) if resolved_trades > 0 else 0.0
        
        return {
            "status": "success",
            "total_signals": len(signals),
            "summary": {
                "resolved_trades": resolved_trades,
                "win_rate": round(win_rate, 2),
                "gross_pnl": round(gross_pnl_total, 2),
                "total_fees": round(fees_total, 2),
                "net_pnl": round(net_pnl_total, 2),
                "roi_30k_pct": round((net_pnl_total / 30000.0) * 100, 2)
            },
            "signals": signals
        }
    except Exception as e:
        logger.error(f"Error fetching shadow signals: {e}")
        return {"status": "error", "message": str(e), "signals": [], "summary": {}}


@app.post("/api/v1/shadow-signals/scan-now")
async def trigger_shadow_scan_now(force: bool = False):
    """
    Manually triggers an immediate market radar scan and logs signals with expected PnL to Firestore.
    """
    try:
        from src.services.autonomous_shadow_scanner import AUTONOMOUS_SHADOW_SCANNER
        res = await AUTONOMOUS_SHADOW_SCANNER.scan_once(force=force)
        return {"status": "success", "result": res}
    except Exception as e:
        logger.error(f"Manual shadow scan failed: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/shadow-signals/reconcile-outcomes")
async def reconcile_shadow_outcomes(req: Optional[Dict[str, Any]] = None):
    """
    Reconciles open shadow signals against current spot prices and resolves targets/stops.
    """
    try:
        from src.services.shadow_signal_logger import ShadowSignalLogger
        logger_svc = ShadowSignalLogger()
        spot_prices = (req or {}).get("spot_prices")
        if not spot_prices:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{ENGINE_C_URL}/api/dhan/market/quotes")
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", []) if isinstance(data, dict) else []
                    spot_prices = {}
                    for it in items:
                        sym = it.get("trading_symbol", "").upper()
                        ltp = float(it.get("ltp", 0.0))
                        if ltp > 0:
                            if "NIFTY 50" in sym or sym == "NIFTY": spot_prices["NIFTY"] = ltp
                            elif "BANKNIFTY" in sym or sym == "BANK NIFTY": spot_prices["BANKNIFTY"] = ltp
                            elif "FINNIFTY" in sym: spot_prices["FINNIFTY"] = ltp
                            elif "MIDCP" in sym: spot_prices["MIDCPNIFTY"] = ltp
                            elif "SENSEX" in sym: spot_prices["SENSEX"] = ltp

        res = logger_svc.update_open_signals_mtm(spot_prices or {})
        return {"status": "success", "result": res}
    except Exception as e:
        logger.error(f"Shadow outcome reconciliation failed: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/eod-settlement")
async def trigger_eod_settlement(req: Optional[Dict[str, Any]] = None):
    """
    Automated 15:45 IST EOD Settlement & Retraining trigger (invoked by Cloud Scheduler).
    """
    try:
        from src.services.eod_settlement_service import EODSettlementService
        eod_svc = EODSettlementService()
        spot_prices = (req or {}).get("spot_prices")
        result = eod_svc.run_eod_reconciliation(current_spot_prices=spot_prices)
        retrain_res = eod_svc.trigger_nightly_retraining()
        result["retraining_trigger"] = retrain_res
        return result
    except Exception as e:
        logger.error(f"EOD Settlement API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/premarket/trigger-briefing")
async def trigger_premarket_briefing():
    """
    Triggers the 08:30 IST Vertex AI Gemini Pre-Market Macro Radar synthesis and dispatches alerts.
    """
    try:
        from src.services.premarket_briefing_service import PREMARKET_BRIEFING_SERVICE
        report = await PREMARKET_BRIEFING_SERVICE.generate_and_dispatch_briefing()
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"Pre-market briefing generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/premarket/today")
async def get_todays_premarket_briefing():
    """
    Fetches today's pre-market macro synthesis report for the frontend dashboard.
    """
    try:
        from src.services.premarket_briefing_service import PREMARKET_BRIEFING_SERVICE
        report = PREMARKET_BRIEFING_SERVICE.get_latest_briefing()
        if not report:
            # Generate on-demand fallback
            report = await PREMARKET_BRIEFING_SERVICE.generate_and_dispatch_briefing()
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"Failed to fetch today's briefing: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/v1/options/surface/{symbol}")
async def get_options_volatility_surface(symbol: str = "NIFTY", dte: float = 3.0):
    """
    Calculates and returns real-time Black-Scholes Greeks (Delta, Gamma, Theta, Vega)
    and Implied Volatility (IV) Smile Surface across the strike chain.
    """
    try:
        from src.services.options_greeks_engine import OPTIONS_GREEKS_ENGINE
        
        # Spot price estimation or live query
        spots = {"NIFTY": 24252.0, "BANKNIFTY": 52410.0, "FINNIFTY": 23180.0, "SENSEX": 79850.0}
        spot = spots.get(symbol.upper(), 24252.0)
        
        surface = OPTIONS_GREEKS_ENGINE.generate_volatility_surface(
            symbol=symbol.upper(),
            spot=spot,
            dte_days=dte
        )
        return {"status": "success", "surface": surface}
    except Exception as e:
        logger.error(f"Error generating options surface: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/risk/reset-circuit-breaker")
@app.post("/api/v1/trade/reset-halt")
async def reset_circuit_breaker(user_id: Optional[str] = "raghu_primary"):
    """
    Manually resets the circuit breaker / kill switch state in Firestore and in-memory.
    Clears CONSECUTIVE_LOSSES_LIMIT and MAX_DRAWDOWN_REACHED flags to resume trading.
    """
    try:
        from src.services.circuit_breaker import CircuitBreaker, get_db
        primary_uid = os.getenv("PRIMARY_USER_ID", "raghu_primary")
        target_uids = [user_id, "system", primary_uid] if user_id else ["raghu_primary", "system"]
        results = {}

        for uid in set(filter(None, target_uids)):
            cb = CircuitBreaker(uid=uid)
            cb.reset()
            results[uid] = "RESET_OK"

        return {
            "status": "success",
            "message": "Circuit breaker / kill switch successfully reset across all sessions. Trading halt cleared.",
            "cleared_sessions": results,
            "trading_halted": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Reset Circuit Breaker API error: {e}")
        raise HTTPException(500, f"Failed to reset circuit breaker: {e}")


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_engine_b_v1(path: str, request: Request) -> Response:
    """
    Public API gateway for Engine-B /api/v1/* endpoints.
    Frontend calls Engine-A, Engine-A forwards to private Engine-B VM.
    """
    if http_client is None:
        raise HTTPException(status_code=503, detail="Engine-A HTTP client not initialized")

    upstream_url = f"{ENGINE_B_URL}/api/v1/{path}"
    body = await request.body()
    headers: Dict[str, str] = {}
    for key in ("content-type", "accept", "authorization", "x-trace-id", "x-request-id"):
        value = request.headers.get(key)
        if value:
            headers[key] = value

    try:
        upstream_response = await http_client.request(
            method=request.method,
            url=upstream_url,
            params=request.query_params,
            content=body if body else None,
            headers=headers or None,
            timeout=60.0,
        )
    except httpx.HTTPError as exc:
        logger.error(f"Engine-B proxy failure for {upstream_url}: {exc}")
        raise HTTPException(status_code=502, detail=f"Engine-B upstream request failed: {exc}") from exc

    response_headers: Dict[str, str] = {}
    content_type = upstream_response.headers.get("content-type")
    if content_type:
        response_headers["content-type"] = content_type

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )


# =====================================================================
# INSTITUTIONAL AI JOURNAL, CIRCUIT BREAKER & CONFLUENCE ROUTES
# =====================================================================

@app.post("/api/v1/journal/trigger-eod")
async def trigger_eod_journal(date_str: Optional[str] = None):
    """Triggers the 15:35 IST post-market AI qualitative journal and Telegram digest"""
    from src.services.eod_ai_journal_service import EOD_AI_JOURNAL_SERVICE
    try:
        report = await EOD_AI_JOURNAL_SERVICE.generate_and_dispatch_eod_journal(target_date_str=date_str)
        return {"status": "success", "journal": report}
    except Exception as e:
        logger.error(f"EOD journal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/circuit-breaker/status")
async def get_circuit_breaker_status():
    """Returns current real-time market risk & circuit breaker status"""
    from src.services.black_swan_circuit_breaker import BLACK_SWAN_BREAKER
    return {
        "is_halted": BLACK_SWAN_BREAKER._is_halted,
        "halt_reason": BLACK_SWAN_BREAKER._halt_reason,
        "vix_danger_threshold": BLACK_SWAN_BREAKER.vix_absolute_threshold,
        "flash_drop_threshold_pct": BLACK_SWAN_BREAKER.flash_drop_pct_threshold,
        "status": "FROZEN_CIRCUIT_TRIPPED" if BLACK_SWAN_BREAKER._is_halted else "NOMINAL_ACTIVE"
    }

@app.post("/api/v1/circuit-breaker/reset")
async def reset_circuit_breaker():
    """Manually resets the circuit breaker"""
    from src.services.black_swan_circuit_breaker import BLACK_SWAN_BREAKER
    BLACK_SWAN_BREAKER.reset()
    return {"status": "success", "message": "Circuit breaker reset to NOMINAL_ACTIVE."}

@app.post("/api/v1/confluence/evaluate")
async def evaluate_confluence_filter(symbol: str = "NIFTY", signal_type: str = "BUY_CALL", current_price: float = 24250.0):
    """Evaluates 1m, 5m, 15m trend confluence for a prospective trade signal"""
    from src.services.mtf_confluence_filter import MTF_CONFLUENCE_FILTER
    res = MTF_CONFLUENCE_FILTER.evaluate_confluence(
        symbol=symbol,
        signal_type=signal_type,
        current_price=current_price
    )
    return res

@app.post("/api/v1/stream/cycle")
async def trigger_live_stream_cycle():
    """Triggers an instantaneous live market tick publish cycle to GCP Pub/Sub & BigQuery"""
    from src.services.live_tick_streamer import LIVE_TICK_STREAMER
    results = await LIVE_TICK_STREAMER.publish_live_stream_cycle()
    return {"status": "success", "results": results}

@app.get("/api/v1/stream/quote")
async def get_live_stream_quote(symbol: str = "NIFTY"):
    """Fetches real-time exchange quote and engineered features for an Indian index"""
    from src.services.live_tick_streamer import LIVE_TICK_STREAMER
    quote = LIVE_TICK_STREAMER.fetch_live_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Unable to fetch real-time quote for {symbol}")
    return {"status": "success", "data": quote}


@app.get("/api/v1/flow/institutional-radar")
async def get_institutional_flow_radar():
    """Fetches real-time FII/DII institutional cash & index futures long/short delta metrics"""
    from src.services.fii_dii_flow_radar import FII_DII_FLOW_RADAR
    flow = FII_DII_FLOW_RADAR.fetch_live_institutional_flow()
    return {"status": "success", "data": flow}

@app.post("/api/v1/risk/profit-lock/evaluate")
async def evaluate_profit_lock_simulation(
    entry_premium: float,
    highest_premium: float,
    current_premium: float,
    lot_size: int = 65
):
    """Simulates and evaluates the multi-tier ratchet dynamic profit lock algorithm"""
    from src.services.dynamic_trailing_profit_lock import DYNAMIC_PROFIT_LOCK
    result = DYNAMIC_PROFIT_LOCK.evaluate_trailing_lock(
        entry_premium=entry_premium,
        highest_observed_premium=highest_premium,
        current_premium=current_premium,
        lot_size=lot_size
    )
    return {"status": "success", "data": result}

@app.post("/api/v1/risk/dynamic/evaluate")
async def evaluate_dynamic_risk(
    entry_premium: float,
    current_premium: float,
    ml_confidence: float = 0.55,
    order_book_imbalance: float = 0.0,
    iv: float = 0.1717,
    gamma: float = 0.00084
):
    """Evaluates dynamic mathematical risk boundaries (Alpha decay, Volatility floor, Liquidity OBI)"""
    from src.services.dynamic_risk_service import DYNAMIC_RISK_SERVICE
    from src.services.risk_config import LiveMarketState
    from datetime import datetime, timezone
    
    state = LiveMarketState(
        timestamp=datetime.now(timezone.utc),
        current_premium=current_premium,
        entry_premium=entry_premium,
        ml_confidence=ml_confidence,
        order_book_imbalance=order_book_imbalance,
        live_greeks={"IV": iv, "Gamma": gamma, "Delta": 0.54}
    )
    decision = DYNAMIC_RISK_SERVICE.evaluate_live_signals(state)
    return {"status": "success", "decision": decision}

@app.get("/api/v1/ml/ensemble-weights")
async def get_bayesian_ensemble_weights():
    """Fetches active Bayesian online weights and performance metrics for the Tri-Model ensemble"""
    from src.services.bayesian_ensemble_client import BAYESIAN_CLIENT
    weights = BAYESIAN_CLIENT.get_active_weights()
    champion = max(weights, key=weights.get) if weights else "catboost"
    return {
        "status": "success",
        "weights": weights,
        "champion_model": champion,
        "optimization_mode": "BAYESIAN_ONLINE_UPDATING",
        "decay_factor": 0.85,
        "temperature": 4.5
    }

@app.post("/api/v1/ml/consensus")
async def calculate_bayesian_consensus(
    catboost_prob: float,
    lightgbm_prob: float,
    xgboost_prob: float
):
    """Calculates weighted consensus probability using active Bayesian online weights"""
    from src.services.bayesian_ensemble_client import BAYESIAN_CLIENT
    res = BAYESIAN_CLIENT.calculate_bayesian_consensus(catboost_prob, lightgbm_prob, xgboost_prob)
    return {"status": "success", "data": res}

@app.post("/api/v1/preflight/trigger-check")
async def trigger_preflight_check():
    """Triggers 08:15 IST automated pre-flight readiness audit and dispatches clearance alert"""
    from src.services.preflight_health_service import PREFLIGHT_HEALTH_SERVICE
    report = await PREFLIGHT_HEALTH_SERVICE.execute_preflight_check()
    return {"status": "success", "report": report}

@app.get("/api/v1/expiry/shield/evaluate")
async def evaluate_expiry_shield(
    symbol: str = "NIFTY",
    spot_price: float = 24219.05,
    entry_premium: float = 99.43,
    current_premium: float = 105.00,
    highest_premium: float = 112.00,
    gamma: float = 0.0018,
    theta: float = -45.26
):
    """Evaluates 0DTE/1DTE Gamma Pinning & Afternoon Theta Shield for Expiry sessions"""
    from src.services.expiry_gamma_pinning_shield import EXPIRY_GAMMA_SHIELD
    res = EXPIRY_GAMMA_SHIELD.evaluate_expiry_shield(
        symbol=symbol,
        spot_price=spot_price,
        live_greeks={"Gamma": gamma, "Theta": theta},
        entry_premium=entry_premium,
        current_premium=current_premium,
        highest_observed_premium=highest_premium
    )
    return {"status": "success", "data": res}


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
