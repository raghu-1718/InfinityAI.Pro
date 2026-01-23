"""
Multi-Provider Market Data Cache with Redis
Supports: DhanHQ, Yahoo Finance, Alpha Vantage, MarketStack, Massive (Polygon)
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

# Try importing Redis
try:
    import redis
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("⚠️ redis package not installed. Install: pip install redis")


class DataSource(Enum):
    """Market data sources in priority order"""
    DHAN_HQ = "dhan_hq"          # Primary: DhanHQ real-time API
    ALPHA_VANTAGE = "alpha_vantage"  # Secondary: Alpha Vantage
    MARKET_STACK = "marketstack"  # Tertiary: MarketStack
    MASSIVE = "massive"          # Quaternary: Massive (Polygon)
    YAHOO_FINANCE = "yahoo"      # Quinary: Yahoo Finance (free, rate-limited)
    CACHE_STALE = "cache_stale"  # Stale cache (better than nothing)
    SYNTHETIC = "synthetic"      # Last resort: synthetic data


class MarketDataCache:
    """
    Redis-backed caching layer for market data with multi-provider support.

    Features:
    - TTL-based caching (default 5 minutes)
    - Source tracking (which provider fetched data)
    - Stale data fallback (if all sources fail)
    - Async operations for performance
    - Connection pooling

    Usage:
        cache = MarketDataCache()

        # Try to get from cache
        data = await cache.get_quote("RELIANCE.NS")

        # Cache miss, fetch from provider
        if not data:
            data = await fetch_from_provider("RELIANCE.NS")
            await cache.set_quote("RELIANCE.NS", data, source=DataSource.DHAN_HQ)
    """

    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = 6379,
        redis_db: int = 0,
        default_ttl: int = 300,  # 5 minutes
        stale_ttl: int = 3600,  # 1 hour (for stale fallback)
    ):
        """
        Initialize market data cache.

        Args:
            redis_host: Redis server hostname (default from env REDIS_HOST)
            redis_port: Redis server port (default 6379)
            redis_db: Redis database number (default 0)
            default_ttl: Cache TTL in seconds (default 300 = 5 min)
            stale_ttl: Stale data TTL in seconds (default 3600 = 1 hour)
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.default_ttl = default_ttl
        self.stale_ttl = stale_ttl

        # Sync client (for synchronous operations)
        self.sync_client: Optional[redis.Redis] = None

        # Async client (preferred for async operations)
        self.async_client: Optional[aioredis.Redis] = None

        # In-memory fallback (if Redis unavailable)
        self.memory_cache: Dict[str, tuple] = {}
        self.cache_enabled = HAS_REDIS and self.redis_host != "localhost"

        if self.cache_enabled:
            try:
                self._init_sync_client()
                logger.info(f"✅ Redis cache connected: {self.redis_host}:{self.redis_port} (db={self.redis_db})")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory cache.")
                self.cache_enabled = False
        else:
            logger.warning("⚠️ Redis not configured. Using in-memory cache only.")

    def _init_sync_client(self):
        """Initialize synchronous Redis client with connection pooling"""
        if not HAS_REDIS:
            return

        self.sync_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Test connection
        self.sync_client.ping()

    async def _get_async_client(self) -> aioredis.Redis:
        """Get or create async Redis client"""
        if not self.async_client:
            if not HAS_REDIS:
                raise RuntimeError("Redis not available")

            self.async_client = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}",
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return self.async_client

    # ========================================================================
    # QUOTE CACHING (Real-time market quotes)
    # ========================================================================

    async def get_quote(
        self,
        symbol: str,
        allow_stale: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached quote for symbol.

        Args:
            symbol: Trading symbol (e.g., "RELIANCE.NS", "NIFTY")
            allow_stale: If True, return stale data if fresh cache miss

        Returns:
            Quote data dict or None if not cached
        """
        key = f"quote:{symbol}"

        # Try fresh cache
        if self.cache_enabled:
            try:
                client = await self._get_async_client()
                cached = await client.get(key)
                if cached:
                    data = json.loads(cached)
                    logger.debug(f"📊 Cache HIT (fresh): {symbol} from {data.get('source')}")
                    return data
            except Exception as e:
                logger.warning(f"⚠️ Redis get failed: {e}")

        # Try in-memory cache
        if key in self.memory_cache:
            data, cached_time = self.memory_cache[key]
            age = (datetime.now() - cached_time).total_seconds()
            if age < self.default_ttl:
                logger.debug(f"📊 Memory cache HIT: {symbol}")
                return data

        # Try stale cache as fallback
        if allow_stale:
            stale_key = f"stale:{symbol}"
            if self.cache_enabled:
                try:
                    client = await self._get_async_client()
                    cached = await client.get(stale_key)
                    if cached:
                        data = json.loads(cached)
                        logger.warning(f"⚠️ Using STALE cache: {symbol} (source: {data.get('source')})")
                        data['source'] = DataSource.CACHE_STALE.value
                        data['is_stale'] = True
                        return data
                except Exception as e:
                    logger.warning(f"⚠️ Stale cache read failed: {e}")

        logger.debug(f"📊 Cache MISS: {symbol}")
        return None

    async def set_quote(
        self,
        symbol: str,
        data: Dict[str, Any],
        source: DataSource = DataSource.DHAN_HQ,
        ttl: Optional[int] = None
    ):
        """
        Cache quote data for symbol.

        Args:
            symbol: Trading symbol
            data: Quote data to cache
            source: Data source (for tracking)
            ttl: Custom TTL in seconds (default: self.default_ttl)
        """
        ttl = ttl or self.default_ttl
        key = f"quote:{symbol}"
        stale_key = f"stale:{symbol}"

        # Add metadata
        cache_data = {
            **data,
            "source": source.value,
            "cached_at": datetime.now().isoformat(),
            "is_stale": False,
        }

        # Write to Redis
        if self.cache_enabled:
            try:
                client = await self._get_async_client()

                # Set fresh cache with TTL
                await client.setex(
                    key,
                    ttl,
                    json.dumps(cache_data)
                )

                # Set stale cache with longer TTL (fallback)
                await client.setex(
                    stale_key,
                    self.stale_ttl,
                    json.dumps(cache_data)
                )

                logger.debug(f"✅ Cached quote: {symbol} (source: {source.value}, TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"⚠️ Redis set failed: {e}")

        # Write to in-memory cache
        self.memory_cache[key] = (cache_data, datetime.now())

    # ========================================================================
    # HISTORICAL DATA CACHING (OHLCV candles)
    # ========================================================================

    async def get_historical(
        self,
        symbol: str,
        days: int = 365,
        interval: str = "1d"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached historical data (OHLCV candles).

        Args:
            symbol: Trading symbol
            days: Number of days of history
            interval: Data interval (1d, 1h, 15m, etc.)

        Returns:
            Historical data dict or None
        """
        key = f"historical:{symbol}:{days}d:{interval}"

        if self.cache_enabled:
            try:
                client = await self._get_async_client()
                cached = await client.get(key)
                if cached:
                    data = json.loads(cached)
                    logger.debug(f"📈 Historical cache HIT: {symbol} ({days}d, {interval})")
                    return data
            except Exception as e:
                logger.warning(f"⚠️ Redis historical get failed: {e}")

        # Try in-memory cache
        if key in self.memory_cache:
            data, cached_time = self.memory_cache[key]
            age = (datetime.now() - cached_time).total_seconds()
            if age < self.default_ttl:
                return data

        return None

    async def set_historical(
        self,
        symbol: str,
        data: Dict[str, Any],
        days: int = 365,
        interval: str = "1d",
        source: DataSource = DataSource.DHAN_HQ,
        ttl: Optional[int] = None
    ):
        """
        Cache historical OHLCV data.

        Args:
            symbol: Trading symbol
            data: Historical data dict
            days: Number of days
            interval: Data interval
            source: Data source
            ttl: Custom TTL (default: 5 min)
        """
        ttl = ttl or self.default_ttl
        key = f"historical:{symbol}:{days}d:{interval}"

        cache_data = {
            **data,
            "source": source.value,
            "cached_at": datetime.now().isoformat(),
        }

        if self.cache_enabled:
            try:
                client = await self._get_async_client()
                await client.setex(key, ttl, json.dumps(cache_data))
                logger.debug(f"✅ Cached historical: {symbol} ({days}d, {interval}, source: {source.value})")
            except Exception as e:
                logger.warning(f"⚠️ Redis historical set failed: {e}")

        self.memory_cache[key] = (cache_data, datetime.now())

    # ========================================================================
    # BATCH OPERATIONS (Pre-fetch top symbols)
    # ========================================================================

    async def prefetch_symbols(
        self,
        symbols: List[str],
        fetch_func,
        source: DataSource = DataSource.DHAN_HQ,
        batch_size: int = 10,
        delay_seconds: float = 0.5
    ):
        """
        Pre-fetch and cache data for multiple symbols (batch operation).

        Args:
            symbols: List of symbols to pre-fetch
            fetch_func: Async function to fetch data (symbol) -> data
            source: Data source
            batch_size: Max concurrent fetches
            delay_seconds: Delay between batches (rate limiting)
        """
        import asyncio

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]

            tasks = []
            for symbol in batch:
                # Check if already cached
                cached = await self.get_quote(symbol)
                if cached:
                    logger.debug(f"⏭️  Skipping {symbol} (already cached)")
                    continue

                # Fetch and cache
                async def fetch_and_cache(sym):
                    try:
                        data = await fetch_func(sym)
                        if data:
                            await self.set_quote(sym, data, source=source)
                            logger.info(f"✅ Pre-fetched: {sym}")
                    except Exception as e:
                        logger.warning(f"⚠️ Pre-fetch failed for {sym}: {e}")

                tasks.append(fetch_and_cache(symbol))

            # Execute batch
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"📦 Pre-fetched batch {i//batch_size + 1}: {len(tasks)} symbols")

            # Rate limiting delay
            if i + batch_size < len(symbols):
                await asyncio.sleep(delay_seconds)

    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================

    async def invalidate(self, pattern: str):
        """
        Invalidate cache keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "quote:RELIANCE*")
        """
        if self.cache_enabled:
            try:
                client = await self._get_async_client()
                cursor = 0
                keys = []

                # Scan for matching keys
                while True:
                    cursor, batch = await client.scan(cursor, match=pattern, count=100)
                    keys.extend(batch)
                    if cursor == 0:
                        break

                # Delete keys
                if keys:
                    await client.delete(*keys)
                    logger.info(f"🗑️  Invalidated {len(keys)} keys matching: {pattern}")
            except Exception as e:
                logger.warning(f"⚠️ Invalidation failed: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "enabled": self.cache_enabled,
            "host": self.redis_host,
            "port": self.redis_port,
            "default_ttl": self.default_ttl,
            "memory_cache_size": len(self.memory_cache),
        }

        if self.cache_enabled:
            try:
                client = await self._get_async_client()
                info = await client.info("stats")
                stats["redis"] = {
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "total_connections_received": info.get("total_connections_received", 0),
                }
            except Exception as e:
                logger.warning(f"⚠️ Stats fetch failed: {e}")

        return stats

    async def close(self):
        """Close Redis connections"""
        if self.async_client:
            await self.async_client.close()
        if self.sync_client:
            self.sync_client.close()
