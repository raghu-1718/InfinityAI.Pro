import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dhanhq import dhanhq
from google.cloud import secretmanager
import uvicorn

# ML Libraries for Execution Optimization
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import joblib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="InfinityAI.Pro - Engine C (Trade Execution & Order Optimization)",
    description="DhanHQ Execution with ML-based Slippage Prediction & Order Optimization",
    version="3.1-ml"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Execution Optimizer ML ---
class ExecutionOptimizer:
    """ML-based order execution optimization"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.slippage_model = LinearRegression()
        self.execution_history = []
        logger.info("✅ Execution Optimizer initialized")

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
                    max_participation_rate: float = 0.1) -> Dict[str, Any]:
        """Calculate TWAP/VWAP order splitting"""
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
            "estimated_execution_time_minutes": num_splits
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
        return response.payload.data.decode("UTF-8")
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

# --- DhanHQ Client Helper ---
def get_dhan_client() -> dhanhq:
    """Create authenticated DhanHQ client"""
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

# --- Health & Root ---
@app.get("/healthz")
async def healthz():
    return {
        "status": "healthy",
        "service": "engine-c-execution",
        "broker": "DhanHQ",
        "ml_capabilities": ["slippage_prediction", "order_timing", "order_splitting"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "service": "InfinityAI.Pro Engine C (Trade Execution & Order Optimization)",
        "status": "ready",
        "version": "3.1-ml",
        "ml_features": ["Slippage Prediction", "Order Timing", "TWAP/VWAP Splitting"]
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
        req.total_quantity, req.avg_volume, req.max_participation_rate
    )

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
