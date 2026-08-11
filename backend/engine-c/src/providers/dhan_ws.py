import json, threading, os
import websocket
from google.cloud import pubsub_v1
from ..core.config import Config
from ..core.utils import setup_logger
from ..core.event_bus import event_bus

log = setup_logger("DhanWS")

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
            data = json.loads(message)
            
            # Pub/Sub payload for BigQuery subscription
            if self.publisher:
                symbol = data.get("symbol", "")
                price = float(data.get("price", data.get("LTP", 0.0)))
                volume = int(data.get("volume", 0))
                event_type = data.get("type", "unknown")
                
                payload = {
                    "symbol": symbol,
                    "price": price,
                    "volume": volume,
                    "event_type": event_type,
                    "raw_data": json.dumps(data)
                }
                
                # Check for timestamp or fallback
                ts = data.get("timestamp")
                if ts:
                    payload["timestamp"] = ts

                future = self.publisher.publish(
                    self.topic_path, 
                    data=json.dumps(payload).encode("utf-8")
                )
                
        except Exception as e:
            data = {"type": "raw", "message": message}
        event_type = data.get("type", "unknown")
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
