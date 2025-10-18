#!/usr/bin/env python3
"""
InfinityAI.Pro - Dashboard Data Aggregation API
Frontend service to aggregate real-time data from all engines
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import aiohttp
import uvicorn
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - FRONTEND-API - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EngineStatus:
    name: str
    url: str
    status: str
    response_time_ms: float
    last_update: datetime
    data: Optional[Dict[str, Any]] = None

class DashboardDataAggregator:
    def __init__(self):
        self.engines = {
            'engine_a': {
                'name': 'Market Data Engine',
                'url': 'https://engine-a-573866363639-573866363639.us-central1.run.app',
                'endpoints': {
                    'health': '/health',
                    'signals': '/api/signals',
                    'market_data': '/api/market-data/NIFTY'
                }
            },
            'engine_b': {
                'name': 'AI/ML Engine',
                'url': 'https://engine-b-573866363639-573866363639.us-central1.run.app',
                'endpoints': {
                    'health': '/health',
                    'predictions': '/api/ai-signals',
                    'models': '/api/models/status'
                }
            },
            'engine_c': {
                'name': 'Trading Engine',
                'url': 'https://engine-c-573866363639-573866363639.us-central1.run.app',
                'endpoints': {
                    'health': '/health',
                    'orders': '/api/orders/demo',
                    'positions': '/api/positions',
                    'oauth_status': '/api/dhan/status'
                }
            },
            'engine_d': {
                'name': 'Chatbot Engine',
                'url': 'https://engine-d-573866363639-573866363639.us-central1.run.app',
                'endpoints': {
                    'health': '/health',
                    'chat': '/api/chat'
                }
            },
            'engine_ultra': {
                'name': 'Ultra Trading Engine',
                'url': 'https://engine-ultra-573866363639-573866363639.us-central1.run.app',
                'endpoints': {
                    'health': '/health',
                    'metrics': '/api/metrics'
                }
            }
        }
        
        self.cached_data = {
            'last_update': datetime.now(),
            'market_data': {},
            'ai_predictions': {},
            'trading_status': {},
            'system_health': {},
            'real_time_metrics': {}
        }
        
        logger.info("🎯 Dashboard Data Aggregator initialized")

    async def create_http_session(self):
        """Create HTTP session with proper configuration"""
        timeout = aiohttp.ClientTimeout(total=10)
        return aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': 'InfinityAI.Pro-Dashboard/1.0'}
        )

    async def fetch_engine_data(self, session: aiohttp.ClientSession, engine_id: str, engine_config: dict) -> EngineStatus:
        """Fetch data from a specific engine"""
        start_time = datetime.now()
        
        try:
            # Health check first
            health_url = f"{engine_config['url']}{engine_config['endpoints']['health']}"
            
            async with session.get(health_url) as response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status == 200:
                    health_data = await response.json()
                    
                    # Fetch additional data based on engine type
                    additional_data = await self.fetch_additional_engine_data(session, engine_id, engine_config)
                    
                    return EngineStatus(
                        name=engine_config['name'],
                        url=engine_config['url'],
                        status='healthy',
                        response_time_ms=response_time,
                        last_update=datetime.now(),
                        data={
                            'health': health_data,
                            'additional': additional_data
                        }
                    )
                else:
                    return EngineStatus(
                        name=engine_config['name'],
                        url=engine_config['url'],
                        status=f'unhealthy_http_{response.status}',
                        response_time_ms=response_time,
                        last_update=datetime.now()
                    )
                    
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error fetching data from {engine_id}: {e}")
            
            return EngineStatus(
                name=engine_config['name'],
                url=engine_config['url'],
                status=f'error_{str(e)[:20]}',
                response_time_ms=response_time,
                last_update=datetime.now()
            )

    async def fetch_additional_engine_data(self, session: aiohttp.ClientSession, engine_id: str, engine_config: dict) -> Dict[str, Any]:
        """Fetch additional data specific to each engine type"""
        additional_data = {}
        
        try:
            if engine_id == 'engine_a':
                # Fetch market signals
                signals_url = f"{engine_config['url']}{engine_config['endpoints']['signals']}"
                async with session.get(signals_url) as response:
                    if response.status == 200:
                        additional_data['signals'] = await response.json()
                        
                # Fetch specific market data
                market_url = f"{engine_config['url']}{engine_config['endpoints']['market_data']}"
                async with session.get(market_url) as response:
                    if response.status == 200:
                        additional_data['nifty_data'] = await response.json()
                        
            elif engine_id == 'engine_b':
                # Fetch AI predictions
                pred_url = f"{engine_config['url']}{engine_config['endpoints']['predictions']}"
                async with session.get(pred_url) as response:
                    if response.status == 200:
                        additional_data['predictions'] = await response.json()
                        
                # Fetch model status
                model_url = f"{engine_config['url']}{engine_config['endpoints']['models']}"
                async with session.get(model_url) as response:
                    if response.status == 200:
                        additional_data['model_status'] = await response.json()
                        
            elif engine_id == 'engine_c':
                # Fetch trading data
                orders_url = f"{engine_config['url']}{engine_config['endpoints']['orders']}"
                async with session.get(orders_url) as response:
                    if response.status == 200:
                        additional_data['orders'] = await response.json()
                        
                # Fetch OAuth status
                oauth_url = f"{engine_config['url']}{engine_config['endpoints']['oauth_status']}"
                async with session.get(oauth_url) as response:
                    if response.status == 200:
                        additional_data['oauth_status'] = await response.json()
                        
            elif engine_id == 'engine_d':
                # Test chatbot functionality
                chat_url = f"{engine_config['url']}{engine_config['endpoints']['chat']}"
                chat_payload = {
                    'message': 'Dashboard data request - system status',
                    'user_id': 'dashboard_system'
                }
                async with session.post(chat_url, json=chat_payload) as response:
                    if response.status == 200:
                        additional_data['chat_response'] = await response.json()
                        
            elif engine_id == 'engine_ultra':
                # Fetch ultra trading metrics
                metrics_url = f"{engine_config['url']}{engine_config['endpoints']['metrics']}"
                async with session.get(metrics_url) as response:
                    if response.status == 200:
                        additional_data['metrics'] = await response.json()
                        
        except Exception as e:
            logger.warning(f"Could not fetch additional data for {engine_id}: {e}")
            
        return additional_data

    async def aggregate_dashboard_data(self) -> Dict[str, Any]:
        """Aggregate data from all engines for dashboard"""
        logger.info("🔄 Aggregating dashboard data from all engines...")
        
        engine_statuses = {}
        
        async with await self.create_http_session() as session:
            # Fetch data from all engines concurrently
            tasks = [
                self.fetch_engine_data(session, engine_id, engine_config)
                for engine_id, engine_config in self.engines.items()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for engine_id, result in zip(self.engines.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {engine_id}: {result}")
                    engine_statuses[engine_id] = {
                        'name': self.engines[engine_id]['name'],
                        'status': 'error',
                        'error': str(result)
                    }
                else:
                    engine_statuses[engine_id] = asdict(result)
        
        # Process and structure the aggregated data
        dashboard_data = self.structure_dashboard_data(engine_statuses)
        
        # Cache the data
        self.cached_data = dashboard_data
        self.cached_data['last_update'] = datetime.now()
        
        logger.info(f"✅ Dashboard data aggregation complete")
        return dashboard_data

    def structure_dashboard_data(self, engine_statuses: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the raw engine data for dashboard consumption"""
        
        # System health summary
        healthy_engines = sum(1 for status in engine_statuses.values() 
                            if status.get('status') == 'healthy')
        total_engines = len(engine_statuses)
        system_health_percent = (healthy_engines / total_engines) * 100
        
        # Extract market data
        market_data = {}
        if 'engine_a' in engine_statuses and engine_statuses['engine_a'].get('data'):
            additional = engine_statuses['engine_a']['data'].get('additional', {})
            if 'signals' in additional:
                market_data['signals'] = additional['signals']
            if 'nifty_data' in additional:
                market_data['nifty'] = additional['nifty_data']
        
        # Extract AI predictions
        ai_predictions = {}
        if 'engine_b' in engine_statuses and engine_statuses['engine_b'].get('data'):
            additional = engine_statuses['engine_b']['data'].get('additional', {})
            if 'predictions' in additional:
                ai_predictions['predictions'] = additional['predictions']
            if 'model_status' in additional:
                ai_predictions['model_status'] = additional['model_status']
        
        # Extract trading data
        trading_data = {}
        if 'engine_c' in engine_statuses and engine_statuses['engine_c'].get('data'):
            additional = engine_statuses['engine_c']['data'].get('additional', {})
            if 'orders' in additional:
                trading_data['orders'] = additional['orders']
            if 'oauth_status' in additional:
                trading_data['oauth'] = additional['oauth_status']
        
        # Extract chatbot data
        chatbot_data = {}
        if 'engine_d' in engine_statuses and engine_statuses['engine_d'].get('data'):
            additional = engine_statuses['engine_d']['data'].get('additional', {})
            if 'chat_response' in additional:
                chatbot_data['system_response'] = additional['chat_response']
        
        # Extract ultra trading data
        ultra_trading_data = {}
        if 'engine_ultra' in engine_statuses and engine_statuses['engine_ultra'].get('data'):
            additional = engine_statuses['engine_ultra']['data'].get('additional', {})
            if 'metrics' in additional:
                ultra_trading_data['metrics'] = additional['metrics']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_status': {
                'health_percentage': system_health_percent,
                'healthy_engines': healthy_engines,
                'total_engines': total_engines,
                'status': 'operational' if system_health_percent >= 80 else 'degraded'
            },
            'engine_statuses': engine_statuses,
            'market_data': market_data,
            'ai_predictions': ai_predictions,
            'trading_signals': trading_data,
            'chatbot_coordination': chatbot_data,
            'ultra_trading': ultra_trading_data,
            'real_time_metrics': {
                'total_rps': sum(1/max(status.get('response_time_ms', 1000)/1000, 0.1) 
                               for status in engine_statuses.values() 
                               if status.get('status') == 'healthy'),
                'avg_response_time': sum(status.get('response_time_ms', 0) 
                                       for status in engine_statuses.values()) / max(len(engine_statuses), 1),
                'data_freshness': 'real-time'
            }
        }

# Global aggregator instance
dashboard_aggregator = DashboardDataAggregator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Dashboard API service starting...")
    yield
    # Shutdown
    logger.info("🛑 Dashboard API service shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="🎯 InfinityAI.Pro - Dashboard Data API",
    description="Real-time dashboard data aggregation from all engines",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "InfinityAI.Pro Dashboard API",
        "status": "active",
        "version": "1.0.0",
        "endpoints": [
            "/api/dashboard/data",
            "/api/system/health",
            "/health"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "InfinityAI.Pro Dashboard API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/dashboard/data")
async def get_dashboard_data(fresh: bool = False):
    """Get aggregated dashboard data from all engines"""
    try:
        if fresh or (datetime.now() - dashboard_aggregator.cached_data.get('last_update', datetime.min)).seconds > 30:
            # Refresh data if requested or cache is older than 30 seconds
            dashboard_data = await dashboard_aggregator.aggregate_dashboard_data()
        else:
            # Use cached data
            dashboard_data = dashboard_aggregator.cached_data
            
        return {
            "status": "success",
            "data": dashboard_data,
            "cache_age_seconds": (datetime.now() - dashboard_data.get('last_update', datetime.now())).seconds,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error aggregating dashboard data: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/system/health")
async def get_system_health():
    """Get system health summary"""
    try:
        dashboard_data = await dashboard_aggregator.aggregate_dashboard_data()
        
        return {
            "status": "success",
            "system_health": dashboard_data.get('system_status', {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/refresh")
async def refresh_dashboard_data():
    """Force refresh of dashboard data"""
    try:
        dashboard_data = await dashboard_aggregator.aggregate_dashboard_data()
        
        return {
            "status": "success",
            "message": "Dashboard data refreshed",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "dashboard_api:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )