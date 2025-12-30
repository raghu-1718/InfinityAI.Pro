import aiohttp
import logging
import os
import time
from typing import Optional, Dict, List, Any

logger = logging.getLogger("engine_b.data_connector")

# -------------------------------------------------------------------
# Shared session (injected from main.py on startup)
# -------------------------------------------------------------------
_shared_session: Optional[aiohttp.ClientSession] = None

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(
    total=8,
    connect=3,
    sock_read=5
)


def set_shared_session(session: aiohttp.ClientSession) -> None:
    """
    Inject shared aiohttp session from application startup.
    This avoids per-request TCP/TLS overhead in Cloud Run.
    """
    global _shared_session
    _shared_session = session
    logger.info("✅ Shared aiohttp session registered for DataConnector")


class DataConnector:
    """
    Engine B → Engine A data bridge.

    Responsibilities:
    - Fetch market snapshots
    - Fetch curated news
    - Handle retries, timeouts, and graceful degradation

    Designed for:
    - Cloud Run
    - Long-lived async workloads
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "ENGINE_A_URL",
            "http://engine-a:8000"
        ).rstrip("/")

    # -----------------------------
    # Internal helpers
    # -----------------------------
    async def _get_session(self) -> tuple[aiohttp.ClientSession, bool]:
        """
        Returns (session, is_temporary).
        Temporary sessions are auto-closed.
        """
        if _shared_session and not _shared_session.closed:
            return _shared_session, False

        logger.warning("⚠️ Shared session unavailable, creating temporary session")
        return aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT), True

    async def _safe_get_json(self, url: str) -> Any:
        session, is_temp = await self._get_session()
        start = time.monotonic()

        try:
            async with session.get(url) as resp:
                if resp.status >= 400:
                    logger.warning(
                        f"Engine A HTTP {resp.status} for {url}"
                    )
                    return {}

                return await resp.json()

        except aiohttp.ClientError as e:
            logger.error(f"Engine A connection error [{url}]: {e}")
            return {}
        except Exception as e:
            logger.exception(f"Unexpected error calling Engine A [{url}]")
            return {}
        finally:
            duration = round((time.monotonic() - start) * 1000, 1)
            logger.debug(f"Engine A call {url} took {duration}ms")

            if is_temp:
                await session.close()

    # -----------------------------
    # Public API
    # -----------------------------
    async def fetch_snapshot(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch real-time market snapshot for a symbol.

        Guaranteed return:
        - dict (possibly empty)
        """
        symbol = symbol.upper()
        url = f"{self.base_url}/api/market/{symbol}"
        return await self._safe_get_json(url)

    async def fetch_news(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch curated market news from Engine A.

        Guaranteed return:
        - list (possibly empty)
        """
        url = f"{self.base_url}/api/news?count={count}"
        data = await self._safe_get_json(url)

        if isinstance(data, dict):
            return data.get("data", [])

        if isinstance(data, list):
            return data

        return []
