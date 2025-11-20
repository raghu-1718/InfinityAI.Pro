"""
InfinityAI.Pro - Dhan Market Data Provider (DATA ONLY)
Real-time market data feeds for NSE/BSE/MCX
NO TRADING FUNCTIONALITY - Data streaming only for Engine A and Engine B

⚠️ IMPORTANT: This provider is ONLY for market data.
   All trading/execution is handled by Angel SmartAPI in Engine C.
"""

import aiohttp
import os
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DhanProvider:
    """
    Dhan Market Data Provider - DATA ONLY

    Provides real-time market data for NSE/BSE/MCX exchanges.
    NO trading, NO OAuth, NO order execution.

    Used by: Engine A (market data ingestion), Engine B (AI/ML features)
    Trading Provider: Angel SmartAPI (Engine C)
    """

    def __init__(self, access_token: str = "", client_id: str = ""):
        self.base_url = "https://api.dhan.co"
        # Use API keys for data-only access (no OAuth tokens)
        self.access_token = access_token or os.getenv("DHAN_API_KEY", "")
        self.client_id = client_id or os.getenv("DHAN_API_SECRET", "")
        self.headers = {
            "access-token": self.access_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._timeout = aiohttp.ClientTimeout(total=15)
        logger.info("📊 Dhan Data Provider initialized (DATA ONLY - No trading)")

    async def _get(self, path: str) -> Any:
        """Internal GET request for market data only"""
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
        """Internal POST request for market data only"""
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
    # MARKET DATA ENDPOINTS (ALLOWED)
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
    # TRADING ENDPOINTS (REMOVED - Use Angel SmartAPI in Engine C)
    # ========================================================================

    async def get_positions(self) -> Any:
        """
        ⚠️ DEPRECATED: Use Angel SmartAPI in Engine C

        This endpoint is no longer available in the data-only Dhan provider.
        All trading functionality has been migrated to Angel One.
        """
        logger.warning("get_positions() called on data-only provider - use Angel SmartAPI")
        return {"error": "Trading endpoints disabled - use Angel SmartAPI", "positions": []}

    async def get_orders(self) -> Any:
        """
        ⚠️ DEPRECATED: Use Angel SmartAPI in Engine C

        This endpoint is no longer available in the data-only Dhan provider.
        All trading functionality has been migrated to Angel One.
        """
        logger.warning("get_orders() called on data-only provider - use Angel SmartAPI")
        return {"error": "Trading endpoints disabled - use Angel SmartAPI", "orders": []}

    async def get_holdings(self) -> Any:
        """
        ⚠️ DEPRECATED: Use Angel SmartAPI in Engine C

        This endpoint is no longer available in the data-only Dhan provider.
        All trading functionality has been migrated to Angel One.
        """
        logger.warning("get_holdings() called on data-only provider - use Angel SmartAPI")
        return {"error": "Trading endpoints disabled - use Angel SmartAPI", "holdings": []}

    async def get_fundlimit(self) -> Any:
        """
        ⚠️ DEPRECATED: Use Angel SmartAPI in Engine C

        This endpoint is no longer available in the data-only Dhan provider.
        All trading functionality has been migrated to Angel One.
        """
        logger.warning("get_fundlimit() called on data-only provider - use Angel SmartAPI")
        return {"error": "Trading endpoints disabled - use Angel SmartAPI", "funds": {}}

    async def handle_callback(self, code: str) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED: OAuth removed from Dhan provider

        Dhan OAuth/callback functionality removed.
        Angel SmartAPI uses TOTP authentication (no OAuth).
        """
        logger.warning("handle_callback() called - OAuth removed from Dhan provider")
        return {"error": "OAuth disabled - Angel uses TOTP authentication"}

    async def get_profile(self) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED: Use Angel SmartAPI in Engine C

        This endpoint is no longer available in the data-only Dhan provider.
        """
        logger.warning("get_profile() called on data-only provider")
        return {"error": "Profile endpoints disabled"}

    async def get_statement(self) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED: Use Angel SmartAPI in Engine C

        This endpoint is no longer available in the data-only Dhan provider.
        """
        logger.warning("get_statement() called on data-only provider")
        return {"source": "none", "rows": [], "error": "Statement endpoints disabled"}
