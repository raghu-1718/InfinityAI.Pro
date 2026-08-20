"""
Real-Time Enhancements Module for Engine-C
Provides Server-Sent Events (SSE), NDJSON streaming, and Google Cloud Firestore event storage.

Features:
- Store postback webhooks to Firestore for audit trail
- Real-time position updates via SSE/NDJSON
- Event broadcasting to all subscribers
- Per-user event queues to prevent cross-user event pollution
"""

import json
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, AsyncGenerator, Optional
from collections import deque, defaultdict

from dhanhq import marketfeed
from google.cloud import bigquery
from src.user_credentials import get_credentials_manager

# BigQuery Configuration for live tick ingestion
BQ_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BQ_DATASET_ID = os.environ.get("BQ_MARKET_DATA_DATASET", "market_data")
BQ_TABLE_ID = os.environ.get("BQ_OPTIONS_TICKS_TABLE", "options_ticks")
_bq_client = None
_bq_table_ref = None


# Global state
_db_client = None
_event_queue = deque(maxlen=1000)  # Global circular buffer for events (deprecated)
_user_event_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))  # Per-user queues
logger = logging.getLogger(__name__)


def on_message(tick: Dict[str, Any]):
    """Callback to process incoming ticks and write to BigQuery."""
    global _bq_client, _bq_table_ref
    if not _bq_client or not _bq_table_ref:
        return

    # Only process live ticks (which have a last traded price)
    if "ltp" not in tick:
        return

    try:
        # Transform tick data to match BigQuery schema
        row_to_insert = {
            "symbol": str(tick.get("security_id")),
            "timestamp": datetime.utcnow().isoformat(),  # Use receive time
            "last_price": float(tick.get("ltp", 0.0)),
            "last_trade_time": tick.get("ltt"),
            "last_trade_qty": int(tick.get("ltq", 0)),
            "volume": int(tick.get("volume", 0)),
            "bid_price": float(tick.get("bid", 0.0)),
            "ask_price": float(tick.get("ask", 0.0)),
            "open_interest": int(tick.get("oi", 0)),
        }

        errors = _bq_client.insert_rows_json(_bq_table_ref, [row_to_insert])
        if errors:
            logger.error(f"BigQuery insert errors for {row_to_insert['symbol']}: {errors}")
        else:
            logger.debug(f"Tick inserted for {row_to_insert['symbol']}")

    except Exception as e:
        logger.error(f"Error processing tick in on_message: {e}")


async def initialize_realtime(db_client=None):
    """
    Initialize the real-time module.
    - Sets up BigQuery client for tick ingestion.
    - Connects to DhanHQ live market feed websocket.
    - Subscribes to instruments for live data.
    """
    global _db_client, _bq_client, _bq_table_ref
    _db_client = db_client
    logger.info("✅ Real-time module initializing...")

    # 1. Initialize BigQuery Client
    try:
        _bq_client = bigquery.Client(project=BQ_PROJECT_ID)
        # Fallback to client's project if BQ_PROJECT_ID is not set
        project_id = BQ_PROJECT_ID or _bq_client.project
        table_name = f"{project_id}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
        _bq_table_ref = _bq_client.get_table(table_name)
        logger.info(f"✅ BigQuery client initialized for table: {table_name}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize BigQuery client: {e}")
        return  # Cannot proceed without BigQuery

    # 2. Get Dhan Credentials
    try:
        creds_manager = get_credentials_manager()
        # Using the primary user for the live feed
        user_id = await creds_manager.resolve_user_id(None)
        creds = await creds_manager.get_user_credentials(user_id)
        if not creds:
            logger.error("❌ No Dhan credentials found for primary user. Cannot start market feed.")
            return

        client_id = creds.get("client_id") or creds.get("dhan_client_id")
        access_token = creds.get("access_token") or creds.get("dhan_access_token")

        if not client_id or not access_token:
            logger.error("❌ Incomplete Dhan credentials. Cannot start market feed.")
            return
    except Exception as e:
        logger.error(f"❌ Failed to get Dhan credentials: {e}")
        return

    # 3. Connect to DhanHQ Market Feed
    try:
        logger.info(f"Connecting to DhanHQ market feed for client_id: {client_id}...")
        instruments = [(1, '13'), (1, '26000')]

        def _run_feed():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                feed = marketfeed.DhanFeed(
                    client_id=client_id,
                    access_token=access_token,
                    instruments=instruments,
                    version='v2'
                )
                logger.info(f"✅ DhanHQ market feed thread starting for: {instruments}")
                feed.run_forever()
            except Exception as fe:
                logger.warning(f"DhanHQ feed loop note: {fe}")

        import threading
        t = threading.Thread(target=_run_feed, daemon=True)
        t.start()
        logger.info(f"✅ DhanHQ market feed started in background thread for instruments: {instruments}")

    except Exception as e:
        logger.error(f"❌ Failed to start DhanHQ market feed: {e}")


async def store_postback_event(order_id: str, client_id: str, event_data: Dict[str, Any]) -> bool:
    """
    Store postback webhook data to Google Cloud Firestore logs collection.
    """
    try:
        from src.user_credentials import get_credentials_manager
        manager = get_credentials_manager()
        if not manager or not manager.db:
            logger.warning("⚠️ Firestore not initialized, skipping postback storage")
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

        manager.db.collection("logs").document().set({
            "level": "INFO",
            "message": f"Postback received for {order_id}",
            "metadata": trade_event_doc,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"✅ Postback stored in Firestore: {order_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to store postback in Firestore: {e}")
        return False


async def update_portfolio_position(client_id: str, symbol: str, event_data: Dict[str, Any]):
    """
    Update portfolio positions based on order status via Google Cloud Firestore
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

            doc_id = f"{client_id}_{symbol}"
            manager.db.collection("portfolios").document(doc_id).set({
                "user_id": client_id,
                "symbol": symbol,
                "quantity": filled_qty,
                "average_price": price,
                "status": "open",
                "updated_at": datetime.utcnow().isoformat()
            }, merge=True)

            logger.info(f"✅ Portfolio updated in Firestore: {symbol} position for {client_id}")
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
    print("1. Google Cloud Firestore event storage for postback webhooks")
    print("2. SSE (Server-Sent Events) bridge for real-time data")
    print("3. NDJSON streaming for alternative clients")
    print("4. Event broadcasting to all subscribers")
