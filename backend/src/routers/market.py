"""
Market Data Ingestion and Streaming Router (REST & WebSocket)
"""
import uuid
import asyncio
from typing import List, Optional, Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Header

from backend.src.schemas import MarketTickRequest, MarketTickResponse

router = APIRouter(prefix="", tags=["Market Data"])

# In-memory tick storage buffer
_market_ticks: List[Dict] = []
_store_lock = asyncio.Lock()


class MarketConnectionManager:
    """Manages WebSocket connections and symbol subscriptions."""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections[websocket] = set()

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.pop(websocket, None)

    async def subscribe(self, websocket: WebSocket, symbol: str):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections[websocket].add(symbol.upper())

    async def broadcast_tick(self, tick_data: Dict):
        """Broadcast tick to subscribed clients or all clients if subscribed to '*'."""
        symbol = tick_data.get("symbol", "").upper()
        async with self._lock:
            targets = [
                ws for ws, subs in self.active_connections.items()
                if not subs or symbol in subs or "*" in subs
            ]

        for ws in targets:
            try:
                await ws.send_json({"event": "tick", "data": tick_data})
            except Exception:
                # Connection might be closed
                pass


ws_manager = MarketConnectionManager()


@router.post("/api/v1/market/ticks", response_model=MarketTickResponse, status_code=status.HTTP_201_CREATED)
async def ingest_market_tick(
    tick: MarketTickRequest,
    x_correlation_id: Optional[str] = Header(None)
):
    """Ingest a live market tick and stream to active WebSocket listeners."""
    tick_id = f"tick-{uuid.uuid4().hex[:12]}"
    tick_record = {
        "tick_id": tick_id,
        "symbol": tick.symbol.upper(),
        "price": tick.price,
        "volume": tick.volume,
        "strike_price": tick.strike_price,
        "option_type": tick.option_type.value if tick.option_type else None,
        "open_interest": tick.open_interest,
        "timestamp": tick.timestamp.isoformat(),
        "correlation_id": x_correlation_id
    }

    async with _store_lock:
        _market_ticks.insert(0, tick_record)
        # Keep buffer bounded to latest 5000 ticks
        if len(_market_ticks) > 5000:
            _market_ticks.pop()

    # Broadcast to WebSocket listeners asynchronously
    asyncio.create_task(ws_manager.broadcast_tick(tick_record))

    return MarketTickResponse(
        tick_id=tick_id,
        status="ingested",
        correlation_id=x_correlation_id,
        symbol=tick_record["symbol"],
        price=tick_record["price"],
        volume=tick_record["volume"],
        timestamp=tick.timestamp
    )


@router.get("/api/v1/market/ticks", response_model=List[Dict])
async def get_market_ticks(
    symbol: Optional[str] = Query(None, description="Filter by ticker symbol"),
    limit: int = Query(50, ge=1, le=500, description="Max rows to return")
):
    """Query recent ticks from the in-memory buffer."""
    async with _store_lock:
        if symbol:
            sym_upper = symbol.upper()
            filtered = [t for t in _market_ticks if t["symbol"] == sym_upper]
            return filtered[:limit]
        return _market_ticks[:limit]


@router.websocket("/ws/market/ticks")
async def websocket_market_ticks(websocket: WebSocket):
    """WebSocket endpoint for real-time market ticks streaming."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "").lower()
            if action == "subscribe":
                symbol = data.get("symbol", "*")
                await ws_manager.subscribe(websocket, symbol)
                await websocket.send_json({
                    "event": "subscribed",
                    "symbol": symbol.upper(),
                    "message": f"Successfully subscribed to ticks for {symbol.upper()}"
                })
            elif action == "ping":
                await websocket.send_json({"event": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
