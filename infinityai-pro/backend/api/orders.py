"""
Orders and Trading API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from services.live_trader import live_trader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders & Trading"])

class OrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: int
    order_type: str = "MARKET"  # MARKET or LIMIT
    price: Optional[float] = None

@router.post("/place")
async def place_order(order: OrderRequest):
    """Place a trading order"""
    
    try:
        result = await live_trader.place_order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=order.order_type,
            price=order.price
        )
        
        return {
            "success": True,
            "order_id": result.get("order_id"),
            "status": result.get("status"),
            "message": "Order placed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to place order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
async def get_positions():
    """Get current positions"""
    
    try:
        positions = await live_trader.get_positions()
        
        return {
            "success": True,
            "positions": positions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders")
async def get_orders():
    """Get order history"""
    
    try:
        orders = await live_trader.get_orders()
        
        return {
            "success": True,
            "orders": orders,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    
    try:
        result = await live_trader.cancel_order(order_id)
        
        return {
            "success": True,
            "order_id": order_id,
            "status": "cancelled",
            "message": "Order cancelled successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))