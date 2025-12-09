"""
InfinityAI.Pro Performance Optimization Module
Provides caching, connection pooling, rate limiting, and health monitoring
for 24/7 high-performance operation.
"""

from .cache import CacheManager, cache_response, get_cache_manager
from .connection_pool import ConnectionPoolManager, get_http_client, get_aiohttp_session
from .rate_limiter import RateLimiter, RateLimitConfig, get_rate_limiter, adaptive_rate_limit
from .health_monitor import (
    HealthMonitor,
    CircuitBreaker,
    CircuitBreakerConfig,
    get_health_monitor,
    with_circuit_breaker
)

__all__ = [
    # Cache
    'CacheManager',
    'cache_response',
    'get_cache_manager',
    # Connection Pool
    'ConnectionPoolManager',
    'get_http_client',
    'get_aiohttp_session',
    # Rate Limiter
    'RateLimiter',
    'RateLimitConfig',
    'get_rate_limiter',
    'adaptive_rate_limit',
    # Health Monitor
    'HealthMonitor',
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'get_health_monitor',
    'with_circuit_breaker',
]
