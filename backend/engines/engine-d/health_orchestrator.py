import asyncio
import aiohttp
import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class HealthOrchestrator:
    def __init__(self):
        self.engines = {
            "A": "https://engine-a-market-data-prod-573866363639.us-central1.run.app",
            "B": "https://engine-b-ai-ml-prod-573866363639.us-central1.run.app", 
            "C": "https://engine-c-execution-prod-573866363639.us-central1.run.app",
            "D": "https://engine-d-chatbot-prod-573866363639.us-central1.run.app",
            "ULTRA": "https://engine-ultra-aggressive-prod-573866363639.us-central1.run.app"
        }
        self.timeout = 3.0
        self.cache_duration = 30  # Cache results for 30 seconds
        self._health_cache = {}
        self._last_check = 0

    async def check_engine_health(self, session: aiohttp.ClientSession, name: str, url: str) -> tuple:
        """Check individual engine health"""
        start_time = time.time()
        try:
            async with session.get(f"{url}/health", timeout=self.timeout) as response:
                response_time = round((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        return name, {
                            "healthy": True,
                            "status": "operational",
                            "response_time_ms": response_time,
                            "details": data.get("service", f"engine-{name.lower()}")
                        }
                    except:
                        return name, {
                            "healthy": True,
                            "status": "responding",
                            "response_time_ms": response_time,
                            "details": "health_ok"
                        }
                else:
                    return name, {
                        "healthy": False,
                        "status": f"http_{response.status}",
                        "response_time_ms": response_time,
                        "details": "bad_response"
                    }
                    
        except asyncio.TimeoutError:
            return name, {
                "healthy": False,
                "status": "timeout",
                "response_time_ms": int(self.timeout * 1000),
                "details": "request_timeout"
            }
        except Exception as e:
            return name, {
                "healthy": False,
                "status": "error",
                "response_time_ms": round((time.time() - start_time) * 1000),
                "details": str(e)[:50]
            }

    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get health status of all engines with caching"""
        current_time = time.time()
        
        # Return cached result if still valid
        if (current_time - self._last_check) < self.cache_duration and self._health_cache:
            return self._health_cache

        # Check all engines concurrently
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.check_engine_health(session, name, url) 
                for name, url in self.engines.items()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Process results
        engine_health = {}
        healthy_count = 0
        total_response_time = 0
        
        for result in results:
            if isinstance(result, tuple):
                name, health_data = result
                engine_health[name] = health_data
                if health_data["healthy"]:
                    healthy_count += 1
                total_response_time += health_data["response_time_ms"]
            else:
                logger.error(f"Health check error: {result}")

        # Calculate summary metrics
        total_engines = len(self.engines)
        health_percentage = round((healthy_count / total_engines) * 100) if total_engines > 0 else 0
        avg_response_time = round(total_response_time / total_engines) if total_engines > 0 else 0

        # Build comprehensive response
        comprehensive_health = {
            "timestamp": current_time,
            "summary": {
                "healthy_engines": healthy_count,
                "total_engines": total_engines,
                "health_percentage": health_percentage,
                "avg_response_time_ms": avg_response_time,
                "overall_status": "healthy" if health_percentage >= 60 else "degraded" if health_percentage >= 40 else "critical"
            },
            "engines": engine_health,
            "system_status": {
                "orchestration": "active",
                "monitoring": "enabled",
                "last_update": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(current_time))
            }
        }

        # Cache the result
        self._health_cache = comprehensive_health
        self._last_check = current_time
        
        return comprehensive_health

    def get_simple_health_status(self) -> Dict[str, bool]:
        """Get simple boolean health status for backward compatibility"""
        if not self._health_cache:
            return {name: False for name in self.engines.keys()}
        
        return {
            name: data["healthy"] 
            for name, data in self._health_cache.get("engines", {}).items()
        }

# Global instance
health_orchestrator = HealthOrchestrator()