"""
Fallback Market Data Service for InfinityAI.Pro
Provides resilient market data with automatic failover between multiple providers
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import os
import yfinance as yf
from services.cache.redis_service import MarketDataCache
import json

logger = logging.getLogger(__name__)

class DataProvider(Enum):
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    POLYGON = "polygon"
    TWELVE_DATA = "twelve_data"
    DHAN = "dhan"

class MarketDataFallback:
    def __init__(self):
        # Provider configurations
        self.providers = {
            DataProvider.ALPHA_VANTAGE: {
                "api_key": os.getenv("ALPHA_VANTAGE_API_KEY"),
                "base_url": "https://www.alphavantage.co/query",
                "rate_limit": 5,  # requests per minute
                "enabled": bool(os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()),
                "priority": 1
            },
            DataProvider.YAHOO_FINANCE: {
                "base_url": "https://query1.finance.yahoo.com",
                "rate_limit": 2000,  # generous limit
                "enabled": True,  # Always available
                "priority": 2
            },
            DataProvider.POLYGON: {
                "api_key": os.getenv("POLYGON_API_KEY"),
                "base_url": "https://api.polygon.io",
                "rate_limit": 5,
                "enabled": bool(os.getenv("POLYGON_API_KEY", "").strip()),
                "priority": 3
            },
            DataProvider.TWELVE_DATA: {
                "api_key": os.getenv("TWELVE_DATA_API_KEY"),
                "base_url": "https://api.twelvedata.com",
                "rate_limit": 8,
                "enabled": bool(os.getenv("TWELVE_DATA_API_KEY", "").strip()),
                "priority": 4
            },
            DataProvider.DHAN: {
                "access_token": os.getenv("DHAN_ACCESS_TOKEN"),
                "base_url": "https://api.dhan.co",
                "rate_limit": 100,
                "enabled": bool(os.getenv("DHAN_ACCESS_TOKEN", "").strip()),
                "priority": 5
            }
        }
        
        # Sort providers by priority
        self.active_providers = [
            provider for provider, config in self.providers.items()
            if config["enabled"]
        ]
        self.active_providers.sort(key=lambda p: self.providers[p]["priority"])
        
        logger.info(f"✅ Market Data Fallback initialized with providers: {[p.value for p in self.active_providers]}")
    
    async def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[Dict]:
        """Get real-time quote with fallback mechanism"""
        
        # Check cache first
        if use_cache:
            cached_data = MarketDataCache.get_quote(symbol)
            if cached_data:
                logger.debug(f"📊 Quote cache hit for {symbol}")
                return cached_data
        
        # Try each provider in order
        for provider in self.active_providers:
            try:
                logger.debug(f"🔍 Trying {provider.value} for quote {symbol}")
                data = await self._get_quote_from_provider(provider, symbol)
                if data:
                    # Cache successful result
                    if use_cache:
                        MarketDataCache.set_quote(symbol, data, ttl=300)  # 5 min cache
                    
                    logger.info(f"✅ Got quote for {symbol} from {provider.value}")
                    return data
            
            except Exception as e:
                logger.warning(f"❌ {provider.value} failed for {symbol}: {e}")
                continue
        
        logger.error(f"🚨 All providers failed for quote {symbol}")
        return None
    
    async def get_historical(self, symbol: str, interval: str = "1d", period: str = "1mo", use_cache: bool = True) -> Optional[List[Dict]]:
        """Get historical data with fallback mechanism"""
        
        # Check cache first
        if use_cache:
            cached_data = MarketDataCache.get_historical(symbol, interval, period)
            if cached_data:
                logger.debug(f"📊 Historical cache hit for {symbol}")
                return cached_data
        
        # Try each provider in order
        for provider in self.active_providers:
            try:
                logger.debug(f"🔍 Trying {provider.value} for historical {symbol}")
                data = await self._get_historical_from_provider(provider, symbol, interval, period)
                if data:
                    # Cache successful result
                    if use_cache:
                        MarketDataCache.set_historical(symbol, interval, period, data, ttl=3600)  # 1 hour cache
                    
                    logger.info(f"✅ Got historical data for {symbol} from {provider.value}")
                    return data
            
            except Exception as e:
                logger.warning(f"❌ {provider.value} failed for historical {symbol}: {e}")
                continue
        
        logger.error(f"🚨 All providers failed for historical {symbol}")
        return None
    
    async def _get_quote_from_provider(self, provider: DataProvider, symbol: str) -> Optional[Dict]:
        """Get quote from specific provider"""
        
        if provider == DataProvider.ALPHA_VANTAGE:
            return await self._alpha_vantage_quote(symbol)
        elif provider == DataProvider.YAHOO_FINANCE:
            return await self._yahoo_finance_quote(symbol)
        elif provider == DataProvider.POLYGON:
            return await self._polygon_quote(symbol)
        elif provider == DataProvider.TWELVE_DATA:
            return await self._twelve_data_quote(symbol)
        elif provider == DataProvider.DHAN:
            return await self._dhan_quote(symbol)
        
        return None
    
    async def _get_historical_from_provider(self, provider: DataProvider, symbol: str, interval: str, period: str) -> Optional[List[Dict]]:
        """Get historical data from specific provider"""
        
        if provider == DataProvider.ALPHA_VANTAGE:
            return await self._alpha_vantage_historical(symbol, interval, period)
        elif provider == DataProvider.YAHOO_FINANCE:
            return await self._yahoo_finance_historical(symbol, interval, period)
        elif provider == DataProvider.POLYGON:
            return await self._polygon_historical(symbol, interval, period)
        elif provider == DataProvider.TWELVE_DATA:
            return await self._twelve_data_historical(symbol, interval, period)
        elif provider == DataProvider.DHAN:
            return await self._dhan_historical(symbol, interval, period)
        
        return None
    
    # Alpha Vantage implementation
    async def _alpha_vantage_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Alpha Vantage"""
        config = self.providers[DataProvider.ALPHA_VANTAGE]
        if not config["api_key"]:
            return None
        
        url = f"{config['base_url']}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={config['api_key']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get("Global Quote", {})
                    if quote:
                        return {
                            "symbol": symbol,
                            "price": float(quote.get("05. price", 0)),
                            "change": float(quote.get("09. change", 0)),
                            "change_percent": quote.get("10. change percent", "0%"),
                            "volume": int(quote.get("06. volume", 0)),
                            "timestamp": quote.get("07. latest trading day"),
                            "provider": "alpha_vantage"
                        }
        return None
    
    async def _alpha_vantage_historical(self, symbol: str, interval: str, period: str) -> Optional[List[Dict]]:
        """Get historical data from Alpha Vantage"""
        config = self.providers[DataProvider.ALPHA_VANTAGE]
        if not config["api_key"]:
            return None
        
        # Map intervals
        function_map = {
            "1m": "TIME_SERIES_INTRADAY",
            "5m": "TIME_SERIES_INTRADAY", 
            "15m": "TIME_SERIES_INTRADAY",
            "30m": "TIME_SERIES_INTRADAY",
            "1h": "TIME_SERIES_INTRADAY",
            "1d": "TIME_SERIES_DAILY"
        }
        
        function = function_map.get(interval, "TIME_SERIES_DAILY")
        url = f"{config['base_url']}?function={function}&symbol={symbol}&apikey={config['api_key']}"
        
        if "INTRADAY" in function:
            url += f"&interval={interval}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    time_series_key = next((key for key in data.keys() if "Time Series" in key), None)
                    if time_series_key and data[time_series_key]:
                        historical_data = []
                        for date, values in data[time_series_key].items():
                            historical_data.append({
                                "timestamp": date,
                                "open": float(values.get("1. open", 0)),
                                "high": float(values.get("2. high", 0)),
                                "low": float(values.get("3. low", 0)),
                                "close": float(values.get("4. close", 0)),
                                "volume": int(values.get("5. volume", 0))
                            })
                        return sorted(historical_data, key=lambda x: x["timestamp"], reverse=True)[:100]  # Limit to 100 records
        return None
    
    # Yahoo Finance implementation
    async def _yahoo_finance_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Yahoo Finance using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if info and "regularMarketPrice" in info:
                return {
                    "symbol": symbol,
                    "price": info.get("regularMarketPrice", 0),
                    "change": info.get("regularMarketChange", 0),
                    "change_percent": f"{info.get('regularMarketChangePercent', 0):.2f}%",
                    "volume": info.get("regularMarketVolume", 0),
                    "timestamp": datetime.now().isoformat(),
                    "provider": "yahoo_finance"
                }
        except Exception as e:
            logger.error(f"Yahoo Finance quote error: {e}")
        return None
    
    async def _yahoo_finance_historical(self, symbol: str, interval: str, period: str) -> Optional[List[Dict]]:
        """Get historical data from Yahoo Finance using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Map periods and intervals to yfinance format
            period_map = {
                "1d": "1d", "5d": "5d", "1mo": "1mo", "3mo": "3mo",
                "6mo": "6mo", "1y": "1y", "2y": "2y", "5y": "5y", "10y": "10y", "ytd": "ytd", "max": "max"
            }
            
            interval_map = {
                "1m": "1m", "2m": "2m", "5m": "5m", "15m": "15m", "30m": "30m",
                "60m": "60m", "90m": "90m", "1h": "1h", "1d": "1d", "5d": "5d",
                "1wk": "1wk", "1mo": "1mo", "3mo": "3mo"
            }
            
            yf_period = period_map.get(period, "1mo")
            yf_interval = interval_map.get(interval, "1d")
            
            hist = ticker.history(period=yf_period, interval=yf_interval)
            
            if not hist.empty:
                historical_data = []
                for index, row in hist.iterrows():
                    historical_data.append({
                        "timestamp": index.isoformat(),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"])
                    })
                return historical_data
        except Exception as e:
            logger.error(f"Yahoo Finance historical error: {e}")
        return None
    
    # Placeholder implementations for other providers
    async def _polygon_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Polygon.io"""
        # Implementation would go here
        return None
    
    async def _polygon_historical(self, symbol: str, interval: str, period: str) -> Optional[List[Dict]]:
        """Get historical data from Polygon.io"""
        # Implementation would go here
        return None
    
    async def _twelve_data_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Twelve Data"""
        # Implementation would go here
        return None
    
    async def _twelve_data_historical(self, symbol: str, interval: str, period: str) -> Optional[List[Dict]]:
        """Get historical data from Twelve Data"""
        # Implementation would go here
        return None
    
    async def _dhan_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Dhan"""
        # Implementation would go here
        return None
    
    async def _dhan_historical(self, symbol: str, interval: str, period: str) -> Optional[List[Dict]]:
        """Get historical data from Dhan"""
        # Implementation would go here
        return None
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for provider, config in self.providers.items():
            status[provider.value] = {
                "enabled": config["enabled"],
                "priority": config["priority"],
                "rate_limit": config["rate_limit"],
                "has_api_key": bool(config.get("api_key") or config.get("access_token"))
            }
        return status

# Global instance
market_data = MarketDataFallback()

# Convenience functions for external use
async def get_quote(symbol: str, use_cache: bool = True) -> Optional[Dict]:
    """Get real-time quote with automatic fallback"""
    return await market_data.get_quote(symbol, use_cache)

async def get_historical(symbol: str, interval: str = "1d", period: str = "1mo", use_cache: bool = True) -> Optional[List[Dict]]:
    """Get historical data with automatic fallback"""
    return await market_data.get_historical(symbol, interval, period, use_cache)

def get_status() -> Dict[str, Any]:
    """Get market data service status"""
    return market_data.get_provider_status()