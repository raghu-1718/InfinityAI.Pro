"""
InfinityAI.Pro - Dhan Trading and Market Data Provider
Real-time market data feeds and trading for NSE/BSE/MCX
"""

import aiohttp
import os
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DhanProvider:
    """
    Dhan Trading and Market Data Provider

    Provides real-time market data and trading for NSE/BSE/MCX exchanges.
    """

    def __init__(self, access_token: str = "", client_id: str = ""):
        self.base_url = "https://api.dhan.co"
        self.access_token = access_token or os.getenv("DHAN_API_KEY", "")
        self.client_id = client_id or os.getenv("DHAN_API_SECRET", "")
        self.headers = {
            "access-token": self.access_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._timeout = aiohttp.ClientTimeout(total=15)
        logger.info("Dhan Provider initialized")

    async def _get(self, path: str) -> Any:
        """Internal GET request"""
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(url, headers=self.headers) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    data = {"error": "invalid_json", "status": resp.status}
                if resp.status != 200:
                    return {"status": resp.status, "error": data}
                return data

    async def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        """Internal POST request"""
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(url, headers=self.headers, json=payload) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    data = {"error": "invalid_json", "status": resp.status}
                if resp.status != 200:
                    return {"status": resp.status, "error": data}
                return data

    # ========================================================================
    # MARKET DATA ENDPOINTS
    # ========================================================================

    async def get_market_quote(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """
        Get real-time market quote for a symbol

        Args:
            symbol: Trading symbol (e.g., "SBIN")
            exchange: Exchange code (NSE, BSE, MCX)

        Returns:
            Market quote data (LTP, volume, OHLC, etc.)
        """
        payload = {"symbols": [f"{exchange}:{symbol}"]}
        return await self._post("/v2/marketfeed", payload)

    async def get_ohlc(self, symbol: str, exchange: str = "NSE", interval: str = "1min") -> Any:
        """
        Get OHLC (candlestick) data for technical analysis

        Args:
            symbol: Trading symbol
            exchange: Exchange code
            interval: Time interval (1min, 5min, 15min, 1hour, 1day)

        Returns:
            OHLC data with timestamps
        """
        from datetime import datetime, timedelta
        payload = {
            "symbol": f"{exchange}:{symbol}",
            "interval": interval,
            "from": (datetime.now() - timedelta(days=7)).isoformat(),
            "to": datetime.now().isoformat()
        }
        return await self._post("/v2/charts/historical", payload)

    async def get_option_chain(self, symbol: str) -> Any:
        """Get option chain data for derivatives trading analysis"""
        return await self._post("/optionchain", {"symbol": symbol})

    async def get_market_depth(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """
        Get market depth (order book) for liquidity analysis

        Args:
            symbol: Trading symbol
            exchange: Exchange code

        Returns:
            Market depth with bid/ask levels
        """
        payload = {"symbol": f"{exchange}:{symbol}"}
        return await self._post("/v2/marketdepth", payload)

    # ========================================================================
    # TRADING ENDPOINTS
    # ========================================================================

    async def get_positions(self) -> Any:
        """Get open positions"""
        return await self._get("/v2/positions")

    async def get_orders(self) -> Any:
        """Get all orders"""
        return await self._get("/v2/orders")

    async def get_holdings(self) -> Any:
        """Get all holdings"""
        return await self._get("/v2/holdings")

    async def get_fundlimit(self) -> Any:
        """Get fund limits"""
        return await self._get("/v2/fundlimit")
        
    async def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        return await self._get("/v2/profile")

    async def get_statement(self) -> Dict[str, Any]:
        """Get account statement"""
        return await self._get("/v2/statement")
