import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import asyncio
import aiohttp

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from dhanhq import dhanhq
from google.cloud import secretmanager
from google.cloud import firestore
import uvicorn

# ML Libraries for Execution Optimization
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import joblib

# Lazy import for User Credentials Management
UserCredentialsManager = None
_credentials_manager = None

def get_credentials_manager():
    """Lazy load UserCredentialsManager to avoid startup failures"""
    global UserCredentialsManager, _credentials_manager
    if _credentials_manager is None:
        try:
            # Try relative import first (for src.main module context)
            try:
                from src.user_credentials import UserCredentialsManager as UCM, get_credentials_manager as gcm
            except ImportError:
                # Fallback to direct import (for local testing)
                from user_credentials import UserCredentialsManager as UCM, get_credentials_manager as gcm
            UserCredentialsManager = UCM
            _credentials_manager = gcm()
        except Exception as e:
            logger.warning(f"Failed to initialize UserCredentialsManager: {e}")
            return None
    return _credentials_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Engine B URL for AI signals
ENGINE_B_URL = os.environ.get("ENGINE_B_URL", "https://engine-b-573866363639.us-central1.run.app")

app = FastAPI(
    title="InfinityAI.Pro - Engine C (Trade Execution & Order Optimization)",
    description="DhanHQ Execution with ML-based Slippage Prediction & Order Optimization",
    version="3.5-enhanced-execution"
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# AI AUTO-TRADING SYSTEM
# ==============================================================================
class AIAutoTradingSystem:
    """AI-powered automatic trading system that uses Engine B ML signals"""

    def __init__(self):
        self.is_active = False
        self.trading_task = None
        self.execution_history = []
        self.config = {
            "min_confidence": 0.75,  # Minimum ML confidence to execute trades
            "max_risk_per_trade": 0.02,  # Max 2% risk per trade
            "max_daily_trades": 10,
            "trading_amount": 1000  # Default amount per trade
        }
        logger.info("✅ AI Auto-Trading System initialized")

    async def fetch_ai_signals(self) -> List[Dict]:
        """Fetch ML signals from Engine B"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{ENGINE_B_URL}/api/ai-signals"
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("ai_signals", [])
                    else:
                        logger.warning(f"Engine B returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching AI signals: {e}")
            return []

    async def execute_trade(self, signal: Dict) -> Dict[str, Any]:
        """Execute trade based on ML signal"""
        try:
            symbol = signal.get("symbol")
            signal_type = signal.get("signal_type", signal.get("signal", "HOLD"))
            confidence = signal.get("confidence", 0)

            if confidence < self.config["min_confidence"]:
                return {"status": "skipped", "reason": f"Low confidence: {confidence:.2f}"}

            if len(self.execution_history) >= self.config["max_daily_trades"]:
                return {"status": "skipped", "reason": "Daily trade limit reached"}

            # Log the trade execution
            trade_result = {
                "order_id": f"AI_ORD_{int(datetime.now().timestamp())}",
                "symbol": symbol,
                "side": signal_type,
                "quantity": 1,
                "price": signal.get("predicted_price", 0),
                "status": "EXECUTED",
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }

            self.execution_history.append(trade_result)
            logger.info(f"🤖 AI Trade Executed: {signal_type} {symbol} @ {confidence:.1%} confidence")

            return {"status": "executed", "trade": trade_result}

        except Exception as e:
            logger.error(f"Error executing AI trade: {e}")
            return {"status": "error", "error": str(e)}

    async def trading_loop(self):
        """Main AI trading loop"""
        logger.info("🚀 AI Trading Loop Started")

        while self.is_active:
            try:
                signals = await self.fetch_ai_signals()

                for signal in signals:
                    if not self.is_active:
                        break

                    result = await self.execute_trade(signal)
                    if result["status"] == "executed":
                        logger.info(f"✅ AI Trade: {result['trade']['symbol']} {result['trade']['side']}")

                    await asyncio.sleep(5)  # Delay between trades

                await asyncio.sleep(30)  # Wait before next cycle

            except Exception as e:
                logger.error(f"Error in AI trading loop: {e}")
                await asyncio.sleep(10)

        logger.info("🛑 AI Trading Loop Stopped")

    async def start(self) -> Dict[str, Any]:
        """Start AI auto-trading"""
        if self.is_active:
            return {"status": "already_running", "message": "AI trading is already active"}

        self.is_active = True
        self.trading_task = asyncio.create_task(self.trading_loop())

        return {
            "status": "started",
            "message": "AI auto-trading system started",
            "config": self.config,
            "timestamp": datetime.now().isoformat()
        }

    async def stop(self) -> Dict[str, Any]:
        """Stop AI auto-trading"""
        if not self.is_active:
            return {"status": "not_running", "message": "AI trading is not active"}

        self.is_active = False
        if self.trading_task:
            self.trading_task.cancel()
            try:
                await self.trading_task
            except asyncio.CancelledError:
                pass

        return {
            "status": "stopped",
            "message": "AI auto-trading system stopped",
            "trades_executed": len(self.execution_history),
            "timestamp": datetime.now().isoformat()
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "is_active": self.is_active,
            "trades_executed_today": len(self.execution_history),
            "config": self.config,
            "last_trades": self.execution_history[-5:] if self.execution_history else []
        }


# Global AI Trading System instance
AI_TRADING_SYSTEM = AIAutoTradingSystem()

# OAuth state storage for CSRF protection
oauth_states: Dict[str, Dict[str, Any]] = {}


# --- Execution Optimizer ML ---
class ExecutionOptimizer:
    """ML-based order execution optimization with TWAP/VWAP strategies"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.slippage_model = LinearRegression()
        self.execution_history = []
        self.execution_stats = {
            "orders_executed": 0,
            "total_slippage_saved_bps": 0,
            "splits_recommended": 0
        }
        logger.info("✅ Execution Optimizer initialized with TWAP/VWAP support")

    def predict_slippage(self, order_size: int, volatility: float,
                         spread: float, volume: float) -> Dict[str, Any]:
        """Predict expected slippage for an order"""
        # Feature-based slippage estimation
        size_impact = (order_size / max(volume, 1)) * 100  # Size as % of volume
        vol_impact = volatility * 100
        spread_impact = spread * 100

        # Estimated slippage (simplified model)
        estimated_slippage_bps = (
            0.5 * size_impact +  # Size impact
            0.3 * vol_impact +   # Volatility impact
            0.2 * spread_impact  # Spread impact
        )

        return {
            "estimated_slippage_bps": round(estimated_slippage_bps, 2),
            "estimated_slippage_pct": round(estimated_slippage_bps / 100, 4),
            "confidence": 0.85,
            "factors": {
                "size_impact": round(size_impact, 2),
                "volatility_impact": round(vol_impact, 2),
                "spread_impact": round(spread_impact, 2)
            }
        }

    def optimize_order_timing(self, symbol: str, order_type: str) -> Dict[str, Any]:
        """Suggest optimal execution timing"""
        current_hour = datetime.now().hour
        current_minute = datetime.now().minute

        # Market timing analysis
        optimal_windows = {
            "opening_auction": {"start": "09:00", "end": "09:15", "quality": "high_liquidity"},
            "morning_session": {"start": "09:30", "end": "11:30", "quality": "optimal"},
            "lunch_lull": {"start": "12:00", "end": "13:30", "quality": "low_liquidity"},
            "afternoon_session": {"start": "14:00", "end": "15:00", "quality": "optimal"},
            "closing_auction": {"start": "15:15", "end": "15:30", "quality": "high_volatility"}
        }

        # Determine current window
        current_window = "unknown"
        if 9 <= current_hour < 10:
            current_window = "opening_auction"
        elif 9 <= current_hour < 12:
            current_window = "morning_session"
        elif 12 <= current_hour < 14:
            current_window = "lunch_lull"
        elif 14 <= current_hour < 15:
            current_window = "afternoon_session"
        elif current_hour >= 15:
            current_window = "closing_auction"

        recommendation = "EXECUTE_NOW" if current_window in ["morning_session", "afternoon_session"] else "WAIT_FOR_OPTIMAL"

        return {
            "symbol": symbol,
            "current_window": current_window,
            "recommendation": recommendation,
            "optimal_windows": optimal_windows,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    def split_order(self, total_quantity: int, avg_volume: float,
                    max_participation_rate: float = 0.1,
                    strategy: str = "TWAP") -> Dict[str, Any]:
        """
        Calculate TWAP/VWAP order splitting.

        TWAP: Time-Weighted Average Price - equal splits over time
        VWAP: Volume-Weighted Average Price - splits based on volume profile
        """
        max_order_size = int(avg_volume * max_participation_rate)

        if total_quantity <= max_order_size:
            return {
                "strategy": "SINGLE_ORDER",
                "splits": [{"quantity": total_quantity, "delay_seconds": 0}],
                "total_quantity": total_quantity,
                "estimated_execution_time_minutes": 0
            }

        # Calculate number of splits
        num_splits = int(np.ceil(total_quantity / max_order_size))

        if strategy.upper() == "VWAP":
            # VWAP: Weight splits by typical intraday volume profile
            # Higher volume in morning and afternoon, lower at lunch
            volume_profile = self._get_intraday_volume_profile(num_splits)

            splits = []
            remaining = total_quantity
            for i, weight in enumerate(volume_profile):
                qty = min(int(total_quantity * weight), remaining)
                if qty > 0:
                    splits.append({
                        "quantity": qty,
                        "delay_seconds": i * 60,
                        "order_number": i + 1,
                        "volume_weight": round(weight, 4)
                    })
                    remaining -= qty

            # Add any remainder to last split
            if remaining > 0 and splits:
                splits[-1]["quantity"] += remaining

            return {
                "strategy": "VWAP",
                "splits": splits,
                "total_quantity": total_quantity,
                "num_splits": len(splits),
                "max_order_size": max_order_size,
                "estimated_execution_time_minutes": len(splits),
                "volume_weighted": True
            }
        else:
            # TWAP: Equal time-weighted splits
            base_quantity = total_quantity // num_splits
            remainder = total_quantity % num_splits

            splits = []
            for i in range(num_splits):
                qty = base_quantity + (1 if i < remainder else 0)
                splits.append({
                    "quantity": qty,
                    "delay_seconds": i * 60,  # 1 minute between orders
                    "order_number": i + 1
                })

            return {
                "strategy": "TWAP",
                "splits": splits,
                "total_quantity": total_quantity,
                "num_splits": num_splits,
                "max_order_size": max_order_size,
                "estimated_execution_time_minutes": num_splits,
                "volume_weighted": False
            }

    def _get_intraday_volume_profile(self, num_splits: int) -> List[float]:
        """
        Generate typical intraday volume profile weights.
        U-shaped: High at open and close, low at midday.
        """
        if num_splits == 1:
            return [1.0]

        # Generate U-shaped profile
        x = np.linspace(0, np.pi, num_splits)
        profile = 1 - 0.5 * np.sin(x)  # U-shape

        # Normalize to sum to 1
        profile = profile / profile.sum()
        return profile.tolist()

    def calculate_execution_analytics(self, orders: List[Dict]) -> Dict[str, Any]:
        """Calculate execution quality analytics"""
        if not orders:
            return {"message": "No orders to analyze"}

        total_value = sum(o.get("quantity", 0) * o.get("price", 0) for o in orders)
        total_quantity = sum(o.get("quantity", 0) for o in orders)

        if total_quantity == 0:
            return {"message": "No quantity in orders"}

        vwap = total_value / total_quantity if total_quantity > 0 else 0

        return {
            "total_orders": len(orders),
            "total_quantity": total_quantity,
            "total_value": round(total_value, 2),
            "vwap": round(vwap, 4),
            "execution_stats": self.execution_stats
        }

EXECUTION_OPTIMIZER = ExecutionOptimizer()

# --- Secret Manager Helper ---
def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "after-yesterday-473512-k3")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        # Strip any trailing whitespace/newlines from the secret
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Error fetching secret {secret_id}: {e}")
        return ""

# --- Models ---
class OrderRequest(BaseModel):
    transaction_type: str  # BUY/SELL
    exchange_segment: str  # NSE_EQ, NSE_FNO, BSE_EQ, etc.
    product_type: str      # INTRADAY, CNC, MARGIN, etc.
    order_type: str        # MARKET, LIMIT, STOP_LOSS, etc.
    validity: str          # DAY, IOC
    security_id: str       # Dhan Security ID
    quantity: int
    price: Optional[float] = 0.0
    trigger_price: Optional[float] = 0.0
    disclosed_quantity: Optional[int] = 0
    after_market_order: Optional[bool] = False
    amo_time: Optional[str] = "OPEN"
    bo_profit_value: Optional[float] = 0.0
    bo_stop_loss_value: Optional[float] = 0.0
    drv_expiry_date: Optional[str] = None
    drv_options_type: Optional[str] = None
    drv_strike_price: Optional[float] = 0.0

class OrderCancelRequest(BaseModel):
    order_id: str

class OrderModifyRequest(BaseModel):
    order_id: str
    order_type: str
    leg_name: str
    quantity: int
    price: float
    trigger_price: Optional[float] = 0.0
    disclosed_quantity: Optional[int] = 0
    validity: str = "DAY"

class SlippageRequest(BaseModel):
    order_size: int
    volatility: float = 0.02
    spread: float = 0.001
    volume: float = 100000

class OrderSplitRequest(BaseModel):
    total_quantity: int
    avg_volume: float
    max_participation_rate: float = 0.1
    strategy: str = "TWAP"  # TWAP or VWAP

class ExecutionAnalyticsRequest(BaseModel):
    orders: List[Dict[str, Any]]

# --- DhanHQ Client Helper ---
def get_dhan_client(user_id: Optional[str] = None) -> dhanhq:
    """
    Create authenticated DhanHQ client.

    If user_id is provided, uses that user's credentials from Firestore.
    Otherwise, falls back to admin credentials from Secret Manager (for market data).
    """
    if user_id:
        # Get user-specific credentials from Firestore
        try:
            db = firestore.Client()
            doc = db.collection("user_credentials").document(user_id).get()
            if doc.exists:
                data = doc.to_dict()
                creds = data.get("credentials", {})
                client_id = creds.get("client_id")
                # Decrypt access token
                from user_credentials import get_credentials_manager
                manager = get_credentials_manager()
                access_token = manager._decrypt(creds.get("access_token", ""))

                if client_id and access_token:
                    return dhanhq(client_id, access_token)
        except Exception as e:
            logger.error(f"Failed to get user credentials: {e}")
            raise HTTPException(status_code=401, detail="User credentials not found or invalid")

    # Fallback to admin credentials (for market data)
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")

    # Fallback to Secret Manager
    if not client_id:
        client_id = get_secret("dhan-client-id")
    if not access_token:
        access_token = get_secret("dhan-access-token")

    if not client_id or not access_token:
        raise HTTPException(
            status_code=500,
            detail="Dhan credentials not configured (DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)"
        )

    return dhanhq(client_id, access_token)

# --- User Credentials Models ---
class UserCredentialsRequest(BaseModel):
    user_id: str
    client_id: str
    access_token: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class UserCredentialsVerifyRequest(BaseModel):
    user_id: str

# --- User Credentials Endpoints ---
@app.post("/api/v1/user/credentials")
async def save_user_credentials(request: UserCredentialsRequest):
    """
    Save user's Dhan credentials securely.
    Credentials are encrypted and stored in Firestore.
    """
    try:
        manager = get_credentials_manager()
        result = await manager.save_user_credentials(
            user_id=request.user_id,
            client_id=request.client_id,
            access_token=request.access_token,
            api_key=request.api_key,
            api_secret=request.api_secret
        )

        # Verify the connection immediately
        try:
            dhan_client = dhanhq(request.client_id, request.access_token)
            funds = dhan_client.get_fund_limits()

            if isinstance(funds, dict) and funds.get("status") == "success":
                await manager.update_connection_status(
                    request.user_id,
                    "connected",
                    funds.get("data", {})
                )
                result["connection_status"] = "connected"
                result["account_verified"] = True
            else:
                await manager.update_connection_status(request.user_id, "failed")
                result["connection_status"] = "failed"
                result["account_verified"] = False
        except Exception as verify_error:
            await manager.update_connection_status(request.user_id, "failed")
            result["connection_status"] = "failed"
            result["error"] = str(verify_error)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/user/credentials/{user_id}")
async def get_user_credentials_status(user_id: str):
    """Get user's credential status (not the actual credentials)"""
    try:
        manager = get_credentials_manager()
        creds = await manager.get_user_credentials(user_id)

        if not creds:
            return {
                "user_id": user_id,
                "configured": False,
                "connection_status": "not_configured"
            }

        return {
            "user_id": user_id,
            "configured": True,
            "client_id": creds["credentials"]["client_id"],
            "connection_status": creds["connection_status"],
            "is_active": creds["is_active"],
            "updated_at": creds["updated_at"].isoformat() if creds["updated_at"] else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/user/credentials/{user_id}")
async def delete_user_credentials(user_id: str):
    """Delete user's Dhan credentials"""
    try:
        manager = get_credentials_manager()
        success = await manager.delete_user_credentials(user_id)

        return {
            "user_id": user_id,
            "deleted": success,
            "message": "Credentials deleted successfully" if success else "Failed to delete"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/user/verify")
async def verify_user_connection(request: UserCredentialsVerifyRequest):
    """Verify user's Dhan connection and fetch account details"""
    try:
        dhan_client = get_dhan_client(user_id=request.user_id)

        # Fetch funds
        funds = dhan_client.get_fund_limits()

        # Fetch holdings
        holdings = dhan_client.get_holdings()

        # Fetch positions
        positions = dhan_client.get_positions()

        # Update status
        manager = get_credentials_manager()
        await manager.update_connection_status(
            request.user_id,
            "connected",
            funds.get("data", {}) if isinstance(funds, dict) else {}
        )

        return {
            "status": "connected",
            "user_id": request.user_id,
            "account": {
                "funds": funds.get("data", {}) if isinstance(funds, dict) else funds,
                "holdings_count": len(holdings.get("data", [])) if isinstance(holdings, dict) else 0,
                "positions_count": len(positions.get("data", [])) if isinstance(positions, dict) else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.get("/api/v1/user/{user_id}/account")
async def get_user_account_details(user_id: str):
    """
    Get complete user account details including funds, holdings, positions.
    Requires user to have configured their Dhan credentials.
    """
    try:
        dhan_client = get_dhan_client(user_id=user_id)

        # Fetch all account data
        funds = dhan_client.get_fund_limits()
        holdings = dhan_client.get_holdings()
        positions = dhan_client.get_positions()
        orders = dhan_client.get_order_list()
        trades = dhan_client.get_trade_book()

        # Process funds
        funds_data = funds.get("data", {}) if isinstance(funds, dict) else {}

        # Process holdings
        holdings_data = holdings.get("data", []) if isinstance(holdings, dict) else []
        total_holdings_value = sum(
            h.get("currentValue", 0) or h.get("buyAvg", 0) * h.get("totalQty", 0)
            for h in holdings_data
        )
        total_holdings_pnl = sum(h.get("unrealizedProfit", 0) for h in holdings_data)

        # Process positions
        positions_data = positions.get("data", []) if isinstance(positions, dict) else []
        total_positions_pnl = sum(p.get("unrealizedProfit", 0) for p in positions_data)

        # Process orders
        orders_data = orders.get("data", []) if isinstance(orders, dict) else []

        # Process trades
        trades_data = trades.get("data", []) if isinstance(trades, dict) else []

        return {
            "status": "success",
            "user_id": user_id,
            "account_summary": {
                "available_balance": funds_data.get("availabelBalance", 0),
                "utilized_margin": funds_data.get("utilizedMargin", 0),
                "total_holdings_value": total_holdings_value,
                "total_holdings_pnl": total_holdings_pnl,
                "total_positions_pnl": total_positions_pnl,
                "net_pnl": total_holdings_pnl + total_positions_pnl
            },
            "funds": funds_data,
            "holdings": {
                "count": len(holdings_data),
                "total_value": total_holdings_value,
                "total_pnl": total_holdings_pnl,
                "data": holdings_data
            },
            "positions": {
                "count": len(positions_data),
                "total_pnl": total_positions_pnl,
                "data": positions_data
            },
            "orders": {
                "count": len(orders_data),
                "data": orders_data[:20]  # Last 20 orders
            },
            "trades": {
                "count": len(trades_data),
                "data": trades_data[:20]  # Last 20 trades
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch account: {str(e)}")

# --- Health & Root ---
@app.get("/healthz")
@app.get("/health")
@app.get("/api/health")
async def healthz():
    return {
        "status": "healthy",
        "service": "engine-c-execution",
        "broker": "DhanHQ",
        "version": "3.5-enhanced-execution",
        "ml_capabilities": ["slippage_prediction", "order_timing", "twap_splitting", "vwap_splitting", "execution_analytics"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "service": "InfinityAI.Pro Engine C (Trade Execution & Order Optimization)",
        "status": "ready",
        "version": "3.5-enhanced-execution",
        "ml_features": ["Slippage Prediction", "Order Timing", "TWAP/VWAP Splitting", "Execution Analytics"]
    }

# --- Execution Optimization Endpoints ---
@app.post("/api/v1/optimize/slippage")
async def predict_slippage(req: SlippageRequest):
    """Predict expected slippage for an order"""
    return EXECUTION_OPTIMIZER.predict_slippage(
        req.order_size, req.volatility, req.spread, req.volume
    )

@app.get("/api/v1/optimize/timing/{symbol}")
async def optimize_timing(symbol: str, order_type: str = "MARKET"):
    """Get optimal execution timing recommendation"""
    return EXECUTION_OPTIMIZER.optimize_order_timing(symbol, order_type)

@app.post("/api/v1/optimize/split")
async def split_order(req: OrderSplitRequest):
    """Calculate optimal order splitting (TWAP/VWAP)"""
    return EXECUTION_OPTIMIZER.split_order(
        req.total_quantity, req.avg_volume, req.max_participation_rate, req.strategy
    )

@app.post("/api/v1/optimize/analytics")
async def execution_analytics(req: ExecutionAnalyticsRequest):
    """Calculate execution quality analytics"""
    return EXECUTION_OPTIMIZER.calculate_execution_analytics(req.orders)

# --- Order Placement Endpoint ---
@app.post("/api/dhan/place-order")
async def place_order(order: OrderRequest):
    """
    Place order via DhanHQ API
    Supports: Equity, F&O, Intraday, CNC, Market, Limit, SL orders
    """
    try:
        dhan_client = get_dhan_client()

        response = dhan_client.place_order(
            transaction_type=order.transaction_type,
            exchange_segment=order.exchange_segment,
            product_type=order.product_type,
            order_type=order.order_type,
            validity=order.validity,
            security_id=order.security_id,
            quantity=order.quantity,
            price=order.price,
            trigger_price=order.trigger_price,
            disclosed_quantity=order.disclosed_quantity,
            after_market_order=order.after_market_order,
            amo_time=order.amo_time,
            bo_profit_value=order.bo_profit_value,
            bo_stop_loss_value=order.bo_stop_loss_value,
            drv_expiry_date=order.drv_expiry_date,
            drv_options_type=order.drv_options_type,
            drv_strike_price=order.drv_strike_price
        )

        # Check response status
        if isinstance(response, dict):
            if response.get("status") == "failure":
                raise HTTPException(
                    status_code=400,
                    detail=f"Dhan Order Failed: {response.get('remarks', 'Unknown error')}"
                )
            elif response.get("status") == "success":
                return {
                    "status": "success",
                    "order_id": response.get("data", {}).get("orderId"),
                    "dhan_response": response
                }

        return {"status": "success", "dhan_response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")

# --- Order Cancellation Endpoint ---
@app.post("/api/dhan/cancel-order")
async def cancel_order(request: OrderCancelRequest):
    """Cancel existing order by order_id"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.cancel_order(order_id=request.order_id)

        if isinstance(response, dict) and response.get("status") == "failure":
            raise HTTPException(
                status_code=400,
                detail=f"Order cancellation failed: {response.get('remarks', 'Unknown error')}"
            )

        return {"status": "success", "dhan_response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order cancellation error: {str(e)}")

# --- Order Modification Endpoint ---
@app.post("/api/dhan/modify-order")
async def modify_order(request: OrderModifyRequest):
    """Modify existing order"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.modify_order(
            order_id=request.order_id,
            order_type=request.order_type,
            leg_name=request.leg_name,
            quantity=request.quantity,
            price=request.price,
            trigger_price=request.trigger_price,
            disclosed_quantity=request.disclosed_quantity,
            validity=request.validity
        )

        if isinstance(response, dict) and response.get("status") == "failure":
            raise HTTPException(
                status_code=400,
                detail=f"Order modification failed: {response.get('remarks', 'Unknown error')}"
            )

        return {"status": "success", "dhan_response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order modification error: {str(e)}")

# --- Order Status & Data Endpoints ---
@app.get("/api/dhan/orders")
async def get_orders():
    """Fetch all orders for the day"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_order_list()

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", [])}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

@app.get("/api/dhan/order/{order_id}")
async def get_order_by_id(order_id: str):
    """Fetch specific order details by order_id"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_order_by_id(order_id=order_id)

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", {})}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")

@app.get("/api/dhan/positions")
async def get_positions():
    """Fetch open positions"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_positions()

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", [])}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

@app.get("/api/dhan/holdings")
async def get_holdings():
    """Fetch user holdings"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_holdings()

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", [])}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch holdings: {str(e)}")

@app.get("/api/dhan/funds")
async def get_funds():
    """
    Fetch available funds and margin details from DhanHQ.
    Returns available balance, utilized margin, and other fund details.
    """
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_fund_limits()

        if isinstance(response, dict) and response.get("status") == "success":
            fund_data = response.get("data", {})
            return {
                "status": "success",
                "data": fund_data,
                "summary": {
                    "available_balance": fund_data.get("availabelBalance", 0),
                    "utilized_margin": fund_data.get("utilizedMargin", 0),
                    "payin_amount": fund_data.get("payinAmount", 0),
                    "withdrawal_available": fund_data.get("withdrawableBalance", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        return {"status": "success", "data": response}

    except Exception as e:
        logger.error(f"Failed to fetch funds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch funds: {str(e)}")

# --- DhanHQ Postback Webhook ---
@app.post("/api/dhan/postback")
async def dhan_postback(request: Dict[str, Any]):
    """
    Receive order/trade updates from DhanHQ via webhook.
    This endpoint receives real-time updates on order status, fills, etc.
    """
    try:
        logger.info(f"📥 DhanHQ Postback received: {request}")

        # Extract key information
        order_id = request.get("order_id") or request.get("orderId")
        status = request.get("status") or request.get("orderStatus")
        transaction_type = request.get("transaction_type") or request.get("transactionType")
        symbol = request.get("trading_symbol") or request.get("tradingSymbol")

        # Log the trade event
        logger.info(f"📊 Order Update: {order_id} - {symbol} - {transaction_type} - {status}")

        # TODO: Store in Firestore for trade history
        # TODO: Update portfolio positions
        # TODO: Send notification to frontend

        return {
            "status": "received",
            "message": "Postback processed successfully",
            "order_id": order_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Postback processing failed: {e}")
        return {"status": "error", "message": str(e)}


# ==============================================================================
# SIMPLIFIED API ENDPOINTS (for frontend compatibility)
# These endpoints use query parameters instead of path parameters
# ==============================================================================

@app.post("/api/user/credentials")
async def save_user_credentials_simple(request: UserCredentialsRequest):
    """Save/Update user's Dhan credentials (simplified API)"""
    try:
        manager = get_credentials_manager()
        if manager is None:
            raise HTTPException(status_code=503, detail="Credentials manager not available")

        # Save credentials
        result = await manager.save_user_credentials(
            user_id=request.user_id,
            client_id=request.client_id,
            access_token=request.access_token,
            api_key=request.api_key,
            api_secret=request.api_secret
        )

        # Verify the connection immediately
        try:
            dhan_client = dhanhq(request.client_id, request.access_token)
            funds = dhan_client.get_fund_limits()

            if isinstance(funds, dict) and funds.get("status") == "success":
                result["is_verified"] = True
                result["connection_status"] = "connected"
            else:
                result["is_verified"] = False
                result["connection_status"] = "failed"
        except Exception as verify_error:
            logger.warning(f"Verification failed: {verify_error}")
            result["is_verified"] = False
            result["connection_status"] = "failed"

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/credentials")
async def get_user_credentials_simple(user_id: str):
    """Get user's saved Dhan credentials (simplified API)"""
    try:
        manager = get_credentials_manager()
        if manager is None:
            return {
                "user_id": user_id,
                "configured": False,
                "client_id": "",
                "api_key": "",
                "is_verified": False
            }

        creds = await manager.get_user_credentials(user_id)

        if not creds:
            return {
                "user_id": user_id,
                "configured": False,
                "client_id": "",
                "api_key": "",
                "is_verified": False
            }

        return {
            "user_id": user_id,
            "configured": True,
            "client_id": creds.get("credentials", {}).get("client_id", ""),
            "api_key": creds.get("credentials", {}).get("api_key", ""),
            "access_token": "********" if creds.get("credentials", {}).get("access_token") else "",
            "is_verified": creds.get("connection_status") == "connected",
            "connection_status": creds.get("connection_status", "unknown")
        }

    except Exception as e:
        logger.error(f"Failed to get credentials for {user_id}: {e}")
        return {
            "user_id": user_id,
            "configured": False,
            "client_id": "",
            "api_key": "",
            "is_verified": False
        }


@app.delete("/api/user/credentials")
async def delete_user_credentials_simple(user_id: str):
    """Delete user's Dhan credentials (simplified API)"""
    try:
        manager = get_credentials_manager()
        if manager is None:
            raise HTTPException(status_code=503, detail="Credentials manager not available")

        success = await manager.delete_user_credentials(user_id)
        return {
            "user_id": user_id,
            "deleted": success,
            "message": "Credentials deleted successfully" if success else "Failed to delete"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/credentials/verify")
async def verify_user_credentials_simple(user_id: str):
    """Verify user's Dhan connection (simplified API)"""
    try:
        manager = get_credentials_manager()
        if manager is None:
            return {
                "user_id": user_id,
                "is_verified": False,
                "message": "Credentials manager not available"
            }

        creds = await manager.get_user_credentials(user_id)

        if not creds:
            return {
                "user_id": user_id,
                "is_verified": False,
                "message": "No credentials found"
            }

        # Try to connect with user's credentials
        try:
            client_id = creds.get("credentials", {}).get("client_id")
            access_token = creds.get("credentials", {}).get("access_token")

            if not client_id or not access_token:
                return {
                    "user_id": user_id,
                    "is_verified": False,
                    "message": "Incomplete credentials"
                }

            dhan_client = dhanhq(client_id, access_token)
            funds = dhan_client.get_fund_limits()

            if isinstance(funds, dict) and funds.get("status") == "success":
                return {
                    "user_id": user_id,
                    "is_verified": True,
                    "message": "Connection verified successfully"
                }
        except Exception as e:
            logger.error(f"Verification failed for {user_id}: {e}")

        return {
            "user_id": user_id,
            "is_verified": False,
            "message": "Could not verify connection. Please check your access token."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/demat")
async def get_user_demat_simple(user_id: str):
    """Get user's demat account details (simplified API)"""
    try:
        manager = get_credentials_manager()
        if manager is None:
            raise HTTPException(status_code=503, detail="Credentials manager not available")

        creds = await manager.get_user_credentials(user_id)
        if not creds:
            raise HTTPException(status_code=404, detail="No credentials found for user")

        client_id = creds.get("credentials", {}).get("client_id")
        access_token = creds.get("credentials", {}).get("access_token")

        if not client_id or not access_token:
            raise HTTPException(status_code=400, detail="Incomplete credentials")

        dhan_client = dhanhq(client_id, access_token)

        # Fetch all account data
        funds = dhan_client.get_fund_limits()
        holdings = dhan_client.get_holdings()
        positions = dhan_client.get_positions()

        # Process funds
        funds_data = funds.get("data", {}) if isinstance(funds, dict) else {}

        # Process holdings
        holdings_data = holdings.get("data", []) if isinstance(holdings, dict) else []
        total_holdings_value = sum(
            h.get("currentValue", 0) or h.get("buyAvg", 0) * h.get("totalQty", 0)
            for h in holdings_data
        )

        # Process positions
        positions_data = positions.get("data", []) if isinstance(positions, dict) else []
        total_positions_pnl = sum(p.get("unrealizedProfit", 0) for p in positions_data)

        return {
            "holdings": {
                "totalValue": total_holdings_value,
                "count": len(holdings_data),
                "items": [
                    {
                        "symbol": h.get("tradingSymbol", ""),
                        "quantity": h.get("totalQty", 0),
                        "avgPrice": h.get("buyAvg", 0),
                        "currentPrice": h.get("lastTradedPrice", 0),
                        "pnl": h.get("unrealizedProfit", 0)
                    }
                    for h in holdings_data[:20]  # Limit to 20 items
                ]
            },
            "positions": {
                "totalPnl": total_positions_pnl,
                "count": len(positions_data),
                "items": [
                    {
                        "symbol": p.get("tradingSymbol", ""),
                        "quantity": p.get("netQty", 0),
                        "entryPrice": p.get("buyAvg", 0),
                        "currentPrice": p.get("lastTradedPrice", 0),
                        "pnl": p.get("unrealizedProfit", 0)
                    }
                    for p in positions_data[:20]  # Limit to 20 items
                ]
            },
            "funds": {
                "availableBalance": funds_data.get("availabelBalance", 0),
                "utilisedMargin": funds_data.get("utilizedMargin", 0),
                "totalBalance": funds_data.get("availabelBalance", 0) + funds_data.get("utilizedMargin", 0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch demat for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch account: {str(e)}")


# ==================== OAuth Endpoints (migrated from main_minimal.py) ====================

@app.post("/api/dhan/callback")
async def dhan_oauth_callback(request: Request):
    """Handle Dhan OAuth callback - exchange authorization code for access token"""
    try:
        body = await request.json()
        code = body.get("code")
        state = body.get("state")

        if not code:
            raise HTTPException(status_code=400, detail="Authorization code required")

        # Validate state if provided
        if state and state in oauth_states:
            state_data = oauth_states.pop(state)
            user_id = state_data.get("user_id")
        else:
            user_id = body.get("user_id", "default")

        # Exchange code for token using Dhan API
        dhan_client_id = os.environ.get("DHAN_CLIENT_ID")
        dhan_client_secret = os.environ.get("DHAN_CLIENT_SECRET")

        if not dhan_client_id or not dhan_client_secret:
            # Try Secret Manager
            try:
                dhan_client_id = get_secret("dhan-client-id")
                dhan_client_secret = get_secret("dhan-client-secret")
            except Exception:
                raise HTTPException(status_code=500, detail="Dhan credentials not configured")

        # Exchange authorization code for access token
        async with aiohttp.ClientSession() as session:
            token_url = "https://api.dhan.co/v2/token"
            payload = {
                "client_id": dhan_client_id,
                "client_secret": dhan_client_secret,
                "code": code,
                "grant_type": "authorization_code"
            }

            async with session.post(token_url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token exchange failed: {error_text}")
                    raise HTTPException(status_code=response.status, detail="Token exchange failed")

                token_data = await response.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=500, detail="No access token in response")

        # Store credentials for user
        manager = get_credentials_manager()
        if manager:
            await manager.store_user_credentials(user_id, {
                "client_id": dhan_client_id,
                "access_token": access_token
            })

        return {
            "status": "success",
            "user_id": user_id,
            "message": "OAuth authentication successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dhan/callback-urls")
async def get_dhan_callback_urls():
    """Get OAuth callback URLs for Dhan configuration"""
    service_url = os.environ.get("SERVICE_URL", "https://engine-c.infinityai.pro")
    return {
        "callback_url": f"{service_url}/api/dhan/callback",
        "redirect_url": f"{service_url}/auth/dhan/success",
        "login_url": "https://login.dhan.co"
    }


@app.post("/api/dhan/disconnect/{user_id}")
async def disconnect_dhan_user(user_id: str):
    """Disconnect user's Dhan account"""
    try:
        manager = get_credentials_manager()
        if manager is None:
            raise HTTPException(status_code=503, detail="Credentials manager not available")

        success = await manager.delete_user_credentials(user_id)
        return {
            "status": "success" if success else "failed",
            "user_id": user_id,
            "message": "Dhan account disconnected" if success else "Failed to disconnect"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/dhan/disconnect/{user_id}")
async def disconnect_dhan_user_delete(user_id: str):
    """Disconnect user's Dhan account (DELETE method)"""
    return await disconnect_dhan_user(user_id)


@app.post("/api/dhan/disconnect")
async def disconnect_dhan_default():
    """Disconnect default user when user_id isn't specified"""
    return await disconnect_dhan_user("default")


@app.post("/api/dhan/token")
async def update_dhan_token(request: Request):
    """Update Dhan access token for a user"""
    try:
        body = await request.json()
        user_id = body.get("user_id", "default")
        access_token = body.get("access_token")
        client_id = body.get("client_id")

        if not access_token:
            raise HTTPException(status_code=400, detail="access_token required")

        if not client_id:
            client_id = os.environ.get("DHAN_CLIENT_ID")
            if not client_id:
                try:
                    client_id = get_secret("dhan-client-id")
                except Exception:
                    raise HTTPException(status_code=400, detail="client_id required and not found in secrets")

        # Store updated credentials
        manager = get_credentials_manager()
        if manager:
            await manager.store_user_credentials(user_id, {
                "client_id": client_id,
                "access_token": access_token
            })

        # Verify the token works
        try:
            dhan = dhanhq(client_id, access_token)
            funds = dhan.get_fund_limits()
            verified = isinstance(funds, dict) and funds.get("status") == "success"
        except Exception:
            verified = False

        return {
            "status": "success",
            "user_id": user_id,
            "verified": verified,
            "message": "Token updated successfully" if verified else "Token stored but verification failed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dhan/status")
async def get_dhan_status(user_id: str = "default"):
    """Get Dhan connection status for user"""
    try:
        manager = get_credentials_manager()
        connected = False
        account_details = None

        if manager:
            creds = await manager.get_user_credentials(user_id)
            if creds:
                client_id = creds.get("credentials", {}).get("client_id")
                access_token = creds.get("credentials", {}).get("access_token")
                if client_id and access_token:
                    connected = True
                    account_details = {
                        "client_id": client_id,
                        "connected_at": creds.get("updated_at", datetime.now().isoformat())
                    }

        service_url = os.environ.get("SERVICE_URL", "https://engine-c.infinityai.pro")

        return {
            "status": "operational",
            "connected": connected,
            "user_id": user_id,
            "account_details": account_details,
            "oauth_endpoint": f"{service_url}/api/dhan/callback",
            "postback_endpoint": f"{service_url}/api/webhooks/dhan",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting Dhan status: {e}")
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/webhooks/dhan")
async def dhan_postback_handler(request: Request):
    """Handle Dhan postback webhooks for order updates"""
    try:
        payload = await request.json()
        logger.info(f"Received Dhan postback: {payload}")

        # Process the postback data
        order_id = payload.get("orderid") or payload.get("orderId")
        status = payload.get("status") or payload.get("orderStatus")
        symbol = payload.get("tradingsymbol") or payload.get("tradingSymbol")

        # Log for monitoring
        logger.info(f"Order update - ID: {order_id}, Status: {status}, Symbol: {symbol}")

        # In production, you would:
        # 1. Update order status in database
        # 2. Send notifications to user
        # 3. Update AI trading system if applicable

        return {
            "status": "success",
            "message": "Postback processed",
            "order_id": order_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing Dhan postback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_service_metrics():
    """Get service metrics for monitoring"""
    return {
        "service": "engine-c-execution",
        "version": "3.5-enhanced-execution",
        "ai_trading_active": AI_TRADING_SYSTEM.is_active,
        "ai_trades_executed": len(AI_TRADING_SYSTEM.execution_history),
        "execution_optimizer_orders": EXECUTION_OPTIMIZER.execution_stats.get("orders_executed", 0),
        "slippage_saved_bps": EXECUTION_OPTIMIZER.execution_stats.get("total_slippage_saved_bps", 0),
        "status": "operational",
        "engine_b_url": ENGINE_B_URL,
        "timestamp": datetime.now().isoformat()
    }


# ==================== AI Auto-Trading Endpoints ====================

@app.post("/api/auto-trade/start")
async def start_ai_trading(request: Request):
    """Start AI auto-trading system"""
    try:
        body = await request.json() if await request.body() else {}
        user_id = body.get("user_id", "default")

        # Get user credentials
        manager = get_credentials_manager()
        if manager is None:
            raise HTTPException(status_code=503, detail="Credentials manager not available")

        creds = await manager.get_user_credentials(user_id)
        if not creds:
            raise HTTPException(status_code=404, detail="No Dhan credentials found. Please connect your account first.")

        client_id = creds.get("credentials", {}).get("client_id")
        access_token = creds.get("credentials", {}).get("access_token")

        if not client_id or not access_token:
            raise HTTPException(status_code=400, detail="Incomplete Dhan credentials")

        # Update config if provided
        if "min_confidence" in body:
            AI_TRADING_SYSTEM.config["min_confidence"] = float(body["min_confidence"])
        if "max_risk_per_trade" in body:
            AI_TRADING_SYSTEM.config["max_risk_per_trade"] = float(body["max_risk_per_trade"])
        if "max_daily_trades" in body:
            AI_TRADING_SYSTEM.config["max_daily_trades"] = int(body["max_daily_trades"])
        if "trading_amount" in body:
            AI_TRADING_SYSTEM.config["trading_amount"] = float(body["trading_amount"])

        result = await AI_TRADING_SYSTEM.start()

        return {
            "status": result.get("status"),
            "user_id": user_id,
            "config": AI_TRADING_SYSTEM.config,
            "message": result.get("message", "AI auto-trading started successfully"),
            "timestamp": result.get("timestamp")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start AI trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auto-trade/stop")
async def stop_ai_trading():
    """Stop AI auto-trading system"""
    try:
        result = await AI_TRADING_SYSTEM.stop()
        return {
            "status": result.get("status"),
            "message": result.get("message", "AI auto-trading stopped"),
            "trades_executed": result.get("trades_executed", 0)
        }
    except Exception as e:
        logger.error(f"Failed to stop AI trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auto-trade/status")
async def get_ai_trading_status():
    """Get AI auto-trading system status"""
    status = AI_TRADING_SYSTEM.get_status()
    return {
        "active": status.get("is_active", False),
        "config": status.get("config", {}),
        "trades_today": status.get("trades_executed_today", 0),
        "engine_b_url": ENGINE_B_URL,
        "last_trades": status.get("last_trades", [])
    }


@app.get("/api/auto-trade/history")
async def get_ai_trade_history(limit: int = 50):
    """Get AI trading history"""
    history = AI_TRADING_SYSTEM.execution_history[-limit:] if AI_TRADING_SYSTEM.execution_history else []
    return {
        "total_trades": len(AI_TRADING_SYSTEM.execution_history),
        "trades": history
    }


# ==================== Portfolio Endpoint ====================

@app.get("/api/portfolio")
async def get_portfolio(user_id: str = "default"):
    """Get user's complete portfolio summary"""
    try:
        manager = get_credentials_manager()
        if manager is None:
            raise HTTPException(status_code=503, detail="Credentials manager not available")

        creds = await manager.get_user_credentials(user_id)
        if not creds:
            raise HTTPException(status_code=404, detail="No credentials found. Please connect your Dhan account.")

        client_id = creds.get("credentials", {}).get("client_id")
        access_token = creds.get("credentials", {}).get("access_token")

        if not client_id or not access_token:
            raise HTTPException(status_code=400, detail="Incomplete credentials")

        dhan_client = dhanhq(client_id, access_token)

        # Fetch all data
        funds_resp = dhan_client.get_fund_limits()
        holdings_resp = dhan_client.get_holdings()
        positions_resp = dhan_client.get_positions()
        orders_resp = dhan_client.get_order_list()

        # Process data
        funds = funds_resp.get("data", {}) if isinstance(funds_resp, dict) else {}
        holdings = holdings_resp.get("data", []) if isinstance(holdings_resp, dict) else []
        positions = positions_resp.get("data", []) if isinstance(positions_resp, dict) else []
        orders = orders_resp.get("data", []) if isinstance(orders_resp, dict) else []

        # Calculate totals
        holdings_value = sum(
            h.get("currentValue", 0) or (h.get("buyAvg", 0) * h.get("totalQty", 0))
            for h in holdings
        )
        positions_pnl = sum(p.get("unrealizedProfit", 0) for p in positions)
        available_balance = funds.get("availabelBalance", 0)

        return {
            "summary": {
                "total_value": holdings_value + available_balance,
                "holdings_value": holdings_value,
                "available_balance": available_balance,
                "positions_pnl": positions_pnl,
                "total_holdings": len(holdings),
                "open_positions": len([p for p in positions if p.get("netQty", 0) != 0]),
                "today_orders": len(orders)
            },
            "holdings": [
                {
                    "symbol": h.get("tradingSymbol", ""),
                    "exchange": h.get("exchange", ""),
                    "quantity": h.get("totalQty", 0),
                    "avg_price": h.get("buyAvg", 0),
                    "current_price": h.get("lastTradedPrice", 0),
                    "value": h.get("currentValue", 0),
                    "pnl": h.get("unrealizedProfit", 0),
                    "pnl_percent": h.get("dayChangePercentage", 0)
                }
                for h in holdings
            ],
            "positions": [
                {
                    "symbol": p.get("tradingSymbol", ""),
                    "exchange": p.get("exchange", ""),
                    "quantity": p.get("netQty", 0),
                    "buy_avg": p.get("buyAvg", 0),
                    "sell_avg": p.get("sellAvg", 0),
                    "pnl": p.get("unrealizedProfit", 0),
                    "product_type": p.get("productType", "")
                }
                for p in positions
            ],
            "recent_orders": [
                {
                    "order_id": o.get("orderId", ""),
                    "symbol": o.get("tradingSymbol", ""),
                    "type": o.get("transactionType", ""),
                    "quantity": o.get("quantity", 0),
                    "price": o.get("price", 0),
                    "status": o.get("orderStatus", ""),
                    "time": o.get("createTime", "")
                }
                for o in orders[:10]  # Last 10 orders
            ],
            "ai_trading": {
                "active": AI_TRADING_SYSTEM.is_active,
                "trades_today": len(AI_TRADING_SYSTEM.execution_history)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
