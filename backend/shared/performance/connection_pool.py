"""
HTTP Connection Pool Manager for 24/7 High-Performance Operation
Reuses connections to reduce latency and resource usage.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import aiohttp
import httpx

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """
    Manages persistent HTTP connection pools for high-frequency API calls.
    Significantly reduces connection overhead for 24/7 operation.
    """

    _instance: Optional['ConnectionPoolManager'] = None
    _httpx_client: Optional[httpx.AsyncClient] = None
    _aiohttp_session: Optional[aiohttp.ClientSession] = None
    _initialized: bool = False
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def initialize(cls):
        """Initialize connection pools"""
        async with cls._lock:
            if cls._initialized:
                return

            # Create httpx client with connection pooling
            cls._httpx_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(
                    max_keepalive_connections=100,
                    max_connections=200,
                    keepalive_expiry=30.0
                ),
                http2=True,  # Enable HTTP/2 for better performance
                follow_redirects=True,
            )

            # Create aiohttp session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                enable_cleanup_closed=True,
                keepalive_timeout=30,
            )

            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=20,
                sock_connect=10
            )

            cls._aiohttp_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "InfinityAI.Pro/3.7",
                    "Accept": "application/json",
                    "Connection": "keep-alive",
                }
            )

            cls._initialized = True
            logger.info("✅ ConnectionPoolManager initialized with HTTP/2 support")

    @classmethod
    async def get_httpx_client(cls) -> httpx.AsyncClient:
        """Get the shared httpx client"""
        if not cls._initialized:
            await cls.initialize()
        return cls._httpx_client

    @classmethod
    async def get_aiohttp_session(cls) -> aiohttp.ClientSession:
        """Get the shared aiohttp session"""
        if not cls._initialized:
            await cls.initialize()
        return cls._aiohttp_session

    @classmethod
    async def shutdown(cls):
        """Graceful shutdown of all connections"""
        async with cls._lock:
            if cls._httpx_client:
                await cls._httpx_client.aclose()
                cls._httpx_client = None

            if cls._aiohttp_session:
                await cls._aiohttp_session.close()
                cls._aiohttp_session = None

            cls._initialized = False
            logger.info("✅ ConnectionPoolManager shutdown complete")

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get connection pool statistics"""
        stats = {
            "initialized": cls._initialized,
            "httpx_client": cls._httpx_client is not None,
            "aiohttp_session": cls._aiohttp_session is not None,
        }

        if cls._aiohttp_session and not cls._aiohttp_session.closed:
            connector = cls._aiohttp_session.connector
            if connector:
                stats["aiohttp_connections"] = len(connector._conns)

        return stats


# Convenience functions
async def get_http_client() -> httpx.AsyncClient:
    """Get the shared httpx client"""
    return await ConnectionPoolManager.get_httpx_client()


async def get_aiohttp_session() -> aiohttp.ClientSession:
    """Get the shared aiohttp session"""
    return await ConnectionPoolManager.get_aiohttp_session()


@asynccontextmanager
async def managed_request(method: str, url: str, **kwargs):
    """
    Context manager for HTTP requests using connection pool.

    Usage:
        async with managed_request("GET", url) as response:
            data = await response.json()
    """
    client = await get_http_client()
    response = await client.request(method, url, **kwargs)
    try:
        yield response
    finally:
        pass  # Connection is kept alive in pool


async def pooled_get(url: str, **kwargs) -> httpx.Response:
    """Perform GET request using connection pool"""
    client = await get_http_client()
    return await client.get(url, **kwargs)


async def pooled_post(url: str, **kwargs) -> httpx.Response:
    """Perform POST request using connection pool"""
    client = await get_http_client()
    return await client.post(url, **kwargs)


async def aiohttp_get(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Perform GET request using aiohttp session pool"""
    session = await get_aiohttp_session()
    return await session.get(url, **kwargs)


async def aiohttp_post(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Perform POST request using aiohttp session pool"""
    session = await get_aiohttp_session()
    return await session.post(url, **kwargs)
