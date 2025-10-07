"""
InfinityAI.Pro - Engine C: Orchestrator & Trading Engine
Handles broker connections, order management, portfolio tracking, and system orchestration
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import uuid
from decimal import Decimal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
import redis
from kafka import KafkaConsumer, KafkaProducer
import asyncpg
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="InfinityAI Engine C - Orchestrator", version="1.0.0")

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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://infinityai:password@localhost:5432/infinityai")
ENGINE_A_URL = os.getenv("ENGINE_A_URL", "http://localhost:8001")
ENGINE_B_URL = os.getenv("ENGINE_B_URL", "http://localhost:8002")
ENGINE_D_URL = os.getenv("ENGINE_D_URL", "http://localhost:8004")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ULTRA_MODE = os.getenv("ULTRA_AGGRESSIVE_MODE", "false").lower() == "true"

# Initialize connections
redis_client = redis.from_url(REDIS_URL)
kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Database setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Models
class BrokerToken(Base):
    __tablename__ = "broker_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    broker_name = Column(String, nullable=False)  # zerodha, upstox, etc.
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    api_key = Column(String)
    api_secret = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    broker_name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    average_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    market_value = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    broker_name = Column(String, nullable=False)
    broker_order_id = Column(String)
    symbol = Column(String, nullable=False)
    order_type = Column(String, nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, EXECUTED, CANCELLED, REJECTED
    signal_source = Column(String)  # AI, MANUAL, CHATBOT
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    executed_price = Column(Float)
    executed_quantity = Column(Integer)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class TokenRegistration(BaseModel):
    user_id: str
    broker_name: str
    access_token: str
    refresh_token: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class OrderRequest(BaseModel):
    user_id: str
    symbol: str
    order_type: str  # BUY, SELL
    quantity: int
    price: Optional[float] = None  # None for market orders
    order_mode: str = "MARKET"  # MARKET, LIMIT
    signal_source: str = "MANUAL"

class PortfolioRequest(BaseModel):
    user_id: str
    broker_name: Optional[str] = None

# Authentication
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class BrokerService:
    """Handles broker API connections and trading operations"""
    
    def __init__(self):
        self.broker_adapters = {
            "zerodha": self.zerodha_adapter,
            "upstox": self.upstox_adapter,
            "angelone": self.angelone_adapter,
            "demo": self.demo_adapter
        }
        
    async def get_broker_token(self, user_id: str, broker_name: str) -> Optional[Dict]:
        """Get broker token for user"""
        db = SessionLocal()
        try:
            token_record = db.query(BrokerToken).filter(
                BrokerToken.user_id == user_id,
                BrokerToken.broker_name == broker_name,
                BrokerToken.is_active == True
            ).first()
            
            if not token_record:
                return None
                
            return {
                "access_token": token_record.access_token,
                "refresh_token": token_record.refresh_token,
                "api_key": token_record.api_key,
                "api_secret": token_record.api_secret
            }
        finally:
            db.close()
    
    async def place_order(self, user_id: str, broker_name: str, order_request: OrderRequest) -> Dict:
        """Place order through broker API"""
        try:
            # Get broker token
            token_data = await self.get_broker_token(user_id, broker_name)
            if not token_data:
                raise HTTPException(status_code=401, detail="Broker token not found")
            
            # Select appropriate broker adapter
            adapter = self.broker_adapters.get(broker_name, self.demo_adapter)
            
            # Place order through broker
            result = await adapter(token_data, order_request)
            
            # Store order in database
            db = SessionLocal()
            try:
                order = Order(
                    user_id=user_id,
                    broker_name=broker_name,
                    broker_order_id=result.get("broker_order_id"),
                    symbol=order_request.symbol,
                    order_type=order_request.order_type,
                    quantity=order_request.quantity,
                    price=order_request.price or 0,
                    status=result.get("status", "PENDING"),
                    signal_source=order_request.signal_source
                )
                db.add(order)
                db.commit()
                
                # Send order update to Kafka
                kafka_producer.send("order_updates", {
                    "order_id": order.id,
                    "user_id": user_id,
                    "broker_name": broker_name,
                    "symbol": order_request.symbol,
                    "order_type": order_request.order_type,
                    "quantity": order_request.quantity,
                    "status": result.get("status"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                logger.info(f"Order placed successfully: {order.id}")
                return {
                    "status": "success",
                    "order_id": order.id,
                    "broker_order_id": result.get("broker_order_id"),
                    "message": result.get("message", "Order placed successfully")
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def demo_adapter(self, token_data: Dict, order_request: OrderRequest) -> Dict:
        """Demo broker adapter for testing"""
        # Simulate order placement
        await asyncio.sleep(0.5)  # Simulate API delay
        
        broker_order_id = f"DEMO_{uuid.uuid4().hex[:8].upper()}"
        
        # Simulate order execution with 90% success rate
        if np.random.random() > 0.1:
            return {
                "broker_order_id": broker_order_id,
                "status": "EXECUTED",
                "message": "Demo order executed successfully"
            }
        else:
            return {
                "broker_order_id": broker_order_id,
                "status": "REJECTED",
                "message": "Demo order rejected (simulated)"
            }
    
    async def zerodha_adapter(self, token_data: Dict, order_request: OrderRequest) -> Dict:
        """Zerodha Kite Connect API adapter"""
        # Implementation for Zerodha API
        # This would use the actual Zerodha Kite Connect library
        return await self.demo_adapter(token_data, order_request)  # Fallback to demo for now
    
    async def upstox_adapter(self, token_data: Dict, order_request: OrderRequest) -> Dict:
        """Upstox API adapter"""
        # Implementation for Upstox API
        return await self.demo_adapter(token_data, order_request)  # Fallback to demo for now
    
    async def angelone_adapter(self, token_data: Dict, order_request: OrderRequest) -> Dict:
        """Angel One API adapter"""
        # Implementation for Angel One API
        return await self.demo_adapter(token_data, order_request)  # Fallback to demo for now

class PortfolioService:
    """Handles portfolio management and tracking"""
    
    async def get_portfolio(self, user_id: str, broker_name: Optional[str] = None) -> Dict:
        """Get user's portfolio"""
        db = SessionLocal()
        try:
            query = db.query(Portfolio).filter(Portfolio.user_id == user_id)
            if broker_name:
                query = query.filter(Portfolio.broker_name == broker_name)
            
            positions = query.all()
            
            portfolio_data = []
            total_value = 0
            total_pnl = 0
            
            for position in positions:
                # Update current prices (this would fetch from market data in production)
                current_price = await self.get_current_price(position.symbol)
                market_value = position.quantity * current_price
                pnl = (current_price - position.average_price) * position.quantity
                
                position.current_price = current_price
                position.market_value = market_value
                position.pnl = pnl
                position.updated_at = datetime.utcnow()
                
                portfolio_data.append({
                    "symbol": position.symbol,
                    "quantity": position.quantity,
                    "average_price": position.average_price,
                    "current_price": current_price,
                    "market_value": market_value,
                    "pnl": pnl,
                    "pnl_percent": (pnl / (position.average_price * position.quantity)) * 100 if position.quantity > 0 else 0
                })
                
                total_value += market_value
                total_pnl += pnl
            
            db.commit()
            
            return {
                "user_id": user_id,
                "positions": portfolio_data,
                "total_value": total_value,
                "total_pnl": total_pnl,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (from Engine A cache)"""
        try:
            # Try to get from Redis cache first
            cached_price = redis_client.get(f"price:{symbol}")
            if cached_price:
                return float(cached_price)
            
            # Fallback to Engine A API
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ENGINE_A_URL}/data/cache/{symbol}")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("current_price", 100.0)  # Default fallback
                    
        except Exception as e:
            logger.warning(f"Error getting current price for {symbol}: {e}")
        
        # Ultimate fallback
        return 100.0

class OrchestrationService:
    """Orchestrates communication between engines and manages workflows"""
    
    def __init__(self):
        self.active_strategies = {}
        self.websocket_connections = {}
    
    async def process_ai_signal(self, signal_data: Dict) -> Dict:
        """Process AI trading signals from Engine B"""
        try:
            user_id = signal_data.get("user_id")
            symbol = signal_data.get("symbol")
            signal = signal_data.get("signal")  # BUY, SELL, HOLD
            confidence = signal_data.get("confidence", 0.0)
            
            if signal == "HOLD" or confidence < 0.7:  # Only act on high-confidence signals
                return {"status": "ignored", "reason": "Low confidence or HOLD signal"}
            
            # Get user's broker info
            db = SessionLocal()
            try:
                broker_token = db.query(BrokerToken).filter(
                    BrokerToken.user_id == user_id,
                    BrokerToken.is_active == True
                ).first()
                
                if not broker_token:
                    return {"status": "error", "reason": "No active broker token found"}
                
                # Determine order quantity (this would be more sophisticated in production)
                quantity = 1  # Base quantity
                
                # Create order request
                order_request = OrderRequest(
                    user_id=user_id,
                    symbol=symbol,
                    order_type=signal,
                    quantity=quantity,
                    signal_source="AI"
                )
                
                # Place order
                broker_service = BrokerService()
                result = await broker_service.place_order(
                    user_id=user_id,
                    broker_name=broker_token.broker_name,
                    order_request=order_request
                )
                
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing AI signal: {e}")
            return {"status": "error", "reason": str(e)}
    
    async def get_system_status(self) -> Dict:
        """Get overall system status"""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engines": {},
            "services": {}
        }
        
        # Check Engine A
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ENGINE_A_URL}/health", timeout=5.0)
                status["engines"]["engine_a"] = response.json() if response.status_code == 200 else {"status": "error"}
        except:
            status["engines"]["engine_a"] = {"status": "unreachable"}
        
        # Check Engine B
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ENGINE_B_URL}/health", timeout=5.0)
                status["engines"]["engine_b"] = response.json() if response.status_code == 200 else {"status": "error"}
        except:
            status["engines"]["engine_b"] = {"status": "unreachable"}
        
        # Check Engine D
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ENGINE_D_URL}/health", timeout=5.0)
                status["engines"]["engine_d"] = response.json() if response.status_code == 200 else {"status": "error"}
        except:
            status["engines"]["engine_d"] = {"status": "unreachable"}
        
        # Check Redis
        try:
            status["services"]["redis"] = {"status": "connected" if redis_client.ping() else "disconnected"}
        except:
            status["services"]["redis"] = {"status": "error"}
        
        # Check Database
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            status["services"]["database"] = {"status": "connected"}
        except:
            status["services"]["database"] = {"status": "error"}
        
        return status

# Initialize services
broker_service = BrokerService()
portfolio_service = PortfolioService()
orchestration_service = OrchestrationService()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
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
        "service": "Engine C - Orchestrator",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# ALB path alias
@app.get("/engine-c/health")
async def health_check_alias():
    return await health_check()

@app.post("/tokens/register")
async def register_broker_token(token_data: TokenRegistration):
    """Register broker token for user"""
    db = SessionLocal()
    try:
        # Check if token already exists
        existing_token = db.query(BrokerToken).filter(
            BrokerToken.user_id == token_data.user_id,
            BrokerToken.broker_name == token_data.broker_name
        ).first()
        
        if existing_token:
            # Update existing token
            existing_token.access_token = token_data.access_token
            existing_token.refresh_token = token_data.refresh_token
            existing_token.api_key = token_data.api_key
            existing_token.api_secret = token_data.api_secret
            existing_token.is_active = True
        else:
            # Create new token
            new_token = BrokerToken(
                user_id=token_data.user_id,
                broker_name=token_data.broker_name,
                access_token=token_data.access_token,
                refresh_token=token_data.refresh_token,
                api_key=token_data.api_key,
                api_secret=token_data.api_secret
            )
            db.add(new_token)
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Broker token registered successfully",
            "postback_url": f"https://infinityai.pro/auth/postback",
            "redirect_url": f"https://infinityai.pro/auth/redirect"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering broker token: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/orders/place")
async def place_order(order_request: OrderRequest):
    """Place trading order"""
    # Determine broker (get first active broker for user)
    db = SessionLocal()
    try:
        broker_token = db.query(BrokerToken).filter(
            BrokerToken.user_id == order_request.user_id,
            BrokerToken.is_active == True
        ).first()
        
        if not broker_token:
            raise HTTPException(status_code=401, detail="No active broker token found")
        
        result = await broker_service.place_order(
            user_id=order_request.user_id,
            broker_name=broker_token.broker_name,
            order_request=order_request
        )
        
        return result
        
    finally:
        db.close()

@app.get("/portfolio/{user_id}")
async def get_portfolio(user_id: str, broker_name: Optional[str] = None):
    """Get user's portfolio"""
    return await portfolio_service.get_portfolio(user_id, broker_name)

@app.get("/orders/{user_id}")
async def get_orders(user_id: str, limit: int = 50):
    """Get user's order history"""
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(limit).all()
        
        order_data = []
        for order in orders:
            order_data.append({
                "id": order.id,
                "symbol": order.symbol,
                "order_type": order.order_type,
                "quantity": order.quantity,
                "price": order.price,
                "status": order.status,
                "signal_source": order.signal_source,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "executed_at": order.executed_at.isoformat() if order.executed_at else None,
                "executed_price": order.executed_price,
                "executed_quantity": order.executed_quantity
            })
        
        return {"orders": order_data}
        
    finally:
        db.close()

@app.get("/status")
async def get_system_status():
    """Get overall system status"""
    return await orchestration_service.get_system_status()

@app.get("/engine-c/status")
async def get_system_status_alias():
    return await get_system_status()

@app.get("/dashboard/summary")
async def dashboard_summary():
    """Summarized health/status for frontend: engines, ultra mode, app health."""
    status = await orchestration_service.get_system_status()
    return {
        "app_health": "healthy" if all((v.get("status") == "healthy" or v.get("status") == True) for v in status.get("engines", {}).values()) else "degraded",
        "ultra_aggressive_mode": ULTRA_MODE,
        "engines": status.get("engines", {}),
        "services": status.get("services", {})
    }

@app.get("/engine-c/dashboard/summary")
async def dashboard_summary_alias():
    return await dashboard_summary()

@app.post("/ultra/toggle")
async def toggle_ultra(mode: bool):
    """Toggle ultra aggressive mode on/off."""
    global ULTRA_MODE
    ULTRA_MODE = bool(mode)
    return {"status": "ok", "ultra_aggressive_mode": ULTRA_MODE}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            portfolio = await portfolio_service.get_portfolio(user_id)
            await manager.send_personal_message({
                "type": "portfolio_update",
                "data": portfolio
            }, websocket)
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task for processing Kafka messages
async def kafka_consumer_task():
    """Background task to consume Kafka messages"""
    consumer = KafkaConsumer(
        'inference_results',
        'model_training',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        try:
            if message.topic == 'inference_results':
                # Process AI trading signals
                signal_data = message.value
                result = await orchestration_service.process_ai_signal(signal_data)
                logger.info(f"Processed AI signal: {result}")
                
        except Exception as e:
            logger.error(f"Error processing Kafka message: {e}")

# Start background tasks
@app.on_event("startup")
async def startup_event():
    # Start Kafka consumer in background
    asyncio.create_task(kafka_consumer_task())
    logger.info("Engine C started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)