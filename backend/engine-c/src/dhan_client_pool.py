"""
DhanHQ Client Connection Pool with Retry Logic and Health Monitoring

Implements:
- Connection pooling for DhanHQ clients
- Retry logic with exponential backoff
- Circuit breaker pattern
- Health monitoring
- Fallback data caching
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dhanhq import dhanhq
from functools import wraps
import json

logger = logging.getLogger(__name__)

# Connection pool configuration
MAX_POOL_SIZE = 10
POOL_TIMEOUT = 30  # seconds
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1  # seconds
RETRY_MAX_DELAY = 10  # seconds

# Circuit breaker configuration
CIRCUIT_BREAKER_THRESHOLD = 5  # failures before opening
CIRCUIT_BREAKER_TIMEOUT = 60  # seconds before trying again

# Fallback data cache
_fallback_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, float] = {}
FALLBACK_CACHE_TTL = 300  # 5 minutes


class DhanClientPool:
    """Connection pool for DhanHQ clients"""
    
    def __init__(self):
        self.pool: List[Dict[str, Any]] = []
        self.pool_lock = asyncio.Lock()
        self.health_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retries": 0,
            "circuit_breaker_trips": 0
        }
        logger.info("DhanClientPool initialized")
    
    async def get_client(self, client_id: str, access_token: str) -> dhanhq:
        """Get a DhanHQ client from pool or create new one"""
        # CRITICAL: Strip trailing \r\n from credentials to prevent HTTP header errors
        client_id = str(client_id).strip()
        access_token = str(access_token).strip()

        async with self.pool_lock:
            # Try to find existing client for this user
            for item in self.pool:
                if item["client_id"] == client_id and not item["in_use"]:
                    item["in_use"] = True
                    item["last_used"] = time.time()
                    logger.info(f"♻️ Reusing pooled client for {client_id}")
                    return item["client"]
            
            # Create new client if pool not full
            if len(self.pool) < MAX_POOL_SIZE:
                client = dhanhq(client_id, access_token)
                pool_item = {
                    "client_id": client_id,
                    "client": client,
                    "in_use": True,
                    "created_at": time.time(),
                    "last_used": time.time()
                }
                self.pool.append(pool_item)
                logger.info(f"➕ Created new pooled client for {client_id} (pool size: {len(self.pool)})")
                return client
            
            # Pool full, wait for available client or create temporary
            logger.warning(f"⚠️ Pool full ({len(self.pool)}), creating temporary client")
            return dhanhq(client_id, access_token)
    
    async def release_client(self, client_id: str):
        """Release a client back to the pool"""
        async with self.pool_lock:
            for item in self.pool:
                if item["client_id"] == client_id and item["in_use"]:
                    item["in_use"] = False
                    logger.info(f"✅ Released client for {client_id}")
                    return
    
    async def cleanup_idle_clients(self, max_idle_time: int = 600):
        """Remove clients that haven't been used recently"""
        async with self.pool_lock:
            current_time = time.time()
            initial_size = len(self.pool)
            self.pool = [
                item for item in self.pool
                if not item["in_use"] or (current_time - item["last_used"]) < max_idle_time
            ]
            removed = initial_size - len(self.pool)
            if removed > 0:
                logger.info(f"🧹 Cleaned up {removed} idle clients")


class CircuitBreaker:
    """Circuit breaker for DhanHQ API calls"""
    
    def __init__(self, threshold: int = CIRCUIT_BREAKER_THRESHOLD, timeout: int = CIRCUIT_BREAKER_TIMEOUT):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self):
        """Record successful API call"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("🔓 Circuit breaker CLOSED (recovered)")
    
    def record_failure(self):
        """Record failed API call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.threshold and self.state == "CLOSED":
            self.state = "OPEN"
            logger.error(f"🔒 Circuit breaker OPEN (failures: {self.failure_count})")
    
    def can_attempt(self) -> bool:
        """Check if request can be attempted"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("🔓 Circuit breaker HALF_OPEN (trying again)")
                return True
            return False
        
        # HALF_OPEN state
        return True


# Global instances
_client_pool = DhanClientPool()
_circuit_breaker = CircuitBreaker()


def with_retry_and_fallback(fallback_key: Optional[str] = None):
    """Decorator for retry logic and fallback data"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check circuit breaker
            if not _circuit_breaker.can_attempt():
                logger.warning("⚠️ Circuit breaker OPEN, using fallback data")
                if fallback_key and fallback_key in _fallback_cache:
                    cache_age = time.time() - _cache_timestamps.get(fallback_key, 0)
                    logger.info(f"📦 Returning fallback data (age: {cache_age:.1f}s)")
                    return {
                        **_fallback_cache[fallback_key],
                        "_fallback": True,
                        "_cache_age": cache_age
                    }
                raise Exception("Circuit breaker OPEN and no fallback data available")
            
            # Retry logic
            last_exception = None
            for attempt in range(RETRY_MAX_ATTEMPTS):
                try:
                    _client_pool.health_stats["total_requests"] += 1
                    
                    # Call the actual function
                    result = await func(*args, **kwargs)
                    
                    # Success
                    _client_pool.health_stats["successful_requests"] += 1
                    _circuit_breaker.record_success()
                    
                    # Cache result as fallback
                    if fallback_key:
                        _fallback_cache[fallback_key] = result
                        _cache_timestamps[fallback_key] = time.time()
                    
                    return result
                
                except Exception as e:
                    last_exception = e
                    _client_pool.health_stats["failed_requests"] += 1
                    
                    if attempt < RETRY_MAX_ATTEMPTS - 1:
                        # Calculate exponential backoff delay
                        delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                        logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        _client_pool.health_stats["retries"] += 1
                        await asyncio.sleep(delay)
                    else:
                        # Final attempt failed
                        logger.error(f"❌ All {RETRY_MAX_ATTEMPTS} attempts failed: {e}")
                        _circuit_breaker.record_failure()
                        
                        # Try fallback data
                        if fallback_key and fallback_key in _fallback_cache:
                            cache_age = time.time() - _cache_timestamps.get(fallback_key, 0)
                            if cache_age < FALLBACK_CACHE_TTL:
                                logger.info(f"📦 Returning fallback data (age: {cache_age:.1f}s)")
                                return {
                                    **_fallback_cache[fallback_key],
                                    "_fallback": True,
                                    "_cache_age": cache_age
                                }
                        
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    return decorator


async def get_dhan_client_with_pool(client_id: str, access_token: str) -> dhanhq:
    """Get DhanHQ client from pool"""
    return await _client_pool.get_client(client_id, access_token)


async def release_dhan_client(client_id: str):
    """Release DhanHQ client back to pool"""
    await _client_pool.release_client(client_id)


def get_health_stats() -> Dict[str, Any]:
    """Get health statistics"""
    stats = _client_pool.health_stats.copy()
    stats["circuit_breaker_state"] = _circuit_breaker.state
    stats["circuit_breaker_failures"] = _circuit_breaker.failure_count
    stats["pool_size"] = len(_client_pool.pool)
    stats["pool_in_use"] = sum(1 for item in _client_pool.pool if item["in_use"])
    
    if stats["total_requests"] > 0:
        stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
    else:
        stats["success_rate"] = 0.0
    
    return stats


# Example usage with parallel API calls
@with_retry_and_fallback(fallback_key="fund_limits")
async def get_fund_limits_with_retry(client: dhanhq) -> Dict[str, Any]:
    """Get fund limits with retry logic"""
    return await asyncio.to_thread(client.get_fund_limits)


@with_retry_and_fallback(fallback_key="holdings")
async def get_holdings_with_retry(client: dhanhq) -> List[Dict[str, Any]]:
    """Get holdings with retry logic"""
    return await asyncio.to_thread(client.get_holdings)


@with_retry_and_fallback(fallback_key="positions")
async def get_positions_with_retry(client: dhanhq) -> List[Dict[str, Any]]:
    """Get positions with retry logic"""
    return await asyncio.to_thread(client.get_positions)


async def get_all_account_data_parallel(client: dhanhq) -> Dict[str, Any]:
    """Fetch all account data in parallel"""
    start_time = time.time()
    
    # Run all API calls in parallel
    results = await asyncio.gather(
        get_fund_limits_with_retry(client),
        get_holdings_with_retry(client),
        get_positions_with_retry(client),
        return_exceptions=True
    )
    
    elapsed = time.time() - start_time
    logger.info(f"⚡ Parallel fetch completed in {elapsed:.2f}s")
    
    # Process results
    fund_limits = results[0] if not isinstance(results[0], Exception) else None
    holdings = results[1] if not isinstance(results[1], Exception) else None
    positions = results[2] if not isinstance(results[2], Exception) else None
    
    return {
        "fund_limits": fund_limits,
        "holdings": holdings,
        "positions": positions,
        "fetch_time": elapsed,
        "timestamp": datetime.utcnow().isoformat()
    }
