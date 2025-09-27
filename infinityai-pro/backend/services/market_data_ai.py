import os
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import json

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Alpha Vantage API client for real-time market data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.session = None

        # Rate limiting: 5 calls/minute, 500/day
        self.call_count = 0
        self.last_reset = datetime.now()
        self.daily_limit = 500
        self.minute_limit = 5

    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _rate_limit_check(self) -> bool:
        """Check and enforce rate limits"""
        now = datetime.now()

        # Reset minute counter
        if (now - self.last_reset).seconds >= 60:
            self.call_count = 0
            self.last_reset = now

        # Check limits
        if self.call_count >= self.minute_limit:
            wait_time = 60 - (now - self.last_reset).seconds
            logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            self.call_count = 0

        self.call_count += 1
        return True

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """Get real-time quote for a symbol"""
        try:
            await self._rate_limit_check()
            await self.initialize()

            # Map exchanges to Alpha Vantage format
            exchange_map = {
                "NSE": "NSE",  # Alpha Vantage supports NSE
                "BSE": "BSE",
                "MCX": None,   # Limited MCX support
            }

            if exchange not in exchange_map:
                logger.warning(f"Exchange {exchange} not supported by Alpha Vantage")
                return None

            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": f"{symbol}.{exchange_map[exchange]}" if exchange_map[exchange] else symbol,
                "apikey": self.api_key
            }

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        return {
                            "symbol": quote.get("01. symbol"),
                            "price": float(quote.get("05. price", 0)),
                            "change": float(quote.get("09. change", 0)),
                            "change_percent": float(quote.get("10. change percent", "0%").strip("%")),
                            "volume": int(quote.get("06. volume", 0)),
                            "latest_trading_day": quote.get("07. latest trading day"),
                            "previous_close": float(quote.get("08. previous close", 0)),
                            "timestamp": datetime.now().isoformat()
                        }

                logger.warning(f"Failed to get quote for {symbol}: {response.status}")
                return None

        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None

    async def get_intraday_data(self, symbol: str, interval: str = "5min", outputsize: str = "compact") -> Optional[pd.DataFrame]:
        """Get intraday time series data"""
        try:
            await self._rate_limit_check()
            await self.initialize()

            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,  # compact=100 points, full=full history
                "apikey": self.api_key
            }

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse time series data
                    time_series_key = f"Time Series ({interval})"
                    if time_series_key in data:
                        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
                        df.index = pd.to_datetime(df.index)
                        df = df.astype(float)
                        df.columns = ['open', 'high', 'low', 'close', 'volume']
                        df = df.sort_index()
                        return df

                logger.warning(f"Failed to get intraday data for {symbol}: {response.status}")
                return None

        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {e}")
            return None

class MarketDataAI:
    """AI-powered market data service"""

    def __init__(self, api_key: str):
        self.alpha_vantage = AlphaVantageClient(api_key)
        self.initialized = False

    async def initialize(self):
        """Initialize the market data service"""
        if not self.initialized:
            await self.alpha_vantage.initialize()
            self.initialized = True
            logger.info("MarketDataAI initialized with Alpha Vantage")

    async def close(self):
        """Close the market data service"""
        await self.alpha_vantage.close()

    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get real-time market quote"""
        quote = await self.alpha_vantage.get_quote(symbol, exchange)
        if quote:
            return quote
        return {"error": f"Could not fetch quote for {symbol}"}

    async def get_intraday_data(self, symbol: str, interval: str = "5min") -> Optional[pd.DataFrame]:
        """Get historical intraday data"""
        return await self.alpha_vantage.get_intraday_data(symbol, interval)

    async def health_check(self) -> Dict:
        """Health check for market data service"""
        return {
            "status": "healthy" if self.initialized else "unhealthy",
            "service": "market_data_ai",
            "provider": "alpha_vantage"
        }