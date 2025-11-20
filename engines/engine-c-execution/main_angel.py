#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine C: Trade Execution Engine (Angel SmartAPI)
Complete trade execution with Angel SmartAPI (TOTP-based daily session)
Replaces Dhan OAuth completely
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
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
import sys
import base64

# Angel SmartAPI SDK (try both module name variants)
try:
    from SmartApi import SmartConnect  # Common upstream import
    import pyotp
    ANGEL_SDK_AVAILABLE = True
except ImportError as e1:
    try:
        from smartapi import SmartConnect  # Fallback for lowercase module name
        import pyotp
        ANGEL_SDK_AVAILABLE = True
    except ImportError as e2:
        ANGEL_SDK_AVAILABLE = False
        logging.warning(
            f"Angel SmartAPI SDK not available - install: pip install smartapi-python pyotp | errors: {e1}; {e2}"
        )

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
    format='%(asctime)s - ENGINE-C-ANGEL - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('engine_c_angel.log'),
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
        return os.getenv(secret_id.upper().replace('-', '_'), '')

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        return os.getenv(secret_id.upper().replace('-', '_'), '')

def store_secret(secret_id: str, value: str) -> bool:
    """Store/update secret in Google Secret Manager"""
    if not GOOGLE_CLOUD_AVAILABLE:
        logger.warning(f"Cannot store {secret_id} - Secret Manager not available")
        return False

    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{PROJECT_ID}"
        secret_name = f"{parent}/secrets/{secret_id}"

        # Try to add version to existing secret
        try:
            client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": value.encode("utf-8")}
                }
            )
            logger.info(f"✅ Updated secret: {secret_id}")
            return True
        except:
            # Create new secret if doesn't exist
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": value.encode("utf-8")}
                }
            )
            logger.info(f"✅ Created secret: {secret_id}")
            return True
    except Exception as e:
        logger.error(f"Error storing secret {secret_id}: {e}")
        return False

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOPLOSS_LIMIT = "STOPLOSS_LIMIT"
    STOPLOSS_MARKET = "STOPLOSS_MARKET"

class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class ProductType(Enum):
    DELIVERY = "DELIVERY"
    INTRADAY = "INTRADAY"
    MARGIN = "MARGIN"
    BO = "BO"  # Bracket Order
    CO = "CO"  # Cover Order

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

class AngelTradingService:
    def __init__(self):
        """Initialize Angel SmartAPI trading service"""
        # Load Angel credentials from Secret Manager
        self.client_id = get_secret('angel-client-id')
        self.api_key = get_secret('angel-api-key')
        self.password = get_secret('angel-password')
        self.mpin = get_secret('angel-mpin')  # MPIN for new Angel auth flow

        # Session tokens (refreshed daily via TOTP)
        self.jwt_token = get_secret('angel-jwt-token')
        self.refresh_token = get_secret('angel-refresh-token')
        self.feed_token = get_secret('angel-feed-token')

        # Angel API configuration
        self.base_url = "https://apiconnect.angelone.in"

        # Initialize SmartConnect (if SDK available)
        self.smart_api = None
        if ANGEL_SDK_AVAILABLE and self.api_key:
            try:
                self.smart_api = SmartConnect(api_key=self.api_key)
                if self.jwt_token:
                    self.smart_api.setAccessToken(self.jwt_token)
                logger.info("✅ Angel SmartAPI initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SmartAPI: {e}")

        # Risk management parameters
        self.max_position_size = 100000  # Max position size in rupees
        self.max_daily_loss = 50000      # Max daily loss limit
        self.max_open_positions = 10     # Max open positions

        # In-memory storage (in production, use database)
        self.orders: Dict[str, TradeOrder] = {}
        self.positions: Dict[str, Any] = {}
        self.daily_pnl = 0.0

        # Execution enabled if we have valid session
        self.execution_enabled = bool(self.jwt_token and self.client_id)

        # Kill switch
        self.kill_switch_active = False

        logger.info(f"🎯 Engine C - Angel SmartAPI Initialized (Execution: {'ENABLED' if self.execution_enabled else 'DISABLED'})")

    def _ensure_smartapi(self):
        """Lazily initialize SmartAPI client if available and not yet created."""
        if not ANGEL_SDK_AVAILABLE:
            return False
        if self.smart_api is None and self.api_key:
            try:
                self.smart_api = SmartConnect(api_key=self.api_key)
                if self.jwt_token:
                    self.smart_api.setAccessToken(self.jwt_token)
                logger.info("🔄 SmartAPI client initialized on-demand")
                return True
            except Exception as e:
                logger.error(f"Lazy SmartAPI init failed: {e}")
                self.smart_api = None
                return False
        return self.smart_api is not None

    async def generate_session(self, totp: str) -> Dict[str, Any]:
        """
        Generate new 24-hour trading session using TOTP

        Args:
            totp: 6-digit TOTP from Google Authenticator

        Returns:
            Session details with expiry timestamp
        """
        if not self.client_id or not self.password or not self.api_key:
            raise HTTPException(status_code=500, detail="Angel credentials not configured")

        try:
            # Prefer MPIN REST flow when MPIN is configured
            if getattr(self, 'mpin', None):
                import httpx
                login_url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByMpin"
                headers = {
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Referer": "https://smartapi.angelone.in/",
                    "Origin": "https://smartapi.angelone.in",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-PrivateKey": self.api_key,
                    # Angel API expects client identifiers in headers
                    "X-ClientLocalIP": os.getenv("CLIENT_LOCAL_IP", "127.0.0.1"),
                    "X-ClientPublicIP": os.getenv("CLIENT_PUBLIC_IP", "0.0.0.0"),
                    "X-MACAddress": os.getenv("CLIENT_MAC", "AA:BB:CC:DD:EE:FF"),
                }
                payload = {
                    "clientcode": self.client_id,
                    "mpin": self.mpin,
                }
                if totp and len(totp) == 6:
                    payload["totp"] = totp

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(login_url, headers=headers, json=payload)
                    try:
                        resp_data = resp.json()
                    except Exception:
                        body = (await resp.aread()).decode(errors='ignore')
                        raise HTTPException(status_code=resp.status_code or 500, detail=f"Angel login error: {body[:200]}")
                    if resp.status_code != 200 or not resp_data.get("status"):
                        message = resp_data.get("message", "MPIN login failed")
                        raise HTTPException(status_code=401, detail=message)
                    data = resp_data.get("data", {})
                    self.jwt_token = (data.get("jwtToken", "") or "").strip()
                    self.refresh_token = (data.get("refreshToken", "") or "").strip()
                    self.feed_token = (data.get("feedToken", "") or "").strip()
            elif ANGEL_SDK_AVAILABLE and self.smart_api is not None:
                # Generate session via Angel SmartAPI SDK
                data = self.smart_api.generateSession(self.client_id, self.password, totp)

                if data.get('status') == False:
                    raise HTTPException(status_code=401, detail=data.get('message', 'TOTP validation failed'))

                # Extract tokens
                self.jwt_token = (data['data']['jwtToken'] or "").strip()
                self.refresh_token = (data['data']['refreshToken'] or "").strip()
                self.feed_token = (self.smart_api.getfeedToken() or "").strip()
            else:
                # Fallback: Direct REST call with password
                import httpx
                login_url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
                headers = {
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Referer": "https://smartapi.angelone.in/",
                    "Origin": "https://smartapi.angelone.in",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-PrivateKey": self.api_key,
                    # Angel API expects client identifiers in headers
                    "X-ClientLocalIP": os.getenv("CLIENT_LOCAL_IP", "127.0.0.1"),
                    "X-ClientPublicIP": os.getenv("CLIENT_PUBLIC_IP", "0.0.0.0"),
                    "X-MACAddress": os.getenv("CLIENT_MAC", "AA:BB:CC:DD:EE:FF"),
                }
                payload = {
                    "clientcode": self.client_id,
                    "password": self.password,
                }
                if totp and len(totp) == 6:
                    payload["totp"] = totp
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(login_url, headers=headers, json=payload)
                    try:
                        resp_data = resp.json()
                    except Exception:
                        body = (await resp.aread()).decode(errors='ignore')
                        raise HTTPException(status_code=resp.status_code or 500, detail=f"Angel login error: {body[:200]}")
                    if resp.status_code != 200 or not resp_data.get("status"):
                        message = resp_data.get("message", "Password login failed")
                        raise HTTPException(status_code=401, detail=message)
                    data = resp_data.get("data", {})
                    self.jwt_token = (data.get("jwtToken", "") or "").strip()
                    self.refresh_token = (data.get("refreshToken", "") or "").strip()
                    self.feed_token = (data.get("feedToken", "") or "").strip()

            # Store tokens in Secret Manager
            if self.jwt_token:
                store_secret('angel-jwt-token', self.jwt_token)
            if self.refresh_token:
                store_secret('angel-refresh-token', self.refresh_token)
            if self.feed_token:
                store_secret('angel-feed-token', self.feed_token)

            # Update SmartAPI instance if present
            if ANGEL_SDK_AVAILABLE and self.smart_api is not None and self.jwt_token:
                self.smart_api.setAccessToken(self.jwt_token)

            self.execution_enabled = bool(self.jwt_token)

            # Calculate expiry (24 hours from now) — SmartAPI JWTs typically ~24h
            expiry_time = datetime.now() + timedelta(hours=24)

            logger.info(f"✅ Angel session generated successfully (expires: {expiry_time.isoformat()})")

            return {
                "success": True,
                "sessionExpiry": expiry_time.isoformat(),
                "message": "Angel One session active for 24 hours"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Session generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Session generation error: {str(e)}")

    async def place_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        order_type: OrderType,
        transaction_type: TransactionType,
        product_type: ProductType = ProductType.INTRADAY,
        exchange: str = "NSE"
    ) -> Dict[str, Any]:
        """
        Place order via Angel SmartAPI

        Args:
            symbol: Trading symbol (e.g., "SBIN-EQ")
            quantity: Order quantity
            price: Order price (0 for market orders)
            order_type: MARKET, LIMIT, STOPLOSS_LIMIT, STOPLOSS_MARKET
            transaction_type: BUY or SELL
            product_type: DELIVERY, INTRADAY, MARGIN
            exchange: NSE, BSE, NFO, MCX

        Returns:
            Order placement response with order ID
        """
        if not self.execution_enabled:
            raise HTTPException(status_code=403, detail="Angel session not active - generate session first")

        if self.kill_switch_active:
            raise HTTPException(status_code=403, detail="Kill switch activated - trading suspended")

        try:
            # Ensure SmartAPI client is available
            if not self._ensure_smartapi():
                raise HTTPException(status_code=503, detail="Angel SmartAPI SDK not available for order placement")
            # Prepare order parameters for Angel API
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": "3045",  # TODO: Fetch from symbol master
                "transactiontype": transaction_type.value,
                "exchange": exchange,
                "ordertype": order_type.value,
                "producttype": product_type.value,
                "duration": "DAY",
                "price": str(price) if order_type != OrderType.MARKET else "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(quantity)
            }

            # Place order via SmartAPI
            order_id = self.smart_api.placeOrder(order_params)

            logger.info(f"✅ Order placed: {order_id} ({transaction_type.value} {quantity} {symbol} @ ₹{price})")

            # Store in memory
            order = TradeOrder(
                order_id=str(order_id),
                symbol=symbol,
                quantity=quantity,
                price=price,
                order_type=order_type,
                transaction_type=transaction_type,
                status=OrderStatus.PENDING,
                created_at=datetime.now()
            )
            self.orders[str(order_id)] = order

            return {
                "success": True,
                "order_id": str(order_id),
                "message": f"Order placed successfully",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            raise HTTPException(status_code=500, detail=f"Order placement error: {str(e)}")

    async def get_holdings(self) -> Dict[str, Any]:
        """Fetch holdings from Angel SmartAPI"""
        if not self.execution_enabled:
            return {"error": "Session not active", "holdings": []}

        try:
            # Try SDK first
            if self._ensure_smartapi():
                try:
                    holdings = self.smart_api.holding()
                    return {
                        "success": True,
                        "holdings": holdings.get('data', []),
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as sdk_err:
                    logger.warning(f"SDK holdings failed, trying REST: {sdk_err}")

            # REST fallback using httpx for better HTTP compliance handling
            import httpx
            url = f"{self.base_url}/rest/secure/angelbroking/portfolio/v1/getHolding"
            token = (self.jwt_token or '').strip()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-PrivateKey": self.api_key,
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "0.0.0.0",
                "X-MACAddress": "AA:BB:CC:DD:EE:FF"
            }

            async with httpx.AsyncClient(timeout=20.0, verify=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return {
                    "success": data.get('status', False),
                    "holdings": data.get('data', []),
                    "timestamp": datetime.now().isoformat(),
                    "source": "rest_api"
                }
        except Exception as e:
            logger.error(f"Get holdings failed: {e}")
            return {"error": str(e), "holdings": []}

    async def get_positions(self) -> Dict[str, Any]:
        """Fetch positions from Angel SmartAPI"""
        if not self.execution_enabled:
            return {"error": "Session not active", "positions": []}

        try:
            # Try SDK first
            if self._ensure_smartapi():
                try:
                    positions = self.smart_api.position()
                    return {
                        "success": True,
                        "positions": positions.get('data', []),
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as sdk_err:
                    logger.warning(f"SDK positions failed, trying REST: {sdk_err}")

            # REST fallback using httpx
            import httpx
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/getPosition"
            token = (self.jwt_token or '').strip()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-PrivateKey": self.api_key,
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "0.0.0.0",
                "X-MACAddress": "AA:BB:CC:DD:EE:FF"
            }

            async with httpx.AsyncClient(timeout=20.0, verify=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return {
                    "success": data.get('status', False),
                    "positions": data.get('data', []),
                    "timestamp": datetime.now().isoformat(),
                    "source": "rest_api"
                }
        except Exception as e:
            logger.error(f"Get positions failed: {e}")
            return {"error": str(e), "positions": []}

    async def get_funds(self) -> Dict[str, Any]:
        """Fetch fund limits from Angel SmartAPI"""
        if not self.execution_enabled:
            return {"error": "Session not active", "funds": {}}

        try:
            # Try SDK first
            if self._ensure_smartapi():
                try:
                    funds = self.smart_api.rmsLimit()
                    return {
                        "success": True,
                        "funds": funds.get('data', {}),
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as sdk_err:
                    logger.warning(f"SDK funds failed, trying REST: {sdk_err}")

            # REST fallback using httpx
            import httpx
            url = f"{self.base_url}/rest/secure/angelbroking/user/v1/getRMS"
            token = (self.jwt_token or '').strip()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-PrivateKey": self.api_key,
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "0.0.0.0",
                "X-MACAddress": "AA:BB:CC:DD:EE:FF"
            }

            async with httpx.AsyncClient(timeout=20.0, verify=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return {
                    "success": data.get('status', False),
                    "funds": data.get('data', {}),
                    "timestamp": datetime.now().isoformat(),
                    "source": "rest_api"
                }
        except Exception as e:
            logger.error(f"Get funds failed: {e}")
            return {"error": str(e), "funds": {}}

# Global service instance
trading_service = AngelTradingService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Engine C - Angel SmartAPI Service starting...")
    yield
    # Shutdown
    logger.info("🛑 Engine C - Angel SmartAPI Service shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="🎯 InfinityAI.Pro - Engine C: Angel SmartAPI Execution",
    description="Complete trade execution via Angel SmartAPI with TOTP-based daily sessions",
    version="2.0.0",
    lifespan=lifespan
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://infinityai.pro,https://www.infinityai.pro,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# ============================================================================
# ANGEL SMARTAPI ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "Engine C - Angel SmartAPI Trade Execution",
        "status": "active",
        "version": "2.0.0",
        "broker": "Angel One SmartAPI",
        "execution_enabled": trading_service.execution_enabled,
        "kill_switch": trading_service.kill_switch_active,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-c-angel",
        "version": "2.0.0",
        "broker": "Angel SmartAPI",
        "execution_status": "enabled" if trading_service.execution_enabled else "disabled",
        "session_active": bool((trading_service.jwt_token or '').strip()),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/angel/generate-session")
async def generate_session(request_data: dict):
    """
    Generate daily trading session using TOTP

    Body: {"totp": "123456"}
    """
    totp = request_data.get('totp', '')
    if totp and len(totp) != 6:
        raise HTTPException(status_code=400, detail="Invalid TOTP - must be 6 digits if provided")
    result = await trading_service.generate_session(totp)
    return result

@app.post("/api/angel/place-order")
async def place_order(request_data: dict):
    """
    Place order via Angel SmartAPI

    Body: {
        "symbol": "SBIN-EQ",
        "quantity": 10,
        "price": 550.25,
        "order_type": "LIMIT",
        "transaction_type": "BUY",
        "product_type": "INTRADAY",
        "exchange": "NSE"
    }
    """
    try:
        symbol = request_data.get('symbol')
        quantity = int(request_data.get('quantity', 1))
        price = float(request_data.get('price', 0))
        order_type = OrderType(request_data.get('order_type', 'MARKET'))
        transaction_type = TransactionType(request_data.get('transaction_type', 'BUY'))
        product_type = ProductType(request_data.get('product_type', 'INTRADAY'))
        exchange = request_data.get('exchange', 'NSE')

        result = await trading_service.place_order(
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type,
            transaction_type=transaction_type,
            product_type=product_type,
            exchange=exchange
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/angel/holdings")
async def get_holdings():
    """Get current holdings from Angel SmartAPI"""
    return await trading_service.get_holdings()

@app.get("/api/angel/positions")
async def get_positions():
    """Get current positions from Angel SmartAPI"""
    return await trading_service.get_positions()

@app.get("/api/angel/funds")
async def get_funds():
    """Get fund limits from Angel SmartAPI"""
    return await trading_service.get_funds()

@app.get("/api/angel/session-status")
async def session_status():
    """Check if Angel session is active"""
    # Decode JWT and check expiry
    jwt_token = trading_service.jwt_token or ""
    if not jwt_token:
        return {
            "active": False,
            "expiresIn": 0,
            "message": "No active session - generate new session with TOTP"
        }

    # Parse JWT payload (without verification)
    try:
        parts = jwt_token.split(".")
        if len(parts) < 2:
            return {"active": False, "expiresIn": 0}

        # Base64 decode payload
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        payload = json.loads(payload_bytes.decode("utf-8"))

        exp = payload.get('exp', 0)
        now = int(datetime.utcnow().timestamp())
        seconds_remaining = max(0, exp - now)

        return {
            "active": exp > now,
            "expiresIn": seconds_remaining,
            "expiryTime": datetime.fromtimestamp(exp).isoformat() if exp else None,
            "message": f"Session expires in {seconds_remaining // 3600}h {(seconds_remaining % 3600) // 60}m"
        }
    except Exception as e:
        logger.error(f"Error parsing JWT: {e}")
        return {"active": False, "expiresIn": 0, "error": str(e)}

@app.post("/api/angel/store-credentials")
async def store_credentials(request_data: dict):
    """
    Store long-term Angel credentials in Secret Manager

    Body: {
        "client_id": "R12345678",
        "api_key": "your_api_key",
        "password": "your_password",  # Legacy - keep for backwards compatibility
        "mpin": "your_4_digit_mpin"   # New Angel auth requirement
    }
    """
    client_id = request_data.get('client_id', '').strip()
    api_key = request_data.get('api_key', '').strip()
    password = request_data.get('password', '').strip()
    mpin = request_data.get('mpin', '').strip()

    if not all([client_id, api_key]):
        raise HTTPException(status_code=400, detail="client_id and api_key are required")

    if not mpin and not password:
        raise HTTPException(status_code=400, detail="Either mpin or password is required")

    # Store in Secret Manager
    success_count = 0
    if store_secret('angel-client-id', client_id):
        success_count += 1
    if store_secret('angel-api-key', api_key):
        success_count += 1
    if password and store_secret('angel-password', password):
        success_count += 1
    if mpin and store_secret('angel-mpin', mpin):
        success_count += 1

    # Update service instance
    trading_service.client_id = client_id
    trading_service.api_key = api_key
    if password:
        trading_service.password = password
    if mpin:
        trading_service.mpin = mpin

    # Reinitialize SmartAPI
    if ANGEL_SDK_AVAILABLE:
        trading_service.smart_api = SmartConnect(api_key=api_key)

    return {
        "success": success_count >= 3,
        "stored": success_count,
        "message": f"Stored {success_count} credentials securely (including MPIN)" if mpin else f"Stored {success_count} credentials securely"
    }

@app.post("/api/kill-switch")
async def toggle_kill_switch(action: str):
    """Activate/deactivate kill switch"""
    if action == "activate":
        trading_service.kill_switch_active = True
        return {"status": "activated", "message": "All trading suspended"}
    elif action == "deactivate":
        trading_service.kill_switch_active = False
        return {"status": "deactivated", "message": "Trading enabled"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
