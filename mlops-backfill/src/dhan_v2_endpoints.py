"""
DhanHQ API v2 Complete Feature Endpoints
Exposes Forever Orders (GTT), Position Conversion, Margin Calculator, Ledger, EDIS, and Trade Details.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from .dhan_client_wrapper import create_dhan_client
from .user_credentials import get_credentials_manager

logger = logging.getLogger(__name__)

dhan_v2_router = APIRouter(prefix="/api/dhan/v2", tags=["DhanHQ v2 Complete API"])


async def get_user_dhan_client(user_id: str):
    """Helper to retrieve credentials and initialize DhanHQ client"""
    manager = get_credentials_manager()
    resolved_id = await manager.resolve_user_id(user_id)
    creds = await manager.get_user_credentials(resolved_id)
    if not creds or not creds.get("client_id") or not creds.get("access_token"):
        raise HTTPException(status_code=401, detail="DhanHQ credentials not configured")
    client_id = creds.get("client_id") or creds.get("dhan_client_id")
    access_token = creds.get("access_token") or creds.get("dhan_access_token")
    return create_dhan_client(client_id, access_token), resolved_id


# --- Request Models ---
class ForeverOrderRequest(BaseModel):
    user_id: Optional[str] = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
    dhan_client_id: Optional[str] = ""
    order_flag: str = "SINGLE"  # SINGLE or OCO
    transaction_type: str = "BUY"  # BUY or SELL
    exchange_segment: str = "NSE_EQ"
    product_type: str = "CNC"
    order_type: str = "LIMIT"
    validity: str = "DAY"
    trading_symbol: str
    security_id: str
    quantity: int
    disclosed_quantity: Optional[int] = 0
    price: float
    trigger_price: float
    price_1: Optional[float] = 0.0
    trigger_price_1: Optional[float] = 0.0


class ConvertPositionRequest(BaseModel):
    user_id: Optional[str] = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
    from_product_type: str  # INTRADAY, CNC, MARGIN
    to_product_type: str
    exchange_segment: str  # NSE_EQ, NSE_FNO, etc.
    position_type: str  # LONG or SHORT
    security_id: str
    convert_qty: int


class MarginCalculatorRequest(BaseModel):
    user_id: Optional[str] = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
    dhan_client_id: Optional[str] = ""
    exchange_segment: str
    transaction_type: str
    quantity: int
    product_type: str
    security_id: str
    price: float
    trigger_price: Optional[float] = 0.0


class BacktestRequest(BaseModel):
    user_id: Optional[str] = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
    security_id: str = "13"
    exchange_segment: str = "IDX_I"
    instrument_type: str = "INDEX"
    strategy_name: str = "MA_CROSSOVER"  # MA_CROSSOVER, RSI_REVERSION, MACD_MOMENTUM, BOLLINGER_BANDS
    months: int = 6
    initial_capital: float = 1000000.0
    position_size_pct: float = 0.2
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04


# --- 6-Month Quantitative Backtester ---
@dhan_v2_router.post("/backtest")
async def run_6month_backtest(req: BacktestRequest):
    """Run 6-month historical strategy backtest using DhanHQ candle data"""
    try:
        from .backtest_engine import BacktestEngine
        engine = BacktestEngine(user_id=req.user_id)
        df = await engine.fetch_historical_data(
            security_id=req.security_id,
            exchange_segment=req.exchange_segment,
            instrument_type=req.instrument_type,
            months=req.months
        )
        res = engine.run_backtest(
            df=df,
            strategy_name=req.strategy_name,
            initial_capital=req.initial_capital,
            position_size_pct=req.position_size_pct,
            stop_loss_pct=req.stop_loss_pct,
            take_profit_pct=req.take_profit_pct
        )
        return {
            "status": "success",
            "security_id": req.security_id,
            "months": req.months,
            "data": res,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing 6-month backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Forever Orders (GTT) ---
@dhan_v2_router.get("/forever/orders")
async def get_forever_orders(user_id: Optional[str] = Query("znyNtT2lW3MKHqFrVA6E0A2Iv3N2")):
    """Get list of all active Forever (GTT) orders"""
    try:
        client, resolved_id = await get_user_dhan_client(user_id)
        res = client.get_forever()
        data = res.get("data") if isinstance(res, dict) and "data" in res else res
        return {
            "status": "success",
            "user_id": resolved_id,
            "data": data if isinstance(data, list) else [],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching forever orders: {e}")
        return {"status": "success", "user_id": user_id, "data": []}


@dhan_v2_router.post("/forever/orders")
async def create_forever_order(req: ForeverOrderRequest):
    """Create a new Forever (GTT) Order (Single-leg or OCO)"""
    try:
        client, resolved_id = await get_user_dhan_client(req.user_id)
        res = client.place_forever(
            order_flag=req.order_flag,
            transaction_type=req.transaction_type,
            exchange_segment=req.exchange_segment,
            product_type=req.product_type,
            order_type=req.order_type,
            validity=req.validity,
            trading_symbol=req.trading_symbol,
            security_id=str(req.security_id),
            quantity=req.quantity,
            disclosed_quantity=req.disclosed_quantity or 0,
            price=req.price,
            trigger_price=req.trigger_price,
            price_1=req.price_1 or 0.0,
            trigger_price_1=req.trigger_price_1 or 0.0
        )
        return {
            "status": "success" if isinstance(res, dict) and res.get("status") == "success" else "failed",
            "user_id": resolved_id,
            "data": res
        }
    except Exception as e:
        logger.error(f"Error placing forever order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dhan_v2_router.delete("/forever/orders/{order_id}")
async def cancel_forever_order(order_id: str, user_id: Optional[str] = Query("znyNtT2lW3MKHqFrVA6E0A2Iv3N2")):
    """Cancel a Forever (GTT) order by ID"""
    try:
        client, resolved_id = await get_user_dhan_client(user_id)
        res = client.cancel_forever(order_id=order_id)
        return {
            "status": "success" if isinstance(res, dict) and res.get("status") == "success" else "failed",
            "user_id": resolved_id,
            "order_id": order_id,
            "data": res
        }
    except Exception as e:
        logger.error(f"Error cancelling forever order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Position Conversion ---
@dhan_v2_router.post("/positions/convert")
async def convert_position(req: ConvertPositionRequest):
    """Convert open position between Intraday and CNC/Delivery"""
    try:
        client, resolved_id = await get_user_dhan_client(req.user_id)
        res = client.convert_position(
            from_product_type=req.from_product_type,
            to_product_type=req.to_product_type,
            exchange_segment=req.exchange_segment,
            position_type=req.position_type,
            security_id=str(req.security_id),
            convert_qty=req.convert_qty
        )
        return {
            "status": "success" if isinstance(res, dict) and res.get("status") == "success" else "failed",
            "user_id": resolved_id,
            "data": res
        }
    except Exception as e:
        logger.error(f"Error converting position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Margin Calculator ---
@dhan_v2_router.post("/margin/calculator")
async def calculate_margin(req: MarginCalculatorRequest):
    """Calculate required margin & leverage for order parameters"""
    try:
        client, resolved_id = await get_user_dhan_client(req.user_id)
        res = client.margin_calculator(
            security_id=str(req.security_id),
            exchange_segment=req.exchange_segment,
            transaction_type=req.transaction_type,
            quantity=req.quantity,
            product_type=req.product_type,
            price=req.price,
            trigger_price=req.trigger_price or 0.0
        )
        return {
            "status": "success",
            "user_id": resolved_id,
            "data": res.get("data") if isinstance(res, dict) and "data" in res else res
        }
    except Exception as e:
        logger.error(f"Error calculating margin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Trades & Ledger ---
@dhan_v2_router.get("/trades/{order_id}")
async def get_trades_by_order(order_id: str, user_id: Optional[str] = Query("znyNtT2lW3MKHqFrVA6E0A2Iv3N2")):
    """Get trade executions for a specific order ID"""
    try:
        client, resolved_id = await get_user_dhan_client(user_id)
        res = client.get_trade_by_order_id(order_id=order_id)
        data = res.get("data") if isinstance(res, dict) and "data" in res else res
        return {
            "status": "success",
            "user_id": resolved_id,
            "order_id": order_id,
            "data": data if isinstance(data, list) else []
        }
    except Exception as e:
        logger.error(f"Error getting trade by order {order_id}: {e}")
        return {"status": "success", "user_id": user_id, "order_id": order_id, "data": []}


@dhan_v2_router.get("/ledger")
async def get_account_ledger(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    user_id: Optional[str] = Query("znyNtT2lW3MKHqFrVA6E0A2Iv3N2")
):
    """Get historical account ledger entries"""
    try:
        client, resolved_id = await get_user_dhan_client(user_id)
        start = from_date or (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        end = to_date or datetime.utcnow().strftime("%Y-%m-%d")
        res = client.get_trade_history(from_date=start, to_date=end)
        data = res.get("data") if isinstance(res, dict) and "data" in res else res
        return {
            "status": "success",
            "user_id": resolved_id,
            "from_date": start,
            "to_date": end,
            "data": data if isinstance(data, list) else []
        }
    except Exception as e:
        logger.error(f"Error getting account ledger: {e}")
        return {"status": "success", "user_id": user_id, "data": []}


# --- E-DIS Authorization ---
@dhan_v2_router.get("/edis/form")
async def generate_edis_form(isin: str = Query(...), quantity: int = Query(...), user_id: Optional[str] = Query("znyNtT2lW3MKHqFrVA6E0A2Iv3N2")):
    """Generate EDIS form HTML / TPIN redirection for delivery sell authorization"""
    try:
        client, resolved_id = await get_user_dhan_client(user_id)
        res = client.generate_tpin()
        return {
            "status": "success",
            "user_id": resolved_id,
            "isin": isin,
            "quantity": quantity,
            "data": res
        }
    except Exception as e:
        logger.error(f"Error generating EDIS form: {e}")
        raise HTTPException(status_code=500, detail=str(e))
