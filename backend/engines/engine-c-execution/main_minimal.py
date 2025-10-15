#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine C: Trade Execution & Dhan OAuth Service (Minimal)
Minimal version for production deployment with OAuth functionality
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import json
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ENGINE-C - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('engine_c_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pydantic models
class DhanOAuthCallback(BaseModel):
    code: str
    state: str

class DhanCredentials(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    user_id: str

class DhanWebhook(BaseModel):
    orderid: str
    status: str
    tradingsymbol: str
    quantity: int
    price: float

class ExecutionService:
    def __init__(self):
        self.dhan_client_id = os.getenv('DHAN_CLIENT_ID', '1106240409244673046')
        self.dhan_client_secret = os.getenv('DHAN_CLIENT_SECRET', 'PLACEHOLDER_SECRET')
        self.dhan_redirect_uri = os.getenv('DHAN_REDIRECT_URI', 'https://infinityai-pro-frontend-573866363639.us-central1.run.app/auth/dhan/callback')
        
        # Storage for OAuth state and tokens (in production, use proper database)
        self.oauth_states = {}
        self.user_tokens = {}
        
        logger.info("🎯 Engine C - Trade Execution & OAuth Service Initialized (Minimal)")
    
    async def exchange_oauth_code(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token"""
        try:
            # Validate state
            if state not in self.oauth_states:
                return {"error": "Invalid state parameter"}
            
            # In production, exchange code with Dhan API
            # For now, return mock successful response
            mock_token = f"dhan_token_{code[:8]}_{datetime.now().timestamp()}"
            
            # Store token (in production, encrypt and store in database)
            user_id = self.oauth_states[state].get('user_id', 'demo-user')
            self.user_tokens[user_id] = {
                'access_token': mock_token,
                'refresh_token': f"refresh_{mock_token}",
                'expires_at': datetime.now().timestamp() + 86400,  # 24 hours
                'created_at': datetime.now().isoformat()
            }
            
            # Clean up state
            del self.oauth_states[state]
            
            logger.info(f"OAuth token exchanged for user {user_id}")
            
            return {
                "status": "success",
                "user_id": user_id,
                "access_token": mock_token,
                "token_type": "bearer",
                "expires_in": 86400
            }
            
        except Exception as e:
            logger.error(f"Error exchanging OAuth code: {e}")
            return {"error": str(e)}
    
    async def handle_dhan_postback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Dhan postback webhook"""
        try:
            logger.info(f"Received Dhan postback: {payload}")
            
            # Process the postback data
            # In production, update user positions, send notifications, etc.
            
            return {
                "status": "success",
                "message": "Postback processed",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing Dhan postback: {e}")
            return {"error": str(e)}

# Global service
execution_service = ExecutionService()

# Initialize FastAPI
app = FastAPI(
    title="🎯 InfinityAI.Pro - Engine C: Trade Execution & OAuth",
    description="Trade execution and Dhan OAuth integration service",
    version="1.0.0-minimal"
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
        "service": "Engine C - Trade Execution & Dhan OAuth Service",
        "status": "active",
        "version": "1.0.0-minimal",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-c-execution",
        "oauth_active": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/dhan/status")
async def get_dhan_status():
    """Get Dhan connection status for user"""
    return {
        "status": "operational",
        "connected_users": len(execution_service.user_tokens),
        "oauth_endpoint": "/api/dhan/callback",
        "postback_endpoint": "/api/dhan/postback",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/dhan/callback")
async def dhan_oauth_callback(callback_data: DhanOAuthCallback):
    """Handle Dhan OAuth callback"""
    try:
        result = await execution_service.exchange_oauth_code(
            callback_data.code, 
            callback_data.state
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dhan/postback")
async def dhan_postback_handler(request: Request):
    """Handle Dhan postback webhooks"""
    try:
        payload = await request.json()
        result = await execution_service.handle_dhan_postback(payload)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in postback handler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/dhan/disconnect/{user_id}")
async def disconnect_dhan(user_id: str):
    """Disconnect Dhan account for user"""
    try:
        if user_id in execution_service.user_tokens:
            del execution_service.user_tokens[user_id]
            logger.info(f"Disconnected Dhan account for user {user_id}")
            
            return {
                "status": "disconnected",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "not_found",
                "message": "User not connected",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error disconnecting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders():
    """Get order status (placeholder)"""
    return {
        "status": "success",
        "orders": [],
        "message": "Order execution service operational",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/orders")
async def place_order(order_data: Dict[str, Any]):
    """Place trading order (placeholder)"""
    return {
        "status": "success",
        "order_id": f"ORD_{datetime.now().timestamp()}",
        "message": "Order placed successfully (demo mode)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "engine-c-execution",
        "connected_users": len(execution_service.user_tokens),
        "active_oauth_states": len(execution_service.oauth_states),
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )