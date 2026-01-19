import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
from .interfaces import MarketDataProvider
from .models import Quote

class MarketStackProvider(MarketDataProvider):
    """MarketStack real-time and historical stock market data provider."""
    
    @property
    def name(self) -> str:
        return "marketstack"
    
    def __init__(self):
        self.api_key = os.getenv("PROVIDER_MARKETSTACK_API_KEY")
        self.base_url = "https://api.marketstack.com/v1"
        self.timeout = 30
        if not self.api_key:
            raise RuntimeError("PROVIDER_MARKETSTACK_API_KEY not set in environment")
    
    async def fetch_quotes(self, symbols: List[str]) -> List[Quote]:
        """
        Fetch EOD data for given symbols.
        Rate limit: 5 req/sec; free plan: 100/day.
        Max 100 symbols per request.
        """
        quotes = []
        chunks = [symbols[i:i+100] for i in range(0, len(symbols), 100)]
        async with aiohttp.ClientSession() as session:
            for chunk in chunks:
                try:
                    params = {
                        "access_key": self.api_key,
                        "symbols": ",".join(chunk),
                    }
                    url = f"{self.base_url}/eod/latest"
                    async with session.get(url, params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for item in data.get("data", []):
                                quote = Quote(
                                    symbol=item.get("symbol"),
                                    price=float(item.get("close", 0)),
                                    timestamp=datetime.fromisoformat(item.get("date", "").replace("Z", "+00:00")),
                                    source=self.name,
                                    currency=None,
                                    bid=None,
                                    ask=None,
                                    volume=float(item.get("volume", 0)) or None,
                                )
                                quotes.append(quote)
                except Exception as e:
                    print(f"Error fetching chunk from MarketStack: {e}")
                    await asyncio.sleep(1)
        return quotes
    
    async def fetch_intraday(self, symbols: List[str], interval: str = "1hour") -> List[Dict[str, Any]]:
        """
        Fetch intraday data for symbols.
        Intervals: 1min, 5min, 10min, 15min, 30min, 1hour, 3hour, 6hour, 12hour, 24hour.
        Note: <15min requires Professional plan.
        """
        all_data = []
        chunks = [symbols[i:i+100] for i in range(0, len(symbols), 100)]
        async with aiohttp.ClientSession() as session:
            for chunk in chunks:
                try:
                    params = {
                        "access_key": self.api_key,
                        "symbols": ",".join(chunk),
                        "interval": interval,
                    }
                    url = f"{self.base_url}/intraday"
                    async with session.get(url, params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            all_data.extend(data.get("data", []))
                except Exception as e:
                    print(f"Error fetching intraday from MarketStack: {e}")
                    await asyncio.sleep(1)
        return all_data
