"""
InfinityAI.Pro Multi-Cloud Routing Configuration
Handles data flow between AWS Engines C&D and Google Cloud Engines A&B
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"

class EngineType(Enum):
    TRADING = "trading"
    ORCHESTRATION = "orchestration"
    AI_INFERENCE = "ai_inference"
    AI_ANALYTICS = "ai_analytics"

@dataclass
class EngineEndpoint:
    name: str
    provider: CloudProvider
    type: EngineType
    url: str
    health_endpoint: str
    capabilities: List[str]
    weight: int = 1

class MultiCloudRouter:
    def __init__(self):
        self.engines = {
            "engine-c": EngineEndpoint(
                name="engine-c",
                provider=CloudProvider.AWS,
                type=EngineType.TRADING,
                url="http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
                health_endpoint="/health",
                capabilities=["order_execution", "portfolio_management", "risk_management"],
                weight=3
            ),
            "engine-d": EngineEndpoint(
                name="engine-d",
                provider=CloudProvider.AWS,
                type=EngineType.ORCHESTRATION,
                url="http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d",
                health_endpoint="/health",
                capabilities=["user_management", "authentication", "data_aggregation"],
                weight=3
            ),
            "engine-a": EngineEndpoint(
                name="engine-a",
                provider=CloudProvider.GCP,
                type=EngineType.AI_INFERENCE,
                url="https://infinityai-engine-a-573866363639.us-central1.run.app",
                health_endpoint="/health",
                capabilities=["gpt4_inference", "claude3_inference", "gemini_inference"],
                weight=2
            ),
            "engine-b": EngineEndpoint(
                name="engine-b",
                provider=CloudProvider.GCP,
                type=EngineType.AI_ANALYTICS,
                url="https://infinityai-engine-b-573866363639.us-central1.run.app",
                health_endpoint="/health",
                capabilities=["market_analysis", "sentiment_analysis", "pattern_recognition"],
                weight=2
            )
        }
        self.session = None
        self.health_status = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        await self.health_check_all()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check_all(self):
        tasks = []
        for engine_name, engine in self.engines.items():
            tasks.append(self._health_check_engine(engine_name, engine))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            engine_name = list(self.engines.keys())[i]
            self.health_status[engine_name] = not isinstance(result, Exception) and result
    
    async def _health_check_engine(self, engine_name: str, engine: EngineEndpoint) -> bool:
        try:
            url = f"{engine.url}{engine.health_endpoint}"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    def get_engine_for_capability(self, capability: str) -> Optional[EngineEndpoint]:
        candidates = []
        for engine_name, engine in self.engines.items():
            if capability in engine.capabilities and self.health_status.get(engine_name, False):
                candidates.append((engine, engine.weight))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    async def route_request(self, capability: str, method: str, path: str, 
                          data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        engine = self.get_engine_for_capability(capability)
        if not engine:
            raise Exception(f"No available engine for capability: {capability}")
        
        url = f"{engine.url}{path}"
        request_headers = headers or {}
        request_headers.update({
            "X-InfinityAI-Engine": engine.name,
            "X-InfinityAI-Provider": engine.provider.value
        })
        
        async with self.session.request(method=method, url=url, json=data, headers=request_headers) as response:
            result = {
                "status_code": response.status,
                "engine": engine.name,
                "provider": engine.provider.value
            }
            
            if response.content_type == 'application/json':
                result["data"] = await response.json()
            else:
                result["data"] = await response.text()
            
            return result

router = MultiCloudRouter()

async def route_to_trading_engine(method: str, path: str, data: Optional[Dict] = None, 
                                headers: Optional[Dict] = None) -> Dict[str, Any]:
    return await router.route_request("order_execution", method, path, data, headers)

async def route_to_ai_inference(method: str, path: str, data: Optional[Dict] = None,
                              headers: Optional[Dict] = None) -> Dict[str, Any]:
    return await router.route_request("gpt4_inference", method, path, data, headers)

async def route_to_ai_analytics(method: str, path: str, data: Optional[Dict] = None,
                              headers: Optional[Dict] = None) -> Dict[str, Any]:
    return await router.route_request("market_analysis", method, path, data, headers)