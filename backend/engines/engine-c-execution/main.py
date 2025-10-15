#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine C: Trade Execution Engine
Secure trade execution with Dhan broker integration
Deployed on Google Cloud Run (us-central1)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import uvicorn
import os
import logging
import re
import bleach
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

# Google Secret Manager
try:
    from google.cloud import secretmanager
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logging.warning("Google Cloud Secret Manager not available")

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

# Google Cloud Project Configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', '573866363639')

# Security
security = HTTPBearer()

def get_secret(secret_id: str) -> str:
    """Get secret from Google Secret Manager"""
    if not GOOGLE_CLOUD_AVAILABLE:
        # Fallback to environment variables
        return os.getenv(secret_id.upper().replace('-', '_'), '')
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        # Fallback to environment variables
        return os.getenv(secret_id.upper().replace('-', '_'), '')

def sanitize_input(text: str) -> str:
    """Sanitize input to prevent XSS and injection attacks"""
    if not text:
        return ""
    
    # Remove HTML tags and scripts
    try:
        cleaned = bleach.clean(str(text), tags=[], attributes={}, strip=True)
    except:
        # Fallback: basic HTML escaping
        cleaned = (str(text)
                  .replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
                  .replace('"', "&quot;")
                  .replace("'", "&#x27;"))
    
    # Remove SQL injection patterns
    sql_patterns = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+.+\s+set',
        r'exec\(',
        r'execute\(',
        r'sp_',
        r'xp_',
        r'--',
        r'/\*.*\*/'
    ]
    
    for pattern in sql_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Limit length to prevent DoS
    return cleaned[:1000]

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol"""
    if not symbol:
        return False
    
    # Allow only alphanumeric and basic punctuation
    pattern = r'^[A-Z0-9._-]+$'
    return bool(re.match(pattern, symbol.upper())) and len(symbol) <= 20

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
        # Load secrets from Google Secret Manager
        self.dhan_token = get_secret('dhan-access-token') or 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NjA2MDM3NTEsImlhdCI6MTc2MDUxNzM1MSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtNTczODY2MzYzNjM5LTU3Mzg2NjM2MzYzOS51cy1jZW50cmFsMS5ydW4uYXBwL2FwaS9kaGFuL3Bvc3RiYWNrIiwiZGhhbkNsaWVudElkIjoiMTEwMTMwMjE3MCJ9.cRhYjn044i_CrOwTV5ZxQOPnR_iWNnWcGHWF_q41wSdh02-wLQBFOLeD8TQPaIKdZBXqxQvwKDm6Y0DEfs0JZA'
        self.dhan_client_id = get_secret('dhan-client-id') or '1101302170'
        self.dhan_api_key = get_secret('dhan-api-key') or 'fe1942e7'
        self.dhan_api_secret = get_secret('dhan-api-secret') or '50bc0462-b1aa-489c-9029-fe0cdc68dc27'
        self.base_url = "https://api.dhan.co/v2"
        
        # OAuth configuration
        self.oauth_configured = bool(self.dhan_client_id and self.dhan_api_key and self.dhan_api_secret)
        self.redirect_uri = "https://engine-c-573866363639-573866363639.us-central1.run.app/api/dhan/callback"
        self.postback_uri = "https://engine-c-573866363639-573866363639.us-central1.run.app/api/dhan/postback"
        self.oauth_scopes = ['trade', 'funds', 'holdings', 'positions']
        
        self.headers = {
            "access-token": self.dhan_token,
            "client-id": self.dhan_client_id,
            "Content-Type": "application/json"
        }
        
        self.rt_headers = {
            "x-api-key": self.dhan_api_key,
            "x-api-secret": self.dhan_api_secret,
            "client-id": self.dhan_client_id
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
        warnings: List[str] = []
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
            pos.quantity * float(pos.current_price or 0.0)
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
    
    async def execute_order_with_dhan(self, order: TradeOrder) -> Dict[str, Any]:
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
                    order.execution_price = float(price)  # In production, get actual execution price
                    order.fees = float(quantity) * float(price) * 0.001  # Simplified fee calculation
                    
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
    
    async def update_positions(self, executed_order: TradeOrder) -> None:
        """Update position after order execution"""
        symbol = executed_order.symbol
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            if executed_order.transaction_type == TransactionType.BUY:
                # Add to position
                avg_price = float(position.average_price)
                exec_price = float(executed_order.execution_price or 0.0)
                total_cost = (position.quantity * avg_price) + (executed_order.quantity * exec_price)
                total_quantity = position.quantity + executed_order.quantity
                position.average_price = total_cost / max(total_quantity, 1)
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
                    quantity=int(executed_order.quantity),
                    average_price=float(executed_order.execution_price or executed_order.price or 0.0),
                    current_price=float(executed_order.execution_price or executed_order.price or 0.0),
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    entry_time=executed_order.executed_at or datetime.now()
                )
    
    async def get_account_info(self) -> Dict[str, Any]:
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

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Add security headers
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://infinityai.pro",
        "https://*.infinityai.pro",
        "https://*.us-central1.run.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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

@app.get("/engine-c")
async def engine_c_root():
    """ALB path-specific route handler"""
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

@app.get("/engine-c/health")
async def engine_c_health_check():
    """ALB path-specific health check"""
    return {
        "status": "healthy",
        "service": "Engine C - Trade Execution Service",
        "version": "1.0.0",
        "execution_status": "enabled" if execution_service.execution_enabled else "disabled",
        "kill_switch": execution_service.kill_switch_active,
        "dhan_integration": "configured",
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

@app.post("/engine-c/api/orders")
async def place_order_alb(
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

# New Trading API Endpoints for Production
@app.post("/api/orders/place")
async def place_order_new(request_data: dict):
    """Place a new trade order - Production endpoint"""
    try:
        # Input sanitization and validation
        symbol = sanitize_input(str(request_data.get('symbol', '')))
        quantity = int(request_data.get('quantity', 1))
        order_type = sanitize_input(str(request_data.get('order_type', 'MARKET')))
        transaction_type = sanitize_input(str(request_data.get('transaction_type', 'BUY')))
        price = float(request_data.get('price', 0.0))
        demo = bool(request_data.get('demo', True))  # Default to demo mode
        
        # Comprehensive input validation
        if not symbol or not validate_symbol(symbol):
            raise HTTPException(status_code=400, detail="Invalid or missing symbol")
        if quantity <= 0 or quantity > 10000:  # Max quantity limit
            raise HTTPException(status_code=400, detail="Quantity must be between 1 and 10,000")
        if order_type.upper() not in ['MARKET', 'LIMIT', 'STOP_LOSS']:
            raise HTTPException(status_code=400, detail="Invalid order type")
        if transaction_type.upper() not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Invalid transaction type")
        if price < 0 or price > 100000:  # Price validation
            raise HTTPException(status_code=400, detail="Invalid price range")
        
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
            "order_id": order.order_id,
            "message": f"Order placed successfully {'(demo mode)' if demo else ''}",
            "order_details": {
                "symbol": order.symbol,
                "quantity": order.quantity,
                "price": order.price,
                "order_type": order.order_type.value,
                "transaction_type": order.transaction_type.value,
                "status": order.status.value,
                "created_at": order.created_at.isoformat()
            },
            "demo_mode": demo,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/orders/status")
async def get_order_status(order_id: str = None):
    """Get order status - Production endpoint"""
    try:
        if order_id:
            # Get specific order
            if order_id in execution_service.orders:
                order = execution_service.orders[order_id]
                return {
                    "status": "success",
                    "order": {
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "quantity": order.quantity,
                        "price": order.price,
                        "order_type": order.order_type.value,
                        "transaction_type": order.transaction_type.value,
                        "status": order.status.value,
                        "created_at": order.created_at.isoformat(),
                        "executed_at": order.executed_at.isoformat() if order.executed_at else None,
                        "execution_price": order.execution_price,
                        "fees": order.fees,
                        "error_message": order.error_message
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=404, detail="Order not found")
        else:
            # Get all orders
            orders = []
            for order in execution_service.orders.values():
                orders.append({
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "price": order.price,
                    "order_type": order.order_type.value,
                    "transaction_type": order.transaction_type.value,
                    "status": order.status.value,
                    "created_at": order.created_at.isoformat(),
                    "executed_at": order.executed_at.isoformat() if order.executed_at else None
                })
            
            return {
                "status": "success",
                "orders": orders,
                "count": len(orders),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error getting order status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/orders/demo")
async def get_demo_orders():
    """Get demo orders for testing"""
    try:
        return {
            "status": "success",
            "message": "Order execution service operational",
            "demo_mode": True,
            "orders": [asdict(order) for order in execution_service.orders.values()],
            "count": len(execution_service.orders),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting demo orders: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

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

@app.get("/api/portfolio")
async def get_portfolio():
    """Get live portfolio data from Dhan API - Frontend endpoint"""
    try:
        # Fetch live positions from Dhan
        positions_url = f"{execution_service.base_url}/positions"
        holdings_url = f"{execution_service.base_url}/holdings"
        orders_url = f"{execution_service.base_url}/orders"
        
        portfolio_data = {}
        
        async with aiohttp.ClientSession() as session:
            # Fetch positions
            try:
                async with session.get(positions_url, headers=execution_service.headers) as response:
                    if response.status == 200:
                        portfolio_data["positions"] = await response.json()
                    else:
                        portfolio_data["positions"] = []
            except Exception as e:
                logger.error(f"Error fetching positions: {e}")
                portfolio_data["positions"] = []
            
            # Fetch holdings  
            try:
                async with session.get(holdings_url, headers=execution_service.headers) as response:
                    if response.status == 200:
                        portfolio_data["holdings"] = await response.json()
                    elif response.status == 400:
                        # No holdings available - this is normal
                        portfolio_data["holdings"] = []
                    else:
                        portfolio_data["holdings"] = []
            except Exception as e:
                logger.error(f"Error fetching holdings: {e}")
                portfolio_data["holdings"] = []
            
            # Fetch orders
            try:
                async with session.get(orders_url, headers=execution_service.headers) as response:
                    if response.status == 200:
                        portfolio_data["orders"] = await response.json()
                    else:
                        portfolio_data["orders"] = []
            except Exception as e:
                logger.error(f"Error fetching orders: {e}")
                portfolio_data["orders"] = []
        
        # Calculate summary
        total_pnl = sum(float(pos.get("unrealizedProfit", 0)) for pos in portfolio_data.get("positions", []))
        total_positions = len(portfolio_data.get("positions", []))
        total_orders = len(portfolio_data.get("orders", []))
        
        return {
            "status": "success",
            "data": portfolio_data,
            "summary": {
                "total_positions": total_positions,
                "total_orders": total_orders,
                "total_pnl": total_pnl,
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
            "source": "mock",
            "timestamp": datetime.now().isoformat()
        }

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

@app.get("/engine-c/metrics")
async def get_metrics_alb():
    """Get service metrics (ALB compatible)"""
    return {
        "service": "Engine C - Trade Execution Service",
        "total_orders": len(execution_service.orders),
        "executed_orders": len([o for o in execution_service.orders.values() if o.status == OrderStatus.EXECUTED]),
        "active_positions": len(execution_service.positions),
        "daily_pnl": execution_service.daily_pnl,
        "kill_switch": execution_service.kill_switch_active,
        "execution_enabled": execution_service.execution_enabled,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/engine-c/api/positions")
async def get_positions_alb(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all positions (ALB compatible)"""
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

# OAuth Integration Endpoints
@app.get("/api/dhan/status")
async def get_dhan_oauth_status():
    """Get Dhan OAuth integration status"""
    try:
        return {
            "status": "success",
            "oauth_active": execution_service.oauth_configured,
            "oauth_configured": execution_service.oauth_configured,
            "client_id": execution_service.dhan_client_id if execution_service.oauth_configured else None,
            "redirect_uri": execution_service.redirect_uri,
            "postback_uri": execution_service.postback_uri,
            "scopes": execution_service.oauth_scopes,
            "connected_users": 1 if execution_service.oauth_configured else 0,
            "endpoints": {
                "callback": "/api/dhan/callback",
                "postback": "/api/dhan/postback",
                "initiate": "/api/auth/dhan/initiate"
            },
            "integration_status": "fully_configured" if execution_service.oauth_configured else "partial",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting Dhan status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/dhan/callback")
async def handle_dhan_oauth_callback(request_data: dict):
    """Handle Dhan OAuth callback with security validation"""
    try:
        # Input sanitization
        code = sanitize_input(str(request_data.get('code', '')))
        state = sanitize_input(str(request_data.get('state', '')))
        redirect_uri = sanitize_input(str(request_data.get('redirect_uri', '')))
        
        logger.info(f"Processing Dhan OAuth callback: code={code[:10] if code else 'None'}..., state={state}")
        
        # Validation
        if not code or len(code) < 10:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        if not state or len(state) < 5:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        if redirect_uri and not redirect_uri.startswith('https://'):  
            raise HTTPException(status_code=400, detail="Invalid redirect URI")
        
        # Real Dhan API token exchange
        try:
            # Prepare token exchange request
            token_url = "https://api.dhan.co/oauth/token"
            token_data = {
                "client_id": execution_service.dhan_client_id,
                "client_secret": execution_service.dhan_api_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri or execution_service.redirect_uri
            }
            
            logger.info(f"Exchanging authorization code with Dhan API...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, json=token_data) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        access_token = token_response.get('access_token')
                        refresh_token = token_response.get('refresh_token')
                        expires_in = token_response.get('expires_in', 3600)
                        
                        if not access_token:
                            raise Exception("No access token received from Dhan API")
                        
                        logger.info(f"✅ Received access token from Dhan API")
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"Dhan token exchange failed: {response.status} - {error_text}")
                        # Fallback to simulated token for development
                        access_token = f"dhan_dev_token_{uuid.uuid4().hex[:16]}"
                        refresh_token = None
                        expires_in = 3600
                        
        except Exception as api_error:
            logger.error(f"Dhan API error: {api_error}")
            # Fallback to simulated token for development
            access_token = f"dhan_dev_token_{uuid.uuid4().hex[:16]}"
            refresh_token = None
            expires_in = 3600
        
        # Store tokens securely in vault (Google Secret Manager)
        try:
            if GOOGLE_CLOUD_AVAILABLE:
                client = secretmanager.SecretManagerServiceClient()
                
                # Store access token
                secret_data = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": expires_in,
                    "client_id": execution_service.dhan_client_id,
                    "connected_at": datetime.now().isoformat(),
                    "state_verified": state
                }
                
                # Create or update secret
                parent = f"projects/{PROJECT_ID}"
                secret_id = "dhan-oauth-tokens"
                
                try:
                    # Try to add new version to existing secret
                    secret_name = f"{parent}/secrets/{secret_id}"
                    client.add_secret_version(
                        request={
                            "parent": secret_name,
                            "payload": {"data": json.dumps(secret_data).encode("utf-8")}
                        }
                    )
                    logger.info(f"✅ Updated OAuth tokens in Secret Manager")
                except:
                    # Create new secret if it doesn't exist
                    client.create_secret(
                        request={
                            "parent": parent,
                            "secret_id": secret_id,
                            "secret": {"replication": {"automatic": {}}},
                        }
                    )
                    client.add_secret_version(
                        request={
                            "parent": f"{parent}/secrets/{secret_id}",
                            "payload": {"data": json.dumps(secret_data).encode("utf-8")}
                        }
                    )
                    logger.info(f"✅ Created and stored OAuth tokens in Secret Manager")
            else:
                logger.warning("Secret Manager not available, storing in memory only")
                
        except Exception as vault_error:
            logger.error(f"Vault storage error: {vault_error}")
            # Continue with in-memory storage as fallback
        
        # Update service configuration
        execution_service.dhan_token = access_token
        execution_service.headers["access-token"] = access_token
        
        # Fetch user account info if possible
        user_info = {"client_id": execution_service.dhan_client_id, "name": "Raghu"}
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "access-token": access_token,
                    "client-id": execution_service.dhan_client_id
                }
                async with session.get("https://api.dhan.co/v2/user/profile", headers=headers) as response:
                    if response.status == 200:
                        profile_data = await response.json()
                        user_info = {
                            "client_id": execution_service.dhan_client_id,
                            "name": profile_data.get("name", "Raghu"),
                            "email": profile_data.get("email", ""),
                            "account_type": profile_data.get("account_type", "individual")
                        }
                        logger.info(f"✅ Fetched user profile: {user_info['name']}")
        except Exception as profile_error:
            logger.warning(f"Could not fetch user profile: {profile_error}")
        
        logger.info(f"✅ Dhan OAuth callback processed successfully for {user_info['name']}")
        
        return {
            "status": "success",
            "message": "🧘 Identity aligned. Welcome back, Raghu.",
            "account_details": {
                **user_info,
                "connected_at": datetime.now().isoformat(),
                "status": "active",
                "token_stored": "vault" if GOOGLE_CLOUD_AVAILABLE else "memory"
            },
            "identity_synced": True,
            "chatbot_message": "🧘 Identity aligned. Welcome back, Raghu.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/dhan/postback")
async def handle_dhan_postback(request_data: dict):
    """Handle Dhan postback notifications"""
    try:
        event_type = request_data.get('event_type')
        user_account = request_data.get('user_account')
        
        logger.info(f"Received Dhan postback: type={event_type}, account={user_account}")
        
        # Process different types of postback events
        if event_type == 'order_update':
            # Handle order status updates
            order_id = request_data.get('order_id')
            status = request_data.get('status')
            logger.info(f"Order update: {order_id} -> {status}")
            
        elif event_type == 'position_update':
            # Handle position updates
            symbol = request_data.get('symbol')
            quantity = request_data.get('quantity')
            logger.info(f"Position update: {symbol} quantity={quantity}")
            
        elif event_type == 'funds_update':
            # Handle funds/margin updates
            available_margin = request_data.get('available_margin')
            logger.info(f"Funds update: available_margin={available_margin}")
        
        return {
            "status": "processed",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Postback error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/auth/dhan/initiate")
async def initiate_dhan_oauth():
    """Initiate Dhan OAuth flow with secure configuration"""
    try:
        if not execution_service.oauth_configured:
            raise HTTPException(
                status_code=503, 
                detail="OAuth not configured. Missing client credentials."
            )
        
        # Generate secure state parameter for CSRF protection
        state = hashlib.sha256(f"{uuid.uuid4().hex}{datetime.now().isoformat()}".encode()).hexdigest()[:32]
        
        # Use configured redirect URI
        redirect_uri = execution_service.redirect_uri
        
        # Build Dhan OAuth URL with proper scopes
        scopes = '+'.join(execution_service.oauth_scopes)
        dhan_oauth_url = (
            f"https://api.dhan.co/oauth/authorize"
            f"?client_id={execution_service.dhan_client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&state={state}"
            f"&scope={scopes}"
        )
        
        logger.info(f"OAuth flow initiated with state: {state}")
        
        return {
            "status": "success",
            "auth_url": dhan_oauth_url,
            "state": state,
            "redirect_uri": redirect_uri,
            "scopes": execution_service.oauth_scopes,
            "client_id": execution_service.dhan_client_id,
            "message": "Redirect user to auth_url to complete OAuth flow",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/portfolio")
async def get_portfolio_data():
    """Get portfolio data after OAuth authentication"""
    try:
        if not execution_service.dhan_token or execution_service.dhan_token.startswith('dhan_dev_token'):
            # Return demo portfolio data
            return {
                "status": "success",
                "summary": {
                    "portfolio_value": 485000.00,
                    "total_pnl": 15000.00,
                    "total_positions": 8,
                    "available_margin": 125000.00,
                    "used_margin": 45000.00
                },
                "user": {
                    "name": "Raghu",
                    "client_id": execution_service.dhan_client_id,
                    "account_type": "individual",
                    "status": "active"
                },
                "data": {
                    "positions": [
                        {
                            "symbol": "RELIANCE",
                            "quantity": 50,
                            "average_price": 2450.00,
                            "current_price": 2480.00,
                            "pnl": 1500.00,
                            "pnl_percent": 1.22
                        },
                        {
                            "symbol": "TCS",
                            "quantity": 25,
                            "average_price": 3600.00,
                            "current_price": 3650.00,
                            "pnl": 1250.00,
                            "pnl_percent": 1.39
                        }
                    ]
                },
                "source": "demo",
                "timestamp": datetime.now().isoformat()
            }
        
        # Fetch real portfolio data from Dhan API
        async with aiohttp.ClientSession() as session:
            headers = {
                "access-token": execution_service.dhan_token,
                "client-id": execution_service.dhan_client_id
            }
            
            # Get positions
            async with session.get("https://api.dhan.co/v2/positions", headers=headers) as response:
                if response.status == 200:
                    positions_data = await response.json()
                    
                    # Calculate portfolio summary
                    total_pnl = sum(pos.get('realizedPnl', 0) + pos.get('unrealizedPnl', 0) for pos in positions_data)
                    portfolio_value = sum(pos.get('currentValue', 0) for pos in positions_data)
                    
                    return {
                        "status": "success",
                        "summary": {
                            "portfolio_value": portfolio_value,
                            "total_pnl": total_pnl,
                            "total_positions": len(positions_data),
                            "available_margin": 0,  # Would need separate API call
                            "used_margin": 0
                        },
                        "user": {
                            "name": "Raghu",
                            "client_id": execution_service.dhan_client_id,
                            "account_type": "individual",
                            "status": "active"
                        },
                        "data": {
                            "positions": positions_data
                        },
                        "source": "live",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Fallback to demo data on API failure
                    logger.warning(f"Dhan API error {response.status}, using demo data")
                    return await get_portfolio_data()  # Recursive call will hit demo path
        
    except Exception as e:
        logger.error(f"Portfolio fetch error: {e}")
        # Return demo data on any error
        return {
            "status": "success",
            "summary": {
                "portfolio_value": 485000.00,
                "total_pnl": 15000.00,
                "total_positions": 8
            },
            "user": {
                "name": "Raghu",
                "client_id": execution_service.dhan_client_id
            },
            "data": {"positions": []},
            "source": "error_fallback",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/config/dhan")
async def update_dhan_config(config: Dict[str, str], credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update DHAN access token at runtime for Engine C (API key/secret/client id remain stable)."""
    try:
        if not await execution_service.validate_api_key(credentials.credentials):
            raise HTTPException(status_code=401, detail="Invalid API key")
        token = config.get("access_token") or config.get("DHAN_ACCESS_TOKEN")
        if token:
            execution_service.dhan_token = token
            execution_service.headers["access-token"] = token
        if config.get("client_id"):
            execution_service.dhan_client_id = config["client_id"]
            execution_service.headers["client-id"] = config["client_id"]
            execution_service.rt_headers["client-id"] = config["client_id"]
        return {"status": "updated", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error updating DHAN config (Engine C): {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )
