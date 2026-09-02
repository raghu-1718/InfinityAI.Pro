import asyncio
import time
import pytest
from backend.src.rate_limiter import BrokerRateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_allows_up_to_nine_per_second():
    """Verify that BrokerRateLimiter allows 9 requests in rapid succession."""
    limiter = BrokerRateLimiter(max_rate=9, time_period=1.0)
    
    start_time = time.monotonic()
    for _ in range(9):
        async with limiter:
            pass
    elapsed = time.monotonic() - start_time
    
    # 9 requests should complete almost instantaneously (< 0.2s)
    assert elapsed < 0.5

@pytest.mark.asyncio
async def test_rate_limiter_throttles_tenth_request():
    """Verify that the 10th request is throttled across the 1-second boundary."""
    limiter = BrokerRateLimiter(max_rate=9, time_period=1.0)
    
    start_time = time.monotonic()
    for _ in range(10):
        async with limiter:
            pass
    elapsed = time.monotonic() - start_time
    
    # The 10th request must wait for the leaky bucket drip (>= 1.0 / 9 = ~0.111s)
    assert elapsed >= 0.10
