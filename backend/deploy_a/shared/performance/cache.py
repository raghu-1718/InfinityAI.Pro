"""
High-Performance In-Memory Cache with TTL Support
Optimized for 24/7 operation with automatic cleanup and memory management.
"""

import asyncio
import logging
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)

class CacheEntry:
    """Individual cache entry with TTL tracking"""
    __slots__ = ['value', 'expires_at', 'hits', 'created_at']

    def __init__(self, value: Any, ttl_seconds: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl_seconds
        self.hits = 0
        self.created_at = time.monotonic()

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at

    def get(self) -> Any:
        self.hits += 1
        return self.value


class CacheManager:
    """
    Thread-safe in-memory cache with TTL, LRU eviction, and automatic cleanup.
    Optimized for high-frequency trading data caching.
    """

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: float = 60.0,
        cleanup_interval: float = 30.0,
        name: str = "default"
    ):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._name = name
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "cleanups": 0,
        }
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False
        logger.info(f"✅ CacheManager '{name}' initialized (max_size={max_size}, ttl={default_ttl}s)")

    async def initialize(self):
        """Start background cleanup task"""
        if not self._initialized:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._initialized = True

    async def _cleanup_loop(self):
        """Background task to remove expired entries"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def _cleanup_expired(self):
        """Remove all expired entries"""
        async with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                self._stats["cleanups"] += 1
                logger.debug(f"Cache '{self._name}': cleaned {len(expired_keys)} expired entries")

    async def _evict_lru(self, count: int = 1):
        """Evict least recently used entries"""
        if not self._cache:
            return

        # Sort by hits (LFU) and creation time (LRU)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: (x[1].hits, x[1].created_at)
        )

        for key, _ in sorted_entries[:count]:
            del self._cache[key]
            self._stats["evictions"] += 1

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return entry.get()

    async def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache with TTL"""
        ttl = ttl or self._default_ttl

        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                await self._evict_lru(max(1, self._max_size // 10))

            self._cache[key] = CacheEntry(value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self):
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            logger.info(f"Cache '{self._name}' cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        return {
            "name": self._name,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2%}",
            "evictions": self._stats["evictions"],
            "cleanups": self._stats["cleanups"],
        }

    async def shutdown(self):
        """Graceful shutdown"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Cache '{self._name}' shutdown complete")


# Global cache instances
_caches: Dict[str, CacheManager] = {}

def get_cache_manager(
    name: str = "default",
    max_size: int = 10000,
    default_ttl: float = 60.0
) -> CacheManager:
    """Get or create a cache manager instance"""
    if name not in _caches:
        _caches[name] = CacheManager(
            max_size=max_size,
            default_ttl=default_ttl,
            name=name
        )
    return _caches[name]


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cache_response(
    ttl: float = 60.0,
    cache_name: str = "api_responses",
    key_prefix: str = ""
):
    """
    Decorator to cache async function responses.

    Usage:
        @cache_response(ttl=300, key_prefix="signals")
        async def get_signals(symbol: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager(cache_name, default_ttl=ttl)

            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached = await cache.get(key)
            if cached is not None:
                return cached

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result

        return wrapper
    return decorator


# Specialized caches for different data types
MARKET_DATA_CACHE = get_cache_manager("market_data", max_size=5000, default_ttl=5.0)
SIGNALS_CACHE = get_cache_manager("signals", max_size=1000, default_ttl=30.0)
USER_SETTINGS_CACHE = get_cache_manager("user_settings", max_size=2000, default_ttl=300.0)
API_RESPONSE_CACHE = get_cache_manager("api_responses", max_size=10000, default_ttl=60.0)
