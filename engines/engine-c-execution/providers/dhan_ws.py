import json, threading
import websocket
from ..core.config import Config
from ..core.utils import setup_logger
from ..core.event_bus import event_bus

log = setup_logger("DhanWS")

class DhanWS:
    def __init__(self):
        self.url = Config.WEBSOCKET_URL
        self.token = Config.DHAN_ACCESS_TOKEN

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except Exception:
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
