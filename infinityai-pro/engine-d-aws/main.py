#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine D (AWS Central Backend API)
Central orchestrator for multi-cloud trading system
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx
import asyncio
import json
import os
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import redis
import hashlib
import websockets
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Engine D - AWS Central Backend API")
    await engine_d.initialize()
    yield
    # Shutdown
    logger.info("🛑 Shutting down Engine D")
    await engine_d.cleanup()

app = FastAPI(
    title="InfinityAI.Pro - Engine D (AWS Central API)",
    description="Central orchestrator for multi-cloud AI trading system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://infinityai.azurewebsites.net", "https://infinityai.pro"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Data Models
class DHANTokenUpdate(BaseModel):
    access_token: str
    user_id: Optional[str] = None

class TradingRequest(BaseModel):
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    price: Optional[float] = None
    order_type: str = "MARKET"

class PortfolioResponse(BaseModel):
    holdings: List[Dict[str, Any]]
    total_value: float
    total_pnl: float
    total_invested: float

class RiskAssessment(BaseModel):
    risk_level: str  # HIGH, MEDIUM, LOW
    confidence: float
    factors: List[str]

# Engine D Core Class
class EngineDCore:
    def __init__(self):
        # Determine engine URLs based on environment
        environment = os.getenv('ENVIRONMENT', 'production')
        if environment == 'development':
            # Use container names for development/testing
            self.engines = {
                "engine_a": {
                    "url": "http://engine-a-test:8001",
                    "cloud": "Azure",
                    "specialization": "AI Sentiment & Technical Analysis",
                    "endpoints": {
                        "sentiment": "/analyze/sentiment",
                        "technical": "/analyze/technical",
                        "prediction": "/predict/price",
                        "health": "/health"
                    }
                },
                "engine_b": {
                    "url": "http://engine-b-test:8002",
                    "cloud": "Google Cloud",
                    "specialization": "ML Pattern Recognition & Risk Assessment",
                    "endpoints": {
                        "patterns": "/analyze/patterns",
                        "risk": "/assess/risk",
                        "optimization": "/optimize/portfolio",
                        "prediction": "/predict/ml",
                        "health": "/health"
                    }
                },
                "engine_c": {
                    "url": "http://engine-c-test:8003",
                    "cloud": "AWS",
                    "specialization": "Advanced Quantitative Analysis & Backtesting",
                    "endpoints": {
                        "quantitative": "/analyze/quantitative",
                        "backtest": "/backtest/strategy",
                        "optimization": "/optimize/portfolio",
                        "health": "/health"
                    }
                }
            }
        else:
            # Production URLs
            self.engines = {
                "engine_a": {
                    "url": "https://engine-a-infinityai.azurecontainerapps.io",
                    "cloud": "Azure",
                    "specialization": "AI Sentiment & Technical Analysis",
                    "endpoints": {
                        "sentiment": "/analyze/sentiment",
                        "technical": "/analyze/technical",
                        "prediction": "/predict/price",
                        "health": "/health"
                    }
                },
                "engine_b": {
                    "url": "https://engine-b-infinityai-run.a.run.app",
                    "cloud": "Google Cloud",
                    "specialization": "ML Pattern Recognition & Risk Assessment",
                    "endpoints": {
                        "patterns": "/analyze/patterns",
                        "risk": "/assess/risk",
                        "optimization": "/optimize/portfolio",
                        "prediction": "/predict/ml",
                        "health": "/health"
                    }
                },
                "engine_c": {
                    "url": "https://engine-c-quant-alb-1234567890.us-east-1.elb.amazonaws.com",
                    "cloud": "AWS",
                    "specialization": "Advanced Quantitative Analysis & Backtesting",
                    "endpoints": {
                        "quantitative": "/analyze/quantitative",
                        "backtest": "/backtest/strategy",
                        "optimization": "/optimize/portfolio",
                        "health": "/health"
                    }
                }
            }
        self.dhan_client = None
        self.redis_client = None
        self.secrets_client = None
        self.http_client = None
        self.engine_health_status = {}
        self.last_health_check = None
        
    async def initialize(self):
        """Initialize all connections and clients"""
        try:
            # Initialize HTTP client first (always needed)
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Initialize AWS services if credentials are available
            environment = os.getenv('ENVIRONMENT', 'production')
            if environment == 'development':
                logger.info("🔧 Running in development mode - skipping AWS services")
                self.secrets_client = None
                self.redis_client = None
                self.dhan_config = {
                    "client_id": "demo_client_id",
                    "client_secret": "demo_client_secret",
                    "base_url": "https://api.dhan.co"
                }
            else:
                # Initialize AWS Secrets Manager
                self.secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
                
                # Initialize Redis (AWS ElastiCache)
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                self.redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True, socket_connect_timeout=5)
                
                # Load DHAN credentials
                await self.load_dhan_credentials()
            
            logger.info("✅ Engine D initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Engine D initialization failed: {e}")
            # In development mode, don't crash on AWS failures
            if os.getenv('ENVIRONMENT') == 'development':
                logger.warning("🔧 Development mode: continuing with limited functionality")
                self.secrets_client = None
                self.redis_client = None
                if not hasattr(self, 'http_client'):
                    self.http_client = httpx.AsyncClient(timeout=30.0)
            else:
                raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.http_client:
            await self.http_client.aclose()
    
    async def load_dhan_credentials(self):
        """Load DHAN credentials from AWS Secrets Manager"""
        try:
            response = self.secrets_client.get_secret_value(SecretId="infinityai/dhan-credentials")
            secret = json.loads(response['SecretString'])
            
            self.dhan_config = {
                "client_id": secret['client_id'],
                "client_secret": secret['client_secret'],
                "base_url": "https://api.dhan.co"
            }
            logger.info("✅ DHAN credentials loaded from AWS Secrets Manager")
            
        except ClientError as e:
            logger.error(f"❌ Failed to load DHAN credentials: {e}")
            # Fallback to environment variables for development
            self.dhan_config = {
                "client_id": os.getenv('DHAN_CLIENT_ID'),
                "client_secret": os.getenv('DHAN_CLIENT_SECRET'), 
                "base_url": "https://api.dhan.co"
            }
    
    async def validate_access_token(self, access_token: str) -> Dict[str, Any]:
        """Validate DHAN access token and get user info"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            response = await self.http_client.get(
                f"{self.dhan_config['base_url']}/user/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # Cache the token
                await self.cache_access_token(access_token, user_data)
                return {"valid": True, "user_data": user_data}
            else:
                return {"valid": False, "error": "Invalid access token"}
                
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            return {"valid": False, "error": str(e)}
    
    async def cache_access_token(self, token: str, user_data: Dict[str, Any]):
        """Cache access token in Redis with 24-hour expiry"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
            cache_data = {
                "token": token,
                "user_data": json.dumps(user_data),
                "cached_at": datetime.now().isoformat()
            }
            
            # Cache for 23 hours (1 hour before expiry)
            self.redis_client.setex(
                f"dhan_token:{token_hash}", 
                23 * 3600, 
                json.dumps(cache_data)
            )
            logger.info(f"✅ Access token cached for user: {user_data.get('name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to cache token: {e}")
    
    async def get_portfolio(self, access_token: str) -> Dict[str, Any]:
        """Get user portfolio from DHAN API"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Get holdings
            holdings_response = await self.http_client.get(
                f"{self.dhan_config['base_url']}/holdings",
                headers=headers
            )
            
            if holdings_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch holdings")
            
            holdings_data = holdings_response.json()
            
            # Get positions
            positions_response = await self.http_client.get(
                f"{self.dhan_config['base_url']}/positions",
                headers=headers
            )
            
            positions_data = []
            if positions_response.status_code == 200:
                positions_data = positions_response.json()
            
            # Calculate portfolio metrics
            portfolio = await self.analyze_portfolio(holdings_data, positions_data)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def analyze_portfolio(self, holdings: List[Dict], positions: List[Dict]) -> Dict[str, Any]:
        """Analyze portfolio and calculate metrics"""
        try:
            total_value = 0
            total_invested = 0
            analyzed_holdings = []
            
            for holding in holdings:
                current_price = holding.get('price', 0)
                quantity = holding.get('quantity', 0)
                avg_price = holding.get('averagePrice', 0)
                
                current_value = current_price * quantity
                invested_value = avg_price * quantity
                pnl = current_value - invested_value
                pnl_percent = (pnl / invested_value * 100) if invested_value > 0 else 0
                
                # Risk assessment for this holding
                risk_assessment = await self.assess_holding_risk(holding, pnl_percent)
                
                analyzed_holding = {
                    "symbol": holding.get('securityId', ''),
                    "name": holding.get('tradingSymbol', ''),
                    "quantity": quantity,
                    "purchase_price": avg_price,
                    "current_price": current_price,
                    "invested_value": invested_value,
                    "current_value": current_value,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "risk_assessment": risk_assessment,
                    "currency": "INR"
                }
                
                analyzed_holdings.append(analyzed_holding)
                total_value += current_value
                total_invested += invested_value
            
            total_pnl = total_value - total_invested
            overall_return = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            return {
                "holdings": analyzed_holdings,
                "summary": {
                    "total_value": total_value,
                    "total_invested": total_invested,
                    "total_pnl": total_pnl,
                    "overall_return_percent": overall_return,
                    "currency": "INR"
                },
                "positions": positions,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Portfolio analysis failed: {e}")
            raise
    
    async def assess_holding_risk(self, holding: Dict[str, Any], pnl_percent: float) -> Dict[str, Any]:
        """Assess risk level for individual holding"""
        try:
            risk_factors = []
            risk_score = 0
            
            # PnL-based risk assessment
            if pnl_percent < -10:
                risk_score += 3
                risk_factors.append("High losses (>10%)")
            elif pnl_percent < -5:
                risk_score += 2
                risk_factors.append("Moderate losses (5-10%)")
            elif pnl_percent > 20:
                risk_score += 1
                risk_factors.append("High gains - consider profit booking")
            
            # Volume-based assessment (if available)
            # Price volatility assessment (if available)
            # Market sector assessment (if available)
            
            # Determine overall risk level
            if risk_score >= 3:
                risk_level = "HIGH"
            elif risk_score >= 1:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "factors": risk_factors,
                "confidence": min(0.8, 0.3 + (len(risk_factors) * 0.1))
            }
            
        except Exception as e:
            logger.error(f"❌ Risk assessment failed: {e}")
            return {
                "risk_level": "UNKNOWN",
                "risk_score": 0,
                "factors": ["Assessment failed"],
                "confidence": 0.0
            }
    
    async def check_engine_health(self) -> Dict[str, Any]:
        """Check health of all engines"""
        health_results = {}
        
        for engine_name, engine_config in self.engines.items():
            try:
                health_url = f"{engine_config['url']}{engine_config['endpoints']['health']}"
                response = await self.http_client.get(health_url, timeout=10.0)
                
                if response.status_code == 200:
                    health_data = response.json()
                    health_results[engine_name] = {
                        "status": "healthy",
                        "cloud": engine_config['cloud'],
                        "specialization": engine_config['specialization'],
                        "response_time": response.elapsed.total_seconds(),
                        "details": health_data
                    }
                else:
                    health_results[engine_name] = {
                        "status": "unhealthy",
                        "cloud": engine_config['cloud'],
                        "error": f"HTTP {response.status_code}"
                    }
                    
            except Exception as e:
                health_results[engine_name] = {
                    "status": "unreachable",
                    "cloud": engine_config['cloud'],
                    "error": str(e)
                }
        
        self.engine_health_status = health_results
        self.last_health_check = datetime.now()
        
        return health_results
    
    async def route_to_engines(self, request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route requests to appropriate engines and aggregate results"""
        try:
            tasks = []
            symbol = data.get("symbol", "NIFTY50")
            
            # Route based on request type
            if request_type == "sentiment_analysis":
                # Engine A: Sentiment Analysis
                tasks.append(self.call_engine_endpoint("engine_a", "sentiment", {
                    "symbol": symbol,
                    "text_data": data.get("news_text", ""),
                    "analysis_type": "comprehensive"
                }))
                
            elif request_type == "technical_analysis":
                # Engine A: Technical Analysis
                tasks.append(self.call_engine_endpoint("engine_a", "technical", {
                    "symbol": symbol,
                    "indicators": ["RSI", "MACD", "EMA", "BOLLINGER"],
                    "timeframe": data.get("timeframe", "1D")
                }))
                
            elif request_type == "pattern_analysis":
                # Engine B: Pattern Recognition
                tasks.append(self.call_engine_endpoint("engine_b", "patterns", {
                    "symbol": symbol,
                    "pattern_types": ["head_shoulders", "double_top", "triangle"],
                    "lookback_days": data.get("lookback_days", 30)
                }))
                
            elif request_type == "risk_assessment":
                # Engine B: Risk Assessment
                tasks.append(self.call_engine_endpoint("engine_b", "risk", {
                    "portfolio": data.get("portfolio", {}),
                    "risk_metrics": ["VAR", "BETA", "SHARPE"],
                    "confidence_level": 0.95
                }))
                
            elif request_type == "quantitative_analysis":
                # Engine C: Quantitative Analysis
                tasks.append(self.call_engine_endpoint("engine_c", "quantitative", {
                    "symbol": symbol,
                    "analysis_type": data.get("analysis_type", "volatility"),
                    "lookback_days": data.get("lookback_days", 30),
                    "parameters": data.get("parameters", {})
                }))
                
            elif request_type == "strategy_backtest":
                # Engine C: Strategy Backtesting
                tasks.append(self.call_engine_endpoint("engine_c", "backtest", {
                    "strategy": data.get("strategy", {"type": "momentum"}),
                    "symbol": symbol,
                    "start_date": data.get("start_date", "2024-01-01"),
                    "end_date": data.get("end_date", "2024-12-31"),
                    "initial_capital": data.get("initial_capital", 100000.0)
                }))
                
            elif request_type == "portfolio_optimization":
                # Engine B and C: Portfolio Optimization
                portfolio_data = data.get("portfolio", {})
                tasks = [
                    self.call_engine_endpoint("engine_b", "optimization", {
                        "portfolio": portfolio_data,
                        "objective": "sharpe",
                        "constraints": data.get("constraints", {})
                    }),
                    self.call_engine_endpoint("engine_c", "optimization", {
                        "portfolio": portfolio_data,
                        "objective": data.get("objective", "sharpe"),
                        "constraints": data.get("constraints", {})
                    })
                ]
                
            elif request_type == "comprehensive":
                # Send to all engines with specialized requests
                tasks = [
                    # Engine A: Sentiment + Technical Analysis
                    self.call_engine_endpoint("engine_a", "sentiment", {
                        "symbol": symbol,
                        "text_data": data.get("news_text", ""),
                        "analysis_type": "comprehensive"
                    }),
                    self.call_engine_endpoint("engine_a", "technical", {
                        "symbol": symbol,
                        "indicators": ["RSI", "MACD", "EMA", "BOLLINGER"],
                        "timeframe": "1D"
                    }),
                    # Engine B: Pattern Recognition + Risk Assessment
                    self.call_engine_endpoint("engine_b", "patterns", {
                        "symbol": symbol,
                        "pattern_types": ["head_shoulders", "double_top", "triangle"],
                        "lookback_days": 30
                    }),
                    self.call_engine_endpoint("engine_b", "risk", {
                        "portfolio": data.get("portfolio", {}),
                        "risk_metrics": ["VAR", "BETA", "SHARPE"],
                        "confidence_level": 0.95
                    }),
                    # Engine C: Quantitative Analysis
                    self.call_engine_endpoint("engine_c", "quantitative", {
                        "symbol": symbol,
                        "analysis_type": "volatility",
                        "lookback_days": 30,
                        "parameters": {}
                    })
                ]
            
            elif request_type == "monday_prediction":
                # Special Monday Nifty prediction using all engines
                tasks = [
                    # Engine A: Technical prediction with sentiment
                    self.call_engine_endpoint("engine_a", "prediction", {
                        "symbol": "NIFTY50",
                        "prediction_type": "monday_opening",
                        "include_sentiment": True,
                        "timeframe": "weekly"
                    }),
                    # Engine B: ML-based prediction
                    self.call_engine_endpoint("engine_b", "prediction", {
                        "symbol": "NIFTY50",
                        "model_type": "ensemble",
                        "prediction_horizon": "1d",
                        "features": ["price", "volume", "patterns"]
                    })
                ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results with enhanced logic
            aggregated_result = await self.aggregate_engine_results(request_type, results)
            
            return aggregated_result
            
        except Exception as e:
            logger.error(f"❌ Engine routing failed: {e}")
            return {"error": str(e), "results": [], "request_type": request_type}
    
    async def call_engine_endpoint(self, engine_name: str, endpoint_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific engine endpoint using the configured endpoint mapping"""
        try:
            engine_config = self.engines.get(engine_name)
            if not engine_config:
                return {"engine": engine_name, "error": "Engine not configured", "success": False}
            
            endpoint_path = engine_config['endpoints'].get(endpoint_key)
            if not endpoint_path:
                return {"engine": engine_name, "error": f"Endpoint '{endpoint_key}' not found", "success": False}
            
            full_url = f"{engine_config['url']}{endpoint_path}"
            
            # Add metadata to request
            request_data = {
                **data,
                "source_engine": "engine_d",
                "timestamp": datetime.now().isoformat(),
                "cloud_provider": engine_config['cloud']
            }
            
            response = await self.http_client.post(
                full_url,
                json=request_data,
                timeout=30.0,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "engine": engine_name,
                    "cloud": engine_config['cloud'],
                    "specialization": engine_config['specialization'],
                    "endpoint": endpoint_key,
                    "success": True,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None,
                    "data": result
                }
            else:
                return {
                    "engine": engine_name,
                    "cloud": engine_config['cloud'],
                    "endpoint": endpoint_key,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to call {engine_name}.{endpoint_key}: {e}")
            return {
                "engine": engine_name,
                "cloud": engine_config.get('cloud', 'unknown') if engine_config else 'unknown',
                "endpoint": endpoint_key,
                "error": str(e),
                "success": False
            }
    
    async def call_engine(self, engine_name: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        # Try to map legacy calls to new endpoint structure
        endpoint_mapping = {
            "ai/analyze": "sentiment",
            "trading/analyze": "quantitative",
            "process": "health"
        }
        
        endpoint_key = endpoint_mapping.get(endpoint, "health")
        return await self.call_engine_endpoint(engine_name, endpoint_key, data)
    
    async def aggregate_engine_results(self, request_type: str, results: List[Any]) -> Dict[str, Any]:
        """Aggregate results from multiple engines with intelligent analysis"""
        try:
            successful_results = []
            failed_results = []
            engine_responses = {}
            
            # Process individual results
            for result in results:
                if isinstance(result, Exception):
                    failed_results.append({"error": str(result), "type": "exception"})
                elif isinstance(result, dict):
                    if result.get("success"):
                        successful_results.append(result)
                        # Group by engine for analysis
                        engine_name = result.get("engine", "unknown")
                        if engine_name not in engine_responses:
                            engine_responses[engine_name] = []
                        engine_responses[engine_name].append(result)
                    else:
                        failed_results.append(result)
                else:
                    failed_results.append({"error": "Unknown result type", "data": str(result)})
            
            # Generate intelligent aggregation based on request type
            aggregated_analysis = await self.generate_intelligent_aggregation(
                request_type, successful_results, engine_responses
            )
            
            # Calculate confidence score
            confidence_score = self.calculate_overall_confidence(successful_results)
            
            # Generate trading recommendation if applicable
            trading_recommendation = None
            if request_type in ["comprehensive", "monday_prediction", "technical_analysis", "quantitative_analysis"]:
                trading_recommendation = await self.generate_trading_recommendation(
                    successful_results, request_type
                )
            
            return {
                "request_type": request_type,
                "total_engines_called": len(results),
                "successful_engines": len(successful_results),
                "failed_engines": len(failed_results),
                "success_rate": round((len(successful_results) / len(results)) * 100, 1) if results else 0,
                "overall_confidence": confidence_score,
                "intelligent_analysis": aggregated_analysis,
                "trading_recommendation": trading_recommendation,
                "engine_responses": engine_responses,
                "individual_results": successful_results,
                "failures": failed_results,
                "aggregated_at": datetime.now().isoformat(),
                "processing_time": None  # Will be set by caller
            }
            
        except Exception as e:
            logger.error(f"❌ Result aggregation failed: {e}")
            return {
                "error": str(e),
                "request_type": request_type,
                "results": [],
                "aggregated_at": datetime.now().isoformat()
            }
    
    async def generate_intelligent_aggregation(self, request_type: str, successful_results: List[Dict], 
                                             engine_responses: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Generate intelligent aggregation based on request type and results"""
        try:
            analysis = {
                "summary": "",
                "key_findings": [],
                "consensus": {},
                "divergences": [],
                "confidence_factors": []
            }
            
            if request_type == "comprehensive":
                # Comprehensive analysis across all engines
                if "engine_a" in engine_responses:
                    # Sentiment and technical insights
                    sentiment_data = [r for r in engine_responses["engine_a"] if r.get("endpoint") == "sentiment"]
                    technical_data = [r for r in engine_responses["engine_a"] if r.get("endpoint") == "technical"]
                    
                    if sentiment_data:
                        analysis["key_findings"].append(f"Market sentiment analysis from Azure engine: {sentiment_data[0]['data'].get('sentiment', 'N/A')}")
                    if technical_data:
                        analysis["key_findings"].append(f"Technical indicators from Azure engine show signals")
                
                if "engine_b" in engine_responses:
                    # Pattern and risk insights
                    pattern_data = [r for r in engine_responses["engine_b"] if r.get("endpoint") == "patterns"]
                    risk_data = [r for r in engine_responses["engine_b"] if r.get("endpoint") == "risk"]
                    
                    if pattern_data:
                        analysis["key_findings"].append(f"Pattern recognition from Google Cloud engine detected patterns")
                    if risk_data:
                        analysis["key_findings"].append(f"Risk assessment from Google Cloud engine completed")
                
                if "engine_c" in engine_responses:
                    # Quantitative insights
                    quant_data = [r for r in engine_responses["engine_c"] if r.get("endpoint") == "quantitative"]
                    if quant_data:
                        analysis["key_findings"].append(f"Quantitative analysis from AWS engine provides statistical insights")
                
                analysis["summary"] = f"Comprehensive analysis completed across {len(engine_responses)} engines with multi-cloud AI insights."
            
            elif request_type == "monday_prediction":
                # Special Monday prediction analysis
                predictions = []
                for engine_name, responses in engine_responses.items():
                    for response in responses:
                        if "prediction" in response.get("data", {}):
                            predictions.append({
                                "engine": engine_name,
                                "cloud": response.get("cloud"),
                                "prediction": response["data"]["prediction"]
                            })
                
                if predictions:
                    analysis["consensus"] = {
                        "prediction_count": len(predictions),
                        "engines_agreement": "analyzing",
                        "predicted_direction": "to be determined"
                    }
                    analysis["summary"] = f"Monday Nifty prediction analysis from {len(predictions)} AI engines."
                
            elif request_type in ["sentiment_analysis", "technical_analysis", "pattern_analysis", "quantitative_analysis"]:
                # Single-focus analysis
                if successful_results:
                    primary_result = successful_results[0]
                    analysis["summary"] = f"{request_type.replace('_', ' ').title()} completed successfully."
                    analysis["key_findings"].append(f"Primary analysis from {primary_result.get('cloud', 'unknown')} cloud engine")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Intelligent aggregation failed: {e}")
            return {
                "summary": "Analysis aggregation encountered errors",
                "error": str(e),
                "key_findings": [],
                "consensus": {},
                "divergences": []
            }
    
    def calculate_overall_confidence(self, successful_results: List[Dict]) -> float:
        """Calculate overall confidence score from successful results"""
        if not successful_results:
            return 0.0
        
        try:
            confidence_scores = []
            
            for result in successful_results:
                # Extract confidence from result data
                data = result.get("data", {})
                if isinstance(data, dict):
                    confidence = data.get("confidence_score", data.get("confidence", 0.5))
                    if isinstance(confidence, (int, float)):
                        confidence_scores.append(float(confidence))
                
                # Factor in response time (faster = slightly higher confidence)
                response_time = result.get("response_time", 1.0)
                if response_time and response_time < 2.0:
                    confidence_scores.append(0.1)  # Small boost for fast response
            
            if confidence_scores:
                # Weight by engine success
                engine_count = len(set(r.get("engine") for r in successful_results))
                multi_engine_boost = min(0.1 * (engine_count - 1), 0.2)  # Boost for multiple engines
                
                base_confidence = sum(confidence_scores) / len(confidence_scores)
                final_confidence = min(1.0, base_confidence + multi_engine_boost)
                
                return round(final_confidence, 3)
            
            return 0.5  # Default moderate confidence
            
        except Exception as e:
            logger.error(f"❌ Confidence calculation failed: {e}")
            return 0.3  # Low confidence due to calculation error
    
    async def generate_trading_recommendation(self, successful_results: List[Dict], request_type: str) -> Dict[str, Any]:
        """Generate trading recommendation based on aggregated results"""
        try:
            recommendation = {
                "action": "HOLD",  # Default conservative action
                "confidence": 0.5,
                "reasoning": [],
                "risk_level": "MEDIUM",
                "time_horizon": "SHORT_TERM",
                "generated_by": "engine_d_aggregator"
            }
            
            # Analyze results for trading signals
            bullish_signals = 0
            bearish_signals = 0
            
            for result in successful_results:
                data = result.get("data", {})
                engine = result.get("engine")
                endpoint = result.get("endpoint")
                
                # Analyze different types of signals
                if endpoint == "sentiment":
                    sentiment = data.get("sentiment", {}).get("label", "neutral").lower()
                    if sentiment in ["positive", "bullish"]:
                        bullish_signals += 1
                        recommendation["reasoning"].append(f"Positive sentiment from {engine}")
                    elif sentiment in ["negative", "bearish"]:
                        bearish_signals += 1
                        recommendation["reasoning"].append(f"Negative sentiment from {engine}")
                
                elif endpoint == "technical":
                    # Look for technical signals
                    signals = data.get("trading_signals", {})
                    if isinstance(signals, dict):
                        if signals.get("overall") == "BUY":
                            bullish_signals += 2  # Technical signals weighted higher
                            recommendation["reasoning"].append(f"Buy signal from technical analysis ({engine})")
                        elif signals.get("overall") == "SELL":
                            bearish_signals += 2
                            recommendation["reasoning"].append(f"Sell signal from technical analysis ({engine})")
                
                elif endpoint == "patterns":
                    patterns = data.get("patterns", {})
                    if isinstance(patterns, dict):
                        bullish_patterns = patterns.get("bullish_patterns", 0)
                        bearish_patterns = patterns.get("bearish_patterns", 0)
                        if bullish_patterns > bearish_patterns:
                            bullish_signals += 1
                            recommendation["reasoning"].append(f"Bullish patterns detected ({engine})")
                        elif bearish_patterns > bullish_patterns:
                            bearish_signals += 1
                            recommendation["reasoning"].append(f"Bearish patterns detected ({engine})")
                
                elif endpoint == "quantitative":
                    # Quantitative analysis signals
                    analysis_type = data.get("analysis_type")
                    if analysis_type == "momentum":
                        momentum_regime = data.get("momentum_regime")
                        if momentum_regime in ["strong_uptrend", "uptrend"]:
                            bullish_signals += 1
                            recommendation["reasoning"].append(f"Positive momentum trend ({engine})")
                        elif momentum_regime in ["strong_downtrend", "downtrend"]:
                            bearish_signals += 1
                            recommendation["reasoning"].append(f"Negative momentum trend ({engine})")
            
            # Determine final recommendation
            signal_difference = bullish_signals - bearish_signals
            
            if signal_difference >= 2:
                recommendation["action"] = "BUY"
                recommendation["confidence"] = min(0.8, 0.6 + (signal_difference * 0.05))
                recommendation["risk_level"] = "LOW" if signal_difference >= 3 else "MEDIUM"
            elif signal_difference <= -2:
                recommendation["action"] = "SELL"
                recommendation["confidence"] = min(0.8, 0.6 + (abs(signal_difference) * 0.05))
                recommendation["risk_level"] = "LOW" if abs(signal_difference) >= 3 else "MEDIUM"
            else:
                recommendation["action"] = "HOLD"
                recommendation["confidence"] = 0.4 + (abs(signal_difference) * 0.1)
                recommendation["risk_level"] = "MEDIUM"
                recommendation["reasoning"].append("Mixed or neutral signals from multiple engines")
            
            # Set time horizon based on request type
            if request_type == "monday_prediction":
                recommendation["time_horizon"] = "INTRADAY"
            elif request_type == "quantitative_analysis":
                recommendation["time_horizon"] = "MEDIUM_TERM"
            else:
                recommendation["time_horizon"] = "SHORT_TERM"
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Trading recommendation generation failed: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.3,
                "reasoning": [f"Recommendation generation failed: {str(e)}"],
                "risk_level": "HIGH",
                "time_horizon": "UNKNOWN",
                "error": str(e)
            }

# Initialize Engine D
engine_d = EngineDCore()

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "InfinityAI.Pro - Engine D (AWS Central API)",
        "version": "2.0.0",
        "status": "operational",
        "architecture": "multi-cloud",
        "engines": list(engine_d.engines.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_status = "connected" if engine_d.redis_client and engine_d.redis_client.ping() else "disconnected"
        
        # Check engine connectivity
        engine_status = {}
        for engine_name in engine_d.engines.keys():
            engine_status[engine_name] = "unknown"  # Would need to ping each engine
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "redis": redis_status,
                "engines": engine_status,
                "dhan_config": "loaded" if engine_d.dhan_config else "not_loaded"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/dhan/token/update")
async def update_dhan_token(token_data: DHANTokenUpdate):
    """Update DHAN access token"""
    try:
        # Validate the access token
        validation_result = await engine_d.validate_access_token(token_data.access_token)
        
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        user_data = validation_result["user_data"]
        
        return {
            "success": True,
            "message": "Access token updated successfully",
            "user_info": {
                "name": user_data.get("name", "Unknown"),
                "client_id": user_data.get("clientId", "Unknown"),
                "status": "active"
            },
            "expires_in": "24 hours"
        }
        
    except Exception as e:
        logger.error(f"❌ Token update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dhan/callback")
async def dhan_oauth_callback(code: str, state: Optional[str] = None):
    """DHAN OAuth callback handler"""
    try:
        # Exchange code for access token
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": engine_d.dhan_config["client_id"],
            "client_secret": engine_d.dhan_config["client_secret"],
            "redirect_uri": "https://infinityai-backend-aws.amazonaws.com/api/dhan/callback"
        }
        
        response = await engine_d.http_client.post(
            f"{engine_d.dhan_config['base_url']}/oauth/token",
            data=token_data
        )
        
        if response.status_code == 200:
            token_response = response.json()
            access_token = token_response["access_token"]
            
            # Validate and cache the token
            validation_result = await engine_d.validate_access_token(access_token)
            
            if validation_result["valid"]:
                # Redirect to frontend with success
                return {
                    "success": True,
                    "redirect_url": f"https://infinityai.azurewebsites.net/dashboard?token_status=success",
                    "access_token": access_token  # Frontend should save this
                }
            else:
                raise HTTPException(status_code=400, detail="Token validation failed")
        else:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
    except Exception as e:
        logger.error(f"❌ OAuth callback failed: {e}")
        return {
            "success": False,
            "redirect_url": f"https://infinityai.azurewebsites.net/dashboard?token_status=error&error={str(e)}"
        }

@app.get("/api/portfolio")
async def get_portfolio(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user portfolio with analysis"""
    try:
        access_token = credentials.credentials
        portfolio_data = await engine_d.get_portfolio(access_token)
        
        return {
            "success": True,
            "data": portfolio_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Portfolio fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/comprehensive")
async def comprehensive_analysis(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Comprehensive analysis using all engines"""
    try:
        # Add user context
        request["access_token"] = credentials.credentials
        request["timestamp"] = datetime.now().isoformat()
        
        # Route to all engines
        results = await engine_d.route_to_engines("comprehensive", request)
        
        return {
            "success": True,
            "analysis": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Comprehensive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/engines/health")
async def check_all_engines_health():
    """Check health status of all engines"""
    try:
        health_results = await engine_d.check_engine_health()
        
        total_engines = len(health_results)
        healthy_engines = sum(1 for h in health_results.values() if h.get("status") == "healthy")
        
        overall_status = "healthy" if healthy_engines == total_engines else "degraded" if healthy_engines > 0 else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "total_engines": total_engines,
            "healthy_engines": healthy_engines,
            "health_percentage": round((healthy_engines / total_engines) * 100, 1) if total_engines > 0 else 0,
            "engines": health_results,
            "last_check": engine_d.last_health_check.isoformat() if engine_d.last_health_check else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Engine health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/sentiment")
async def sentiment_analysis(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Sentiment analysis using Azure Engine A"""
    try:
        start_time = datetime.now()
        request["access_token"] = credentials.credentials
        
        results = await engine_d.route_to_engines("sentiment_analysis", request)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = round(processing_time, 3)
        
        return {
            "success": True,
            "analysis_type": "sentiment",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/technical")
async def technical_analysis(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Technical analysis using Azure Engine A"""
    try:
        start_time = datetime.now()
        request["access_token"] = credentials.credentials
        
        results = await engine_d.route_to_engines("technical_analysis", request)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = round(processing_time, 3)
        
        return {
            "success": True,
            "analysis_type": "technical",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Technical analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/patterns")
async def pattern_analysis(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Pattern recognition using Google Cloud Engine B"""
    try:
        start_time = datetime.now()
        request["access_token"] = credentials.credentials
        
        results = await engine_d.route_to_engines("pattern_analysis", request)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = round(processing_time, 3)
        
        return {
            "success": True,
            "analysis_type": "patterns",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/quantitative")
async def quantitative_analysis(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Quantitative analysis using AWS Engine C"""
    try:
        start_time = datetime.now()
        request["access_token"] = credentials.credentials
        
        results = await engine_d.route_to_engines("quantitative_analysis", request)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = round(processing_time, 3)
        
        return {
            "success": True,
            "analysis_type": "quantitative",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Quantitative analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest/strategy")
async def strategy_backtest(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Strategy backtesting using AWS Engine C"""
    try:
        start_time = datetime.now()
        request["access_token"] = credentials.credentials
        
        results = await engine_d.route_to_engines("strategy_backtest", request)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = round(processing_time, 3)
        
        return {
            "success": True,
            "analysis_type": "backtest",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Strategy backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize/portfolio")
async def portfolio_optimization(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Portfolio optimization using Engines B and C"""
    try:
        start_time = datetime.now()
        request["access_token"] = credentials.credentials
        
        results = await engine_d.route_to_engines("portfolio_optimization", request)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = round(processing_time, 3)
        
        return {
            "success": True,
            "analysis_type": "optimization",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Portfolio optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/monday")
async def monday_nifty_prediction(
    request: Dict[str, Any] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Special Monday Nifty prediction using all engines"""
    try:
        start_time = datetime.now()
        
        if not request:
            request = {}
            
        request.update({
            "access_token": credentials.credentials,
            "symbol": "NIFTY50",
            "prediction_type": "monday_opening",
            "include_sentiment": True,
            "include_technical": True,
            "include_patterns": True,
            "timeframe": "weekly"
        })
        
        results = await engine_d.route_to_engines("monday_prediction", request)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = round(processing_time, 3)
        
        return {
            "success": True,
            "prediction_type": "monday_nifty",
            "symbol": "NIFTY50",
            "results": results,
            "generated_at": datetime.now().isoformat(),
            "next_monday": (datetime.now() + timedelta(days=(7-datetime.now().weekday()))).strftime("%Y-%m-%d")
        }
        
    except Exception as e:
        logger.error(f"❌ Monday prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/engines/{engine_name}/proxy")
async def engine_proxy(
    engine_name: str,
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Proxy requests to specific engines"""
    try:
        if engine_name not in engine_d.engines:
            raise HTTPException(status_code=404, detail=f"Engine {engine_name} not found")
        
        request["access_token"] = credentials.credentials
        result = await engine_d.call_engine(engine_name, "process", request)
        
        return {
            "success": True,
            "engine": engine_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Engine proxy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/engines/status")
async def engines_status():
    """Get comprehensive status of all engines"""
    try:
        return {
            "central_engine": "Engine D (AWS)",
            "total_engines": len(engine_d.engines),
            "engines": {
                engine_name: {
                    "url": config["url"],
                    "cloud": config["cloud"],
                    "specialization": config["specialization"],
                    "endpoints": list(config["endpoints"].keys())
                }
                for engine_name, config in engine_d.engines.items()
            },
            "capabilities": [
                "Multi-cloud AI trading analysis",
                "Sentiment analysis (Azure)",
                "Technical analysis (Azure)",
                "Pattern recognition (Google Cloud)",
                "Risk assessment (Google Cloud)",
                "Quantitative analysis (AWS)",
                "Strategy backtesting (AWS)",
                "Portfolio optimization (Multi-cloud)",
                "Monday Nifty predictions",
                "Real-time DHAN integration"
            ],
            "last_health_check": engine_d.last_health_check.isoformat() if engine_d.last_health_check else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Engine status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True if os.getenv("ENVIRONMENT") != "production" else False
    )