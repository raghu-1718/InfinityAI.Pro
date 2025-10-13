#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine C: Trade Execution Engine
Secure trade execution with Dhan broker integration
Deployed on AWS ECS/Fargate
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import uvicorn
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import json
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from contextlib import asynccontextmanager
import hashlib
import hmac

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

# Security
security = HTTPBearer()

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"

class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class TradeOrder:
    order_id: str
    symbol: str
    quantity: int
    price: float
    order_type: OrderType
    transaction_type: TransactionType
    status: OrderStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
    execution_price: Optional[float] = None
    fees: float = 0.0
    error_message: Optional[str] = None

@dataclass
class Position:
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    entry_time: datetime

@dataclass
class RiskCheck:
    passed: bool
    risk_score: float
    warnings: List[str]
    max_position_size: int
    current_exposure: float

class TradeExecutionService:
    def __init__(self):
        self.dhan_token = os.getenv('DHAN_ACCESS_TOKEN', 'PLACEHOLDER_TOKEN')
        self.dhan_client_id = os.getenv('DHAN_CLIENT_ID', 'PLACEHOLDER_CLIENT_ID')
        self.base_url = "https://api.dhan.co/v2"
        
        self.headers = {
            "access-token": self.dhan_token,
            "Content-Type": "application/json"
        }
        
        # Risk management parameters
        self.max_position_size = 100000  # Max position size in rupees
        self.max_daily_loss = 50000      # Max daily loss limit
        self.max_open_positions = 10     # Max open positions
        
        # In-memory storage (in production, use database)
        self.orders: Dict[str, TradeOrder] = {}
        self.positions: Dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.execution_enabled = True
        
        # Kill switch
        self.kill_switch_active = False
        
        logger.info("🎯 Engine C - Trade Execution Service Initialized")
    
    async def validate_api_key(self, token: str) -> bool:
        """Validate API access token"""
        # In production, implement proper token validation
        return token == "valid_api_key"
    
    def generate_order_id(self) -> str:
        """Generate unique order ID"""
        return f"ORD_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
    
    async def perform_risk_checks(self, symbol: str, quantity: int, price: float, transaction_type: TransactionType) -> RiskCheck:
        """Perform comprehensive risk checks"""
        warnings = []
        risk_score = 0.0
        
        # Check kill switch
        if self.kill_switch_active:
            return RiskCheck(
                passed=False,
                risk_score=1.0,
                warnings=["Kill switch activated - all trading suspended"],
                max_position_size=0,
                current_exposure=0.0
            )
        
        # Calculate position value
        position_value = quantity * price
        
        # Check maximum position size
        if position_value > self.max_position_size:
            warnings.append(f"Position size exceeds limit (₹{position_value:,.2f} > ₹{self.max_position_size:,.2f})")
            risk_score += 0.3
        
        # Check daily loss limit
        if self.daily_pnl < -self.max_daily_loss:
            warnings.append(f"Daily loss limit exceeded (₹{self.daily_pnl:,.2f})")
            risk_score += 0.5
        
        # Check open positions count
        if len(self.positions) >= self.max_open_positions:
            warnings.append(f"Maximum open positions reached ({len(self.positions)})")
            risk_score += 0.2
        
        # Calculate current exposure
        current_exposure = sum(
            pos.quantity * pos.current_price 
            for pos in self.positions.values()
        )
        
        # Check total exposure
        total_exposure = current_exposure + position_value
        max_total_exposure = self.max_position_size * 5  # 5x leverage
        
        if total_exposure > max_total_exposure:
            warnings.append(f"Total exposure limit exceeded")
            risk_score += 0.4
        
        # Risk assessment
        passed = risk_score < 0.7 and len(warnings) == 0
        
        return RiskCheck(
            passed=passed,
            risk_score=risk_score,
            warnings=warnings,
            max_position_size=self.max_position_size,
            current_exposure=current_exposure
        )
    
    async def execute_order_with_dhan(self, order: TradeOrder) -> Dict:
        """Execute order through Dhan API"""
        try:
            # Prepare order payload for Dhan API
            payload = {
                "dhanClientId": self.dhan_client_id,
                "transactionType": order.transaction_type.value,
                "exchangeSegment": "NSE_EQ",
                "productType": "INTRADAY",
                "orderType": order.order_type.value,
                "validity": "DAY",
                "tradingSymbol": order.symbol,
                "securityId": "2885",  # Example: NIFTY security ID
                "quantity": str(order.quantity),
                "disclosedQuantity": "0",
                "price": str(order.price) if order.order_type != OrderType.MARKET else "0",
                "afterMarketOrderFlag": "false"
            }
            
            # Execute order
            url = f"{self.base_url}/orders"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    response_data = await response.json()
                    
                    if response.status == 200 and response_data.get('status') == 'success':
                        return {
                            'success': True,
                            'order_id': response_data.get('data', {}).get('orderId'),
                            'message': 'Order executed successfully'
                        }
                    else:
                        return {
                            'success': False,
                            'error': response_data.get('message', 'Unknown error'),
                            'details': response_data
                        }
                        
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def place_order(self, symbol: str, quantity: int, price: float, order_type: OrderType, transaction_type: TransactionType) -> TradeOrder:
        """Place a new trade order"""
        order_id = self.generate_order_id()
        
        # Create order object
        order = TradeOrder(
            order_id=order_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type,
            transaction_type=transaction_type,
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )
        
        try:
            # Perform risk checks
            risk_check = await self.perform_risk_checks(symbol, quantity, price, transaction_type)
            
            if not risk_check.passed:
                order.status = OrderStatus.REJECTED
                order.error_message = f"Risk check failed: {', '.join(risk_check.warnings)}"
                self.orders[order_id] = order
                logger.warning(f"Order {order_id} rejected: {order.error_message}")
                return order
            
            # Execute order if execution is enabled
            if self.execution_enabled:
                execution_result = await self.execute_order_with_dhan(order)
                
                if execution_result['success']:
                    order.status = OrderStatus.EXECUTED
                    order.executed_at = datetime.now()
                    order.execution_price = price  # In production, get actual execution price
                    order.fees = quantity * price * 0.001  # Simplified fee calculation
                    
                    # Update positions
                    await self.update_positions(order)
                    
                    logger.info(f"✅ Order {order_id} executed: {transaction_type.value} {quantity} {symbol} @ ₹{price}")
                else:
                    order.status = OrderStatus.REJECTED
                    order.error_message = execution_result['error']
                    logger.error(f"❌ Order {order_id} rejected: {order.error_message}")
            else:
                order.status = OrderStatus.PENDING
                logger.info(f"📋 Order {order_id} placed (execution disabled)")
            
            # Store order
            self.orders[order_id] = order
            return order
            
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.error_message = str(e)
            self.orders[order_id] = order
            logger.error(f"Error placing order {order_id}: {e}")
            return order
    
    async def update_positions(self, executed_order: TradeOrder):
        """Update position after order execution"""
        symbol = executed_order.symbol
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            if executed_order.transaction_type == TransactionType.BUY:
                # Add to position
                total_cost = (position.quantity * position.average_price) + (executed_order.quantity * executed_order.execution_price)
                total_quantity = position.quantity + executed_order.quantity
                position.average_price = total_cost / total_quantity
                position.quantity = total_quantity
            else:
                # Reduce position
                position.quantity -= executed_order.quantity
                if position.quantity <= 0:
                    # Position closed
                    del self.positions[symbol]
                    return
        else:
            # New position
            if executed_order.transaction_type == TransactionType.BUY:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=executed_order.quantity,
                    average_price=executed_order.execution_price,
                    current_price=executed_order.execution_price,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    entry_time=executed_order.executed_at
                )
    
    async def get_account_info(self) -> Dict:
        """Get account information from Dhan"""
        try:
            url = f"{self.base_url}/funds"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return {"error": "Failed to fetch account info"}
                        
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return {"error": str(e)}
    
    def activate_kill_switch(self, reason: str = "Manual activation"):
        """Activate kill switch to stop all trading"""
        self.kill_switch_active = True
        logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")
    
    def deactivate_kill_switch(self):
        """Deactivate kill switch"""
        self.kill_switch_active = False
        logger.info("✅ Kill switch deactivated")

# Global service instance
execution_service = TradeExecutionService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Engine C - Trade Execution Service starting...")
    yield
    # Shutdown
    logger.info("🛑 Engine C - Trade Execution Service shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="🎯 InfinityAI.Pro - Engine C: Trade Execution",
    description="Secure trade execution with comprehensive risk management",
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
        "service": "Engine C - Trade Execution Service",
        "status": "active",
        "version": "1.0.0",
        "execution_enabled": execution_service.execution_enabled,
        "kill_switch": execution_service.kill_switch_active,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-c-execution",
        "execution_status": "enabled" if execution_service.execution_enabled else "disabled",
        "kill_switch": execution_service.kill_switch_active,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/orders")
async def place_order(
    symbol: str,
    quantity: int,
    price: float,
    order_type: str = "MARKET",
    transaction_type: str = "BUY",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Place a new trade order"""
    try:
        # Validate token
        if not await execution_service.validate_api_key(credentials.credentials):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Convert string enums
        order_type_enum = OrderType(order_type.upper())
        transaction_type_enum = TransactionType(transaction_type.upper())
        
        # Place order
        order = await execution_service.place_order(
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type_enum,
            transaction_type=transaction_type_enum
        )
        
        return {
            "status": "success",
            "order": asdict(order),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all orders"""
    try:
        if not await execution_service.validate_api_key(credentials.credentials):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return {
            "status": "success",
            "orders": [asdict(order) for order in execution_service.orders.values()],
            "count": len(execution_service.orders),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all positions"""
    try:
        if not await execution_service.validate_api_key(credentials.credentials):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return {
            "status": "success",
            "positions": [asdict(position) for position in execution_service.positions.values()],
            "count": len(execution_service.positions),
            "total_pnl": execution_service.daily_pnl,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/kill-switch")
async def toggle_kill_switch(
    action: str,  # "activate" or "deactivate"
    reason: str = "Manual",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Toggle kill switch"""
    try:
        if not await execution_service.validate_api_key(credentials.credentials):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if action == "activate":
            execution_service.activate_kill_switch(reason)
            return {"status": "activated", "reason": reason}
        elif action == "deactivate":
            execution_service.deactivate_kill_switch()
            return {"status": "deactivated"}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
    except Exception as e:
        logger.error(f"Error toggling kill switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/account")
async def get_account(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get account information"""
    try:
        if not await execution_service.validate_api_key(credentials.credentials):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        account_info = await execution_service.get_account_info()
        
        return {
            "status": "success",
            "account": account_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "engine-c-execution",
        "total_orders": len(execution_service.orders),
        "executed_orders": len([o for o in execution_service.orders.values() if o.status == OrderStatus.EXECUTED]),
        "active_positions": len(execution_service.positions),
        "daily_pnl": execution_service.daily_pnl,
        "kill_switch": execution_service.kill_switch_active,
        "execution_enabled": execution_service.execution_enabled,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )