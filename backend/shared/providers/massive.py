import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
from .interfaces import MarketDataProvider
from .models import Quote

class MassiveProvider(MarketDataProvider):
    """Massive (formerly Polygon) real-time market data provider."""
    
    @property
    def name(self) -> str:
        return "massive"
    
    def __init__(self):
        self.api_key = os.getenv("PROVIDER_MASSIVE_API_KEY")
        self.base_url = "https://api.massive.com/v1"
        self.timeout = 30
        if not self.api_key:
            raise RuntimeError("PROVIDER_MASSIVE_API_KEY not set in environment")
    
    async def fetch_quotes(self, symbols: List[str]) -> List[Quote]:
        """
        Fetch latest quotes for stocks via REST API.
        Supports real-time, daily, and historical data.
        """
        quotes = []
        async with aiohttp.ClientSession() as session:
            for symbol in symbols:
                try:
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    url = f"{self.base_url}/stocks/{symbol}/latest"
                    async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            result = data.get("result", {})
                            if result:
                                quote = Quote(
                                    symbol=symbol,
                                    price=float(result.get("price", 0)),
                                    timestamp=datetime.utcfromtimestamp(result.get("sip_timestamp", 0) / 1000),
                                    source=self.name,
                                    bid=float(result.get("bid", 0)) or None,
                                    ask=float(result.get("ask", 0)) or None,
                                    volume=float(result.get("volume", 0)) or None,
                                )
                                quotes.append(quote)
                except Exception as e:
                    print(f"Error fetching {symbol} from Massive: {e}")
                    await asyncio.sleep(0.5)
        return quotes
    
    async def websocket_stream(self, symbols: List[str], on_message: callable):
        """
        Stream real-time quotes via WebSocket for supported symbols.
        Callback receives Quote objects as they arrive.
        """
        ws_url = "wss://stream.massive.com/stocks"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(ws_url) as ws:
                    # Subscribe to symbols
                    subscribe_msg = {
                        "type": "subscribe",
                        "subscriptions": [f"Q.{sym}" for sym in symbols]
                    }
                    await ws.send_json(subscribe_msg)
                    
                    # Listen for messages
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = msg.json()
                            if data.get("type") == "quote":
                                quote = Quote(
                                    symbol=data.get("symbol"),
                                    price=float(data.get("price", 0)),
                                    timestamp=datetime.utcfromtimestamp(data.get("timestamp", 0) / 1000),
                                    source=self.name,
                                    bid=float(data.get("bid", 0)) or None,
                                    ask=float(data.get("ask", 0)) or None,
                                )
                                await on_message(quote)
        except Exception as e:
            print(f"WebSocket stream error: {e}")
