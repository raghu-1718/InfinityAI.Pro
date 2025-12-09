import aiohttp, logging, os
from typing import Optional

logger = logging.getLogger("data_connector")

# Shared session reference (set from main.py on startup)
_shared_session: Optional[aiohttp.ClientSession] = None


def set_shared_session(session: aiohttp.ClientSession):
    """Set the shared aiohttp session from main.py"""
    global _shared_session
    _shared_session = session


class DataConnector:
    """
    Reads snapshots (and later, streams) from Engine A.
    Optimized with connection pooling for 24/7 operation.
    """
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("ENGINE_A_URL", "http://engine-a:8000")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get shared session or create temporary one"""
        if _shared_session and not _shared_session.closed:
            return _shared_session
        return aiohttp.ClientSession()

    async def fetch_snapshot(self, symbol: str) -> dict:
        url = f"{self.base_url}/api/market/{symbol}"
        session = await self._get_session()
        is_temp = session != _shared_session

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                return await r.json()
        except Exception as e:
            logger.error(f"Engine A snapshot error for {symbol}: {e}")
            return {}
        finally:
            if is_temp:
                await session.close()

    async def fetch_news(self, count: int = 5) -> list[dict]:
        url = f"{self.base_url}/api/news?count={count}"
        session = await self._get_session()
        is_temp = session != _shared_session

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                j = await r.json()
                return j.get("data", j) if isinstance(j, dict) else j
        except Exception as e:
            logger.warning(f"Engine A news fetch failed: {e}")
            return []
        finally:
            if is_temp:
                await session.close()
