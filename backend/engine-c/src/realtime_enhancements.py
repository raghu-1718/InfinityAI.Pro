"""
Real-Time Enhancements Module for Engine-C
Provides Server-Sent Events (SSE), NDJSON streaming, and Firestore event storage.

Features:
- Store postback webhooks to Firestore for audit trail
- Real-time position updates via SSE/NDJSON
- Event broadcasting to all subscribers
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, AsyncGenerator
from collections import deque

# Global state
_firestore_db = None
_event_queue = deque(maxlen=1000)  # Circular buffer for events
logger = logging.getLogger(__name__)


def initialize_realtime(firestore_db):
    """Initialize the real-time module with Firestore client."""
    global _firestore_db
    _firestore_db = firestore_db
    logger.info("✅ Real-time module initialized with Firestore")


async def store_postback_event(order_id: str, client_id: str, event_data: Dict[str, Any]) -> bool:
    """
    Store postback webhook data to Firestore.
    Collection: trade_events
    Document ID: {order_id}_{timestamp}
    """
    if _firestore_db is None:
        logger.warning("⚠️ Firestore not initialized, skipping postback storage")
        return False

    try:
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
            "timestamp": datetime.utcnow(),
            "processor_version": "1.0"
        }

        # Store in Firestore trade_events collection
        doc_id = f"{order_id}_{datetime.utcnow().timestamp()}".replace('.', '_')
        _firestore_db.collection("trade_events").document(doc_id).set(trade_event_doc)

        logger.info(f"✅ Postback stored in Firestore: {order_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to store postback in Firestore: {e}")
        return False


async def update_portfolio_position(client_id: str, symbol: str, event_data: Dict[str, Any]):
    """
    Update portfolio positions based on order status.
    Stores to: user_positions/{client_id}
    """
    if _firestore_db is None:
        logger.warning("⚠️ Firestore not initialized, skipping position update")
        return False

    try:
        status = event_data.get("orderStatus")
        filled_qty = event_data.get("filledQuantity", 0)
        price = event_data.get("price", 0)

        if status in ["FILLED", "PARTIALLY_FILLED"]:
            positions_ref = _firestore_db.collection("user_positions").document(client_id)
            positions_ref.set({
                f"position_{symbol}": {
                    "symbol": symbol,
                    "qty": filled_qty,
                    "avg_price": price,
                    "status": "open",
                    "last_updated": datetime.utcnow().isoformat()
                },
                "last_modified": datetime.utcnow().isoformat()
            }, merge=True)

            logger.info(f"✅ Portfolio updated: {symbol} position for {client_id}")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to update portfolio: {e}")
        return False

    return False


async def broadcast_realtime_event(event_type: str, event_data: Dict[str, Any]):
    """
    Broadcast event to all SSE subscribers.
    Format: {"event": "...", "data": {...}, "timestamp": "..."}
    """
    try:
        event_message = {
            "event": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        _event_queue.append(event_message)
        logger.info(f"📢 Broadcast: {event_type} - {event_data.get('order_id', 'N/A')}")
        return True
    except Exception as e:
        logger.error(f"Failed to broadcast event: {e}")
        return False


async def sse_event_generator(user_id: str) -> AsyncGenerator[str, None]:
    """
    Server-Sent Events (SSE) generator for streaming real-time data.

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

        for i in range(max_duration):
            try:
                # Send queued events
                if _event_queue:
                    event = _event_queue.pop(0)
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
    print("1. Firestore event storage for postback webhooks")
    print("2. SSE (Server-Sent Events) bridge for real-time data")
    print("3. NDJSON streaming for alternative clients")
    print("4. Event broadcasting to all subscribers")
