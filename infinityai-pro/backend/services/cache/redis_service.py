"""
Redis caching service for InfinityAI.Pro
Provides high-performance caching for API responses, market data, and AI computations
"""

import redis
import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import os
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.default_ttl = int(os.getenv("REDIS_TTL", "3600"))  # 1 hour default
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected successfully to {self.redis_url}")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and available"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _serialize_key(self, key: str, prefix: str = "") -> str:
        """Create a standardized cache key"""
        if prefix:
            key = f"{prefix}:{key}"
        return f"infinityai:{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for Redis storage"""
        try:
            # Try JSON first (faster, human readable)
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(value, default=str).encode('utf-8')
            else:
                # Fall back to pickle for complex objects
                return pickle.dumps(value)
        except Exception as e:
            logger.warning(f"Failed to serialize value: {e}")
            return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from Redis storage"""
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(value)
            except Exception as e:
                logger.error(f"Failed to deserialize value: {e}")
                return None
    
    def get(self, key: str, prefix: str = "") -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected():
            return None
        
        try:
            redis_key = self._serialize_key(key, prefix)
            value = self.redis_client.get(redis_key)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: str = "") -> bool:
        """Set value in cache with TTL"""
        if not self.is_connected():
            return False
        
        try:
            redis_key = self._serialize_key(key, prefix)
            serialized_value = self._serialize_value(value)
            ttl = ttl or self.default_ttl
            
            result = self.redis_client.setex(redis_key, ttl, serialized_value)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str, prefix: str = "") -> bool:
        """Delete key from cache"""
        if not self.is_connected():
            return False
        
        try:
            redis_key = self._serialize_key(key, prefix)
            result = self.redis_client.delete(redis_key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def exists(self, key: str, prefix: str = "") -> bool:
        """Check if key exists in cache"""
        if not self.is_connected():
            return False
        
        try:
            redis_key = self._serialize_key(key, prefix)
            return bool(self.redis_client.exists(redis_key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int, prefix: str = "") -> bool:
        """Set TTL for existing key"""
        if not self.is_connected():
            return False
        
        try:
            redis_key = self._serialize_key(key, prefix)
            return bool(self.redis_client.expire(redis_key, ttl))
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    def get_many(self, keys: List[str], prefix: str = "") -> Dict[str, Any]:
        """Get multiple values from cache"""
        if not self.is_connected() or not keys:
            return {}
        
        try:
            redis_keys = [self._serialize_key(key, prefix) for key in keys]
            values = self.redis_client.mget(redis_keys)
            
            result = {}
            for i, (original_key, value) in enumerate(zip(keys, values)):
                if value is not None:
                    result[original_key] = self._deserialize_value(value)
            
            return result
        except Exception as e:
            logger.error(f"Redis MGET error: {e}")
            return {}
    
    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None, prefix: str = "") -> bool:
        """Set multiple values in cache"""
        if not self.is_connected() or not data:
            return False
        
        try:
            pipe = self.redis_client.pipeline()
            ttl = ttl or self.default_ttl
            
            for key, value in data.items():
                redis_key = self._serialize_key(key, prefix)
                serialized_value = self._serialize_value(value)
                pipe.setex(redis_key, ttl, serialized_value)
            
            results = pipe.execute()
            return all(results)
        except Exception as e:
            logger.error(f"Redis MSET error: {e}")
            return False
    
    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_connected():
            return 0
        
        try:
            redis_pattern = self._serialize_key(pattern)
            keys = self.redis_client.keys(redis_pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis FLUSH_PATTERN error for {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        if not self.is_connected():
            return {"status": "disconnected"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace": {db: info.get(f"db{db}", {}) for db in range(16) if f"db{db}" in info}
            }
        except Exception as e:
            logger.error(f"Redis STATS error: {e}")
            return {"status": "error", "error": str(e)}


# Global cache instance
cache = RedisCache()


def cache_result(ttl: int = 3600, prefix: str = "", key_func=None):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix
        key_func: Function to generate cache key (default: use function name + args hash)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                args_str = str(args) + str(sorted(kwargs.items()))
                key_hash = hashlib.md5(args_str.encode()).hexdigest()
                cache_key = f"{func.__name__}:{key_hash}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key, prefix)
            if cached_result is not None:
                logger.debug(f"Cache HIT for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache MISS for {cache_key}")
            result = func(*args, **kwargs)
            
            # Only cache successful results (not None, not errors)
            if result is not None:
                cache.set(cache_key, result, ttl, prefix)
            
            return result
        
        return wrapper
    return decorator


# Specialized cache functions for common use cases

class MarketDataCache:
    """Specialized caching for market data"""
    
    @staticmethod
    def get_quote(symbol: str) -> Optional[Dict]:
        """Get cached market quote"""
        return cache.get(f"quote:{symbol}", "market")
    
    @staticmethod
    def set_quote(symbol: str, data: Dict, ttl: int = 300) -> bool:
        """Cache market quote (5 minute TTL)"""
        return cache.set(f"quote:{symbol}", data, ttl, "market")
    
    @staticmethod
    def get_historical(symbol: str, interval: str, period: str) -> Optional[List]:
        """Get cached historical data"""
        key = f"historical:{symbol}:{interval}:{period}"
        return cache.get(key, "market")
    
    @staticmethod
    def set_historical(symbol: str, interval: str, period: str, data: List, ttl: int = 3600) -> bool:
        """Cache historical data (1 hour TTL)"""
        key = f"historical:{symbol}:{interval}:{period}"
        return cache.set(key, data, ttl, "market")


class AICache:
    """Specialized caching for AI computations"""
    
    @staticmethod
    def get_sentiment(text_hash: str) -> Optional[Dict]:
        """Get cached sentiment analysis"""
        return cache.get(f"sentiment:{text_hash}", "ai")
    
    @staticmethod
    def set_sentiment(text_hash: str, result: Dict, ttl: int = 86400) -> bool:
        """Cache sentiment analysis (24 hour TTL)"""
        return cache.set(f"sentiment:{text_hash}", result, ttl, "ai")
    
    @staticmethod
    def get_embedding(text_hash: str) -> Optional[List]:
        """Get cached text embedding"""
        return cache.get(f"embedding:{text_hash}", "ai")
    
    @staticmethod
    def set_embedding(text_hash: str, embedding: List, ttl: int = 86400) -> bool:
        """Cache text embedding (24 hour TTL)"""
        return cache.set(f"embedding:{text_hash}", embedding, ttl, "ai")


class TradingCache:
    """Specialized caching for trading data"""
    
    @staticmethod
    def get_positions() -> Optional[List]:
        """Get cached trading positions"""
        return cache.get("positions", "trading")
    
    @staticmethod
    def set_positions(positions: List, ttl: int = 60) -> bool:
        """Cache trading positions (1 minute TTL)"""
        return cache.set("positions", positions, ttl, "trading")
    
    @staticmethod
    def get_orders() -> Optional[List]:
        """Get cached orders"""
        return cache.get("orders", "trading")
    
    @staticmethod
    def set_orders(orders: List, ttl: int = 30) -> bool:
        """Cache orders (30 second TTL)"""
        return cache.set("orders", orders, ttl, "trading")


# Health check function
async def health_check():
    """Check Redis health for monitoring"""
    if cache.is_connected():
        stats = cache.get_stats()
        return {
            "service": "redis_cache",
            "status": "healthy",
            "stats": stats
        }
    else:
        return {
            "service": "redis_cache",
            "status": "unhealthy",
            "error": "Redis connection failed"
        }