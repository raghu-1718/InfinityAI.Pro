# Archived from `engines/engine-d/services/event_broadcaster.py` on 2025-11-25

```python
"""
Event Broadcaster for Engine D
Broadcasts trade execution events, AI signals, and market updates to WebSocket clients
"""
from typing import Dict, Any
from datetime import datetime, timezone
import asyncio
import logging

logger = logging.getLogger(__name__)

class EventBroadcaster:
    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
        self.event_count = 0
    
    async def broadcast_trade_event(self, trade_data: Dict[str, Any]):
        """Broadcast trade execution event"""
        self.event_count += 1
        event: Dict[str, Any] = {
            "type": "trade",
            "event_id": f"trade_{self.event_count}",
            "data": trade_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.ws_manager.broadcast(event, channel="trades")
        await self.ws_manager.broadcast(event, channel="dashboard")
        logger.info(f"Broadcasted trade event: {trade_data.get('symbol', 'unknown')}")
    
    async def broadcast_signal_event(self, signal_data: Dict[str, Any]):
        """Broadcast AI signal event"""
        self.event_count += 1
        event: Dict[str, Any] = {
            "type": "signal",
            "event_id": f"signal_{self.event_count}",
            "data": signal_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.ws_manager.broadcast(event, channel="signals")
        await self.ws_manager.broadcast(event, channel="dashboard")
        logger.info(f"Broadcasted signal event: {signal_data.get('symbol', 'unknown')}")
    
    async def broadcast_health_event(self, health_data: Dict[str, Any]):
        """Broadcast health status update"""
        self.event_count += 1
        event: Dict[str, Any] = {
            "type": "health",
            "event_id": f"health_{self.event_count}",
            "data": health_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.ws_manager.broadcast(event, channel="health")
        await self.ws_manager.broadcast(event, channel="dashboard")
    
    async def broadcast_market_event(self, market_data: Dict[str, Any]):
        """Broadcast market data update"""
        self.event_count += 1
        event: Dict[str, Any] = {
            "type": "market",
            "event_id": f"market_{self.event_count}",
            "data": market_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.ws_manager.broadcast(event, channel="dashboard")
    
    async def broadcast_custom_event(self, event_type: str, data: Dict[str, Any], channel: str = "dashboard"):
        """Broadcast custom event"""
        self.event_count += 1
        event: Dict[str, Any] = {
            "type": event_type,
            "event_id": f"{event_type}_{self.event_count}",
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.ws_manager.broadcast(event, channel=channel)
    
    def get_stats(self) -> dict:
        """Get broadcaster statistics"""
        return {
            "total_events": self.event_count,
            "connections": self.ws_manager.get_connection_stats()
        }
```