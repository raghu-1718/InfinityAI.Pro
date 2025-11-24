import asyncio
import aiohttp
import time
from typing import Dict, Any, Tuple
import logging
import os

logger = logging.getLogger(__name__)

class HealthOrchestrator:
    def __init__(self):
        self.engines = {
            "A": os.getenv("ENGINE_A_URL", "http://localhost:8001"),
            "B": os.getenv("ENGINE_B_URL", "http://localhost:8002"),
            "C": os.getenv("ENGINE_C_URL", "http://localhost:8003"),
        }
        self.timeout = 3.0
        self.cache_duration = 30
        self._health_cache = {}
        self._last_check = 0.0

    async def check_engine_health(self, session: aiohttp.ClientSession, name: str, url: str) -> Tuple[str, Dict[str, Any]]:
        start_time = time.time()
        try:
            async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                response_time = round((time.time() - start_time) * 1000)
                if response.status == 200:
                    try:
                        data = await response.json()
                    except Exception:
                        data = {"service": "health_ok"}
                    return name, {"healthy": True, "status": "operational", "response_time_ms": response_time, "details": data.get("service", f"engine-{name.lower()}")}
                else:
                    return name, {"healthy": False, "status": f"http_{response.status}", "response_time_ms": response_time, "details": "bad_response"}
        except asyncio.TimeoutError:
            return name, {"healthy": False, "status": "timeout", "response_time_ms": int(self.timeout * 1000), "details": "request_timeout"}
        except Exception as e:
            return name, {"healthy": False, "status": "error", "response_time_ms": round((time.time() - start_time) * 1000), "details": str(e)[:50]}

    async def get_comprehensive_health(self) -> Dict[str, Any]:
        current_time = time.time()
        if (current_time - self._last_check) < self.cache_duration and self._health_cache:
            return self._health_cache

        async with aiohttp.ClientSession() as session:
            tasks = [self.check_engine_health(session, name, url) for name, url in self.engines.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        engine_health = {}
        healthy_count = 0
        total_response_time = 0

        for result in results:
            if isinstance(result, tuple):
                name, health_data = result
                engine_health[name] = health_data
                if health_data.get("healthy"):
                    healthy_count += 1
                total_response_time += health_data.get("response_time_ms", 0)
            else:
                logger.error(f"Health check error: {result}")

        total_engines = len(self.engines)
        health_percentage = round((healthy_count / total_engines) * 100) if total_engines > 0 else 0
        avg_response_time = round(total_response_time / total_engines) if total_engines > 0 else 0

        if health_percentage >= 60:
            overall_status = "healthy"
        elif health_percentage >= 40:
            overall_status = "degraded"
        else:
            overall_status = "critical"

        comprehensive_health = {
            "timestamp": current_time,
            "summary": {"healthy_engines": healthy_count, "total_engines": total_engines, "health_percentage": health_percentage, "avg_response_time_ms": avg_response_time, "overall_status": overall_status},
            "engines": engine_health,
            "system_status": {"orchestration": "active", "monitoring": "enabled", "last_update": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(current_time))}
        }

        self._health_cache = comprehensive_health
        self._last_check = current_time
        return comprehensive_health

    def get_simple_health_status(self) -> Dict[str, bool]:
        if not self._health_cache:
            return dict.fromkeys(self.engines.keys(), False)
        return {name: data.get("healthy", False) for name, data in self._health_cache.get("engines", {}).items()}

# Global instance
health_orchestrator = HealthOrchestrator()
