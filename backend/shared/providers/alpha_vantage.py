import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from .interfaces import MarketDataProvider
from .models import Quote

class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage market data provider - stocks, forex, crypto, commodities."""
    
    @property
    def name(self) -> str:
        return "alpha-vantage"
    
    def __init__(self):
        self.api_key = os.getenv("PROVIDER_ALPHAVANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.timeout = 30
        if not self.api_key:
            raise RuntimeError("PROVIDER_ALPHAVANTAGE_API_KEY not set in environment")
    
    async def fetch_quotes(self, symbols: List[str]) -> List[Quote]:
        """
        Fetch latest quotes for given symbols using GLOBAL_QUOTE endpoint.
        Rate limit: 5 req/min free, 600 req/min premium.
        """
        quotes = []
        async with aiohttp.ClientSession() as session:
            for symbol in symbols:
                try:
                    params = {
                        "function": "GLOBAL_QUOTE",
                        "symbol": symbol,
                        "apikey": self.api_key,
                    }
                    async with session.get(self.base_url, params=params, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            quote_data = data.get("Global Quote", {})
                            if quote_data and quote_data.get("05. price"):
                                quote = Quote(
                                    symbol=symbol,
                                    price=float(quote_data.get("05. price", 0)),
                                    timestamp=datetime.utcnow(),
                                    source=self.name,
                                    currency=None,
                                    bid=float(quote_data.get("07. bid price", 0)) or None,
                                    ask=float(quote_data.get("08. ask price", 0)) or None,
                                    volume=float(quote_data.get("06. volume", 0)) or None,
                                )
                                quotes.append(quote)
                except Exception as e:
                    print(f"Error fetching {symbol} from AlphaVantage: {e}")
                    await asyncio.sleep(0.5)  # Backoff
        return quotes
    
    async def fetch_intraday(self, symbol: str, interval: str = "5min") -> List[Dict[str, Any]]:
        """
        Fetch intraday data for a symbol.
        Intervals: 1min, 5min, 15min, 30min, 60min.
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params, timeout=self.timeout) as resp:
                data = await resp.json()
                key = f"Time Series ({interval})"
                return data.get(key, {})
