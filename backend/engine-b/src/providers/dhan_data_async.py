"""
Async Dhan Market Data Client - Engine B
Dedicated to high-volume market data ingestion for AI analysis.
Isolated from execution flow to prevent blocking.
"""
import asyncio
import aiohttp
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DhanMarketDataClient:
    """
    Async Dhan Data Client for AI/ML Engine (Engine B).
    Handles heavy payloads: Charts, Option Chains, Historical Data.
    READ-ONLY Authority.
    """
    
    BASE_URL = "https://api.dhan.co"

    def __init__(self, access_token: Optional[str] = None, client_id: Optional[str] = None):
        self.access_token = access_token or os.environ.get("DHAN_ACCESS_TOKEN", "")
        self.client_id = client_id or os.environ.get("DHAN_CLIENT_ID", "")
        
        self.headers = {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self._session: Optional[aiohttp.ClientSession] = None
        logger.info("DhanMarketDataClient (Engine B) initialized")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create local aiohttp session"""
        if self._session is None or self._session.closed:
            # Optimized for data throughput
            connector = aiohttp.TCPConnector(
                limit=50,  # Higher limit for data fetching
                limit_per_host=20,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def _request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Internal request handler"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            session = await self._get_session()
            async with session.request(method, url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error(f"Data Fetch Error {response.status}: {text}")
                    return {"status": "error", "code": response.status, "message": text}
        except Exception as e:
            logger.error(f"Connection Error: {e}")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # CHARTS & HISTORICAL DATA
    # =========================================================================

    async def get_intraday_charts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch Intraday OHLC packets.
        Payload: {SecurityId, ExchangeSegment, Instrument, Interval, FromDate, ToDate}
        """
        return await self._request("POST", "/v2/charts/intraday", payload)

    async def get_historical_charts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch Daily/Historical OHLC.
        Payload: {SecurityId, ExchangeSegment, Instrument, ExpiryCode, FromDate, ToDate}
        """
        return await self._request("POST", "/v2/charts/historical", payload)

    # =========================================================================
    # OPTIONS & DERIVATIVES
    # =========================================================================

    async def get_rolling_option_chain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch Rolling Option Chain Data (Expired/Historic).
        Values: IV, Delta, Theta, Gamma, Vega, OI, Volume.
        """
        return await self._request("POST", "/v2/charts/rollingoption", payload)

    async def get_notional_option_chain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch Live Option Chain Snapshot.
        """
        return await self._request("POST", "/v2/optionchain", payload)

    # =========================================================================
    # MARKET FEED & QUOTES
    # =========================================================================

    async def get_quote(self, security_id: str, exchange_segment: str = "NSE_EQ") -> Dict[str, Any]:
        """Get Real-time Snapshot (LTP, Depth, OHLC)"""
        return await self._request("POST", "/v2/marketfeed/ltp", {
            "SecurityId": security_id,
            "ExchangeSegment": exchange_segment
        })
    
    async def get_ohlc(self, security_id: str, exchange_segment: str = "NSE_EQ") -> Dict[str, Any]:
        """Get Today's OHLC Snapshot"""
        return await self._request("POST", "/v2/marketfeed/ohlc", {
            "SecurityId": security_id,
            "ExchangeSegment": exchange_segment
        })

    async def close(self):
        """Cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()
