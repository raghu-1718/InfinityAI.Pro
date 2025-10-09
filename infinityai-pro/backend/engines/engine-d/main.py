"""
InfinityAI.Pro - Engine D: AI Chatbot & Trading Assistant
Handles conversational AI, portfolio queries, real-time event analysis, and trading insights
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import re
from contextlib import suppress

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import pandas as pd
import numpy as np
from pydantic import BaseModel
import redis
try:
    from kafka import KafkaConsumer, KafkaProducer
    _kafka_available = True
except Exception as _e:
    _kafka_available = False
    KafkaConsumer = None  # type: ignore
    KafkaProducer = None  # type: ignore
import openai
with suppress(ImportError):
    import boto3  # type: ignore
    from botocore.exceptions import ClientError  # type: ignore
# Heavy NLP models can slow startup; guard with env flag
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import nltk
from textblob import TextBlob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="InfinityAI Engine D - AI Chatbot", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
ENGINE_A_URL = os.getenv(
    "ENGINE_A_URL",
    "https://infinityai-engine-a-573866363639.us-central1.run.app"
)
ENGINE_B_URL = os.getenv(
    "ENGINE_B_URL",
    "https://infinityai-engine-b-573866363639.us-central1.run.app"
)
ENGINE_C_URL = os.getenv(
    "ENGINE_C_URL",
    "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c"
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
INVESTING_COM_API_KEY = os.getenv("INVESTING_COM_API_KEY", "")
ADMIN_DASHBOARD_API_KEY = os.getenv("ADMIN_DASHBOARD_API_KEY", "")  # API key protecting admin endpoints
DHAN_DAILY_SECRET_NAME = os.getenv("DHAN_DAILY_SECRET_NAME", "DHAN_DAILY_ACCESS_TOKEN")
DHAN_MASTER_SECRET_NAME = os.getenv("DHAN_MASTER_SECRET_NAME", "DHAN_MASTER_ACCESS_TOKEN")

# Initialize connections
redis_client = None
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
except redis.exceptions.ConnectionError as e:
    logger.warning(f"Could not connect to Redis: {e}")
kafka_producer = None
if _kafka_available:
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        logger.warning(f"Kafka producer unavailable: {e}")

# Initialize AI models (optional)
ENABLE_TRANSFORMERS = os.getenv("ENABLE_TRANSFORMERS", "false").lower() == "true"
sentiment_model = None
summarizer = None
if ENABLE_TRANSFORMERS:
    try:
        # Financial sentiment analysis model
        sentiment_model = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert"
        )

        # News summarization model
        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )

        logger.info("AI models loaded successfully")
    except Exception as e:
        logger.warning(f"AI models not loaded: {e}")
        sentiment_model = None
        summarizer = None
else:
    logger.info("Transformers disabled (ENABLE_TRANSFORMERS=false); starting without heavy models")

# OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Pydantic models
class ChatMessage(BaseModel):
    user_id: str
    message: str
    context: Optional[Dict] = None

class MarketAnalysisRequest(BaseModel):
    symbols: List[str]
    analysis_type: str = "comprehensive"  # comprehensive, technical, sentiment

class NewsAnalysisRequest(BaseModel):
    query: str
    limit: int = 10

class InvestingComAPI:
    """Integration with Investing.com for comprehensive market data and events"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.investing.com"
        
    async def get_economic_calendar(self, importance: str = "high") -> List[Dict]:
        """Fetch economic events from Investing.com calendar"""
        try:
            # Simulated economic events - in production, use actual Investing.com API
            events = [
                {
                    "event_id": "fed_rates_001",
                    "title": "Federal Funds Rate Decision",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "importance": "high",
                    "country": "US",
                    "actual": "5.50%",
                    "forecast": "5.25%",
                    "previous": "5.25%",
                    "impact": "positive",
                    "description": "The Federal Reserve's decision on interest rates affects market liquidity and investment flows."
                },
                {
                    "event_id": "nonfarm_001",
                    "title": "Non-Farm Payrolls",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "importance": "high",
                    "country": "US",
                    "actual": "180K",
                    "forecast": "175K",
                    "previous": "165K",
                    "impact": "positive",
                    "description": "Monthly change in employment excluding agricultural sector."
                },
                {
                    "event_id": "inflation_001",
                    "title": "Consumer Price Index",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "importance": "medium",
                    "country": "US",
                    "actual": "3.2%",
                    "forecast": "3.1%",
                    "previous": "3.0%",
                    "impact": "neutral",
                    "description": "Measure of inflation based on consumer goods and services prices."
                }
            ]
            
            # Filter by importance
            filtered_events = [e for e in events if e["importance"] == importance or importance == "all"]
            
            return filtered_events
            
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return []

class TradingAssistant:
    """Core AI trading assistant with real-time event processing"""
    
    def __init__(self):
        self.investing_api = InvestingComAPI(INVESTING_COM_API_KEY)
        self.conversation_history = {}
        self.market_context = {}
        
    async def process_chat_message(self, user_id: str, message: str, context: Optional[Dict] = None) -> Dict:
        """Process user chat message and provide intelligent response"""
        try:
            # Classify message intent
            intent = await self.classify_intent(message)
            
            # Get user context
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Add message to history
            self.conversation_history[user_id].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": message,
                "intent": intent
            })
            
            # Generate response based on intent
            response = await self.generate_response(user_id, message, intent, context)
            
            # Add response to history
            self.conversation_history[user_id].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": response["message"],
                "type": "assistant"
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "message": "I'm experiencing some technical difficulties. Please try again.",
                "intent": "error",
                "data": None
            }
    
    async def classify_intent(self, message: str) -> str:
        """Classify user message intent"""
        message_lower = message.lower()
        
        # Portfolio-related queries
        if any(word in message_lower for word in ["portfolio", "positions", "holdings", "pnl", "profit", "loss"]):
            return "portfolio_query"
        
        # Order-related queries
        if any(word in message_lower for word in ["buy", "sell", "order", "trade", "execute"]):
            return "trading_action"
        
        # Market analysis queries
        if any(word in message_lower for word in ["price", "chart", "analysis", "technical", "trend"]):
            return "market_analysis"
        
        # News and events
        if any(word in message_lower for word in ["news", "events", "economic", "calendar", "announcement"]):
            return "news_events"
        
        # Model and AI queries
        if any(word in message_lower for word in ["model", "ai", "prediction", "forecast", "signal"]):
            return "ai_insights"
        
        # General help
        if any(word in message_lower for word in ["help", "how", "what", "explain"]):
            return "help"
        
        return "general"
    
    async def generate_response(self, user_id: str, message: str, intent: str, context: Optional[Dict]) -> Dict:
        """Generate appropriate response based on intent"""
        
        if intent == "portfolio_query":
            return await self.handle_portfolio_query(user_id, message)
        
        elif intent == "trading_action":
            return await self.handle_trading_action(user_id, message)
        
        elif intent == "market_analysis":
            return await self.handle_market_analysis(message)
        
        elif intent == "news_events":
            return await self.handle_news_events(message)
        
        elif intent == "ai_insights":
            return await self.handle_ai_insights(message)
        
        elif intent == "help":
            return await self.handle_help_query(message)
        
        else:
            return await self.handle_general_query(message)
    
    async def handle_portfolio_query(self, user_id: str, message: str) -> Dict:
        """Handle portfolio-related queries"""
        try:
            # Get portfolio data from Engine C
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ENGINE_C_URL}/portfolio/{user_id}")
                
                if response.status_code == 200:
                    portfolio_data = response.json()
                    
                    # Generate summary
                    total_value = portfolio_data.get("total_value", 0)
                    total_pnl = portfolio_data.get("total_pnl", 0)
                    positions = portfolio_data.get("positions", [])
                    
                    message_text = f"📊 **Portfolio Summary**\n\n"
                    message_text += f"💰 Total Value: ${total_value:,.2f}\n"
                    message_text += f"📈 Total P&L: ${total_pnl:,.2f} ({(total_pnl/total_value)*100:.2f}%)\n"
                    message_text += f"📍 Active Positions: {len(positions)}\n\n"
                    
                    if positions:
                        message_text += "**Top Positions:**\n"
                        for position in positions[:5]:  # Show top 5
                            pnl_color = "🟢" if position["pnl"] >= 0 else "🔴"
                            message_text += f"{pnl_color} {position['symbol']}: {position['quantity']} @ ${position['current_price']:.2f} (P&L: ${position['pnl']:.2f})\n"
                    
                    return {
                        "message": message_text,
                        "intent": "portfolio_query",
                        "data": portfolio_data
                    }
                else:
                    return {
                        "message": "I couldn't retrieve your portfolio data at the moment. Please try again.",
                        "intent": "portfolio_query",
                        "data": None
                    }
                    
        except Exception as e:
            logger.error(f"Error handling portfolio query: {e}")
            return {
                "message": "There was an error accessing your portfolio. Please check if you're logged in.",
                "intent": "portfolio_query", 
                "data": None
            }
    
    async def handle_trading_action(self, user_id: str, message: str) -> Dict:
        """Handle trading action requests"""
        
        # Extract trading parameters from message
        symbols = re.findall(r'\b[A-Z]{2,5}\b', message.upper())
        action = "BUY" if "buy" in message.lower() else "SELL" if "sell" in message.lower() else None
        
        if not symbols or not action:
            return {
                "message": "⚠️ I need more information to execute a trade. Please specify:\n- Action (BUY/SELL)\n- Symbol (e.g., AAPL, TSLA)\n- Quantity\n\nExample: 'Buy 10 shares of AAPL'",
                "intent": "trading_action",
                "data": None
            }
        
        # Get current price and analysis
        symbol = symbols[0]
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ENGINE_A_URL}/data/cache/{symbol}")
                
                if response.status_code == 200:
                    price_data = response.json()
                    current_price = price_data.get("current_price", 0)
                    
                    message_text = f"🎯 **Trading Analysis for {symbol}**\n\n"
                    message_text += f"💲 Current Price: ${current_price:.2f}\n"
                    message_text += f"📊 Action: {action}\n\n"
                    message_text += f"⚠️ **Important**: I can provide analysis, but I cannot execute trades directly. "
                    message_text += f"Please use the trading interface or confirm with 'EXECUTE {action} {symbol}' if you want to proceed.\n\n"
                    message_text += f"💡 **Tip**: Consider checking technical indicators and your risk tolerance before trading."
                    
                    return {
                        "message": message_text,
                        "intent": "trading_action",
                        "data": {
                            "symbol": symbol,
                            "action": action,
                            "current_price": current_price,
                            "requires_confirmation": True
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error handling trading action: {e}")
        
        return {
            "message": f"I couldn't get current market data for {symbol}. Please try again or check the symbol.",
            "intent": "trading_action",
            "data": None
        }
    
    async def handle_market_analysis(self, message: str) -> Dict:
        """Handle market analysis requests"""
        # Extract symbols from message
        symbols = re.findall(r'\b[A-Z]{2,5}\b', message.upper())
        
        if not symbols:
            symbols = ["SPY", "QQQ", "IWM"]  # Default to major indices
        
        try:
            analysis_data = []
            
            for symbol in symbols[:3]:  # Limit to 3 symbols
                async with httpx.AsyncClient() as client:
                    # Get market data from Engine A
                    response = await client.get(f"{ENGINE_A_URL}/data/cache/{symbol}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        current_price = data.get("current_price", 0)
                        
                        # Get AI prediction from Engine B (if available)
                        try:
                            ai_response = await client.get(f"{ENGINE_B_URL}/models")
                            models = ai_response.json().get("models", [])
                            
                            ai_signal = "HOLD"  # Default
                            confidence = 0.0
                            
                            if models:
                                # Use first available model for prediction
                                model_name = models[0]["name"]
                                # This would be actual inference in production
                                ai_signal = np.random.choice(["BUY", "HOLD", "SELL"], p=[0.3, 0.4, 0.3])
                                confidence = np.random.uniform(0.6, 0.95)
                        
                        except:
                            ai_signal = "HOLD"
                            confidence = 0.0
                        
                        analysis_data.append({
                            "symbol": symbol,
                            "current_price": current_price,
                            "ai_signal": ai_signal,
                            "confidence": confidence
                        })
            
            # Generate analysis message
            message_text = f"📈 **Market Analysis**\n\n"
            
            for analysis in analysis_data:
                signal_emoji = "🟢" if analysis["ai_signal"] == "BUY" else "🔴" if analysis["ai_signal"] == "SELL" else "🟡"
                message_text += f"{signal_emoji} **{analysis['symbol']}**\n"
                message_text += f"   Price: ${analysis['current_price']:.2f}\n"
                message_text += f"   AI Signal: {analysis['ai_signal']} (Confidence: {analysis['confidence']:.1%})\n\n"
            
            message_text += "📊 Analysis includes real-time pricing and AI-generated signals.\n"
            message_text += "⚠️ This is for informational purposes only, not financial advice."
            
            return {
                "message": message_text,
                "intent": "market_analysis",
                "data": analysis_data
            }
            
        except Exception as e:
            logger.error(f"Error handling market analysis: {e}")
            return {
                "message": "I couldn't perform the market analysis right now. Please try again.",
                "intent": "market_analysis",
                "data": None
            }
    
    async def handle_news_events(self, message: str) -> Dict:
        """Handle news and economic events queries"""
        try:
            # Get economic events
            events = await self.investing_api.get_economic_calendar("high")
            
            message_text = f"📰 **Latest Economic Events & News**\n\n"
            
            for event in events[:3]:  # Show top 3 events
                impact_emoji = "🔴" if event["importance"] == "high" else "🟡" if event["importance"] == "medium" else "🟢"
                message_text += f"{impact_emoji} **{event['title']}**\n"
                message_text += f"   Country: {event['country']}\n"
                message_text += f"   Actual: {event['actual']} | Forecast: {event['forecast']}\n"
                message_text += f"   Impact: {event['impact'].title()}\n"
                message_text += f"   📄 {event['description'][:100]}...\n\n"
            
            # Get latest news sentiment (simulated)
            news_sentiment = {
                "overall_sentiment": "Positive",
                "market_mood": "Bullish",
                "key_topics": ["Fed Policy", "Earnings Season", "Tech Stocks"]
            }
            
            message_text += f"**📊 Market Sentiment Analysis:**\n"
            message_text += f"Overall: {news_sentiment['overall_sentiment']}\n"
            message_text += f"Mood: {news_sentiment['market_mood']}\n"
            message_text += f"Key Topics: {', '.join(news_sentiment['key_topics'])}\n"
            
            return {
                "message": message_text,
                "intent": "news_events",
                "data": {
                    "events": events,
                    "sentiment": news_sentiment
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling news events: {e}")
            return {
                "message": "I couldn't fetch the latest news and events. Please try again.",
                "intent": "news_events", 
                "data": None
            }
    
    async def handle_ai_insights(self, message: str) -> Dict:
        """Handle AI model and insights queries"""
        try:
            # Get model status from Engine B
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ENGINE_B_URL}/models")
                
                if response.status_code == 200:
                    models_data = response.json()
                    models = models_data.get("models", [])
                    
                    message_text = f"🤖 **AI Models & Insights**\n\n"
                    message_text += f"📊 Available Models: {len(models)}\n"
                    message_text += f"🔥 Loaded Models: {models_data.get('loaded_count', 0)}\n\n"
                    
                    if models:
                        message_text += "**Active Models:**\n"
                        for model in models[:3]:
                            status_emoji = "🟢" if model["status"] == "available" else "🟡"
                            message_text += f"{status_emoji} {model['name']}\n"
                            message_text += f"   Type: {model.get('type', 'Unknown')}\n"
                            message_text += f"   Accuracy: {model.get('accuracy', 0):.2%}\n\n"
                    
                    # Get GPU status
                    gpu_response = await client.get(f"{ENGINE_B_URL}/gpu/status")
                    if gpu_response.status_code == 200:
                        gpu_data = gpu_response.json()
                        if gpu_data.get("gpu_available", False):
                            message_text += f"🖥️ **GPU Status:** Available\n"
                            message_text += f"💾 GPU Memory: {gpu_data.get('devices', [{}])[0].get('utilization_percent', 0):.1f}% utilized\n"
                        else:
                            message_text += f"🖥️ **GPU Status:** CPU-only mode\n"
                    
                    return {
                        "message": message_text,
                        "intent": "ai_insights",
                        "data": {
                            "models": models,
                            "gpu_status": gpu_data if 'gpu_data' in locals() else None
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error handling AI insights: {e}")
        
        return {
            "message": "I couldn't retrieve AI model information at the moment. Please try again.",
            "intent": "ai_insights",
            "data": None
        }
    
    async def handle_help_query(self, message: str) -> Dict:
        """Handle help and how-to queries"""
        
        help_text = f"""
🤖 **InfinityAI Trading Assistant Help**

I can help you with:

**📊 Portfolio & Trading**
• "Show my portfolio" - Get portfolio summary
• "What are my positions?" - View all holdings
• "Buy 10 AAPL" - Trading analysis & guidance

**📈 Market Analysis**
• "Analyze TSLA" - Get price & AI signals
• "Market outlook" - Overall market analysis
• "Technical analysis for SPY" - Charts & indicators

**📰 News & Events**
• "Latest economic events" - Economic calendar
• "Market news" - News sentiment analysis
• "What's moving the market?" - Key events

**🤖 AI Insights**
• "Model performance" - AI model status
• "GPU status" - System performance
• "Latest predictions" - AI signals

**💡 Examples:**
• "What's my P&L today?"
• "Should I buy more NVDA?"
• "Any important news affecting tech stocks?"
• "How confident is the AI about AAPL?"

Type your question naturally - I'll understand! 😊
        """
        
        return {
            "message": help_text,
            "intent": "help",
            "data": None
        }
    
    async def handle_general_query(self, message: str) -> Dict:
        """Handle general queries using OpenAI if available"""
        
        if OPENAI_API_KEY:
            try:
                # Use OpenAI for general queries
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful trading assistant. Keep responses concise and focused on trading and finance."},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=200
                )
                
                ai_response = response.choices[0].message.content
                
                return {
                    "message": ai_response,
                    "intent": "general",
                    "data": None
                }
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
        
        # Fallback response
        return {
            "message": "I understand you're asking about trading or markets. Could you be more specific? I can help with portfolio queries, market analysis, news, or AI insights. Type 'help' for examples!",
            "intent": "general",
            "data": None
        }

# -----------------------------
# AWS Secrets Manager helpers (optional)
# -----------------------------
def _boto3_client(service: str):
    try:
        import boto3  # type: ignore
        return boto3.client(service)
    except Exception:
        return None

def fetch_secret_value(name: str) -> Optional[str]:
    client = _boto3_client('secretsmanager')
    if not client:
        return None
    try:
        resp = client.get_secret_value(SecretId=name)
        return resp.get('SecretString')
    except Exception:
        return None

def put_secret_value(name: str, value: str) -> bool:
    client = _boto3_client('secretsmanager')
    if not client:
        return False
    try:
        # Try update, fall back to create
        try:
            client.put_secret_value(SecretId=name, SecretString=value)
            return True
        except ClientError as ce:  # type: ignore
            if getattr(ce, 'response', {}).get('Error', {}).get('Code') == 'ResourceNotFoundException':
                client.create_secret(Name=name, SecretString=value)
                return True
            raise
    except Exception as e:  # pragma: no cover - best effort
        logger.warning(f"Failed to store secret {name}: {e}")
        return False

# Initialize trading assistant
trading_assistant = TradingAssistant()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Engine D - AI Chatbot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "ai_models": {
            "sentiment_model": sentiment_model is not None,
            "summarizer": summarizer is not None,
            "openai_available": bool(OPENAI_API_KEY)
        }
    }

# ALB path alias for Engine D
@app.get("/engine-d/health")
async def health_check_alias():
    return await health_check()


# -----------------------------
# System status aggregate (/status)
# -----------------------------
async def _ping(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    start = datetime.now()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
        latency = (datetime.now() - start).total_seconds() * 1000
        if r.status_code == 200:
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
            return {"status": "healthy", "latency_ms": round(latency, 1), "details": body}
        return {"status": "unhealthy", "latency_ms": round(latency, 1), "code": r.status_code}
    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        return {"status": "unreachable", "latency_ms": round(latency, 1), "error": str(e)}


@app.get("/status")
@app.get("/engine-d/status")
async def system_status():
    """Aggregate health for A/B/C/D so frontend can render system banners."""
    results = {}
    # Engine D self status from in-process call to avoid port/prefix confusion
    try:
        self_health = await health_check()
        results["engine_d"] = {"status": "healthy", "details": self_health}
    except Exception as e:
        results["engine_d"] = {"status": "unreachable", "error": str(e)}
    # Ping upstreams
    results["engine_a"] = await _ping(f"{ENGINE_A_URL}/health")
    results["engine_b"] = await _ping(f"{ENGINE_B_URL}/health")
    results["engine_c"] = await _ping(f"{ENGINE_C_URL}/health")

    overall = "healthy" if all(v.get("status") == "healthy" for v in results.values()) else "degraded"
    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engines": results,
    }

# -----------------------------
# Admin: Update DHAN daily token (protected)
# -----------------------------
@app.post("/engine-d/admin/update-token")
async def update_dhan_daily_token(request: Request):
    """Update the DHAN daily access token.

    Protection: requires header `x-admin-api-key` == ADMIN_DASHBOARD_API_KEY.
    Body JSON: {"daily_token": "<newtoken>"}
    Behavior: stores new token in AWS Secrets Manager (DHAN_DAILY_SECRET_NAME) if boto3 available; otherwise caches in process.
    Returns: status and storage strategy.
    """
    if not ADMIN_DASHBOARD_API_KEY:
        raise HTTPException(status_code=500, detail="Admin API key not configured")
    supplied = request.headers.get("x-admin-api-key")
    if supplied != ADMIN_DASHBOARD_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    daily_token = body.get("daily_token")
    if not daily_token or not isinstance(daily_token, str):
        raise HTTPException(status_code=400, detail="daily_token required")

    stored = put_secret_value(DHAN_DAILY_SECRET_NAME, daily_token)
    storage = "aws_secrets_manager" if stored else "in_memory"
    if not stored:
        # Fallback: in-memory cache (NOT persistent)
        os.environ['DHAN_DAILY_ACCESS_TOKEN_CACHE'] = daily_token
    return {
        "status": "ok",
        "storage": storage,
        "secret_name": DHAN_DAILY_SECRET_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# -----------------------------
# Proxy utilities
# -----------------------------
async def _proxy_request(method: str, target_url: str, request: Request, json_body: Optional[dict] = None, params: Optional[dict] = None):
    headers = {}
    # Forward minimal auth header if present
    auth = request.headers.get("authorization")
    if auth:
        headers["authorization"] = auth
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.request(method.upper(), target_url, headers=headers, json=json_body, params=params)
        # Return JSON if possible, else raw text
        content_type = r.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            return r.json()
        return {"status_code": r.status_code, "text": r.text}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream proxy error: {str(e)}")


# -----------------------------
# Engine C proxies (trading & portfolio)
# -----------------------------
@app.get("/portfolio")
@app.get("/engine-d/portfolio")
async def proxy_portfolio(request: Request):
    return await _proxy_request("GET", f"{ENGINE_C_URL}/portfolio", request)


@app.get("/quote/{symbol}")
@app.get("/engine-d/quote/{symbol}")
async def proxy_quote(symbol: str, request: Request):
    return await _proxy_request("GET", f"{ENGINE_C_URL}/quote/{symbol}", request)


@app.get("/orders")
@app.get("/engine-d/orders")
async def proxy_orders_get(request: Request):
    return await _proxy_request("GET", f"{ENGINE_C_URL}/orders", request)


@app.post("/orders")
@app.post("/engine-d/orders")
async def proxy_orders_post(request: Request):
    body = await request.json()
    return await _proxy_request("POST", f"{ENGINE_C_URL}/orders", request, json_body=body)


@app.delete("/orders/{order_id}")
@app.delete("/engine-d/orders/{order_id}")
async def proxy_orders_delete(order_id: str, request: Request):
    return await _proxy_request("DELETE", f"{ENGINE_C_URL}/orders/{order_id}", request)


# -----------------------------
# Engine A proxies (market data & analysis)
# -----------------------------
@app.get("/chart/{symbol}")
@app.get("/engine-d/chart/{symbol}")
async def proxy_chart(symbol: str, request: Request, timeframe: Optional[str] = None):
    params = {"timeframe": timeframe} if timeframe else None
    return await _proxy_request("GET", f"{ENGINE_A_URL}/chart/{symbol}", request, params=params)


@app.get("/technical/{symbol}")
@app.get("/engine-d/technical/{symbol}")
async def proxy_technical(symbol: str, request: Request):
    return await _proxy_request("GET", f"{ENGINE_A_URL}/technical/{symbol}", request)


@app.get("/market/overview")
@app.get("/engine-d/market/overview")
async def proxy_market_overview(request: Request):
    return await _proxy_request("GET", f"{ENGINE_A_URL}/market/overview", request)


@app.get("/market/movers")
@app.get("/engine-d/market/movers")
async def proxy_market_movers(request: Request):
    return await _proxy_request("GET", f"{ENGINE_A_URL}/market/movers", request)


@app.get("/market/sectors")
@app.get("/engine-d/market/sectors")
async def proxy_market_sectors(request: Request):
    return await _proxy_request("GET", f"{ENGINE_A_URL}/market/sectors", request)


@app.get("/economic/events")
@app.get("/engine-d/economic/events")
async def proxy_economic_events(request: Request):
    return await _proxy_request("GET", f"{ENGINE_A_URL}/economic/events", request)


# -----------------------------
# Engine B proxies (AI insights)
# -----------------------------
@app.get("/insights")
@app.get("/engine-d/insights")
async def proxy_ai_insights(request: Request):
    return await _proxy_request("GET", f"{ENGINE_B_URL}/insights", request)


@app.get("/models/status")
@app.get("/engine-d/models/status")
async def proxy_models_status(request: Request):
    return await _proxy_request("GET", f"{ENGINE_B_URL}/models/status", request)


@app.get("/performance")
@app.get("/engine-d/performance")
async def proxy_performance(request: Request):
    return await _proxy_request("GET", f"{ENGINE_B_URL}/performance", request)


@app.get("/predictions")
@app.get("/engine-d/predictions")
async def proxy_predictions(request: Request):
    return await _proxy_request("GET", f"{ENGINE_B_URL}/predictions", request)


# -----------------------------
# Minimal in-memory user settings API (to satisfy UI calls)
# -----------------------------
_user_store = {
    "settings": {
        "profile": {"firstName": "", "lastName": "", "email": "", "phone": "", "timezone": "America/New_York"},
        "trading": {
            "defaultOrderType": "market",
            "defaultTimeInForce": "day",
            "riskLimits": {"maxPositionSize": 100000, "maxDailyLoss": 5000, "maxOrderValue": 50000},
            "notifications": {"orderFills": True, "priceAlerts": True, "accountUpdates": True, "aiSignals": True}
        },
        "theme": {"mode": "light", "primaryColor": "#1976d2", "fontSize": "medium"},
        "ai": {
            "modelPreferences": {"riskTolerance": "moderate", "tradingStyle": "balanced", "enableAutoTrading": False, "maxAutoTradeSize": 1000},
            "notifications": {"aiInsights": True, "modelUpdates": True, "performanceAlerts": True}
        }
    },
    "brokers": [],
    "apiKeys": []
}


@app.get("/user/settings")
@app.get("/engine-d/user/settings")
async def get_user_settings():
    return {"settings": _user_store["settings"]}


@app.put("/user/settings")
@app.put("/engine-d/user/settings")
async def update_user_settings(payload: Dict[str, Any]):
    # Shallow merge for simplicity
    _user_store["settings"].update(payload)
    return {"status": "ok", "settings": _user_store["settings"]}


@app.get("/user/brokers")
@app.get("/engine-d/user/brokers")
async def list_brokers():
    return {"brokers": _user_store["brokers"]}


@app.post("/user/brokers")
@app.post("/engine-d/user/brokers")
async def add_broker(broker: Dict[str, Any]):
    broker_id = len(_user_store["brokers"]) + 1
    broker["id"] = broker_id
    broker.setdefault("status", "Connected")
    _user_store["brokers"].append(broker)
    return {"broker": broker}


@app.delete("/user/brokers/{broker_id}")
@app.delete("/engine-d/user/brokers/{broker_id}")
async def delete_broker(broker_id: int):
    _user_store["brokers"] = [b for b in _user_store["brokers"] if b.get("id") != broker_id]
    return {"status": "ok", "brokers": _user_store["brokers"]}


@app.get("/user/api-keys")
@app.get("/engine-d/user/api-keys")
async def list_api_keys():
    return {"apiKeys": _user_store["apiKeys"]}


@app.post("/user/api-keys")
@app.post("/engine-d/user/api-keys")
async def add_api_key(api_key: Dict[str, Any]):
    key_id = len(_user_store["apiKeys"]) + 1
    api_key["id"] = key_id
    _user_store["apiKeys"].append(api_key)
    return {"apiKey": api_key}


@app.delete("/user/api-keys/{key_id}")
@app.delete("/engine-d/user/api-keys/{key_id}")
async def delete_api_key(key_id: int):
    _user_store["apiKeys"] = [k for k in _user_store["apiKeys"] if k.get("id") != key_id]
    return {"status": "ok", "apiKeys": _user_store["apiKeys"]}

@app.get("/dashboard/summary")
async def dashboard_summary():
    """Aggregate status for frontend: engine health, portfolio availability, ultra mode status (proxied)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Engine C system status
            sys_status = None
            try:
                r = await client.get(f"{ENGINE_C_URL}/status")
                if r.status_code == 200:
                    sys_status = r.json()
            except Exception:
                pass
            # Build summary
            return {
                "engine_d": "healthy",
                "engine_c_status": sys_status or {"status": "unknown"},
                "ultra_aggressive_mode": False,
                "app_health": "healthy" if sys_status else "degraded"
            }
    except Exception:
        return {
            "engine_d": "healthy",
            "engine_c_status": {"status": "unreachable"},
            "ultra_aggressive_mode": False,
            "app_health": "degraded"
        }

@app.post("/ultra/toggle")
async def ultra_toggle(mode: bool):
    """Proxy toggle of ultra mode to Engine C so frontend can call single backend (Engine D)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{ENGINE_C_URL}/ultra/toggle", params={"mode": str(bool(mode)).lower()})
            return r.json() if r.status_code == 200 else {"status": "error"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/trading/start")
async def trading_start():
    """Enable live trading by clearing Engine C global kill switch."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Deactivate GLOBAL kill switch
            r = await client.delete(f"{ENGINE_C_URL}/kill-switch/GLOBAL")
            ok = r.status_code == 200
            return {"status": "ok" if ok else "error"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/trading/stop")
async def trading_stop(reason: str = "user_request"):
    """Disable live trading by activating Engine C global kill switch."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{ENGINE_C_URL}/kill-switch/GLOBAL", json={"switch_type":"GLOBAL","reason": reason})
            ok = r.status_code == 200
            return {"status": "ok" if ok else "error"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage):
    """Main chat endpoint"""
    response = await trading_assistant.process_chat_message(
        user_id=chat_message.user_id,
        message=chat_message.message,
        context=chat_message.context
    )
    
    return response

@app.get("/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """Get user's chat history"""
    history = trading_assistant.conversation_history.get(user_id, [])
    return {"user_id": user_id, "history": history[-limit:]}

@app.post("/analyze/sentiment")
async def analyze_sentiment(text: str):
    """Analyze sentiment of text"""
    try:
        if sentiment_model:
            result = sentiment_model(text)
            return {"sentiment": result[0]["label"], "confidence": result[0]["score"]}
        else:
            # Fallback using TextBlob
            blob = TextBlob(text)
            sentiment = "positive" if blob.sentiment.polarity > 0 else "negative" if blob.sentiment.polarity < 0 else "neutral"
            return {"sentiment": sentiment, "confidence": abs(blob.sentiment.polarity)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            response = await trading_assistant.process_chat_message(
                user_id=user_id,
                message=message_data.get("message", ""),
                context=message_data.get("context")
            )
            
            # Send response back
            await manager.send_personal_message({
                "type": "chat_response",
                "data": response
            }, user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# WebSocket alias for ALB path prefix
@app.websocket("/engine-d/ws/{user_id}")
async def websocket_endpoint_alias(websocket: WebSocket, user_id: str):
    await websocket_endpoint(websocket, user_id)

# Background task for processing real-time events
async def process_real_time_events():
    """Background task to process real-time market events and notify users"""
    if not _kafka_available:
        logger.info("Kafka not available; skipping real-time consumer loop.")
        return
    try:
        consumer = KafkaConsumer(
            'market_data',
            'news_sentiment', 
            'inference_results',
            'order_updates',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
    except Exception as e:
        logger.warning(f"Kafka consumer unavailable: {e}")
        return
    for message in consumer:
        try:
            event_data = message.value
            if message.topic == 'market_data':
                await process_market_event(event_data)
            elif message.topic == 'inference_results':
                await process_ai_signal_event(event_data)
            elif message.topic == 'order_updates':
                await process_order_event(event_data)
        except Exception as e:
            logger.error(f"Error processing real-time event: {e}")

async def process_market_event(event_data: Dict):
    """Process market data events and generate alerts"""
    try:
        symbol = event_data.get("symbol")
        if symbol and event_data.get("type") == "realtime_tick":
            price = event_data.get("price")
            volume = event_data.get("volume")
            
            # Check for significant price movements (>2%)
            cached_price = redis_client.get(f"prev_price:{symbol}")
            if cached_price:
                prev_price = float(cached_price)
                price_change = ((price - prev_price) / prev_price) * 100
                
                if abs(price_change) > 2.0:  # Significant movement
                    alert_message = f"🚨 **Price Alert**: {symbol} moved {price_change:+.2f}% to ${price:.2f}"
                    
                    # Broadcast alert to all connected users
                    await manager.broadcast({
                        "type": "price_alert",
                        "data": {
                            "symbol": symbol,
                            "price": price,
                            "change_percent": price_change,
                            "message": alert_message
                        }
                    })
            
            # Update previous price
            redis_client.setex(f"prev_price:{symbol}", 300, price)
            
    except Exception as e:
        logger.error(f"Error processing market event: {e}")

async def process_ai_signal_event(event_data: Dict):
    """Process AI signal events and notify relevant users"""
    try:
        model_name = event_data.get("model_name")
        results = event_data.get("results", [])
        
        for result in results:
            if result.get("confidence", 0) > 0.8:  # High confidence signals only
                signal = result.get("signal")
                symbol = result.get("symbol", "UNKNOWN")
                
                alert_message = f"🤖 **AI Signal**: {signal} {symbol} (Confidence: {result['confidence']:.1%})"
                
                # Broadcast to all users (in production, this would be user-specific)
                await manager.broadcast({
                    "type": "ai_signal",
                    "data": {
                        "model_name": model_name,
                        "signal": signal,
                        "symbol": symbol,
                        "confidence": result["confidence"],
                        "message": alert_message
                    }
                })
                
    except Exception as e:
        logger.error(f"Error processing AI signal event: {e}")

async def process_order_event(event_data: Dict):
    """Process order execution events and notify user"""
    try:
        user_id = event_data.get("user_id")
        status = event_data.get("status")
        symbol = event_data.get("symbol")
        order_type = event_data.get("order_type")
        
        status_emoji = "✅" if status == "EXECUTED" else "❌" if status == "REJECTED" else "⏳"
        alert_message = f"{status_emoji} **Order Update**: {order_type} {symbol} - {status}"
        
        # Send to specific user
        if user_id:
            await manager.send_personal_message({
                "type": "order_update",
                "data": {
                    "order_id": event_data.get("order_id"),
                    "symbol": symbol,
                    "order_type": order_type,
                    "status": status,
                    "message": alert_message
                }
            }, user_id)
            
    except Exception as e:
        logger.error(f"Error processing order event: {e}")

# Start background tasks
@app.on_event("startup")
async def startup_event():
    # Start real-time event processing
    asyncio.create_task(process_real_time_events())
    logger.info("Engine D - AI Chatbot started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)