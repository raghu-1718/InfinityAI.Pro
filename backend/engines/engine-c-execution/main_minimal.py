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
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
        self.dhan_client_id = os.getenv('DHAN_CLIENT_ID', '1101302170')
        self.dhan_client_secret = os.getenv('DHAN_CLIENT_SECRET', 'PLACEHOLDER_SECRET')
        self.dhan_redirect_uri = os.getenv('DHAN_REDIRECT_URI', 'https://engine-c-573866363639.us-central1.run.app/api/dhan/callback')
        
        # Dhan API configuration
        self.dhan_base_url = "https://api.dhan.co"
        self.access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NjA2MDM3NTEsImlhdCI6MTc2MDUxNzM1MSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtNTczODY2MzYzNjM5LTU3Mzg2NjM2MzYzOS51cy1jZW50cmFsMS5ydW4uYXBwL2FwaS9kaGFuL3Bvc3RiYWNrIiwiZGhhbkNsaWVudElkIjoiMTEwMTMwMjE3MCJ9.cRhYjn044i_CrOwTV5ZxQOPnR_iWNnWcGHWF_q41wSdh02-wLQBFOLeD8TQPaIKdZBXqxQvwKDm6Y0DEfs0JZA"
        self.headers = {
            "access-token": self.access_token,
            "Content-Type": "application/json"
        }
        
        # Storage for OAuth state and tokens (in production, use proper database)
        self.oauth_states = {}
        self.user_tokens = {}
        
        # AI Auto-Trading System
        self.ai_trading_active = False
        self.ai_trading_task = None
        self.ai_engine_b_url = "https://engine-b-ai-ml-573866363639.us-central1.run.app"
        self.execution_history = []
        self.trading_config = {
            "min_confidence": 0.75,  # Minimum AI confidence to execute trades
            "max_risk_per_trade": 0.02,  # Max 2% risk per trade
            "max_daily_trades": 10,
            "trading_amount": 1000  # Default amount per trade
        }
        
        logger.info("🎯 Engine C - Trade Execution & OAuth Service Initialized (Minimal)")
    
    async def fetch_dhan_data(self, endpoint: str):
        """Fetch data from Dhan API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.dhan_base_url}{endpoint}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        # Handle expected errors (like no holdings)
                        error_data = await response.json()
                        if "No holdings available" in error_data.get("internalErrorMessage", ""):
                            return []
                        return None
                    else:
                        return None
        except Exception as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            return None
    
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
    
    async def fetch_ai_signals(self) -> Optional[List[Dict]]:
        """Fetch AI signals from Engine B"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ai_engine_b_url}/api/ai-signals"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("ai_signals", [])
                    else:
                        logger.error(f"Failed to fetch AI signals: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching AI signals: {e}")
            return []
    
    async def execute_ai_trade(self, signal: Dict) -> Dict[str, Any]:
        """Execute trade based on AI signal"""
        try:
            symbol = signal.get("symbol")
            signal_type = signal.get("signal_type") 
            confidence = signal.get("confidence", 0)
            
            if confidence < self.trading_config["min_confidence"]:
                return {"status": "skipped", "reason": f"Low confidence: {confidence}"}
            
            if len(self.execution_history) >= self.trading_config["max_daily_trades"]:
                return {"status": "skipped", "reason": "Daily trade limit reached"}
            
            # Simulate trade execution (in production, call actual Dhan API)
            trade_result = {
                "order_id": f"AI_ORD_{datetime.now().timestamp()}",
                "symbol": symbol,
                "side": signal_type,
                "quantity": 1,
                "price": signal.get("predicted_price", 0),
                "status": "EXECUTED",
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            self.execution_history.append(trade_result)
            logger.info(f"🤖 AI Trade Executed: {signal_type} {symbol} @ {confidence:.1f}% confidence")
            
            return {"status": "executed", "trade": trade_result}
            
        except Exception as e:
            logger.error(f"Error executing AI trade: {e}")
            return {"status": "error", "error": str(e)}
    
    async def ai_trading_loop(self):
        """Main AI trading loop that runs in background"""
        logger.info("🚀 AI Trading Loop Started")
        
        while self.ai_trading_active:
            try:
                # Fetch AI signals
                signals = await self.fetch_ai_signals()
                
                if signals:
                    for signal in signals:
                        if not self.ai_trading_active:  # Check if stopped
                            break
                            
                        result = await self.execute_ai_trade(signal)
                        if result["status"] == "executed":
                            logger.info(f"✅ AI Trade: {result['trade']['symbol']} {result['trade']['side']}")
                        
                        # Small delay between trades
                        await asyncio.sleep(5)
                
                # Wait before next cycle (30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in AI trading loop: {e}")
                await asyncio.sleep(10)  # Short delay on error
        
        logger.info("🛑 AI Trading Loop Stopped")
    
    async def start_ai_trading(self) -> Dict[str, Any]:
        """Start AI auto-trading system"""
        if self.ai_trading_active:
            return {"status": "already_running", "message": "AI trading is already active"}
        
        self.ai_trading_active = True
        self.ai_trading_task = asyncio.create_task(self.ai_trading_loop())
        
        return {
            "status": "started",
            "message": "AI auto-trading system started",
            "config": self.trading_config,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stop_ai_trading(self) -> Dict[str, Any]:
        """Stop AI auto-trading system"""
        if not self.ai_trading_active:
            return {"status": "not_running", "message": "AI trading is not active"}
        
        self.ai_trading_active = False
        
        if self.ai_trading_task:
            self.ai_trading_task.cancel()
            try:
                await self.ai_trading_task
            except asyncio.CancelledError:
                pass
        
        return {
            "status": "stopped",
            "message": "AI auto-trading system stopped",
            "trades_executed": len(self.execution_history),
            "timestamp": datetime.now().isoformat()
        }

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

@app.get("/api/portfolio")
async def get_portfolio():
    """Get live portfolio data from Dhan API - Frontend endpoint"""
    try:
        # Fetch live data from Dhan API
        positions = await execution_service.fetch_dhan_data("/positions") or []
        holdings = await execution_service.fetch_dhan_data("/holdings") or []
        orders = await execution_service.fetch_dhan_data("/orders") or []
        
        # Calculate summary metrics
        total_pnl = sum(float(pos.get("unrealizedProfit", 0)) for pos in positions)
        total_positions = len(positions)
        total_orders = len(orders)
        
        # Calculate portfolio value
        portfolio_value = sum(float(pos.get("netQty", 0)) * float(pos.get("buyAvg", 0)) for pos in positions)
        
        return {
            "status": "success",
            "user": {
                "client_id": "1101302170",
                "name": "Raghu Chandra Raj"
            },
            "data": {
                "positions": positions,
                "holdings": holdings,
                "orders": orders
            },
            "summary": {
                "total_positions": total_positions,
                "total_orders": total_orders,
                "total_pnl": round(total_pnl, 2),
                "portfolio_value": round(portfolio_value, 2),
                "currency": "INR"
            },
            "source": "live",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user": {
                "client_id": "1101302170",
                "name": "Raghu Chandra Raj"
            },
            "source": "error",
            "timestamp": datetime.now().isoformat()
        }

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

@app.post("/api/auto-trade/start")
async def start_ai_auto_trading():
    """Start AI auto-trading system"""
    try:
        result = await execution_service.start_ai_trading()
        return result
    except Exception as e:
        logger.error(f"Error starting AI auto-trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-trade/stop")
async def stop_ai_auto_trading():
    """Stop AI auto-trading system"""
    try:
        result = await execution_service.stop_ai_trading()
        return result
    except Exception as e:
        logger.error(f"Error stopping AI auto-trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-trade/status")
async def get_ai_trading_status():
    """Get AI auto-trading status"""
    return {
        "status": "success",
        "ai_trading_active": execution_service.ai_trading_active,
        "trading_status": "running" if execution_service.ai_trading_active else "stopped",
        "trades_executed_today": len(execution_service.execution_history),
        "config": execution_service.trading_config,
        "last_execution_history": execution_service.execution_history[-5:] if execution_service.execution_history else [],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/auto-trade/history")
async def get_ai_trading_history():
    """Get AI trading execution history"""
    return {
        "status": "success",
        "total_trades": len(execution_service.execution_history),
        "execution_history": execution_service.execution_history,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "engine-c-execution",
        "connected_users": len(execution_service.user_tokens),
        "active_oauth_states": len(execution_service.oauth_states),
        "ai_trading_active": execution_service.ai_trading_active,
        "ai_trades_executed": len(execution_service.execution_history),
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