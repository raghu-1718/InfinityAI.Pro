"""
Real-Time Enhancements Module for Engine-C
Provides Server-Sent Events (SSE), NDJSON streaming, and Supabase event storage.

Features:
- Store postback webhooks to Supabase for audit trail
- Real-time position updates via SSE/NDJSON
- Event broadcasting to all subscribers
- Per-user event queues to prevent cross-user event pollution
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, AsyncGenerator, Optional
from collections import deque, defaultdict

# Global state
_db_client = None
_event_queue = deque(maxlen=1000)  # Global circular buffer for events (deprecated)
_user_event_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))  # Per-user queues
logger = logging.getLogger(__name__)


def initialize_realtime(db_client=None):
    """Initialize the real-time module."""
    global _db_client
    _db_client = db_client
    logger.info("✅ Real-time module initialized")


async def store_postback_event(order_id: str, client_id: str, event_data: Dict[str, Any]) -> bool:
    """
    Store postback webhook data to Supabase logs table.
    """
    try:
        from src.user_credentials import get_credentials_manager
        manager = get_credentials_manager()
        if not manager or not manager.db:
            logger.warning("⚠️ Supabase not initialized, skipping postback storage")
            return False

        trade_event_doc = {
            "order_id": order_id,
            "client_id": client_id,
            "symbol": event_data.get("symbol"),
            "status": event_data.get("orderStatus"),
            "side": event_data.get("transactionType"),
            "price": event_data.get("price", 0),
            "quantity": event_data.get("quantity", 0),
            "filled_qty": event_data.get("filledQuantity", 0),
            "full_payload": event_data,
            "received_at": datetime.utcnow().isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
            "processor_version": "1.0"
        }

        # For now, just logging to Supabase trades or logs if schema supports it
        # You may need a specific 'trade_events' table in Supabase
        manager.db.table("logs").insert({
            "level": "INFO",
            "message": f"Postback received for {order_id}",
            "metadata": trade_event_doc
        }).execute()

        logger.info(f"✅ Postback stored in Supabase: {order_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to store postback in Supabase: {e}")
        return False


async def update_portfolio_position(client_id: str, symbol: str, event_data: Dict[str, Any]):
    """
    Update portfolio positions based on order status via Supabase
    """
    try:
        status = event_data.get("orderStatus")
        filled_qty = event_data.get("filledQuantity", 0)
        price = event_data.get("price", 0)

        if status in ["FILLED", "PARTIALLY_FILLED"]:
            from src.user_credentials import get_credentials_manager
            manager = get_credentials_manager()
            if not manager or not manager.db:
                return False

            manager.db.table("portfolios").upsert({
                "user_id": client_id,
                "symbol": symbol,
                "quantity": filled_qty,
                "average_price": price,
                "status": "open",
                "updated_at": datetime.utcnow().isoformat()
            }).execute()

            logger.info(f"✅ Portfolio updated: {symbol} position for {client_id}")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to update portfolio: {e}")
        return False

    return False


async def broadcast_realtime_event(event_type: str, event_data: Dict[str, Any], user_id: Optional[str] = None):
    """
    Broadcast event to all SSE subscribers.
    Format: {"event": "...", "data": {...}, "timestamp": "..."}

    Args:
        event_type: Type of event (e.g., 'order_update', 'position_update')
        event_data: Event payload
        user_id: Optional user ID for per-user event tracking. If provided, event goes to user-specific queue
    """
    try:
        event_message = {
            "event": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to global queue (backward compatibility)
        _event_queue.append(event_message)

        # Add to per-user queue if user_id provided
        if user_id:
            _user_event_queues[user_id].append(event_message)
            logger.info(f"📢 Per-User Broadcast: {event_type} for user {user_id}")
        else:
            logger.info(f"📢 Broadcast: {event_type} - {event_data.get('order_id', 'N/A')}")

        return True
    except Exception as e:
        logger.error(f"Failed to broadcast event: {e}")
        return False


async def sse_event_generator(user_id: str) -> AsyncGenerator[str, None]:
    """
    Server-Sent Events (SSE) generator for streaming real-time data.
    Now uses per-user event queues to prevent cross-user event pollution.

    Usage (Frontend):
    const eventSource = new EventSource(`/api/realtime/stream/${userId}`);
    eventSource.addEventListener('order_update', (event) => {
        console.log('Order:', JSON.parse(event.data));
    });
    eventSource.addEventListener('position_update', (event) => {
        console.log('Position:', JSON.parse(event.data));
    });
    """
    try:
        logger.info(f"🔌 SSE stream started for user: {user_id}")

        # Send initial connection confirmation
        yield f"data: {json.dumps({'event': 'connected', 'user_id': user_id, 'timestamp': datetime.utcnow().isoformat()})}\n\n"

        heartbeat_count = 0
        max_duration = 1200  # Stream for up to 20 minutes

        # Get or create per-user queue
        user_queue = _user_event_queues[user_id]

        for i in range(max_duration):
            try:
                # Send queued events specific to this user
                if user_queue:
                    event = user_queue.popleft()
                    yield f"data: {json.dumps(event)}\n\n"
                else:
                    # Send heartbeat every 30 seconds
                    if heartbeat_count % 30 == 0:
                        yield f": heartbeat - {datetime.utcnow().isoformat()}\n\n"
                        heartbeat_count = 0
                    heartbeat_count += 1

                await asyncio.sleep(1)

            except Exception as e:
                logger.warning(f"SSE event error: {e}")
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
                break

    except Exception as e:
        logger.error(f"SSE generator error: {e}")
    finally:
        logger.info(f"🔌 SSE stream closed for user: {user_id}")


async def ndjson_event_generator(user_id: str) -> AsyncGenerator[str, None]:
    """
    Real-time updates as JSON Lines (NDJSON) format.
    Each line is a valid JSON object.

    Usage (Frontend):
    const response = await fetch(`/api/realtime/updates/${userId}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        const line = decoder.decode(value).trim();
        if (line) {
            const event = JSON.parse(line);
            console.log('Update:', event);
        }
    }
    """
    logger.info(f"🔌 NDJSON stream started for user: {user_id}")

    # Send initial connection message
    yield json.dumps({
        "event": "connected",
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }) + "\n"

    try:
        heartbeat_count = 0
        max_duration = 1200  # Stream for up to 20 minutes

        for i in range(max_duration):
            try:
                # Send queued events
                if _event_queue:
                    event = _event_queue.pop(0)
                    yield json.dumps(event) + "\n"
                else:
                    # Send heartbeat every 30 seconds
                    if heartbeat_count % 30 == 0:
                        yield json.dumps({
                            "event": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        }) + "\n"
                        heartbeat_count = 0
                    heartbeat_count += 1

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"NDJSON stream error: {e}")
                break

    finally:
        logger.info(f"🔌 NDJSON stream closed for user: {user_id}")


if __name__ == "__main__":
    print("✅ Real-time enhancements module loaded")
    print("\nFeatures:")
    print("1. Supabase event storage for postback webhooks")
    print("2. SSE (Server-Sent Events) bridge for real-time data")
    print("3. NDJSON streaming for alternative clients")
    print("4. Event broadcasting to all subscribers")
