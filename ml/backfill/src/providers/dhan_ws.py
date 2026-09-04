import json, threading, os
import websocket
from google.cloud import pubsub_v1
from ..core.config import Config
from ..core.utils import setup_logger
from ..core.event_bus import event_bus

from datetime import datetime, timezone

def format_tick_for_pubsub(dhan_tick: dict) -> bytes:
    """Format Dhan tick to strictly match BigQuery market_data.live_ticks schema"""
    symbol = (
        dhan_tick.get("tradingSymbol")
        or dhan_tick.get("symbol")
        or dhan_tick.get("trading_symbol")
        or str(dhan_tick.get("security_id") or dhan_tick.get("securityId") or "NIFTY")
    )
    try:
        price = float(
            dhan_tick.get("LTP")
            or dhan_tick.get("price")
            or dhan_tick.get("ltp")
            or dhan_tick.get("last_price")
            or (dhan_tick.get("ohlc", {}).get("close") if isinstance(dhan_tick.get("ohlc"), dict) else None)
            or 0.0
        )
    except (ValueError, TypeError):
        price = 0.0

    try:
        volume = int(
            dhan_tick.get("volume")
            or dhan_tick.get("qty")
            or dhan_tick.get("quantity")
            or dhan_tick.get("last_quantity")
            or 0
        )
    except (ValueError, TypeError):
        volume = 0

    ts = dhan_tick.get("timestamp") or dhan_tick.get("time")
    if not ts:
        ts = datetime.now(timezone.utc).isoformat()
    elif isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    event_type = str(dhan_tick.get("type") or dhan_tick.get("event_type") or "TICK")

    payload = {
        "symbol": symbol,
        "price": price,
        "volume": volume,
        "timestamp": ts,
        "event_type": event_type,
        "raw_data": json.dumps(dhan_tick),
        "data": "live_stream"
    }
    return json.dumps(payload).encode("utf-8")


class DhanWS:
    def __init__(self):
        self.url = Config.WEBSOCKET_URL
        self.token = Config.DHAN_ACCESS_TOKEN
        
        # Initialize Pub/Sub Publisher
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, "market-ticks")
            log.info(f"Initialized Pub/Sub Publisher for topic: {self.topic_path}")
        except Exception as e:
            self.publisher = None
            log.warning(f"Failed to initialize Pub/Sub Publisher: {e}")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Pub/Sub payload formatted for BigQuery subscription
            if self.publisher and isinstance(data, dict):
                formatted_bytes = format_tick_for_pubsub(data)
                self.publisher.publish(self.topic_path, data=formatted_bytes)
                
        except Exception as e:
            data = {"type": "raw", "message": message}
            log.error(f"Error processing WS message: {e}")
        event_type = data.get("type", "unknown") if isinstance(data, dict) else "unknown"
        event_bus.publish(event_type, data)
        log.info(f"WS: {event_type} -> {data}")

    def _on_open(self, ws):
        log.info("✅ Connected to Dhan WebSocket")
        auth_msg = json.dumps({"channel": "multi", "token": self.token})
        ws.send(auth_msg)

    def _on_error(self, ws, error):
        log.error(f"WebSocket Error: {error}")

    def _on_close(self, ws, code, msg):
        log.warning("WebSocket closed — reconnecting…")
        self.connect()

    def connect(self):
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            self.url,
            on_message=self._on_message,
            on_open=self._on_open,
            on_error=self._on_error,
            on_close=self._on_close
        )
        thread = threading.Thread(target=ws.run_forever, daemon=True)
        thread.start()
        log.info("WebSocket listening on: orders/trades/price channels.")
