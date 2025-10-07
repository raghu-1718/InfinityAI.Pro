"""
Lightweight metrics collector for Engine A using aioredis
"""
import asyncio
import time
from typing import Dict, Any, Optional

import redis.asyncio as aioredis  # type: ignore


class MetricsCollector:
    def __init__(self, redis_client: Optional[aioredis.Redis]):
        self.redis = redis_client

    async def increment(self, name: str, value: int = 1, tags: Dict[str, str] | None = None) -> None:
        if not self.redis:
            return
        key = f"metrics:counter:{name}{':' + ','.join(f'{k}={v}' for k, v in sorted(tags.items())) if tags else ''}"
        await self.redis.incrby(key, value)
        await self.redis.expire(key, 7 * 24 * 3600)

    async def timing(self, name: str, duration_ms: float, tags: Dict[str, str] | None = None) -> None:
        if not self.redis:
            return
        key = f"metrics:timing:{name}{':' + ','.join(f'{k}={v}' for k, v in sorted(tags.items())) if tags else ''}"
        ts = time.time()
        await self.redis.zadd(key, {str(ts): duration_ms})
        await self.redis.expire(key, 7 * 24 * 3600)

    async def get_all_metrics(self) -> Dict[str, Any]:
        return {"status": "ok"}
