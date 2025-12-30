"""
Adaptive Rate Limiter for 24/7 Operation
Prevents API rate limit errors with intelligent backoff and request throttling.
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Callable
from functools import wraps
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 10.0
    requests_per_minute: float = 100.0
    burst_size: int = 20
    backoff_base: float = 1.0
    backoff_max: float = 60.0
    backoff_multiplier: float = 2.0


class RateLimiter:
    """
    Token bucket rate limiter with adaptive backoff.
    Supports multiple rate limits (per-second, per-minute, etc.)
    """

    def __init__(self, config: Optional[RateLimitConfig] = None, name: str = "default"):
        self.config = config or RateLimitConfig()
        self.name = name

        # Token bucket state
        self._tokens = float(self.config.burst_size)
        self._last_update = time.monotonic()

        # Request tracking for per-minute limits
        self._request_times: deque = deque(maxlen=1000)

        # Backoff state
        self._consecutive_errors = 0
        self._backoff_until = 0.0

        # Statistics
        self._stats = {
            "requests_total": 0,
            "requests_throttled": 0,
            "rate_limit_hits": 0,
            "current_backoff": 0.0,
        }

        self._lock = asyncio.Lock()
        logger.info(f"✅ RateLimiter '{name}' initialized ({self.config.requests_per_second} req/s)")

    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        # Add tokens based on rate
        self._tokens = min(
            self.config.burst_size,
            self._tokens + elapsed * self.config.requests_per_second
        )

    def _check_minute_limit(self) -> bool:
        """Check if we're within the per-minute limit"""
        now = time.monotonic()
        minute_ago = now - 60.0

        # Remove old request times
        while self._request_times and self._request_times[0] < minute_ago:
            self._request_times.popleft()

        return len(self._request_times) < self.config.requests_per_minute

    async def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire permission to make a request.
        Returns True if allowed, False if timed out.
        """
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            async with self._lock:
                now = time.monotonic()

                # Check if in backoff period
                if now < self._backoff_until:
                    wait_time = min(self._backoff_until - now, 1.0)
                    self._stats["current_backoff"] = self._backoff_until - now
                else:
                    self._stats["current_backoff"] = 0.0

                    # Refill tokens
                    self._refill_tokens()

                    # Check limits
                    if self._tokens >= 1.0 and self._check_minute_limit():
                        self._tokens -= 1.0
                        self._request_times.append(now)
                        self._stats["requests_total"] += 1
                        return True

                    self._stats["requests_throttled"] += 1
                    wait_time = 0.1

            await asyncio.sleep(wait_time)

        return False

    async def record_success(self):
        """Record successful request - reset backoff"""
        async with self._lock:
            self._consecutive_errors = 0
            self._backoff_until = 0.0

    async def record_rate_limit_error(self):
        """Record rate limit error - increase backoff"""
        async with self._lock:
            self._stats["rate_limit_hits"] += 1
            self._consecutive_errors += 1

            # Calculate exponential backoff
            backoff = min(
                self.config.backoff_max,
                self.config.backoff_base * (self.config.backoff_multiplier ** self._consecutive_errors)
            )

            self._backoff_until = time.monotonic() + backoff
            logger.warning(f"RateLimiter '{self.name}': backing off for {backoff:.1f}s")

    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        return {
            "name": self.name,
            "tokens_available": self._tokens,
            "requests_in_window": len(self._request_times),
            **self._stats,
        }


# Global rate limiters for different services
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(
    name: str = "default",
    config: Optional[RateLimitConfig] = None
) -> RateLimiter:
    """Get or create a rate limiter"""
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter(config, name)
    return _rate_limiters[name]


# Pre-configured rate limiters for known APIs
DHAN_RATE_LIMITER = get_rate_limiter(
    "dhan_api",
    RateLimitConfig(requests_per_second=5.0, requests_per_minute=100.0, burst_size=10)
)

ENGINE_B_RATE_LIMITER = get_rate_limiter(
    "engine_b",
    RateLimitConfig(requests_per_second=20.0, requests_per_minute=500.0, burst_size=50)
)

ENGINE_C_RATE_LIMITER = get_rate_limiter(
    "engine_c",
    RateLimitConfig(requests_per_second=20.0, requests_per_minute=500.0, burst_size=50)
)

GEMINI_RATE_LIMITER = get_rate_limiter(
    "gemini_api",
    RateLimitConfig(requests_per_second=2.0, requests_per_minute=60.0, burst_size=5)
)


def adaptive_rate_limit(
    limiter_name: str = "default",
    config: Optional[RateLimitConfig] = None,
    timeout: float = 30.0
):
    """
    Decorator for rate-limited async functions.

    Usage:
        @adaptive_rate_limit("dhan_api")
        async def call_dhan_api():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            limiter = get_rate_limiter(limiter_name, config)

            if not await limiter.acquire(timeout):
                raise Exception(f"Rate limit timeout for {limiter_name}")

            try:
                result = await func(*args, **kwargs)
                await limiter.record_success()
                return result
            except Exception as e:
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str or "too many" in error_str:
                    await limiter.record_rate_limit_error()
                raise

        return wrapper
    return decorator
