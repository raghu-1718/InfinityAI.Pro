import pytest
from datetime import datetime

def test_websocket_market_ticks(client):
    """Verify WebSocket client connects, subscribes, and receives ticks."""
    with client.websocket_connect("/ws/market/ticks") as ws:
        # Subscribe to NIFTY
        ws.send_json({"action": "subscribe", "symbol": "NIFTY"})
        ack = ws.receive_json()
        assert ack["event"] == "subscribed"
        assert ack["symbol"] == "NIFTY"

        # Push a market tick through REST
        client.post(
            "/api/v1/market/ticks",
            json={
                "symbol": "NIFTY",
                "price": 24550.0,
                "volume": 3000,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Receive broadcast tick on WebSocket
        broadcast = ws.receive_json()
        assert broadcast["event"] == "tick"
        assert broadcast["data"]["symbol"] == "NIFTY"
        assert broadcast["data"]["price"] == 24550.0

def test_websocket_portfolio_stream(client):
    """Verify WebSocket client receives initial portfolio state upon connection."""
    with client.websocket_connect("/ws/portfolio") as ws:
        initial_msg = ws.receive_json()
        assert initial_msg["event"] == "portfolio_update"
        assert "data" in initial_msg
        assert "total_equity" in initial_msg["data"]
