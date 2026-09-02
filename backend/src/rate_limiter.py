"""
Broker Rate Limiter for InfinityAI.Pro
Enforces institutional execution guardrails strictly capped at 9 requests per second.
"""
import asyncio
import time
from typing import Optional

try:
    from aiolimiter import AsyncLimiter
except ImportError:
    AsyncLimiter = None


class BrokerRateLimiter:
    """
    Async rate limiter ensuring no more than `max_rate` calls per `time_period` seconds.
    Standardized to 9 req/s for DhanHQ API compliance.
    Loop-safe: dynamically maintains per-event-loop limiters to avoid cross-loop
    re-use warnings and race conditions across async test and service lifecycles.
    """

    def __init__(self, max_rate: int = 9, time_period: float = 1.0):
        self.max_rate = max_rate
        self.time_period = time_period
        self._limiters = {}
        self._tokens = float(max_rate)
        self._last_refill = time.monotonic()
        self._lock: Optional[asyncio.Lock] = None

    def _get_limiter(self):
        if AsyncLimiter is None:
            return None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        loop_id = id(loop) if loop is not None else 0
        if loop_id not in self._limiters:
            self._limiters[loop_id] = AsyncLimiter(max_rate=self.max_rate, time_period=self.time_period)
        return self._limiters[loop_id]

    async def acquire(self) -> None:
        """Acquire permission to make one request."""
        limiter = self._get_limiter()
        if limiter is not None:
            await limiter.acquire()
            return

        # Fallback async token bucket
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(float(self.max_rate), self._tokens + elapsed * (self.max_rate / self.time_period))
            self._last_refill = now

            if self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) * (self.time_period / self.max_rate)
                await asyncio.sleep(wait_time)
                self._tokens = 0.0
                self._last_refill = time.monotonic()
            else:
                self._tokens -= 1.0

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Global singleton instance for broker outbound calls
broker_rate_limiter = BrokerRateLimiter(max_rate=9, time_period=1.0)
