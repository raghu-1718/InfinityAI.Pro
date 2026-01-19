"""
DhanHQ WebSocket Real-Time Data Streamer - Cloud Run Service
Connects to DhanHQ WebSocket and streams live ticks to Pub/Sub
"""
import os
import json
import asyncio
import logging
from datetime import datetime
from google.cloud import pubsub_v1
from google.cloud import secretmanager
import websockets
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "galvanic-pulsar-482815-h0")
MARKET_DATA_RAW_TOPIC = f"projects/{PROJECT_ID}/topics/market-data.raw"
PORT = int(os.getenv("PORT", 8080))

# Pub/Sub Publisher
publisher = pubsub_v1.PublisherClient()

# WebSocket state
websocket_task = None
is_connected = False

def get_secret(secret_id: str) -> str:
    """Fetch secret from Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Secret fetch failed for {secret_id}: {e}")
        return ""

def publish_tick_data(tick_data: dict):
    """Publish tick data to Pub/Sub"""
    try:
        message = json.dumps({
            "type": "websocket_tick",
            "data": tick_data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "dhan-websocket"
        }).encode("utf-8")

        future = publisher.publish(
            MARKET_DATA_RAW_TOPIC,
            message,
            source="websocket",
            data_type="tick"
        )
        future.result(timeout=5)
        logger.debug(f"✅ Published tick: {tick_data.get('symbol', 'unknown')}")
    except Exception as e:
        logger.error(f"❌ Publish failed: {e}")

async def subscribe_to_instruments(websocket, instruments: list):
    """Subscribe to specific instruments for tick data"""
    try:
        # DhanHQ WebSocket subscription format
        subscribe_message = {
            "RequestCode": 15,  # Subscribe to Market Depth
            "InstrumentCount": len(instruments),
            "InstrumentList": instruments
        }
        await websocket.send(json.dumps(subscribe_message))
        logger.info(f"✅ Subscribed to {len(instruments)} instruments")
    except Exception as e:
        logger.error(f"❌ Subscription failed: {e}")

async def handle_websocket_messages(websocket):
    """Handle incoming WebSocket messages"""
    global is_connected
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", data.get("T", "unknown"))

                # Check for different message types
                if msg_type in ["Ticker Data", "Quote", "td", "mf"]:
                    # Market data tick
                    publish_tick_data(data)

                elif msg_type == "connection_ack":
                    logger.info("✅ WebSocket connection acknowledged")
                    is_connected = True

                elif msg_type == "error":
                    logger.error(f"⚠️ WebSocket error: {data}")

                else:
                    logger.debug(f"Received: {msg_type}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON: {message[:100]}")
            except Exception as e:
                logger.error(f"Message handling error: {e}")

    except websockets.exceptions.ConnectionClosed:
        logger.warning("WebSocket connection closed")
        is_connected = False
    except Exception as e:
        logger.error(f"❌ WebSocket handler error: {e}")
        is_connected = False

async def connect_dhan_websocket():
    """Main WebSocket connection handler"""
    global is_connected

    # Get credentials
    client_id = os.getenv("DHAN_CLIENT_ID") or get_secret("dhan-client-id")
    access_token = os.getenv("DHAN_ACCESS_TOKEN") or get_secret("dhan-access-token")

    if not client_id or not access_token:
        logger.error("❌ DhanHQ credentials not found")
        return

    # DhanHQ WebSocket URL with authentication in query params (as per working implementation)
    ws_url = f"wss://api-feed.dhan.co?version=2&token={access_token}&clientId={client_id}"

    # Instruments to subscribe (NIFTY=13, BANKNIFTY=25, CRUDEOIL, GOLD, SILVER)
    instruments = [
        {"ExchangeSegment": 2, "SecurityId": "13"},      # NIFTY (IDX_I)
        {"ExchangeSegment": 2, "SecurityId": "25"},      # BANKNIFTY (IDX_I)
        {"ExchangeSegment": 3, "SecurityId": "114"},     # CRUDEOIL (MCX)
        {"ExchangeSegment": 3, "SecurityId": "11"},      # GOLD (MCX)
        {"ExchangeSegment": 3, "SecurityId": "12"},      # SILVER (MCX)
    ]

    try:
        logger.info(f"🔌 Connecting to DhanHQ WebSocket (v2 protocol)")

        # No custom headers needed - auth in URL params
        async with websockets.connect(ws_url) as websocket:
            logger.info("✅ WebSocket connected")
            is_connected = True

            # Subscribe to instruments
            await subscribe_to_instruments(websocket, instruments)

            # Handle messages
            await handle_websocket_messages(websocket)

    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"❌ WebSocket auth failed (HTTP {e.status_code}): {e}")
        is_connected = False
        # Retry after delay
        await asyncio.sleep(30)
    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")
        is_connected = False
        # Retry after delay
        await asyncio.sleep(10)

async def websocket_loop():
    """Continuous WebSocket connection with auto-reconnect"""
    logger.info("🚀 Starting DhanHQ WebSocket Streamer")

    while True:
        try:
            await connect_dhan_websocket()
        except Exception as e:
            logger.error(f"❌ WebSocket loop error: {e}")

        # Wait before retry
        logger.info("⏳ Waiting 30 seconds before reconnect...")
        await asyncio.sleep(30)

async def health_check(request):
    """Health check endpoint for Cloud Run"""
    status = {
        "status": "healthy" if is_connected else "disconnected",
        "service": "dhan-websocket-streamer",
        "websocket_connected": is_connected,
        "timestamp": datetime.utcnow().isoformat()
    }
    return web.json_response(status)

async def start_background_tasks(app):
    """Start WebSocket task in background"""
    global websocket_task
    websocket_task = asyncio.create_task(websocket_loop())

async def cleanup_background_tasks(app):
    """Cleanup on shutdown"""
    global websocket_task
    if websocket_task:
        websocket_task.cancel()
        try:
            await websocket_task
        except asyncio.CancelledError:
            pass

def main():
    """Main entry point for Cloud Run"""
    app = web.Application()
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)

    logger.info(f"🚀 Starting WebSocket Streamer on port {PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
