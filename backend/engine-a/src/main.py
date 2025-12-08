import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from google.cloud import secretmanager
import httpx
import uvicorn

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

app = FastAPI(
    title="InfinityAI.Pro - Engine A (Orchestration & Risk Management)",
    description="Orchestration, OAuth, Risk Scoring & Portfolio Optimization",
    version="3.1-ml"
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Risk Management ML Models ---
class RiskManager:
    """ML-based risk assessment and portfolio optimization with advanced metrics"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.covariance_estimator = LedoitWolf()
        self.risk_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 1.0
        }
        logger.info("✅ Risk Manager initialized with advanced metrics")

    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95,
                      method: str = "historical") -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) using multiple methods.
        Methods: historical, parametric, cornish-fisher
        """
        if len(returns) == 0:
            return {"var": 0.0, "method": method}

        returns = np.array(returns)

        if method == "historical":
            var = float(np.percentile(returns, (1 - confidence) * 100))
        elif method == "parametric":
            # Assumes normal distribution
            from scipy.stats import norm
            z_score = norm.ppf(1 - confidence)
            var = float(np.mean(returns) + z_score * np.std(returns))
        elif method == "cornish-fisher":
            # Adjusts for skewness and kurtosis
            from scipy.stats import norm
            z = norm.ppf(1 - confidence)
            s = float(pd.Series(returns).skew())
            k = float(pd.Series(returns).kurtosis())
            cf_z = z + (1/6) * (z**2 - 1) * s + (1/24) * (z**3 - 3*z) * k - (1/36) * (2*z**3 - 5*z) * s**2
            var = float(np.mean(returns) + cf_z * np.std(returns))
        else:
            var = float(np.percentile(returns, (1 - confidence) * 100))

        return {
            "var": round(var, 6),
            "var_pct": round(abs(var) * 100, 4),
            "confidence": confidence,
            "method": method,
            "samples": len(returns)
        }

    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> Dict[str, float]:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
        CVaR represents the expected loss given that VaR threshold is breached.
        """
        if len(returns) == 0:
            return {"cvar": 0.0, "var": 0.0}

        returns = np.array(returns)
        var_threshold = np.percentile(returns, (1 - confidence) * 100)
        cvar = float(np.mean(returns[returns <= var_threshold]))

        return {
            "cvar": round(cvar, 6),
            "cvar_pct": round(abs(cvar) * 100, 4),
            "var": round(var_threshold, 6),
            "confidence": confidence,
            "tail_observations": int(np.sum(returns <= var_threshold)),
            "samples": len(returns)
        }

    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.05) -> float:
        """Calculate Sharpe Ratio (annualized)"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        excess_returns = np.mean(returns) - risk_free_rate / 252
        return float(round(excess_returns / np.std(returns) * np.sqrt(252), 4))

    def calculate_sortino_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.05,
                                 target_return: float = 0.0) -> Dict[str, float]:
        """
        Calculate Sortino Ratio - uses downside deviation instead of total std.
        Better for asymmetric return distributions.
        """
        if len(returns) == 0:
            return {"sortino": 0.0, "downside_deviation": 0.0}

        returns = np.array(returns)
        excess_returns = np.mean(returns) - risk_free_rate / 252

        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            downside_deviation = 0.0001  # Avoid division by zero
        else:
            downside_deviation = float(np.std(downside_returns))

        sortino = float(excess_returns / downside_deviation * np.sqrt(252)) if downside_deviation > 0 else 0.0

        return {
            "sortino_ratio": round(sortino, 4),
            "downside_deviation": round(downside_deviation, 6),
            "annualized_downside_deviation": round(downside_deviation * np.sqrt(252), 6),
            "mean_return": round(float(np.mean(returns)), 6),
            "negative_return_days": len(downside_returns)
        }

    def calculate_kelly_criterion(self, win_rate: float, avg_win: float,
                                   avg_loss: float) -> Dict[str, float]:
        """
        Calculate Kelly Criterion for optimal position sizing.
        Returns the optimal fraction of capital to bet.
        """
        if avg_loss == 0 or avg_win == 0:
            return {"kelly_fraction": 0.0, "half_kelly": 0.0}

        # Kelly = W - [(1-W) / R], where W = win rate, R = win/loss ratio
        win_loss_ratio = abs(avg_win / avg_loss)
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)

        # Cap at reasonable levels
        kelly = max(0, min(kelly, 1.0))

        return {
            "kelly_fraction": round(kelly, 4),
            "kelly_pct": round(kelly * 100, 2),
            "half_kelly": round(kelly / 2, 4),  # More conservative
            "quarter_kelly": round(kelly / 4, 4),  # Very conservative
            "win_rate": round(win_rate, 4),
            "win_loss_ratio": round(win_loss_ratio, 4),
            "recommendation": "half_kelly" if kelly > 0.2 else "quarter_kelly"
        }

    def calculate_portfolio_risk(self, returns_matrix: np.ndarray,
                                  weights: np.ndarray) -> Dict[str, Any]:
        """
        Calculate portfolio risk using Ledoit-Wolf covariance estimation.
        More stable than sample covariance for high-dimensional portfolios.
        """
        if returns_matrix.shape[0] < 2 or returns_matrix.shape[1] < 1:
            return {"portfolio_variance": 0.0, "portfolio_std": 0.0}

        try:
            # Fit Ledoit-Wolf shrinkage estimator
            lw = LedoitWolf()
            lw.fit(returns_matrix)
            cov_matrix = lw.covariance_
            shrinkage = lw.shrinkage_

            # Calculate portfolio variance
            portfolio_variance = float(np.dot(weights.T, np.dot(cov_matrix, weights)))
            portfolio_std = float(np.sqrt(portfolio_variance))

            # Annualize
            annualized_std = portfolio_std * np.sqrt(252)

            return {
                "portfolio_variance": round(portfolio_variance, 8),
                "portfolio_std": round(portfolio_std, 6),
                "annualized_volatility": round(annualized_std, 4),
                "annualized_volatility_pct": round(annualized_std * 100, 2),
                "shrinkage_coefficient": round(shrinkage, 4),
                "covariance_method": "ledoit-wolf",
                "assets_count": returns_matrix.shape[1]
            }
        except Exception as e:
            logger.error(f"Portfolio risk calculation failed: {e}")
            return {"error": str(e), "portfolio_variance": 0.0}

    def calculate_max_drawdown(self, cumulative_returns: np.ndarray) -> Dict[str, float]:
        """Calculate Maximum Drawdown from cumulative returns"""
        if len(cumulative_returns) == 0:
            return {"max_drawdown": 0.0, "max_drawdown_pct": 0.0}

        cumulative_returns = np.array(cumulative_returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        max_dd = float(np.min(drawdown))

        # Find drawdown period
        peak_idx = np.argmax(cumulative_returns[:np.argmin(drawdown) + 1])
        trough_idx = np.argmin(drawdown)

        return {
            "max_drawdown": round(max_dd, 6),
            "max_drawdown_pct": round(abs(max_dd) * 100, 2),
            "peak_index": int(peak_idx),
            "trough_index": int(trough_idx),
            "recovery_needed_pct": round((1 / (1 + max_dd) - 1) * 100, 2) if max_dd > -1 else 0
        }

    def score_risk(self, position_size: float, volatility: float, max_drawdown: float) -> Dict[str, Any]:
        """Score risk for a trade"""
        # Normalize inputs
        size_score = min(position_size / 100000, 1.0)  # Normalize by max position
        vol_score = min(volatility / 0.5, 1.0)  # Normalize by max volatility
        dd_score = min(abs(max_drawdown) / 0.2, 1.0)  # Normalize by max drawdown

        # Weighted risk score
        risk_score = 0.3 * size_score + 0.4 * vol_score + 0.3 * dd_score

        # Determine risk level
        if risk_score < self.risk_thresholds["low"]:
            risk_level = "LOW"
        elif risk_score < self.risk_thresholds["medium"]:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "components": {
                "position_size_risk": round(size_score, 4),
                "volatility_risk": round(vol_score, 4),
                "drawdown_risk": round(dd_score, 4)
            },
            "recommendation": "PROCEED" if risk_score < 0.7 else "REVIEW"
        }

    def optimize_position_size(self, capital: float, risk_per_trade: float,
                                stop_loss_pct: float) -> Dict[str, Any]:
        """Calculate optimal position size based on risk parameters"""
        risk_amount = capital * risk_per_trade
        position_size = risk_amount / stop_loss_pct if stop_loss_pct > 0 else 0

        return {
            "optimal_position_size": round(position_size, 2),
            "risk_amount": round(risk_amount, 2),
            "max_loss": round(risk_amount, 2),
            "position_pct_of_capital": round((position_size / capital) * 100, 2) if capital > 0 else 0
        }

    def get_comprehensive_metrics(self, returns: np.ndarray,
                                   risk_free_rate: float = 0.05) -> Dict[str, Any]:
        """Get all risk metrics in a single call"""
        returns = np.array(returns)
        cumulative = np.cumprod(1 + returns)

        var_result = self.calculate_var(returns, 0.95, "historical")
        cvar_result = self.calculate_cvar(returns, 0.95)
        sortino_result = self.calculate_sortino_ratio(returns, risk_free_rate)
        drawdown_result = self.calculate_max_drawdown(cumulative)

        return {
            "sharpe_ratio": self.calculate_sharpe_ratio(returns, risk_free_rate),
            "sortino_ratio": sortino_result["sortino_ratio"],
            "var_95": var_result["var"],
            "cvar_95": cvar_result["cvar"],
            "max_drawdown_pct": drawdown_result["max_drawdown_pct"],
            "annualized_return": round(float(np.mean(returns) * 252), 4),
            "annualized_volatility": round(float(np.std(returns) * np.sqrt(252)), 4),
            "total_return": round(float(cumulative[-1] - 1) if len(cumulative) > 0 else 0, 4),
            "samples": len(returns)
        }

RISK_MANAGER = RiskManager()

# --- Google Cloud Integrations ---
TRADING_LOGGER = None
MODEL_STORAGE = None
HISTORY_STORAGE = None
GENAI_CLIENT = None
AGENT_ORCHESTRATOR = None

if GOOGLE_INTEGRATIONS_AVAILABLE:
    try:
        PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0779271931")

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

        # Initialize Agent Orchestrator for multi-agent workflows
        AGENT_ORCHESTRATOR = create_trading_workflow(GENAI_CLIENT)
        logger.info("✅ Agent Orchestrator initialized with trading workflow")

    except Exception as e:
        logger.warning(f"⚠️ Error initializing Google integrations: {e}")

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

class ComprehensiveRiskRequest(BaseModel):
    returns: List[float]
    risk_free_rate: float = 0.05

# --- Config ---
# Use custom domains for production inter-engine communication
ENGINE_B_URL = os.getenv("ENGINE_B_URL", "https://engine-b.infinityai.pro")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c.infinityai.pro")

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

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(token_url, json=payload)
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

    # 1. Get AI Signal from Engine-B
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            signal_response = await client.post(
                f"{ENGINE_B_URL}/api/v1/signal",
                json={"symbol": req.symbol}
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

    # 3. Schedule Execution with Engine C (Background Task)
    async def send_execution():
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                exec_response = await client.post(
                    f"{ENGINE_C_URL}/api/dhan/place-order",
                    json=exec_payload
                )
                exec_response.raise_for_status()
                print(f"✅ Execution successful: {exec_response.json()}")
            except Exception as e:
                print(f"❌ Execution failed: {str(e)}")

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

    # 1. Get AI Signals from Engine-B with instrument filter
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Request signals for selected instruments
            signal_response = await client.post(
                f"{ENGINE_B_URL}/api/v1/signals/instruments",
                json={
                    "instruments": req.instruments,
                    "min_confidence": risk_config["minConfidence"],
                    "strategy": req.strategy
                }
            )
            signal_response.raise_for_status()
            signals_data = signal_response.json()
        except httpx.HTTPError as e:
            logger.warning(f"Engine B instrument signals not available, falling back to standard: {str(e)}")
            # Fallback to standard signal endpoint if instrument endpoint not available
            try:
                signal_response = await client.post(
                    f"{ENGINE_B_URL}/api/v1/signal",
                    json={"symbol": req.symbol or "NIFTY"}
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

        # Schedule execution in background
        async def send_execution(payload):
            async with httpx.AsyncClient(timeout=15.0) as client:
                try:
                    exec_response = await client.post(
                        f"{ENGINE_C_URL}/api/dhan/place-order",
                        json=payload
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
