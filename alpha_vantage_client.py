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

    async def get_daily_data(self, symbol: str, outputsize: str = "compact") -> Optional[pd.DataFrame]:
        """Get daily time series data"""
        try:
            await self._rate_limit_check()
            await self.initialize()

            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": outputsize,
                "apikey": self.api_key
            }

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if "Time Series (Daily)" in data:
                        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
                        df.index = pd.to_datetime(df.index)
                        df = df.astype(float)
                        df.columns = ['open', 'high', 'low', 'close', 'volume']
                        df = df.sort_index()
                        return df

                logger.warning(f"Failed to get daily data for {symbol}: {response.status}")
                return None

        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {e}")
            return None

    async def get_technical_indicator(self, symbol: str, indicator: str, interval: str = "daily", **kwargs) -> Optional[pd.DataFrame]:
        """Get technical indicators (SMA, EMA, RSI, MACD, etc.)"""
        try:
            await self._rate_limit_check()
            await self.initialize()

            # Supported indicators
            indicators = {
                "SMA": "SMA", "EMA": "EMA", "RSI": "RSI", "MACD": "MACD",
                "BBANDS": "BBANDS", "STOCH": "STOCH", "ADX": "ADX"
            }

            if indicator not in indicators:
                logger.error(f"Unsupported indicator: {indicator}")
                return None

            params = {
                "function": indicators[indicator],
                "symbol": symbol,
                "interval": interval,
                "apikey": self.api_key,
                **kwargs  # Additional parameters like time_period, series_type
            }

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse indicator data
                    indicator_key = f"Technical Analysis: {indicator}"
                    if indicator_key in data:
                        df = pd.DataFrame.from_dict(data[indicator_key], orient='index')
                        df.index = pd.to_datetime(df.index)
                        df = df.astype(float)
                        df = df.sort_index()
                        return df

                logger.warning(f"Failed to get {indicator} for {symbol}: {response.status}")
                return None

        except Exception as e:
            logger.error(f"Error getting {indicator} for {symbol}: {e}")
            return None

    async def get_symbol_search(self, keywords: str) -> List[Dict]:
        """Search for symbols matching keywords"""
        try:
            await self._rate_limit_check()
            await self.initialize()

            params = {
                "function": "SYMBOL_SEARCH",
                "keywords": keywords,
                "apikey": self.api_key
            }

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if "bestMatches" in data:
                        matches = []
                        for match in data["bestMatches"]:
                            matches.append({
                                "symbol": match.get("1. symbol"),
                                "name": match.get("2. name"),
                                "type": match.get("3. type"),
                                "region": match.get("4. region"),
                                "market_open": match.get("5. marketOpen"),
                                "market_close": match.get("6. marketClose"),
                                "timezone": match.get("7. timezone"),
                                "currency": match.get("8. currency"),
                                "match_score": match.get("9. matchScore")
                            })
                        return matches

                return []

        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            return []

# Usage example
async def main():
    client = AlphaVantageClient("YOUR_API_KEY")
    await client.initialize()

    # Get quote
    quote = await client.get_quote("RELIANCE", "NSE")
    print(f"RELIANCE Quote: {quote}")

    # Get intraday data
    data = await client.get_intraday_data("RELIANCE.NSE", "5min")
    print(f"Intraday data shape: {data.shape if data is not None else 'None'}")

    # Get RSI
    rsi = await client.get_technical_indicator("RELIANCE.NSE", "RSI", time_period=14)
    print(f"RSI data shape: {rsi.shape if rsi is not None else 'None'}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())