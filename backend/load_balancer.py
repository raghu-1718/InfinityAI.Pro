#!/usr/bin/env python3
"""
InfinityAI.Pro Load Balancer Integration
Multi-Cloud Engine Routing and Health Management

This script provides intelligent routing between all four engines:
- Engine A (Azure): Market Data Ingestion
- Engine B (GCP): AI Signal Processing  
- Engine C (AWS): Trade Execution
- Engine D (AWS): AI Chatbot Assistant
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EngineHealth:
    """Engine health status"""
    name: str
    endpoint: str
    status: str
    response_time_ms: float
    last_check: datetime
    consecutive_failures: int
    is_available: bool

@dataclass
class RoutingDecision:
    """Routing decision result"""
    target_engine: str
    target_endpoint: str
    reason: str
    backup_engines: List[str]
    timestamp: datetime

class LoadBalancer:
    """Intelligent load balancer for InfinityAI engines"""
    
    def __init__(self, config_path: str = "load-balancer-config.json"):
        self.config = self._load_config(config_path)
        self.engines = self.config["load_balancer_configuration"]["engines"]
        self.routing_rules = self.config["load_balancer_configuration"]["routing_rules"]
        self.health_status: Dict[str, EngineHealth] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "engine_stats": {}
        }
        
    def _load_config(self, config_path: str) -> Dict:
        """Load load balancer configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    async def initialize(self):
        """Initialize the load balancer"""
        logger.info("Initializing InfinityAI Load Balancer")
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Initialize engine health status
        for engine_id, engine_config in self.engines.items():
            self.health_status[engine_id] = EngineHealth(
                name=engine_config["name"],
                endpoint=engine_config["endpoint"],
                status="unknown",
                response_time_ms=0.0,
                last_check=datetime.now(timezone.utc),
                consecutive_failures=0,
                is_available=False
            )
            
            # Initialize engine metrics
            self.metrics["engine_stats"][engine_id] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "avg_response_time": 0.0
            }
        
        # Initial health check
        await self.check_all_engines_health()
        
        logger.info(f"Load balancer initialized with {len(self.engines)} engines")
    
    async def check_all_engines_health(self) -> Dict[str, EngineHealth]:
        """Check health of all engines"""
        logger.info("Performing health checks on all engines")
        
        health_tasks = [
            self.check_engine_health(engine_id, engine_config)
            for engine_id, engine_config in self.engines.items()
        ]
        
        await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Log summary
        healthy_count = sum(1 for h in self.health_status.values() if h.is_available)
        logger.info(f"Health check complete: {healthy_count}/{len(self.engines)} engines healthy")
        
        return self.health_status
    
    async def check_engine_health(self, engine_id: str, engine_config: Dict) -> None:
        """Check health of a specific engine"""
        endpoint = engine_config["endpoint"]
        health_endpoint = endpoint + engine_config["health_endpoint"]
        
        start_time = time.time()
        
        try:
            async with self.session.get(health_endpoint) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    # Successful health check
                    self.health_status[engine_id] = EngineHealth(
                        name=engine_config["name"],
                        endpoint=endpoint,
                        status="healthy",
                        response_time_ms=response_time,
                        last_check=datetime.now(timezone.utc),
                        consecutive_failures=0,
                        is_available=True
                    )
                    
                    logger.debug(f"✅ {engine_config['name']} ({engine_id}): {response_time:.2f}ms")
                    
                else:
                    # Non-200 status
                    raise Exception(f"HTTP {response.status}")
                    
        except Exception as e:
            # Health check failed
            consecutive_failures = self.health_status[engine_id].consecutive_failures + 1
            
            self.health_status[engine_id] = EngineHealth(
                name=engine_config["name"],
                endpoint=endpoint,
                status=f"unhealthy: {str(e)}",
                response_time_ms=0.0,
                last_check=datetime.now(timezone.utc),
                consecutive_failures=consecutive_failures,
                is_available=False
            )
            
            logger.warning(f"❌ {engine_config['name']} ({engine_id}): {e}")
    
    def route_request(self, path: str, method: str = "GET") -> RoutingDecision:
        """Intelligent routing decision based on path and engine health"""
        
        # Find matching routing rule
        target_engine = None
        backup_engines = []
        reason = "default"
        
        for rule_name, rule_config in self.routing_rules.items():
            if "path_patterns" in rule_config:
                for pattern in rule_config["path_patterns"]:
                    if self._path_matches_pattern(path, pattern):
                        if "target_engine" in rule_config:
                            target_engine = rule_config["target_engine"]
                            backup_engines = rule_config.get("backup_engines", [])
                            reason = f"matched_{rule_name}_rule"
                        elif rule_config.get("all_engines"):
                            # Round robin for health checks
                            target_engine = self._get_next_healthy_engine()
                            reason = f"round_robin_{rule_name}"
                        break
                        
                if target_engine:
                    break
        
        # Default routing if no rule matched
        if not target_engine:
            target_engine = self._get_next_healthy_engine()
            reason = "default_round_robin"
        
        # Check if target engine is healthy
        if target_engine and not self.health_status[target_engine].is_available:
            # Try backup engines
            for backup in backup_engines:
                if self.health_status[backup].is_available:
                    target_engine = backup
                    reason += "_failover_to_backup"
                    break
            else:
                # No backup available, find any healthy engine
                target_engine = self._get_next_healthy_engine()
                reason += "_failover_to_any_healthy"
        
        if not target_engine:
            # No healthy engines available
            target_engine = list(self.engines.keys())[0]  # Fallback to first engine
            reason = "emergency_fallback"
            logger.error("No healthy engines available! Using emergency fallback.")
        
        # Get target endpoint
        target_endpoint = self.engines[target_engine]["endpoint"]
        
        decision = RoutingDecision(
            target_engine=target_engine,
            target_endpoint=target_endpoint,
            reason=reason,
            backup_engines=backup_engines,
            timestamp=datetime.now(timezone.utc)
        )
        
        logger.info(f"Route decision: {path} → {target_engine} ({reason})")
        return decision
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches routing pattern"""
        if pattern.endswith("/*"):
            return path.startswith(pattern[:-2])
        else:
            return path == pattern or path.startswith(pattern + "/")
    
    def _get_next_healthy_engine(self) -> Optional[str]:
        """Get next healthy engine using round robin"""
        healthy_engines = [
            engine_id for engine_id, health in self.health_status.items()
            if health.is_available
        ]
        
        if not healthy_engines:
            return None
        
        # Simple round robin based on request count
        engine_requests = [
            self.metrics["engine_stats"][engine_id]["requests"]
            for engine_id in healthy_engines
        ]
        
        # Choose engine with least requests
        min_requests = min(engine_requests)
        candidates = [
            healthy_engines[i] for i, requests in enumerate(engine_requests)
            if requests == min_requests
        ]
        
        # Return first candidate (deterministic)
        return candidates[0]
    
    async def proxy_request(self, decision: RoutingDecision, path: str, 
                          method: str = "GET", **kwargs) -> Tuple[int, Dict, str]:
        """Proxy request to target engine"""
        
        target_url = decision.target_endpoint + path
        engine_id = decision.target_engine
        
        # Update metrics
        self.metrics["total_requests"] += 1
        self.metrics["engine_stats"][engine_id]["requests"] += 1
        
        start_time = time.time()
        
        try:
            async with self.session.request(method, target_url, **kwargs) as response:
                response_time = (time.time() - start_time) * 1000
                response_text = await response.text()
                response_headers = dict(response.headers)
                
                # Update success metrics
                self.metrics["successful_requests"] += 1
                self.metrics["engine_stats"][engine_id]["successes"] += 1
                
                # Update response time
                engine_stats = self.metrics["engine_stats"][engine_id]
                current_avg = engine_stats["avg_response_time"]
                request_count = engine_stats["requests"]
                
                # Calculate new average
                new_avg = ((current_avg * (request_count - 1)) + response_time) / request_count
                engine_stats["avg_response_time"] = new_avg
                
                logger.debug(f"✅ Proxied {method} {path} to {engine_id}: {response.status} ({response_time:.2f}ms)")
                
                return response.status, response_headers, response_text
                
        except Exception as e:
            # Update failure metrics
            self.metrics["failed_requests"] += 1
            self.metrics["engine_stats"][engine_id]["failures"] += 1
            
            logger.error(f"❌ Proxy error for {method} {path} to {engine_id}: {e}")
            
            # Return error response
            return 502, {"Content-Type": "application/json"}, json.dumps({
                "error": "Engine unavailable",
                "target_engine": engine_id,
                "message": str(e)
            })
    
    async def get_status(self) -> Dict:
        """Get comprehensive load balancer status"""
        
        # Calculate overall metrics
        total_requests = self.metrics["total_requests"]
        if total_requests > 0:
            success_rate = (self.metrics["successful_requests"] / total_requests) * 100
            
            # Calculate overall average response time
            engine_avg_times = [
                stats["avg_response_time"] for stats in self.metrics["engine_stats"].values()
                if stats["requests"] > 0
            ]
            
            overall_avg_time = statistics.mean(engine_avg_times) if engine_avg_times else 0.0
        else:
            success_rate = 0.0
            overall_avg_time = 0.0
        
        status = {
            "load_balancer": {
                "status": "operational",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_engines": len(self.engines),
                "healthy_engines": sum(1 for h in self.health_status.values() if h.is_available),
                "unhealthy_engines": sum(1 for h in self.health_status.values() if not h.is_available)
            },
            "engines": {
                engine_id: {
                    "name": health.name,
                    "status": health.status,
                    "endpoint": health.endpoint,
                    "response_time_ms": health.response_time_ms,
                    "last_check": health.last_check.isoformat(),
                    "consecutive_failures": health.consecutive_failures,
                    "is_available": health.is_available
                }
                for engine_id, health in self.health_status.items()
            },
            "metrics": {
                "total_requests": total_requests,
                "successful_requests": self.metrics["successful_requests"],
                "failed_requests": self.metrics["failed_requests"],
                "success_rate_percent": success_rate,
                "average_response_time_ms": overall_avg_time
            },
            "engine_stats": self.metrics["engine_stats"]
        }
        
        return status
    
    async def start_health_monitoring(self):
        """Start continuous health monitoring"""
        interval = self.config["load_balancer_configuration"]["health_monitoring"]["interval_seconds"]
        
        logger.info(f"Starting health monitoring (interval: {interval}s)")
        
        while True:
            try:
                await self.check_all_engines_health()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)  # Short retry interval on error
    
    async def close(self):
        """Close the load balancer"""
        if self.session:
            await self.session.close()
        logger.info("Load balancer closed")

# FastAPI integration example
def create_fastapi_app():
    """Create FastAPI app with load balancer integration"""
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import Response
    import uvicorn
    
    app = FastAPI(title="InfinityAI Load Balancer", version="1.0.0")
    
    # Global load balancer instance
    lb = LoadBalancer()
    
    @app.on_event("startup")
    async def startup():
        await lb.initialize()
        # Start background health monitoring
        asyncio.create_task(lb.start_health_monitoring())
    
    @app.on_event("shutdown")
    async def shutdown():
        await lb.close()
    
    @app.get("/lb/status")
    async def get_load_balancer_status():
        """Get load balancer status"""
        return await lb.get_status()
    
    @app.get("/lb/health")
    async def health_check():
        """Load balancer health check"""
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_to_engines(request: Request, path: str):
        """Proxy requests to appropriate engines"""
        
        # Make routing decision
        decision = lb.route_request(f"/{path}", request.method)
        
        # Prepare request data
        headers = dict(request.headers)
        query_params = str(request.query_params)
        
        try:
            body = await request.body()
        except:
            body = b""
        
        # Proxy the request
        status_code, response_headers, response_body = await lb.proxy_request(
            decision=decision,
            path=f"/{path}",
            method=request.method,
            headers=headers,
            params=query_params,
            data=body
        )
        
        return Response(
            content=response_body,
            status_code=status_code,
            headers=response_headers
        )
    
    return app

async def main():
    """Main function for testing the load balancer"""
    
    # Initialize load balancer
    lb = LoadBalancer()
    await lb.initialize()
    
    try:
        # Start health monitoring
        health_task = asyncio.create_task(lb.start_health_monitoring())
        
        # Test routing decisions
        test_paths = [
            "/health",
            "/api/market/data",
            "/api/ai/signals",
            "/api/trade/orders",
            "/api/chat/message"
        ]
        
        logger.info("Testing routing decisions:")
        for path in test_paths:
            decision = lb.route_request(path)
            logger.info(f"  {path} → {decision.target_engine} ({decision.reason})")
        
        # Show status
        status = await lb.get_status()
        logger.info(f"\nLoad Balancer Status:")
        logger.info(f"  Healthy engines: {status['load_balancer']['healthy_engines']}/{status['load_balancer']['total_engines']}")
        
        # Wait a bit then close
        await asyncio.sleep(30)
        health_task.cancel()
        
    finally:
        await lb.close()

if __name__ == "__main__":
    # For testing
    asyncio.run(main())
    
    # To run as FastAPI server, uncomment below:
    # app = create_fastapi_app()
    # uvicorn.run(app, host="0.0.0.0", port=8080)