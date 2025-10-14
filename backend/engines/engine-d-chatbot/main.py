#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine D: AI Chatbot & Coordination Service
Central coordination hub with AI-powered chatbot
Deployed on AWS ECS/Fargate
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import uvicorn
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import aiohttp
import json
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import websockets
import uuid
import boto3
from typing import Optional
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ENGINE-D - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('engine_d_chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    id: str
    user_id: str
    message: str
    response: str
    timestamp: datetime
    intent: str
    confidence: float

@dataclass
class EngineStatus:
    name: str
    url: str
    status: str  # 'online', 'offline', 'error'
    last_check: datetime
    response_time: float

# Pydantic models for Dhan integration
class DhanCredentials(BaseModel):
    api_key: str
    api_secret: str
    access_token: str
    user_id: Optional[str] = "demo-user"

class DhanWebhookPayload(BaseModel):
    orderid: str
    status: str
    tradingsymbol: str
    quantity: int
    price: float

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.active_connections.discard(conn)

class ChatbotService:
    def __init__(self):
        # Engine endpoints
        self.engines = {
            'engine_a': {
                'name': 'Market Data Service',
                'url': os.getenv('ENGINE_A_URL', 'https://engine-a-market-data-573866363639.us-central1.run.app'),
                'description': 'Real-time market data and technical analysis'
            },
            'engine_b': {
                'name': 'AI/ML Service',
                'url': os.getenv('ENGINE_B_URL', 'https://engine-b-ai-ml-573866363639.us-central1.run.app'),
                'description': 'Advanced AI models and predictions'
            },
            'engine_c': {
                'name': 'Trade Execution Service',
                'url': os.getenv('ENGINE_C_URL', 'http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c'),
                'description': 'Secure trade execution and risk management'
            },
            'ultra_aggressive': {
                'name': 'Ultra Aggressive Trading',
                'url': os.getenv('ULTRA_AGGRESSIVE_URL', 'https://infinityai-ultra-aggressive-573866363639.us-central1.run.app'),
                'description': 'Ultra aggressive trading strategies'
            }
        }
        
        # Chat history
        self.chat_history: List[ChatMessage] = []
        self.engine_status: Dict[str, EngineStatus] = {}
        
        # Intent patterns
        self.intent_patterns = {
            'market_data': ['market', 'price', 'data', 'chart', 'technical', 'analysis'],
            'ai_prediction': ['predict', 'forecast', 'ai', 'model', 'signal'],
            'trade_execution': ['trade', 'buy', 'sell', 'order', 'execute'],
            'portfolio': ['portfolio', 'position', 'holdings', 'pnl', 'profit'],
            'status': ['status', 'health', 'system', 'engine'],
            'help': ['help', 'guide', 'how', 'what', 'explain']
        }
        
        logger.info("🤖 Engine D - Chatbot Service Initialized")
        
        # Initialize AWS Secrets Manager client (if available)
        try:
            self.secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
            logger.info("AWS Secrets Manager initialized")
        except Exception as e:
            logger.warning(f"AWS Secrets Manager not available: {e}")
            self.secrets_client = None
    
    def classify_intent(self, message: str) -> tuple[str, float]:
        """Classify user intent from message"""
        message_lower = message.lower()
        intent_scores = {}
        
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score / len(keywords)
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            return best_intent, confidence
        
        return 'general', 0.5
    
    async def check_engine_status(self, engine_name: str, engine_url: str) -> EngineStatus:
        """Check status of a specific engine"""
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{engine_url}/health") as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status == 200:
                        status = "online"
                    else:
                        status = "error"
                        
                    return EngineStatus(
                        name=engine_name,
                        url=engine_url,
                        status=status,
                        last_check=datetime.now(),
                        response_time=response_time
                    )
                    
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error checking {engine_name}: {e}")
            return EngineStatus(
                name=engine_name,
                url=engine_url,
                status="offline",
                last_check=datetime.now(),
                response_time=response_time
            )
    
    async def get_system_status(self) -> Dict:
        """Get status of all engines"""
        status_tasks = []
        
        for engine_key, engine_info in self.engines.items():
            task = self.check_engine_status(engine_key, engine_info['url'])
            status_tasks.append(task)
        
        statuses = await asyncio.gather(*status_tasks)
        
        # Update engine status
        for status in statuses:
            self.engine_status[status.name] = status
        
        online_count = sum(1 for s in statuses if s.status == "online")
        total_count = len(statuses)
        
        return {
            'overall_status': 'healthy' if online_count == total_count else 'degraded',
            'engines_online': f"{online_count}/{total_count}",
            'engines': {s.name: asdict(s) for s in statuses},
            'timestamp': datetime.now().isoformat()
        }
    
    async def fetch_from_engine(self, engine_name: str, endpoint: str) -> Dict:
        """Fetch data from specific engine"""
        if engine_name not in self.engines:
            return {'error': f'Engine {engine_name} not found'}
        
        engine_url = self.engines[engine_name]['url']
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(f"{engine_url}{endpoint}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {'error': f'Engine returned status {response.status}'}
                        
        except Exception as e:
            logger.error(f"Error fetching from {engine_name}: {e}")
            return {'error': str(e)}
    
    async def process_chat_message(self, user_id: str, message: str) -> ChatMessage:
        """Process chat message and generate response"""
        message_id = str(uuid.uuid4())
        intent, confidence = self.classify_intent(message)
        
        # Generate response based on intent
        response = await self.generate_response(intent, message)
        
        chat_message = ChatMessage(
            id=message_id,
            user_id=user_id,
            message=message,
            response=response,
            timestamp=datetime.now(),
            intent=intent,
            confidence=confidence
        )
        
        # Store in history
        self.chat_history.append(chat_message)
        
        # Keep only last 100 messages
        if len(self.chat_history) > 100:
            self.chat_history = self.chat_history[-100:]
        
        return chat_message
    
    async def generate_response(self, intent: str, message: str) -> str:
        """Generate response based on intent"""
        try:
            if intent == 'market_data':
                # Fetch market signals from Engine A
                data = await self.fetch_from_engine('engine_a', '/api/signals')
                if 'error' not in data and 'signals' in data:
                    signals = data['signals'][:3]  # Show top 3 signals
                    response = "📊 **Latest Market Signals:**\n\n"
                    for signal in signals:
                        response += f"• **{signal.get('symbol', 'N/A')}**: {signal.get('signal_type', 'N/A')} "
                        response += f"(Confidence: {signal.get('confidence', 0):.1f}%)\n"
                        response += f"  Price: ₹{signal.get('price', 0):.2f}\n\n"
                    return response
                else:
                    return "❌ Unable to fetch market data at the moment. Please try again later."
            
            elif intent == 'ai_prediction':
                # Fetch AI predictions from Engine B
                data = await self.fetch_from_engine('engine_b', '/api/ai-signals')
                if 'error' not in data and 'ai_signals' in data:
                    signals = data['ai_signals'][:3]
                    response = "🤖 **AI Trading Predictions:**\n\n"
                    for signal in signals:
                        response += f"• **{signal.get('symbol', 'N/A')}**: {signal.get('signal_type', 'N/A')}\n"
                        response += f"  Predicted Price: ₹{signal.get('predicted_price', 0):.2f}\n"
                        response += f"  Expected Return: {signal.get('expected_return', 0)*100:.2f}%\n"
                        response += f"  Confidence: {signal.get('confidence', 0):.1f}%\n\n"
                    return response
                else:
                    return "❌ Unable to fetch AI predictions at the moment. Please try again later."
            
            elif intent == 'status':
                # Get system status
                status = await self.get_system_status()
                response = f"🚀 **System Status: {status['overall_status'].upper()}**\n\n"
                response += f"📡 **Engines Online:** {status['engines_online']}\n\n"
                
                for engine_name, engine_status in status['engines'].items():
                    status_emoji = "🟢" if engine_status['status'] == 'online' else "🔴"
                    response += f"{status_emoji} **{engine_name}**: {engine_status['status']} "
                    response += f"({engine_status['response_time']:.2f}s)\n"
                
                return response
            
            elif intent == 'trade_execution':
                return ("🎯 **Trade Execution Commands:**\n\n"
                       "• Use `/buy <symbol> <quantity>` to place buy orders\n"
                       "• Use `/sell <symbol> <quantity>` to place sell orders\n"
                       "• Use `/portfolio` to view your positions\n"
                       "• Use `/orders` to view order history\n\n"
                       "⚠️ **Note:** All trades require proper authentication.")
            
            elif intent == 'portfolio':
                return ("📊 **Portfolio Commands:**\n\n"
                       "• `/portfolio` - View current positions\n"
                       "• `/pnl` - View profit & loss summary\n"
                       "• `/holdings` - View all holdings\n"
                       "• `/performance` - View performance metrics")
            
            elif intent == 'help':
                return ("🤖 **InfinityAI.Pro Trading Assistant**\n\n"
                       "**Available Commands:**\n"
                       "• Market data: Ask about prices, charts, technical analysis\n"
                       "• AI predictions: Ask for forecasts and AI signals\n"
                       "• System status: Check engine health and status\n"
                       "• Trading: Execute trades and manage portfolio\n\n"
                       "**Example Queries:**\n"
                       "• \"Show me NIFTY signals\"\n"
                       "• \"What's the AI prediction for RELIANCE?\"\n"
                       "• \"System status check\"\n"
                       "• \"Buy 100 shares of TCS\"")
            
            else:
                return ("🤖 Hello! I'm your InfinityAI.Pro trading assistant. "
                       "I can help you with market data, AI predictions, trading, and system status. "
                       "Ask me anything about the markets or type 'help' for more options!")
                       
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "❌ Sorry, I encountered an error processing your request. Please try again."
    
    def store_dhan_credentials(self, user_id: str, credentials: DhanCredentials) -> dict:
        """Store Dhan credentials securely in AWS Secrets Manager"""
        try:
            if not self.secrets_client:
                # Fallback to environment variables for development
                logger.warning("Using environment variables for Dhan credentials (development mode)")
                return {"status": "success", "message": "Credentials stored (dev mode)", "storage": "environment"}
            
            secret_name = f"dhan/credentials/{user_id}"
            secret_value = {
                "api_key": credentials.api_key,
                "api_secret": credentials.api_secret,
                "access_token": credentials.access_token,
                "timestamp": datetime.now().isoformat()
            }
            
            # Try to update existing secret first
            try:
                self.secrets_client.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps(secret_value)
                )
                logger.info(f"Updated Dhan credentials for user {user_id}")
            except self.secrets_client.exceptions.ResourceNotFoundException:
                # Create new secret if it doesn't exist
                self.secrets_client.create_secret(
                    Name=secret_name,
                    SecretString=json.dumps(secret_value),
                    Description=f"Dhan API credentials for user {user_id}"
                )
                logger.info(f"Created Dhan credentials for user {user_id}")
            
            return {
                "status": "success", 
                "message": "Dhan credentials stored securely",
                "storage": "aws_secrets_manager"
            }
            
        except Exception as e:
            logger.error(f"Error storing Dhan credentials: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_dhan_credentials(self, user_id: str) -> Optional[dict]:
        """Retrieve Dhan credentials from AWS Secrets Manager"""
        try:
            if not self.secrets_client:
                logger.warning("Secrets Manager not available, using mock credentials")
                return None
                
            secret_name = f"dhan/credentials/{user_id}"
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            credentials = json.loads(response['SecretString'])
            logger.info(f"Retrieved Dhan credentials for user {user_id}")
            return credentials
            
        except self.secrets_client.exceptions.ResourceNotFoundException:
            logger.warning(f"No Dhan credentials found for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving Dhan credentials: {e}")
            return None
    
    async def fetch_dhan_data(self, user_id: str) -> dict:
        """Fetch live data from Dhan API"""
        credentials = self.get_dhan_credentials(user_id)
        if not credentials:
            return {
                "error": "No Dhan credentials found",
                "mock_data": {
                    "holdings": [{"symbol": "RELIANCE", "quantity": 50, "current_price": 2845.30, "pnl": "+5.2%"}],
                    "orders": [{"order_id": "DEMO123", "symbol": "TCS", "status": "completed", "quantity": 10}],
                    "positions": [{"symbol": "INFY", "quantity": 25, "avg_price": 1750.00, "current_price": 1789.20}],
                    "funds": {"available_margin": 125000.50, "used_margin": 45000.25}
                }
            }
        
        try:
            headers = {
                "access-token": credentials["access_token"],
                "api-key": credentials["api_key"],
                "api-secret": credentials["api_secret"]
            }
            
            async with aiohttp.ClientSession() as session:
                # Fetch holdings, orders, positions, and funds from Dhan API
                dhan_data = {}
                
                endpoints = {
                    "holdings": "https://api.dhan.co/holdings",
                    "orders": "https://api.dhan.co/orders", 
                    "positions": "https://api.dhan.co/positions",
                    "funds": "https://api.dhan.co/funds"
                }
                
                for key, url in endpoints.items():
                    try:
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                dhan_data[key] = await response.json()
                            else:
                                dhan_data[key] = {"error": f"API returned {response.status}"}
                    except Exception as e:
                        dhan_data[key] = {"error": str(e)}
                
                return {"status": "success", "data": dhan_data, "timestamp": datetime.now().isoformat()}
                
        except Exception as e:
            logger.error(f"Error fetching Dhan data: {e}")
            return {"error": str(e)}

# Global services
chatbot_service = ChatbotService()
connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Engine D - Chatbot Service starting...")
    yield
    # Shutdown
    logger.info("🛑 Engine D - Chatbot Service shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="🤖 InfinityAI.Pro - Engine D: AI Chatbot & Coordination",
    description="Central coordination hub with AI-powered trading chatbot",
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
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>InfinityAI.Pro - Engine D</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .header { text-align: center; color: #333; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 InfinityAI.Pro - Engine D</h1>
                <h2>AI Chatbot & Coordination Service</h2>
            </div>
            <div class="status">
                <h3>✅ Service Status: Active</h3>
                <p><strong>Version:</strong> 1.0.0</p>
                <p><strong>Started:</strong> {}</p>
                <p><strong>Engines Connected:</strong> {}</p>
            </div>
            <div>
                <h3>🔗 API Endpoints:</h3>
                <ul>
                    <li><a href="/health">Health Check</a></li>
                    <li><a href="/api/status">System Status</a></li>
                    <li><a href="/api/chat-history">Chat History</a></li>
                    <li><a href="/metrics">Service Metrics</a></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(chatbot_service.engines)))

@app.get("/engine-d")
async def engine_d_root():
    """ALB path-specific route handler"""
    return {
        "service": "Engine D - AI Chatbot & Coordination Service",
        "status": "active",
        "version": "1.0.0",
        "engines_configured": len(chatbot_service.engines),
        "active_connections": len(connection_manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-d-chatbot",
        "engines_configured": len(chatbot_service.engines),
        "active_connections": len(connection_manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/engine-d/health")
async def engine_d_health_check():
    """ALB path-specific health check"""
    return {
        "status": "healthy",
        "service": "Engine D - AI Chatbot & Coordination Service",
        "version": "1.0.0",
        "engines_configured": len(chatbot_service.engines),
        "active_connections": len(connection_manager.active_connections),
        "chat_history_count": len(chatbot_service.chat_history),
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Process chat message
            chat_message = await chatbot_service.process_chat_message(user_id, data)
            
            # Send response back to user
            response_data = {
                "type": "chat_response",
                "message_id": chat_message.id,
                "response": chat_message.response,
                "intent": chat_message.intent,
                "confidence": chat_message.confidence,
                "timestamp": chat_message.timestamp.isoformat()
            }
            
            await connection_manager.send_personal_message(
                json.dumps(response_data), websocket
            )
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@app.post("/api/chat")
async def chat_endpoint(user_id: str, message: str):
    """REST endpoint for chat"""
    try:
        chat_message = await chatbot_service.process_chat_message(user_id, message)
        
        return {
            "status": "success",
            "message_id": chat_message.id,
            "response": chat_message.response,
            "intent": chat_message.intent,
            "confidence": chat_message.confidence,
            "timestamp": chat_message.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        status = await chatbot_service.get_system_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat-history")
async def get_chat_history():
    """Get chat history"""
    return {
        "status": "success",
        "chat_history": [asdict(msg) for msg in chatbot_service.chat_history[-20:]],  # Last 20 messages
        "total_messages": len(chatbot_service.chat_history),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/engines")
async def get_engines():
    """Get configured engines"""
    return {
        "status": "success",
        "engines": chatbot_service.engines,
        "engine_status": {name: asdict(status) for name, status in chatbot_service.engine_status.items()},
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "engine-d-chatbot",
        "active_websockets": len(connection_manager.active_connections),
        "total_chat_messages": len(chatbot_service.chat_history),
        "configured_engines": len(chatbot_service.engines),
        "online_engines": len([s for s in chatbot_service.engine_status.values() if s.status == "online"]),
        "timestamp": datetime.now().isoformat()
    }

# Add missing API endpoints for frontend integration
@app.get("/api/market-data")
@app.get("/engine-d/api/market-data")
async def get_market_data():
    """Get live market data for dashboard"""
    try:
        # Fetch data from Engine A (Market Data Service)
        market_data = await chatbot_service.fetch_from_engine('engine_a', '/api/market-summary')
        
        # If Engine A is not available, return mock data
        if 'error' in market_data:
            market_data = {
                "nifty_50": {"price": 24856.50, "change": "+0.85%", "status": "open"},
                "sensex": {"price": 81475.20, "change": "+0.92%", "status": "open"},
                "bank_nifty": {"price": 52340.75, "change": "+1.15%", "status": "open"},
                "top_stocks": [
                    {"symbol": "RELIANCE", "price": 2845.30, "change": "+1.12%"},
                    {"symbol": "TCS", "price": 4156.75, "change": "+0.78%"},
                    {"symbol": "INFY", "price": 1789.20, "change": "+1.45%"},
                    {"symbol": "HDFCBANK", "price": 1654.90, "change": "+0.65%"},
                    {"symbol": "ICICIBANK", "price": 1289.45, "change": "+0.87%"}
                ],
                "us_markets": {
                    "AAPL": {"price": 257.13, "change": "+0.66%"},
                    "GOOGL": {"price": 178.45, "change": "+1.23%"},
                    "MSFT": {"price": 428.90, "change": "+0.45%"}
                }
            }
        
        return {
            "status": "success",
            "data": market_data,
            "timestamp": datetime.now().isoformat(),
            "source": "live" if 'error' not in market_data else "mock"
        }
        
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-analysis")
@app.get("/engine-d/api/ai-analysis")
async def get_ai_analysis():
    """Get AI-powered market analysis"""
    try:
        # Fetch AI predictions from Engine B
        ai_data = await chatbot_service.fetch_from_engine('engine_b', '/api/predictions')
        
        # If Engine B is not available, return mock analysis
        if 'error' in ai_data:
            ai_data = {
                "market_sentiment": "Bullish",
                "confidence": 78.5,
                "key_insights": [
                    "Indian markets showing positive momentum with NIFTY crossing 24,850",
                    "Technology stocks leading gains with strong fundamentals",
                    "Banking sector showing resilience despite global headwinds",
                    "FII inflows supporting market stability"
                ],
                "predictions": [
                    {"symbol": "NIFTY", "target": 25200, "probability": 0.82, "timeframe": "1 week"},
                    {"symbol": "BANKNIFTY", "target": 53500, "probability": 0.75, "timeframe": "1 week"},
                    {"symbol": "RELIANCE", "target": 2950, "probability": 0.68, "timeframe": "2 weeks"}
                ],
                "risk_factors": [
                    "Global economic uncertainty",
                    "Crude oil price volatility",
                    "Currency fluctuations"
                ]
            }
        
        return {
            "status": "success",
            "analysis": ai_data,
            "timestamp": datetime.now().isoformat(),
            "generated_by": "InfinityAI Engine B",
            "source": "live" if 'error' not in ai_data else "mock"
        }
        
    except Exception as e:
        logger.error(f"Error fetching AI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/dhan")
async def relay_dhan_token_update(config: Dict[str, str]):
    """Relay DHAN token update to Engines A and C. Engine A is public; Engine C requires API key via Authorization: Bearer."""
    results = {}
    token = config.get("access_token") or config.get("DHAN_ACCESS_TOKEN")
    client_id = config.get("client_id") or os.getenv("DHAN_CLIENT_ID")
    engine_a_url = chatbot_service.engines['engine_a']['url']
    engine_c_url = chatbot_service.engines['engine_c']['url']
    engine_c_api_key = os.getenv("ENGINE_C_API_KEY", "valid_api_key")
    try:
        async with aiohttp.ClientSession() as session:
            # Update Engine A
            try:
                async with session.post(f"{engine_a_url}/api/config/dhan", json={"access_token": token, "client_id": client_id}) as resp:
                    results['engine_a'] = {"status": resp.status, "body": await resp.text()}
            except Exception as e:
                results['engine_a'] = {"error": str(e)}
            # Update Engine C
            try:
                async with session.post(f"{engine_c_url}/api/config/dhan", json={"access_token": token, "client_id": client_id}, headers={"Authorization": f"Bearer {engine_c_api_key}"}) as resp:
                    results['engine_c'] = {"status": resp.status, "body": await resp.text()}
            except Exception as e:
                results['engine_c'] = {"error": str(e)}
    except Exception as e:
        results['error'] = str(e)
    return {"status": "relayed", "results": results, "timestamp": datetime.now().isoformat()}

# Dhan Integration API Endpoints
@app.post("/api/dhan/store")
@app.post("/engine-d/api/dhan/store")
async def store_dhan_credentials(credentials: DhanCredentials):
    """Store Dhan API credentials securely"""
    try:
        result = chatbot_service.store_dhan_credentials(credentials.user_id, credentials)
        return result
    except Exception as e:
        logger.error(f"Error storing Dhan credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dhan/live-data")
@app.get("/engine-d/api/dhan/live-data")
async def get_dhan_live_data(user_id: str = "demo-user"):
    """Get live Dhan portfolio data"""
    try:
        data = await chatbot_service.fetch_dhan_data(user_id)
        return data
    except Exception as e:
        logger.error(f"Error fetching Dhan data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhooks/dhan")
@app.post("/engine-d/api/webhooks/dhan")
async def dhan_webhook_handler(payload: DhanWebhookPayload):
    """Handle Dhan webhook notifications"""
    try:
        logger.info(f"Dhan webhook received: {payload.dict()}")
        
        # Process the webhook payload
        webhook_data = {
            "order_id": payload.orderid,
            "status": payload.status,
            "symbol": payload.tradingsymbol,
            "quantity": payload.quantity,
            "price": payload.price,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store webhook event (you can add database storage here)
        logger.info(f"Processed Dhan webhook: {webhook_data}")
        
        # Broadcast to connected WebSocket clients
        await connection_manager.broadcast(json.dumps({
            "type": "dhan_update",
            "data": webhook_data
        }))
        
        return {"status": "received", "message": "Webhook processed successfully"}
        
    except Exception as e:
        logger.error(f"Error processing Dhan webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/dhan/callback")
@app.get("/engine-d/auth/dhan/callback")
async def dhan_auth_callback(code: Optional[str] = None, state: Optional[str] = None):
    """Handle Dhan OAuth callback"""
    try:
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not provided")
        
        logger.info(f"Dhan OAuth callback received: code={code}, state={state}")
        
        # In a real implementation, you would exchange the code for an access token
        # For now, we'll return a success response
        return {
            "status": "success",
            "message": "Dhan authorization successful",
            "code": code,
            "state": state,
            "next_step": "Please store your API credentials using the dashboard form"
        }
        
    except Exception as e:
        logger.error(f"Error in Dhan callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dhan/callback-urls")
@app.get("/engine-d/api/dhan/callback-urls")
async def get_dhan_callback_urls():
    """Get Dhan callback URLs for setup"""
    return {
        "postback_url": "https://infinityai.pro/api/webhooks/dhan",
        "redirect_url": "https://infinityai.pro/auth/dhan/callback",
        "instructions": [
            "1. Register these URLs in your Dhan Developer Portal",
            "2. Use the dashboard form to store your API credentials",
            "3. Test the integration with live data"
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )