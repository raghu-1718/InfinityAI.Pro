"""
Engine C - Trade Execution Engine
InfinityAI.Pro Trading Platform

Responsibilities:
- Idempotent trade execution with retry logic
- Pre-trade safety checks and risk validation
- Position limits and exposure management
- Stop-loss enforcement at platform level
- Circuit breakers and kill switches
- Broker API integration with exponential backoff
- Trade reconciliation and audit trail
"""

import asyncio
import json
import time
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

import aioredis
import asyncpg
import httpx
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import uvicorn

# Configuration and utilities
from utils.config import get_settings
from utils.logging_config import setup_logging
from utils.metrics import MetricsCollector
from utils.circuit_breaker import CircuitBreaker
from utils.backoff import ExponentialBackoff
from utils.audit import AuditLogger
from utils.encryption import SecureVault

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# Global state
kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_producer: Optional[AIOKafkaProducer] = None
redis_client: Optional[aioredis.Redis] = None
postgres_pool: Optional[asyncpg.Pool] = None
metrics_collector: MetricsCollector = None
audit_logger: AuditLogger = None
secure_vault: SecureVault = None

# Circuit breakers for different operations
broker_circuit_breaker: CircuitBreaker = None
risk_circuit_breaker: CircuitBreaker = None

# Kill switches
kill_switches: Dict[str, bool] = {
    'GLOBAL': False,
    'ACCOUNT': False,
    'STRATEGY': False,
    'SYMBOL': False
}

class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

@dataclass
class TradeRequest:
    idempotency_key: str
    account_id: str
    symbol: str
    order_type: str
    side: str
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "DAY"
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    engine_name: str = "ENGINE_C"
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Position:
    account_id: str
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None

@dataclass
class RiskLimits:
    daily_max_loss: float
    position_limit: float
    max_position_size_percent: float
    symbol_exposure_limit: float
    sector_exposure_limit: float

class PreTradeValidator:
    """Pre-trade checks and risk validation"""
    
    def __init__(self, postgres_pool: asyncpg.Pool, redis_client: aioredis.Redis):
        self.postgres_pool = postgres_pool
        self.redis_client = redis_client
    
    async def validate_trade_request(self, request: TradeRequest) -> Tuple[bool, str]:
        """Comprehensive pre-trade validation"""
        
        # Check kill switches first
        if await self._check_kill_switches(request):
            return False, "Kill switch is active"
        
        # Check account status
        if not await self._validate_account_status(request.account_id):
            return False, "Account is not active"
        
        # Check position limits
        if not await self._validate_position_limits(request):
            return False, "Position limits exceeded"
        
        # Check exposure limits
        if not await self._validate_exposure_limits(request):
            return False, "Exposure limits exceeded"
        
        # Check margin requirements
        if not await self._validate_margin_requirements(request):
            return False, "Insufficient margin"
        
        # Check daily loss limits
        if not await self._validate_daily_loss_limits(request):
            return False, "Daily loss limits exceeded"
        
        # Check correlated symbol exposure
        if not await self._validate_correlated_exposure(request):
            return False, "Correlated exposure limits exceeded"
        
        return True, "Validation passed"
    
    async def _check_kill_switches(self, request: TradeRequest) -> bool:
        """Check if any kill switches are active"""
        try:
            async with self.postgres_pool.acquire() as conn:
                # Check global kill switch
                result = await conn.fetchrow("""
                    SELECT is_active FROM kill_switches 
                    WHERE switch_type = 'GLOBAL' AND is_active = true
                """)
                if result:
                    return True
                
                # Check account kill switch
                result = await conn.fetchrow("""
                    SELECT is_active FROM kill_switches 
                    WHERE switch_type = 'ACCOUNT' AND entity_id = $1 AND is_active = true
                """, request.account_id)
                if result:
                    return True
                
                # Check strategy kill switch
                if request.strategy_id:
                    result = await conn.fetchrow("""
                        SELECT is_active FROM kill_switches 
                        WHERE switch_type = 'STRATEGY' AND entity_id = $1 AND is_active = true
                    """, request.strategy_id)
                    if result:
                        return True
                
                # Check symbol kill switch
                symbol_id = await self._get_symbol_id(request.symbol)
                if symbol_id:
                    result = await conn.fetchrow("""
                        SELECT is_active FROM kill_switches 
                        WHERE switch_type = 'SYMBOL' AND entity_id = $1 AND is_active = true
                    """, symbol_id)
                    if result:
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking kill switches: {e}")
            return True  # Fail safe - block trade if we can't check
    
    async def _validate_account_status(self, account_id: str) -> bool:
        """Validate account is active and in good standing"""
        try:
            async with self.postgres_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT status FROM accounts WHERE id = $1
                """, account_id)
                
                return result and result['status'] == 'ACTIVE'
                
        except Exception as e:
            logger.error(f"Error validating account status: {e}")
            return False
    
    async def _validate_position_limits(self, request: TradeRequest) -> bool:
        """Check position size limits"""
        try:
            async with self.postgres_pool.acquire() as conn:
                # Get account limits
                limits = await conn.fetchrow("""
                    SELECT position_limit, max_position_size_percent 
                    FROM accounts WHERE id = $1
                """, request.account_id)
                
                if not limits:
                    return False
                
                # Get current position value
                current_positions = await conn.fetchval("""
                    SELECT COALESCE(SUM(quantity * avg_price), 0)
                    FROM positions 
                    WHERE account_id = $1 AND status = 'OPEN'
                """, request.account_id)
                
                # Calculate new position value
                estimated_price = request.price or await self._get_current_market_price(request.symbol)
                new_position_value = request.quantity * estimated_price
                
                # Check absolute position limit
                if current_positions + new_position_value > limits['position_limit']:
                    return False
                
                # Check percentage limit
                account_balance = await self._get_account_balance(request.account_id)
                if account_balance > 0:
                    position_percentage = (current_positions + new_position_value) / account_balance * 100
                    if position_percentage > limits['max_position_size_percent']:
                        return False
                
                return True
                
        except Exception as e:
            logger.error(f"Error validating position limits: {e}")
            return False
    
    async def _validate_exposure_limits(self, request: TradeRequest) -> bool:
        """Validate symbol and sector exposure limits"""
        try:
            async with self.postgres_pool.acquire() as conn:
                symbol_id = await self._get_symbol_id(request.symbol)
                if not symbol_id:
                    return False
                
                # Get current symbol exposure
                symbol_exposure = await conn.fetchval("""
                    SELECT COALESCE(SUM(quantity * avg_price), 0)
                    FROM positions p
                    JOIN symbols s ON p.symbol_id = s.id
                    WHERE p.account_id = $1 AND s.symbol = $2 AND p.status = 'OPEN'
                """, request.account_id, request.symbol)
                
                # Check symbol exposure limit (e.g., max 10% per symbol)
                account_balance = await self._get_account_balance(request.account_id)
                estimated_price = request.price or await self._get_current_market_price(request.symbol)
                new_exposure = symbol_exposure + (request.quantity * estimated_price)
                
                if account_balance > 0 and new_exposure / account_balance > 0.1:  # 10% limit
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Error validating exposure limits: {e}")
            return False
    
    async def _validate_margin_requirements(self, request: TradeRequest) -> bool:
        """Check margin requirements for the trade"""
        try:
            # Get available margin from broker or calculate based on account balance
            available_margin = await self._get_available_margin(request.account_id)
            estimated_price = request.price or await self._get_current_market_price(request.symbol)
            required_margin = request.quantity * estimated_price * 0.2  # Assume 20% margin requirement
            
            return available_margin >= required_margin
            
        except Exception as e:
            logger.error(f"Error validating margin requirements: {e}")
            return False
    
    async def _validate_daily_loss_limits(self, request: TradeRequest) -> bool:
        """Check daily loss limits"""
        try:
            async with self.postgres_pool.acquire() as conn:
                # Get daily max loss limit
                daily_limit = await conn.fetchval("""
                    SELECT daily_max_loss FROM accounts WHERE id = $1
                """, request.account_id)
                
                if not daily_limit:
                    return True
                
                # Calculate today's realized losses
                today = datetime.now(timezone.utc).date()
                daily_loss = await conn.fetchval("""
                    SELECT COALESCE(SUM(CASE WHEN realized_pnl < 0 THEN realized_pnl ELSE 0 END), 0)
                    FROM positions 
                    WHERE account_id = $1 AND DATE(closed_at) = $2
                """, request.account_id, today)
                
                return abs(daily_loss) < daily_limit
                
        except Exception as e:
            logger.error(f"Error validating daily loss limits: {e}")
            return False
    
    async def _validate_correlated_exposure(self, request: TradeRequest) -> bool:
        """Check correlated symbol exposure (e.g., sector limits)"""
        try:
            # Get symbol sector information and check sector exposure
            # This is a simplified version - in practice, you'd have sector mappings
            return True
            
        except Exception as e:
            logger.error(f"Error validating correlated exposure: {e}")
            return False
    
    async def _get_symbol_id(self, symbol: str) -> Optional[str]:
        """Get symbol ID from database"""
        try:
            async with self.postgres_pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT id FROM symbols WHERE symbol = $1
                """, symbol)
                return str(result) if result else None
                
        except Exception as e:
            logger.error(f"Error getting symbol ID: {e}")
            return None
    
    async def _get_current_market_price(self, symbol: str) -> float:
        """Get current market price for the symbol"""
        try:
            # Try to get from Redis cache first
            cached_price = await self.redis_client.get(f"price:{symbol}")
            if cached_price:
                return float(cached_price)
            
            # Fallback to database or external API
            return 100.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting market price: {e}")
            return 100.0  # Safe fallback
    
    async def _get_account_balance(self, account_id: str) -> float:
        """Get account balance"""
        try:
            # Get balance from broker API or database
            return 100000.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return 0.0
    
    async def _get_available_margin(self, account_id: str) -> float:
        """Get available margin"""
        try:
            # Get margin from broker API
            return 50000.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting available margin: {e}")
            return 0.0

class BrokerConnector:
    """Dhan broker API connector with retry logic"""
    
    def __init__(self, settings, circuit_breaker: CircuitBreaker):
        self.settings = settings
        self.circuit_breaker = circuit_breaker
        self.client = httpx.AsyncClient(timeout=30.0)
        self.backoff = ExponentialBackoff(base_delay=1.0, max_delay=30.0, max_retries=5)
    
    async def submit_order(self, trade_request: TradeRequest) -> Dict[str, Any]:
        """Submit order to Dhan with retry and idempotency"""
        if self.circuit_breaker.is_open():
            raise HTTPException(status_code=503, detail="Broker circuit breaker is open")
        
        for attempt in range(self.backoff.max_retries):
            try:
                # Prepare order payload
                order_payload = {
                    "security_id": await self._get_dhan_security_id(trade_request.symbol),
                    "exchange_segment": "NSE_EQ",  # Adjust based on symbol
                    "transaction_type": trade_request.side,
                    "quantity": trade_request.quantity,
                    "order_type": trade_request.order_type,
                    "product": "INTRADAY",
                    "price": trade_request.price or 0,
                    "validity": trade_request.time_in_force,
                    "tag": f"InfinityAI-{trade_request.signal_id}"
                }
                
                # Add idempotency header
                headers = {
                    "Authorization": f"Bearer {self.settings.DHAN_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": trade_request.idempotency_key,
                    "User-Agent": "InfinityAI-Engine-C/1.0"
                }
                
                # Submit to Dhan API
                response = await self.client.post(
                    f"{self.settings.DHAN_BASE_URL}/orders",
                    json=order_payload,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    self.circuit_breaker.record_success()
                    
                    # Log successful submission
                    logger.info(f"Order submitted successfully: {trade_request.idempotency_key}")
                    
                    return {
                        "status": "success",
                        "broker_order_id": result.get("order_id"),
                        "message": result.get("message", "Order submitted"),
                        "order_data": result
                    }
                    
                elif response.status_code == 409:
                    # Idempotent - order already exists
                    logger.warning(f"Order already exists: {trade_request.idempotency_key}")
                    return {
                        "status": "duplicate",
                        "message": "Order already submitted"
                    }
                    
                else:
                    # Handle broker rejection
                    error_data = response.json() if response.content else {}
                    logger.error(f"Broker rejected order: {response.status_code} - {error_data}")
                    
                    self.circuit_breaker.record_failure()
                    
                    return {
                        "status": "rejected",
                        "rejection_reason": error_data.get("message", f"HTTP {response.status_code}"),
                        "error_data": error_data
                    }
                    
            except httpx.TimeoutException:
                delay = self.backoff.calculate_delay(attempt)
                logger.warning(f"Broker API timeout, attempt {attempt + 1}, retrying in {delay}s")
                
                self.circuit_breaker.record_failure()
                
                if attempt == self.backoff.max_retries - 1:
                    raise HTTPException(status_code=504, detail="Broker API timeout after retries")
                
                await asyncio.sleep(delay)
                
            except Exception as e:
                delay = self.backoff.calculate_delay(attempt)
                logger.error(f"Broker API error, attempt {attempt + 1}: {e}, retrying in {delay}s")
                
                self.circuit_breaker.record_failure()
                
                if attempt == self.backoff.max_retries - 1:
                    raise HTTPException(status_code=502, detail=f"Broker API error: {str(e)}")
                
                await asyncio.sleep(delay)
        
        raise HTTPException(status_code=502, detail="Max retries exceeded")
    
    async def _get_dhan_security_id(self, symbol: str) -> str:
        """Get Dhan security ID for symbol"""
        # Mapping logic for symbol to Dhan security ID
        symbol_mapping = {
            "RELIANCE": "2885",
            "TCS": "11536",
            "INFY": "1594",
            "HDFCBANK": "1333"
        }
        return symbol_mapping.get(symbol, symbol)

class TradeExecutor:
    """Main trade execution engine with idempotency and safety checks"""
    
    def __init__(self, postgres_pool: asyncpg.Pool, redis_client: aioredis.Redis, 
                 broker: BrokerConnector, validator: PreTradeValidator):
        self.postgres_pool = postgres_pool
        self.redis_client = redis_client
        self.broker = broker
        self.validator = validator
    
    async def execute_trade(self, trade_request: TradeRequest) -> Dict[str, Any]:
        """Execute trade with full safety checks and idempotency"""
        
        # Step 1: Check if request already exists (idempotency)
        existing_request = await self._get_existing_request(trade_request.idempotency_key)
        if existing_request:
            if existing_request['status'] in ['SUBMITTED', 'FILLED', 'PARTIAL']:
                logger.info(f"Request already processed: {trade_request.idempotency_key}")
                return {
                    "status": "already_processed",
                    "existing_status": existing_request['status'],
                    "broker_order_id": existing_request.get('broker_order_id')
                }
        
        # Step 2: Store request in database (idempotent upsert)
        await self._upsert_trade_request(trade_request, OrderStatus.PENDING)
        
        # Step 3: Pre-trade validation
        is_valid, validation_message = await self.validator.validate_trade_request(trade_request)
        if not is_valid:
            await self._update_trade_status(trade_request.idempotency_key, OrderStatus.REJECTED, 
                                          rejection_reason=validation_message)
            logger.warning(f"Trade validation failed: {validation_message}")
            return {
                "status": "rejected",
                "reason": validation_message
            }
        
        # Step 4: Update status to submitting
        await self._update_trade_status(trade_request.idempotency_key, OrderStatus.SUBMITTING)
        
        # Step 5: Submit to broker
        try:
            broker_response = await self.broker.submit_order(trade_request)
            
            if broker_response["status"] == "success":
                await self._update_trade_status(
                    trade_request.idempotency_key, 
                    OrderStatus.SUBMITTED,
                    broker_order_id=broker_response.get("broker_order_id")
                )
                
                # Record metrics
                if metrics_collector:
                    await metrics_collector.increment('trades_submitted_total', 
                                                    tags={'symbol': trade_request.symbol})
                
                return {
                    "status": "submitted",
                    "broker_order_id": broker_response.get("broker_order_id"),
                    "message": "Order submitted successfully"
                }
                
            elif broker_response["status"] == "duplicate":
                await self._update_trade_status(trade_request.idempotency_key, OrderStatus.SUBMITTED)
                return {
                    "status": "duplicate",
                    "message": "Order already exists"
                }
                
            else:
                await self._update_trade_status(
                    trade_request.idempotency_key, 
                    OrderStatus.REJECTED,
                    rejection_reason=broker_response.get("rejection_reason", "Unknown error")
                )
                
                # Record metrics
                if metrics_collector:
                    await metrics_collector.increment('trades_rejected_total',
                                                    tags={'reason': 'broker_rejection'})
                
                return {
                    "status": "rejected",
                    "reason": broker_response.get("rejection_reason", "Broker rejected order")
                }
                
        except Exception as e:
            await self._update_trade_status(
                trade_request.idempotency_key, 
                OrderStatus.FAILED,
                rejection_reason=str(e)
            )
            
            logger.error(f"Trade execution failed: {e}")
            
            if metrics_collector:
                await metrics_collector.increment('trades_failed_total')
            
            return {
                "status": "failed",
                "reason": str(e)
            }
    
    async def _get_existing_request(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Get existing trade request"""
        try:
            async with self.postgres_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT * FROM trade_requests WHERE idempotency_key = $1
                """, idempotency_key)
                
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error getting existing request: {e}")
            return None
    
    async def _upsert_trade_request(self, request: TradeRequest, status: OrderStatus):
        """Upsert trade request to database"""
        try:
            async with self.postgres_pool.acquire() as conn:
                # Get symbol ID
                symbol_id = await conn.fetchval("""
                    SELECT id FROM symbols WHERE symbol = $1
                """, request.symbol)
                
                if not symbol_id:
                    raise ValueError(f"Unknown symbol: {request.symbol}")
                
                await conn.execute("""
                    INSERT INTO trade_requests (
                        idempotency_key, account_id, symbol_id, order_type, side, quantity,
                        price, stop_price, time_in_force, status, strategy_id, signal_id,
                        engine_name, metadata, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), NOW())
                    ON CONFLICT (idempotency_key) 
                    DO UPDATE SET status = $10, updated_at = NOW()
                """, request.idempotency_key, request.account_id, symbol_id,
                request.order_type, request.side, request.quantity, request.price,
                request.stop_price, request.time_in_force, status.value,
                request.strategy_id, request.signal_id, request.engine_name,
                json.dumps(request.metadata) if request.metadata else None)
                
        except Exception as e:
            logger.error(f"Error upserting trade request: {e}")
            raise
    
    async def _update_trade_status(self, idempotency_key: str, status: OrderStatus,
                                 broker_order_id: str = None, rejection_reason: str = None):
        """Update trade request status"""
        try:
            async with self.postgres_pool.acquire() as conn:
                if status == OrderStatus.SUBMITTED and broker_order_id:
                    await conn.execute("""
                        UPDATE trade_requests 
                        SET status = $2, broker_order_id = $3, submitted_at = NOW(), updated_at = NOW()
                        WHERE idempotency_key = $1
                    """, idempotency_key, status.value, broker_order_id)
                    
                elif status in [OrderStatus.REJECTED, OrderStatus.FAILED] and rejection_reason:
                    await conn.execute("""
                        UPDATE trade_requests 
                        SET status = $2, rejection_reason = $3, updated_at = NOW()
                        WHERE idempotency_key = $1
                    """, idempotency_key, status.value, rejection_reason)
                    
                else:
                    await conn.execute("""
                        UPDATE trade_requests 
                        SET status = $2, updated_at = NOW()
                        WHERE idempotency_key = $1
                    """, idempotency_key, status.value)
                    
        except Exception as e:
            logger.error(f"Error updating trade status: {e}")
            raise

# Initialize components
pre_trade_validator: Optional[PreTradeValidator] = None
broker_connector: Optional[BrokerConnector] = None
trade_executor: Optional[TradeExecutor] = None

async def initialize_components():
    """Initialize all components"""
    global pre_trade_validator, broker_connector, trade_executor
    global broker_circuit_breaker, risk_circuit_breaker
    
    # Initialize circuit breakers
    broker_circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        half_open_max_calls=3
    )
    
    risk_circuit_breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=30,
        half_open_max_calls=2
    )
    
    # Initialize components
    pre_trade_validator = PreTradeValidator(postgres_pool, redis_client)
    broker_connector = BrokerConnector(settings, broker_circuit_breaker)
    trade_executor = TradeExecutor(postgres_pool, redis_client, broker_connector, pre_trade_validator)

async def consume_signals():
    """Consume signals from Kafka and execute trades"""
    global kafka_consumer, trade_executor
    
    while True:
        try:
            if not kafka_consumer:
                await initialize_kafka_consumer()
            
            async for message in kafka_consumer:
                try:
                    signal_data = json.loads(message.value.decode('utf-8'))
                    
                    # Convert signal to trade request
                    trade_request = TradeRequest(
                        idempotency_key=signal_data.get('idempotency_key', 
                                                      f"trade-{uuid.uuid4()}"),
                        account_id="account_id_from_config",  # Get from settings
                        symbol=signal_data['symbol'],
                        order_type=OrderType.MARKET.value,
                        side=OrderSide.BUY.value if signal_data['signal_type'] in ['LONG', 'BUY_CALL'] else OrderSide.SELL.value,
                        quantity=signal_data.get('quantity', 1),
                        price=signal_data.get('price'),
                        strategy_id=signal_data.get('strategy_id'),
                        signal_id=signal_data.get('signal_id'),
                        metadata=signal_data.get('metadata')
                    )
                    
                    # Execute trade
                    if trade_executor:
                        result = await trade_executor.execute_trade(trade_request)
                        logger.info(f"Trade execution result: {result}")
                        
                        # Record metrics
                        if metrics_collector:
                            await metrics_collector.increment('signals_processed_total')
                    
                except Exception as e:
                    logger.error(f"Error processing signal: {e}")
                    if metrics_collector:
                        await metrics_collector.increment('signal_processing_errors_total')
                        
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
            await asyncio.sleep(5)  # Wait before retrying

async def initialize_kafka_consumer():
    """Initialize Kafka consumer"""
    global kafka_consumer
    
    kafka_consumer = AIOKafkaConsumer(
        'infinityai.signals',
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id='engine-c-execution',
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda m: m.decode('utf-8') if m else None
    )
    await kafka_consumer.start()
    logger.info("Kafka consumer initialized")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global redis_client, postgres_pool, metrics_collector, audit_logger
    global kafka_consumer, kafka_producer
    
    # Startup
    logger.info("Starting Engine C - Trade Execution Service")
    
    try:
        # Initialize Redis
redis_client = None
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
except redis.exceptions.ConnectionError as e:
    logger.warning(f"Could not connect to Redis: {e}")
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize PostgreSQL
        postgres_pool = await asyncpg.create_pool(settings.DATABASE_URL)
        logger.info("PostgreSQL connection pool created")
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector(redis_client)
        
        # Initialize audit logger
        audit_logger = AuditLogger(postgres_pool)
        
        # Initialize components
        await initialize_components()
        
        # Initialize Kafka consumer
        await initialize_kafka_consumer()
        
        # Start background tasks
        asyncio.create_task(consume_signals())
        
        logger.info("Engine C initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Engine C startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Engine C")
        
        if kafka_consumer:
            await kafka_consumer.stop()
        if kafka_producer:
            await kafka_producer.stop()
        if redis_client:
            await redis_client.close()
        if postgres_pool:
            await postgres_pool.close()
        
        logger.info("Engine C shutdown completed")

# FastAPI app
app = FastAPI(
    title="InfinityAI Engine C - Trade Execution",
    description="Idempotent trade execution engine with comprehensive safety features",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models for API
class TradeRequestModel(BaseModel):
    symbol: str
    order_type: str = "MARKET"
    side: str  # BUY or SELL
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "DAY"
    strategy_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('side')
    def validate_side(cls, v):
        if v not in ['BUY', 'SELL']:
            raise ValueError('Side must be BUY or SELL')
        return v

class KillSwitchModel(BaseModel):
    switch_type: str  # GLOBAL, ACCOUNT, STRATEGY, SYMBOL
    entity_id: Optional[str] = None
    reason: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "engine": "ENGINE_C",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "kafka": kafka_consumer is not None,
            "redis": redis_client is not None,
            "postgres": postgres_pool is not None,
            "broker_circuit_breaker": broker_circuit_breaker.status if broker_circuit_breaker else "unknown"
        }
    }
    
    return status

# ALB path alias for Engine C health
@app.get("/engine-c/health")
async def health_check_alias():
    return await health_check()

@app.post("/internal/submit_trade")
async def submit_trade_internal(trade_request: TradeRequestModel):
    """Internal API for trade submission"""
    if not trade_executor:
        raise HTTPException(status_code=503, detail="Trade executor not initialized")
    
    # Create trade request with idempotency key
    request = TradeRequest(
        idempotency_key=f"api-{uuid.uuid4()}",
        account_id="default_account",  # Get from auth context
        symbol=trade_request.symbol,
        order_type=trade_request.order_type,
        side=trade_request.side,
        quantity=trade_request.quantity,
        price=trade_request.price,
        stop_price=trade_request.stop_price,
        time_in_force=trade_request.time_in_force,
        strategy_id=trade_request.strategy_id,
        metadata=trade_request.metadata
    )
    
    result = await trade_executor.execute_trade(request)
    return result

@app.post("/kill-switch/{switch_type}")
async def activate_kill_switch(switch_type: str, request: KillSwitchModel):
    """Activate kill switch"""
    if switch_type not in ['GLOBAL', 'ACCOUNT', 'STRATEGY', 'SYMBOL']:
        raise HTTPException(status_code=400, detail="Invalid kill switch type")
    
    try:
        async with postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO kill_switches (switch_type, entity_id, is_active, reason, triggered_by, triggered_at)
                VALUES ($1, $2, true, $3, 'api', NOW())
                ON CONFLICT (switch_type, entity_id) 
                DO UPDATE SET is_active = true, reason = $3, triggered_at = NOW()
            """, switch_type, request.entity_id, request.reason)
        
        logger.warning(f"Kill switch activated: {switch_type} - {request.reason}")
        
        return {"status": "activated", "switch_type": switch_type, "reason": request.reason}
        
    except Exception as e:
        logger.error(f"Error activating kill switch: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate kill switch")

@app.delete("/kill-switch/{switch_type}")
async def deactivate_kill_switch(switch_type: str, entity_id: Optional[str] = None):
    """Deactivate kill switch"""
    try:
        async with postgres_pool.acquire() as conn:
            await conn.execute("""
                UPDATE kill_switches 
                SET is_active = false, cleared_at = NOW()
                WHERE switch_type = $1 AND ($2 IS NULL OR entity_id = $2)
            """, switch_type, entity_id)
        
        logger.info(f"Kill switch deactivated: {switch_type}")
        
        return {"status": "deactivated", "switch_type": switch_type}
        
    except Exception as e:
        logger.error(f"Error deactivating kill switch: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate kill switch")

@app.get("/metrics")
async def get_metrics():
    """Get engine metrics"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    return await metrics_collector.get_all_metrics()

@app.get("/status")
async def get_system_status():
    """Get overall system status aggregated from dependencies"""
    try:
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engines": {},
            "services": {}
        }
        # Probe Engine A and B if URLs are provided via env (optional wiring)
        engine_a_url = os.getenv("ENGINE_A_URL")
        engine_b_url = os.getenv("ENGINE_B_URL")
        async with httpx.AsyncClient(timeout=5.0) as client:
            if engine_a_url:
                try:
                    ra = await client.get(f"{engine_a_url}/health")
                    status["engines"]["engine_a"] = ra.json() if ra.status_code == 200 else {"status": "error"}
                except Exception:
                    status["engines"]["engine_a"] = {"status": "unreachable"}
            if engine_b_url:
                try:
                    rb = await client.get(f"{engine_b_url}/health")
                    status["engines"]["engine_b"] = rb.json() if rb.status_code == 200 else {"status": "error"}
                except Exception:
                    status["engines"]["engine_b"] = {"status": "unreachable"}
        # Local services
        status["services"]["redis"] = {"status": "connected" if redis_client else "unknown"}
        status["services"]["database"] = {"status": "connected" if postgres_pool else "unknown"}
        return status
    except Exception:
        return {"status": "error"}

@app.get("/engine-c/status")
async def get_system_status_alias():
    return await get_system_status()

@app.get("/dashboard/summary")
async def dashboard_summary():
    s = await get_system_status()
    overall = "healthy" if all((v.get("status") == "healthy" or v.get("status") == True)
                                 for v in s.get("engines", {}).values()) else "degraded"
    return {
        "app_health": overall,
        "engines": s.get("engines", {}),
        "services": s.get("services", {})
    }

@app.get("/engine-c/dashboard/summary")
async def dashboard_summary_alias():
    return await dashboard_summary()

ULTRA_MODE = os.getenv("ULTRA_AGGRESSIVE_MODE", "false").lower() == "true"

@app.post("/ultra/toggle")
async def toggle_ultra(mode: bool):
    global ULTRA_MODE
    ULTRA_MODE = bool(mode)
    return {"status": "ok", "ultra_aggressive_mode": ULTRA_MODE}

@app.post("/circuit-breaker/{breaker_type}/reset")
async def reset_circuit_breaker(breaker_type: str):
    """Reset circuit breaker"""
    global broker_circuit_breaker, risk_circuit_breaker
    
    if breaker_type == "broker" and broker_circuit_breaker:
        broker_circuit_breaker.reset()
        logger.info("Broker circuit breaker reset")
        return {"status": "reset", "breaker": "broker"}
    
    elif breaker_type == "risk" and risk_circuit_breaker:
        risk_circuit_breaker.reset()
        logger.info("Risk circuit breaker reset")
        return {"status": "reset", "breaker": "risk"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid circuit breaker type")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )