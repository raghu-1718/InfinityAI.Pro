"""
Portfolio State and Risk Management Router (REST & WebSocket)
"""
import asyncio
from typing import Dict, List, Set
from datetime import datetime
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, status

from backend.src.schemas import (
    PortfolioStateResponse,
    PortfolioPosition,
    OrderRequest
)
from backend.src.middleware import check_market_hours_guardrail

router = APIRouter(prefix="", tags=["Portfolio & Risk"])

# In-memory portfolio state
_portfolio = {
    "total_equity": 500000.0,
    "cash_balance": 385000.0,
    "margin_used": 115000.0,
    "dynamic_var_99": 14250.0,
    "unrealized_pnl": 4820.0,
    "realized_pnl": 19450.0,
    "positions": [
        {
            "symbol": "NIFTY26AUG24500CE",
            "quantity": 65,
            "entry_price": 142.50,
            "current_price": 168.20,
            "pnl": 1670.50,
            "pnl_pct": 18.04
        },
        {
            "symbol": "BANKNIFTY26AUG51500PE",
            "quantity": 30,
            "entry_price": 210.00,
            "current_price": 315.00,
            "pnl": 3150.00,
            "pnl_pct": 50.00
        }
    ]
}
_portfolio_lock = asyncio.Lock()


class PortfolioConnectionManager:
    """Manages WebSocket clients listening for portfolio updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.discard(websocket)

    async def broadcast_update(self, state: Dict):
        async with self._lock:
            targets = list(self.active_connections)
        for ws in targets:
            try:
                await ws.send_json({"event": "portfolio_update", "data": state})
            except Exception:
                pass


portfolio_ws_manager = PortfolioConnectionManager()


@router.get("/api/v1/portfolio/state", response_model=PortfolioStateResponse)
async def get_portfolio_state():
    """Retrieve current portfolio equity, cash, margin, and 99% Dynamic VaR."""
    async with _portfolio_lock:
        positions = [PortfolioPosition(**p) for p in _portfolio["positions"]]
        return PortfolioStateResponse(
            total_equity=_portfolio["total_equity"],
            cash_balance=_portfolio["cash_balance"],
            margin_used=_portfolio["margin_used"],
            dynamic_var_99=_portfolio["dynamic_var_99"],
            unrealized_pnl=_portfolio["unrealized_pnl"],
            realized_pnl=_portfolio["realized_pnl"],
            positions=positions
        )


@router.post("/api/v1/portfolio/order", status_code=status.HTTP_201_CREATED)
async def place_portfolio_order(
    order: OrderRequest,
    request: Request,
    _guardrail: None = Depends(check_market_hours_guardrail)
):
    """
    Execute order subject to market hours enforcement (HTTP 403 block outside 09:15-15:30 IST for live).
    Updates portfolio positions and broadcasts state.
    """
    async with _portfolio_lock:
        cost = order.price * order.quantity
        if order.action == "BUY":
            _portfolio["cash_balance"] -= cost
            _portfolio["margin_used"] += cost
            _portfolio["positions"].append({
                "symbol": order.symbol,
                "quantity": order.quantity,
                "entry_price": order.price,
                "current_price": order.price,
                "pnl": 0.0,
                "pnl_pct": 0.0
            })
        else:
            _portfolio["cash_balance"] += cost
            _portfolio["margin_used"] = max(0.0, _portfolio["margin_used"] - cost)

        state_copy = dict(_portfolio)

    asyncio.create_task(portfolio_ws_manager.broadcast_update(state_copy))

    return {
        "status": "executed",
        "order": order.model_dump(),
        "executed_at": datetime.utcnow().isoformat()
    }


@router.websocket("/ws/portfolio")
async def websocket_portfolio_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time portfolio state and risk streaming."""
    await portfolio_ws_manager.connect(websocket)
    try:
        # Immediately stream current portfolio state upon connection
        async with _portfolio_lock:
            state = dict(_portfolio)
        await websocket.send_json({"event": "portfolio_update", "data": state})

        while True:
            # Keep alive and listen for client pings
            data = await websocket.receive_json()
            if data.get("action") == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        await portfolio_ws_manager.disconnect(websocket)
    except Exception:
        await portfolio_ws_manager.disconnect(websocket)
