"""
Performance optimization configuration for InfinityAI.Pro services
Optimized for sub-1s response times
"""
import asyncio
import aiohttp
from typing import Optional


class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        # Connection pool settings for optimal performance
        self.connector_settings = {
            'limit': 100,  # Max connections
            'limit_per_host': 30,  # Max per host
            'ttl_dns_cache': 300,  # DNS cache TTL
            'use_dns_cache': True,
        }
        
        # Timeout settings
        self.timeout_settings = aiohttp.ClientTimeout(
            total=3.0,  # 3s max total time
            connect=1.0,  # 1s connection timeout
            sock_read=2.0,  # 2s read timeout
        )
    
    def get_optimized_session(self) -> aiohttp.ClientSession:
        """Get optimized aiohttp session"""
        connector = aiohttp.TCPConnector(**self.connector_settings)
        return aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout_settings,
            headers={
                'User-Agent': 'InfinityAI-Pro/1.0',
                'Connection': 'keep-alive'
            }
        )


# Async caching decorator
def async_cache(ttl: int = 300):
    """Simple async cache decorator with TTL"""
    cache = {}
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            key = str(args) + str(sorted(kwargs.items()))
            
            # Check cache
            if key in cache:
                value, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return value
            
            # Execute function
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            
            # Cleanup old entries (simple approach)
            if len(cache) > 1000:
                current_time = time.time()
                cache.clear()  # Simple cleanup
            
            return result
        return wrapper
    return decorator


# Global performance optimizer instance
optimizer = PerformanceOptimizer()