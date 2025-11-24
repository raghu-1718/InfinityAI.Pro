import aiohttp, logging, os
logger = logging.getLogger("data_connector")

class DataConnector:
    """
    Reads snapshots (and later, streams) from Engine A.
    """
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("ENGINE_A_URL", "http://engine-a:8000")

    async def fetch_snapshot(self, symbol: str) -> dict:
        url = f"{self.base_url}/api/market/{symbol}"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=8) as r:
                    return await r.json()
        except Exception as e:
            logger.error(f"Engine A snapshot error for {symbol}: {e}")
            return {}

    async def fetch_news(self, count: int = 5) -> list[dict]:
        url = f"{self.base_url}/api/news?count={count}"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=8) as r:
                    j = await r.json()
                    return j.get("data", j) if isinstance(j, dict) else j
        except Exception as e:
            logger.warning(f"Engine A news fetch failed: {e}")
            return []
