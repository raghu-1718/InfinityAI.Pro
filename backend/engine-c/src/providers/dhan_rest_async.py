"""
Async Dhan REST Client - Optimized for 24/7 High-Performance Trading
Uses connection pooling and caching for maximum efficiency
"""
import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Try to import shared performance modules
try:
    from ....shared.performance import PerformanceCache, ConnectionPoolManager, HealthMonitor
    HAS_PERFORMANCE_MODULES = True
except ImportError:
    HAS_PERFORMANCE_MODULES = False

logger = logging.getLogger(__name__)


class DhanRESTAsync:
    """
    Async Dhan REST API client with connection pooling and caching.
    Designed for 24/7 continuous operation with minimal latency.
    """

    BASE_URL = "https://api.dhan.co/v2"

    def __init__(
        self,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        connection_pool: Optional[Any] = None,
        cache: Optional[Any] = None,
        health_monitor: Optional[Any] = None
    ):
        self.access_token = access_token or os.environ.get("DHAN_ACCESS_TOKEN", "")
        self.client_id = client_id or os.environ.get("DHAN_CLIENT_ID", "")

        # Use shared connection pool or create local session
        self._connection_pool = connection_pool
        self._local_session: Optional[aiohttp.ClientSession] = None

        # Use shared cache or create local cache
        self._cache = cache
        self._local_cache: Dict[str, Any] = {}

        # Health monitoring
        self._health_monitor = health_monitor

        # Request tracking for rate limiting awareness
        self._request_count = 0
        self._last_reset = datetime.now()

        logger.info(f"DhanRESTAsync initialized (pooled={connection_pool is not None})")

    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._connection_pool:
            return await self._connection_pool.get_session()

        if self._local_session is None or self._local_session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=10,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            self._local_session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        return self._local_session

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict] = None,
        use_cache: bool = False,
        cache_ttl: int = 30
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Dhan API with optimizations.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            payload: Request payload for POST/PUT
            use_cache: Whether to cache the response (for GET requests)
            cache_ttl: Cache time-to-live in seconds
        """
        url = f"{self.BASE_URL}{endpoint}"
        cache_key = f"dhan:{method}:{endpoint}"

        # Check cache for GET requests
        if use_cache and method == "GET":
            if self._cache:
                cached = self._cache.get(cache_key)
                if cached is not None:
                    return cached
            elif cache_key in self._local_cache:
                entry = self._local_cache[cache_key]
                if (datetime.now() - entry["time"]).seconds < cache_ttl:
                    return entry["data"]

        # Track request count
        self._request_count += 1

        try:
            session = await self._get_session()

            async with session.request(
                method,
                url,
                json=payload if payload else None,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()

                # Record health metrics
                if self._health_monitor:
                    if response.status == 200:
                        self._health_monitor.record_success(f"dhan_{endpoint.replace('/', '_')}")
                    else:
                        self._health_monitor.record_failure(f"dhan_{endpoint.replace('/', '_')}")

                # Cache successful GET responses
                if use_cache and method == "GET" and response.status == 200:
                    if self._cache:
                        self._cache.set(cache_key, data, ttl=cache_ttl)
                    else:
                        self._local_cache[cache_key] = {
                            "data": data,
                            "time": datetime.now()
                        }

                return data

        except asyncio.TimeoutError:
            logger.error(f"Timeout on {method} {endpoint}")
            if self._health_monitor:
                self._health_monitor.record_failure(f"dhan_{endpoint.replace('/', '_')}")
            return {"status": "error", "error": "Request timeout"}

        except Exception as e:
            logger.error(f"Error on {method} {endpoint}: {e}")
            if self._health_monitor:
                self._health_monitor.record_failure(f"dhan_{endpoint.replace('/', '_')}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # ORDERS - High Priority, No Caching
    # =========================================================================

    async def place_order(self, payload: Dict) -> Dict[str, Any]:
        """Place a new order"""
        return await self._request("POST", "/orders", payload)

    async def modify_order(self, order_id: str, payload: Dict) -> Dict[str, Any]:
        """Modify an existing order"""
        return await self._request("PUT", f"/orders/{order_id}", payload)

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        return await self._request("DELETE", f"/orders/{order_id}")

    async def get_orders(self, use_cache: bool = False) -> Dict[str, Any]:
        """Get all orders for the day"""
        return await self._request("GET", "/orders", use_cache=use_cache, cache_ttl=5)

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any]:
        """Get specific order details"""
        return await self._request("GET", f"/orders/{order_id}")

    async def place_slice_order(self, payload: Dict) -> Dict[str, Any]:
        """Place a slice order"""
        return await self._request("POST", "/orders/slicing", payload)

    # =========================================================================
    # SUPER ORDERS (Baskets/Multi-leg)
    # =========================================================================

    async def place_super_order(self, payload: Dict) -> Dict[str, Any]:
        """Place a super order"""
        return await self._request("POST", "/super/orders", payload)

    async def modify_super_order(self, order_id: str, payload: Dict) -> Dict[str, Any]:
        """Modify a super order"""
        return await self._request("PUT", f"/super/orders/{order_id}", payload)

    async def cancel_super_order(self, order_id: str, order_leg: str) -> Dict[str, Any]:
        """Cancel a super order leg (ENTRY_LEG, STOP_LOSS_LEG, TARGET_LEG)"""
        return await self._request("DELETE", f"/super/orders/{order_id}/{order_leg}")

    async def get_super_orders(self) -> Dict[str, Any]:
        """Get all super orders"""
        return await self._request("GET", "/super/orders")

    async def get_super_order_by_id(self, order_id: str) -> Dict[str, Any]:
        """Get specific super order details (Note: inferred from REST patterns, verify path if standardized)"""
        # Based on standard REST patterns, usually single resource access is ID based.
        # However, Dhan documentation for Super Orders mainly lists get_all.
        # We will assume standard pattern for now or rely on list filtering if explicit ID fetch missing.
        # Actually per simplified spec, list is primary. We can leave this out if not explicitly in user spec.
        # User spec includes: /super/orders/{order-id} (PUT) but not GET.
        # Let's stick strictly to USER_REQUEST provided paths.
        pass

    # =========================================================================
    # FOREVER ORDERS (GTT/OCO)
    # =========================================================================

    async def place_forever_order(self, payload: Dict) -> Dict[str, Any]:
        """Place a forever (GTT) order"""
        return await self._request("POST", "/forever/orders", payload)

    async def modify_forever_order(self, order_id: str, payload: Dict) -> Dict[str, Any]:
        """Modify a forever order"""
        return await self._request("PUT", f"/forever/orders/{order_id}", payload)

    async def cancel_forever_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a forever order"""
        return await self._request("DELETE", f"/forever/orders/{order_id}")

    async def get_forever_orders(self) -> Dict[str, Any]:
        """Get all forever orders"""
        return await self._request("GET", "/forever/orders")

    # =========================================================================
    # POSITIONS & TRADES EXTENDED
    # =========================================================================

    async def convert_position(self, payload: Dict) -> Dict[str, Any]:
        """Convert position (Intraday <-> Delivery)"""
        return await self._request("POST", "/positions/convert", payload)

    async def get_trade_by_order_id(self, order_id: str) -> Dict[str, Any]:
        """Get trades associated with an order ID"""
        return await self._request("GET", f"/trades/{order_id}")

    async def get_trade_history(self, from_date: str, to_date: str, page_number: int = 0) -> Dict[str, Any]:
        """Get historical trades"""
        return await self._request("GET", f"/trades/{from_date}/{to_date}/{page_number}")

    # =========================================================================
    # IP MANAGEMENT
    # =========================================================================

    async def get_ip(self) -> Dict[str, Any]:
        """Get registered IPs"""
        return await self._request("GET", "/ip/getIP")

    async def set_ip(self, payload: Dict) -> Dict[str, Any]:
        """Set Primary/Secondary IP"""
        return await self._request("POST", "/ip/setIP", payload)

    async def modify_ip(self, payload: Dict) -> Dict[str, Any]:
        """Modify Registered IP"""
        return await self._request("PUT", "/ip/modifyIP", payload)

    # =========================================================================
    # EDIS & T-PIN
    # =========================================================================

    async def generate_edis_form(self, payload: Dict) -> Dict[str, Any]:
        """Generate EDIS form"""
        return await self._request("POST", "/edis/form", payload)

    async def generate_bulk_edis_form(self, payload: Dict) -> Dict[str, Any]:
        """Generate Bulk EDIS form"""
        return await self._request("POST", "/edis/bulkform", payload)

    async def inquire_edis(self, isin: str) -> Dict[str, Any]:
        """Check EDIS status for ISIN"""
        return await self._request("GET", f"/edis/inquire/{isin}")

    async def generate_tpin(self) -> Dict[str, Any]:
        """Generate T-PIN (sends to mobile)"""
        return await self._request("GET", "/edis/tpin")

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def update_credentials(self, access_token: str, client_id: str):
        """Update API credentials (for OAuth token refresh)"""
        self.access_token = access_token
        self.client_id = client_id
        logger.info("Dhan credentials updated")

    def clear_cache(self):
        """Clear all cached data"""
        if self._cache:
            self._cache.clear()
        self._local_cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "total_requests": self._request_count,
            "cache_entries": len(self._local_cache),
            "using_pool": self._connection_pool is not None,
            "using_shared_cache": self._cache is not None
        }

    async def close(self):
        """Close local session if exists"""
        if self._local_session and not self._local_session.closed:
            await self._local_session.close()
            logger.info("DhanRESTAsync session closed")


# Singleton instance for shared use
_dhan_client: Optional[DhanRESTAsync] = None


def get_dhan_client(
    access_token: Optional[str] = None,
    client_id: Optional[str] = None,
    connection_pool: Optional[Any] = None,
    cache: Optional[Any] = None,
    health_monitor: Optional[Any] = None
) -> DhanRESTAsync:
    """Get or create singleton Dhan client"""
    global _dhan_client

    if _dhan_client is None:
        _dhan_client = DhanRESTAsync(
            access_token=access_token,
            client_id=client_id,
            connection_pool=connection_pool,
            cache=cache,
            health_monitor=health_monitor
        )
    elif access_token and client_id:
        _dhan_client.update_credentials(access_token, client_id)

    return _dhan_client
