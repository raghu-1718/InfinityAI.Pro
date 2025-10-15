from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from typing import Dict, Any, Optional
import asyncio
import json
import time

# Import our health orchestrator
from health_orchestrator import health_orchestrator

app = FastAPI(
    title="InfinityAI Engine D - Chatbot & Orchestration",
    description="Multi-engine orchestration and AI chatbot service",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    status: str
    message_id: str
    response: str
    intent: str
    confidence: float
    timestamp: str

# Simple chat intent classifier
def classify_intent(message: str) -> tuple[str, float]:
    """Simple intent classification"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['status', 'health', 'system', 'running']):
        return 'status', 0.9
    elif any(word in message_lower for word in ['market', 'price', 'signal', 'data']):
        return 'market_data', 0.8
    elif any(word in message_lower for word in ['ai', 'predict', 'forecast', 'analysis']):
        return 'ai_prediction', 0.8
    elif any(word in message_lower for word in ['trade', 'buy', 'sell', 'order']):
        return 'trade_execution', 0.7
    elif any(word in message_lower for word in ['portfolio', 'balance', 'holdings']):
        return 'portfolio', 0.8
    elif any(word in message_lower for word in ['dhan', 'oauth', 'connect', 'account']):
        return 'account_management', 0.7
    else:
        return 'general', 0.5

async def generate_response(intent: str, message: str, confidence: float) -> str:
    """Generate contextual responses based on intent"""
    
    if intent == 'status':
        # Get real-time health status
        try:
            health_data = await health_orchestrator.get_comprehensive_health()
            summary = health_data['summary']
            
            response = f"🚀 **System Status Report**\n\n"
            response += f"📊 **Health**: {summary['healthy_engines']}/{summary['total_engines']} engines online ({summary['health_percentage']}%)\n"
            response += f"⚡ **Performance**: {summary['avg_response_time_ms']}ms avg response time\n"
            response += f"🎯 **Status**: {summary['overall_status'].upper()}\n\n"
            
            response += "**Engine Details:**\n"
            for name, engine_data in health_data['engines'].items():
                status_icon = "✅" if engine_data['healthy'] else "❌"
                response += f"{status_icon} **Engine {name}**: {engine_data['status']} ({engine_data['response_time_ms']}ms)\n"
            
            return response
            
        except Exception as e:
            return f"⚠️ **System Status**: Error retrieving health data - {str(e)[:50]}"
    
    elif intent == 'market_data':
        return "📈 **Market Data**: Connecting to Engine A for live NSE/BSE/MCX data. Please check market signals endpoint for real-time information."
    
    elif intent == 'ai_prediction':
        return "🤖 **AI Predictions**: Engine B provides ML-powered trading signals with 11 technical indicators. Check AI signals endpoint for live predictions."
    
    elif intent == 'trade_execution':
        return "💰 **Trading**: Engine C handles trade execution via Dhan API integration. Please ensure your Dhan account is connected for live trading."
    
    elif intent == 'portfolio':
        return "📊 **Portfolio**: Portfolio data available through Engine C. Connect your Dhan account to view live holdings and P&L."
    
    elif intent == 'account_management':
        return "🔐 **Account Management**: Use Engine C's OAuth endpoints to connect your Dhan trading account securely."
    
    else:
        return f"🤖 **InfinityAI Assistant**: I understand you're asking about '{message}'. I can help with system status, market data, AI predictions, trading, and account management. What would you like to know?"

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Get quick health summary
        health_data = await health_orchestrator.get_comprehensive_health()
        summary = health_data['summary']
        
        return {
            "status": "healthy",
            "service": "engine-d-chatbot",
            "engines_configured": summary['total_engines'],
            "engines_healthy": summary['healthy_engines'],
            "health_percentage": summary['health_percentage'],
            "overall_status": summary['overall_status'],
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            "uptime": "running"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "engine-d-chatbot", 
            "error": str(e)[:100],
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }

@app.get("/api/health/comprehensive")
async def comprehensive_health():
    """Comprehensive health check of all engines"""
    try:
        return await health_orchestrator.get_comprehensive_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/health/simple")
async def simple_health():
    """Simple boolean health status for frontend"""
    try:
        health_data = await health_orchestrator.get_comprehensive_health()
        return {
            "engines": health_orchestrator.get_simple_health_status(),
            "summary": health_data['summary']
        }
    except Exception as e:
        return {
            "engines": {name: False for name in ['A', 'B', 'C', 'D', 'ULTRA']},
            "summary": {"healthy_engines": 0, "total_engines": 5, "health_percentage": 0, "overall_status": "critical"},
            "error": str(e)[:100]
        }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Enhanced chat endpoint with real-time system awareness"""
    try:
        # Classify intent
        intent, confidence = classify_intent(request.message)
        
        # Generate response
        response_text = await generate_response(intent, request.message, confidence)
        
        # Create response
        response = ChatResponse(
            status="success",
            message_id=f"msg_{int(time.time())}_{hash(request.user_id) % 10000}",
            response=response_text,
            intent=intent,
            confidence=confidence,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        )
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message_id": f"error_{int(time.time())}",
            "response": f"Sorry, I encountered an error: {str(e)[:100]}",
            "intent": "error",
            "confidence": 0.0,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }

@app.get("/api/engines/status")
async def engines_status():
    """Get detailed status of all engines"""
    try:
        health_data = await health_orchestrator.get_comprehensive_health()
        return {
            "status": "success",
            "data": health_data,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get engine status: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "InfinityAI Engine D - Chatbot & Orchestration",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Multi-engine health monitoring",
            "Real-time system orchestration", 
            "AI-powered chatbot",
            "Intent recognition",
            "Comprehensive health reporting"
        ],
        "endpoints": [
            "/health - Basic health check",
            "/api/health/comprehensive - Full system health",
            "/api/health/simple - Boolean health status",
            "/api/chat - AI chatbot interface",
            "/api/engines/status - Detailed engine status"
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)