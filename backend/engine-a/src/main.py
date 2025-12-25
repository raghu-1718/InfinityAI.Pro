import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from google.cloud import secretmanager
import httpx
import uvicorn
from src.trace_middleware import TraceIDMiddleware

# ML Libraries for Risk & Portfolio Management
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import LedoitWolf
import joblib

# Google Cloud Integrations (Official SDKs)
try:
    from src.google_integrations import (
        GenAIClient,
        GeminiModel,  # Added for model selection
        TradingLogger,
        TradingEventType,
        ModelStorage,
        TradingHistoryStorage,
        AgentOrchestrator,
        create_trading_workflow
    )
    GOOGLE_INTEGRATIONS_AVAILABLE = True
except ImportError as e:
    GOOGLE_INTEGRATIONS_AVAILABLE = False
    GeminiModel = None  # Fallback
    print(f"⚠️ Google integrations not available: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    # Start Autonomous Trader
    await AUTONOMOUS_TRADER.start()

    yield  # App is running

    # Shutdown
    logger.info("🛑 Engine A shutting down...")
    
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

# CORS allowed origins for production
ALLOWED_ORIGINS = [
    "https://infinityai.pro",
    "https://www.infinityai.pro",
    "https://app.infinityai.pro",
    "https://engine-a.infinityai.pro",
    "https://engine-b.infinityai.pro",
    "https://engine-c.infinityai.pro",
    f"https://{PROJECT_ID}.web.app",
    f"https://{PROJECT_ID}.firebaseapp.com",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Risk Management ML Models ---
from src.services.risk_manager import RiskManager
from src.services.autonomous_trader import AutonomousTrader

# Initialize Risk Manager (from service)
RISK_MANAGER = RiskManager()
# Initialize Autonomous Trader
AUTONOMOUS_TRADER = AutonomousTrader(RISK_MANAGER)

# --- Google Cloud Integrations ---
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

# --- Secret Manager Helper ---
def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
             logger.warning("Using default project ID 'infinity-ai-pro-dev' for secret retrieval")
             project_id = "infinity-ai-pro-dev"
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        # Strip any trailing whitespace/newlines from the secret
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Error fetching secret {secret_id}: {e}")
        return ""

# --- Models ---
class OrchestrateRequest(BaseModel):
    symbol: str
    qty: Optional[float] = 1.0
    strategy: Optional[str] = None

class InstrumentTradeRequest(BaseModel):
    """Request model for instrument-specific auto trading"""
    instruments: List[str]  # e.g., ['equities', 'nifty-options', 'banknifty-options']
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
    asset_class: Literal["equities", "fno", "commodities"]
    user_id: str

from src.services.session_manager import acquire_session_lock, release_session_lock, SessionExistsError
from src.services.audit_logger import AuditLogger

audit_logger = AuditLogger()

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
                headers = {"X-User-ID": user_id}
                resp = await client.get(f"{ENGINE_C_URL}/api/system/status", headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("dhan_connected"):
                        dhan_connected = True
                        trader_identity = data.get("account_name", "Trader")
                    
                    if data.get("status") != "NORMAL":
                         status = "DEGRADED"
    except Exception as e:
        logger.warning(f"Failed to fetch Engine C status: {e}")
        status = "DEGRADED"

    # 2. Check Engine A Status
    if not AUTONOMOUS_TRADER.is_active:
        # If trader is not active, status is effectively STANDBY for A
        pass 
        
    # 3. Optimism & Volatility Logic (Real-Time from Engine B)
    global _MARKET_CACHE
    current_time = datetime.utcnow()
    
    # Check In-Memory Cache (TTL: 60s)
    if _MARKET_CACHE["last_updated"] and (current_time - _MARKET_CACHE["last_updated"]).total_seconds() < 60:
        current_vix = _MARKET_CACHE["vix"]
    else:
        # Fetch fresh data from Engine B (Optimistic: don't block heavily, short timeout)
        try:
            async with httpx.AsyncClient() as client:
                # Using Engine B's market summary which includes VIX/Volatility analysis
                # Attempting to get 'pulse' or 'nifty-overview'
                resp = await client.get(f"{ENGINE_B_URL}/api/v1/market/nifty-overview", timeout=3.0)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    # Try to find VIX in various common fields
                    current_vix = data.get("india_vix") or data.get("vix") or data.get("volatility", 14.5)
                    
                    # Update Cache
                    _MARKET_CACHE["vix"] = float(current_vix)
                    _MARKET_CACHE["last_updated"] = current_time
                    logger.info(f"🔄 Market VIX Updated: {current_vix}")
                else:
                    current_vix = _MARKET_CACHE["vix"] # Fallback to last known
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch VIX from Engine B: {e}")
            current_vix = _MARKET_CACHE["vix"]

    # Calculate Optimism Level
    optimism_level = "NORMAL"
    if current_vix < 12.0:
        optimism_level = "HIGH"
    elif current_vix > 20.0:
        optimism_level = "LOW"

    return SystemStateResponse(
        system_status=status,
        dhan_connected=dhan_connected,
        trader_identity=trader_identity,
        engine_active=AUTONOMOUS_TRADER.is_active,
        optimism_level=optimism_level,
        current_vix=current_vix,
        timestamp=datetime.utcnow().isoformat()
    )


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
# Use Cloud Run URLs for production inter-engine communication (subdomains not mapped)
ENGINE_B_URL = os.getenv("ENGINE_B_URL", "https://engine-b-429140669077.us-central1.run.app")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c-429140669077.us-central1.run.app")

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

        # TODO: Store access_token securely in Firestore or GSM
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
    current_price = signal_data.get("entry_price") or 0.0
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
        "RELIANCE": "1333",
        "TCS": "2968",
        "HDFCBANK": "1394",
        "INFY": "1594",
        "ICICIBANK": "1270",
        "NIFTY": "13",
        "BANKNIFTY": "25"
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
                timeout=15.0
            )
            exec_response.raise_for_status()
            logger.info(f"✅ Execution successful: {exec_response.json()}")
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

    # Map instrument types to exchange segments and symbol patterns
    instrument_config = {
        "equities": {
            "exchange_segment": "NSE_EQ",
            "product_type": "INTRADAY",
            "pattern": None,  # No pattern filter for general equities
        },
        "nifty-options": {
            "exchange_segment": "NSE_FNO",
            "product_type": "INTRADAY",
            "pattern": "NIFTY",
            "exclude_patterns": ["BANKNIFTY", "FINNIFTY"]
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
        analysis = await GENAI_CLIENT.generate_trading_signal(
            symbol=req.symbol,
            market_data=market_data
        )

        # Log the signal generation
        if TRADING_LOGGER:
            TRADING_LOGGER.log_signal(
                symbol=req.symbol,
                signal_type=analysis.get("signal", "HOLD"),
                confidence=analysis.get("confidence", 0.0),
                source="gemini-2.0-flash",
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
    """Global Kill Switch"""
    try:
        if req.active:
            await AUTONOMOUS_TRADER.stop()
            # In a real scenario, this would also cancel all open orders via Engine C
            # await cancel_all_orders()
            # Check if kill switch state needs persistence
            
        return {
            "success": True,
            "kill_switch_active": req.active,
            "message": "Kill Switch " + ("ACTIVATED" if req.active else "DEACTIVATED")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/state")
async def get_system_state():
    """Global System State for Frontend Banner"""
    status = "NORMAL"
    message = "All systems operational"
    
    if not AUTONOMOUS_TRADER.is_active:
        status = "STANDBY"
        message = "Engine is ready to start"
    else:
        status = "LIVE_TRADING"
        message = "AI Engine Active"

    # Check dependencies (simplified)
    if not GOOGLE_INTEGRATIONS_AVAILABLE:
        status = "DEGRADED"
        message = "ML Services Unavailable"

    return {
        "status": status,
        "message": message,
        "engine_version": "v4.0",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
