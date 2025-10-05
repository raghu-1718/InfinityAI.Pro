"""
Engine A - Market Data Ingestion Service
InfinityAI.Pro Trading Platform

Responsibilities:
- Real-time market data ingestion from Dhan WebSocket
- Signal generation from technical indicators  
- Publishing to Kafka event bus with exponential backoff
- Local buffering during event bus partitions
- Heartbeat monitoring and circuit breaker integration
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import pandas as pd
import numpy as np
import websockets
import aioredis
import asyncpg
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configuration
from utils.config import get_settings
from utils.logging_config import setup_logging
from utils.metrics import MetricsCollector
from utils.circuit_breaker import CircuitBreaker
from utils.backoff import ExponentialBackoff

# Initialize logging and settings
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# Global state
kafka_producer: Optional[AIOKafkaProducer] = None
redis_client: Optional[aioredis.Redis] = None
postgres_pool: Optional[asyncpg.Pool] = None
metrics_collector: MetricsCollector = None
circuit_breaker: CircuitBreaker = None
backoff_strategy: ExponentialBackoff = None

# Event Bus Topics
KAFKA_TOPICS = {
    'signals': 'infinityai.signals',
    'market_data': 'infinityai.market_data',
    'heartbeat': 'infinityai.heartbeat',
    'metrics': 'infinityai.metrics'
}

@dataclass
class MarketTick:
    symbol: str
    timestamp: float
    last_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int
    change: float
    change_percent: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass  
class Signal:
    signal_id: str
    symbol: str
    timestamp: float
    signal_type: str  # BUY_CALL, SELL_PUT, LONG, SHORT
    confidence: float
    price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    quantity: Optional[int] = None
    strategy_name: str = "engine-a-v1"
    engine_name: str = "ENGINE_A"
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class TechnicalIndicators:
    """Technical analysis indicators for signal generation"""
    
    def __init__(self, lookback_period: int = 50):
        self.lookback_period = lookback_period
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[int]] = {}
        
    def update_data(self, symbol: str, price: float, volume: int):
        """Update price and volume history"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            self.volume_history[symbol] = []
            
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)
        
        # Keep only recent data
        if len(self.price_history[symbol]) > self.lookback_period:
            self.price_history[symbol] = self.price_history[symbol][-self.lookback_period:]
            self.volume_history[symbol] = self.volume_history[symbol][-self.lookback_period:]
    
    def calculate_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < period + 1:
            return None
            
        prices = np.array(self.price_history[symbol])
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def calculate_ema(self, symbol: str, period: int = 21) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < period:
            return None
            
        prices = np.array(self.price_history[symbol])
        return float(pd.Series(prices).ewm(span=period).mean().iloc[-1])
    
    def calculate_bollinger_bands(self, symbol: str, period: int = 20, std_dev: float = 2.0) -> Optional[Dict[str, float]]:
        """Calculate Bollinger Bands"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < period:
            return None
            
        prices = np.array(self.price_history[symbol][-period:])
        sma = np.mean(prices)
        std = np.std(prices)
        
        return {
            'upper': sma + (std_dev * std),
            'middle': sma,
            'lower': sma - (std_dev * std)
        }
    
    def generate_signals(self, symbol: str, current_price: float) -> List[Signal]:
        """Generate trading signals based on technical indicators"""
        signals = []
        
        # Get indicators
        rsi = self.calculate_rsi(symbol)
        ema_fast = self.calculate_ema(symbol, 9)
        ema_slow = self.calculate_ema(symbol, 21)
        bb_bands = self.calculate_bollinger_bands(symbol)
        
        if not all([rsi, ema_fast, ema_slow, bb_bands]):
            return signals
            
        current_time = time.time()
        
        # RSI-based signals
        if rsi < 30 and current_price < bb_bands['lower']:
            # Oversold + below lower BB = BUY signal
            signal = Signal(
                signal_id=f"sig-{symbol}-{int(current_time * 1000)}",
                symbol=symbol,
                timestamp=current_time,
                signal_type="LONG",
                confidence=0.75,
                price=current_price,
                target_price=bb_bands['middle'],
                stop_loss=current_price * 0.98,
                metadata={
                    'rsi': rsi,
                    'ema_fast': ema_fast,
                    'ema_slow': ema_slow,
                    'bb_upper': bb_bands['upper'],
                    'bb_lower': bb_bands['lower'],
                    'signal_reason': 'rsi_oversold_bb_lower'
                }
            )
            signals.append(signal)
            
        elif rsi > 70 and current_price > bb_bands['upper']:
            # Overbought + above upper BB = SELL signal
            signal = Signal(
                signal_id=f"sig-{symbol}-{int(current_time * 1000)}",
                symbol=symbol,
                timestamp=current_time,
                signal_type="SHORT",
                confidence=0.75,
                price=current_price,
                target_price=bb_bands['middle'],
                stop_loss=current_price * 1.02,
                metadata={
                    'rsi': rsi,
                    'ema_fast': ema_fast,
                    'ema_slow': ema_slow,
                    'bb_upper': bb_bands['upper'],
                    'bb_lower': bb_bands['lower'],
                    'signal_reason': 'rsi_overbought_bb_upper'
                }
            )
            signals.append(signal)
        
        # EMA crossover signals
        if len(self.price_history[symbol]) >= 2:
            prev_ema_fast = self.calculate_ema(symbol[:-1], 9) if len(symbol) > 1 else ema_fast
            prev_ema_slow = self.calculate_ema(symbol[:-1], 21) if len(symbol) > 1 else ema_slow
            
            # Bullish crossover
            if (ema_fast > ema_slow and 
                prev_ema_fast <= prev_ema_slow and 
                rsi > 40 and rsi < 60):
                
                signal = Signal(
                    signal_id=f"sig-{symbol}-{int(current_time * 1000)}-ema",
                    symbol=symbol,
                    timestamp=current_time,
                    signal_type="LONG",
                    confidence=0.65,
                    price=current_price,
                    target_price=current_price * 1.02,
                    stop_loss=current_price * 0.99,
                    metadata={
                        'rsi': rsi,
                        'ema_fast': ema_fast,
                        'ema_slow': ema_slow,
                        'signal_reason': 'ema_bullish_crossover'
                    }
                )
                signals.append(signal)
                
        return signals

class LocalBuffer:
    """Local disk/S3 buffer for when event bus is partitioned"""
    
    def __init__(self, buffer_dir: str = "/tmp/engine-a-buffer"):
        self.buffer_dir = buffer_dir
        self.buffer_file = f"{buffer_dir}/signals_buffer.jsonl"
        
    async def initialize(self):
        """Initialize buffer directory"""
        import os
        os.makedirs(self.buffer_dir, exist_ok=True)
        
    async def store_signal(self, signal: Signal):
        """Store signal to local buffer"""
        try:
            with open(self.buffer_file, 'a') as f:
                f.write(json.dumps(signal.to_dict()) + '\n')
            logger.debug(f"Buffered signal {signal.signal_id}")
        except Exception as e:
            logger.error(f"Failed to buffer signal: {e}")
    
    async def replay_buffered_signals(self):
        """Replay buffered signals when event bus is restored"""
        try:
            if not os.path.exists(self.buffer_file):
                return 0
                
            replayed_count = 0
            with open(self.buffer_file, 'r') as f:
                for line in f:
                    if line.strip():
                        signal_data = json.loads(line.strip())
                        signal = Signal(**signal_data)
                        await publish_signal_with_retry(signal)
                        replayed_count += 1
                        
            # Clear buffer after successful replay
            os.remove(self.buffer_file)
            logger.info(f"Replayed {replayed_count} buffered signals")
            return replayed_count
            
        except Exception as e:
            logger.error(f"Failed to replay buffered signals: {e}")
            return 0

# Initialize components
technical_indicators = TechnicalIndicators(lookback_period=100)
local_buffer = LocalBuffer()

async def initialize_kafka_producer():
    """Initialize Kafka producer with retry logic"""
    global kafka_producer, backoff_strategy
    
    backoff_strategy = ExponentialBackoff(
        base_delay=1.0,
        max_delay=60.0,
        max_retries=10
    )
    
    for attempt in range(backoff_strategy.max_retries):
        try:
            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                # Performance optimizations for HFT
                batch_size=16384,
                linger_ms=5,
                compression_type='snappy',
                acks='all',
                retries=3,
                request_timeout_ms=30000,
                delivery_timeout_ms=120000
            )
            await kafka_producer.start()
            logger.info("Kafka producer initialized successfully")
            return kafka_producer
            
        except Exception as e:
            delay = backoff_strategy.calculate_delay(attempt)
            logger.error(f"Kafka producer init attempt {attempt + 1} failed: {e}, retrying in {delay}s")
            await asyncio.sleep(delay)
    
    raise Exception("Failed to initialize Kafka producer after max retries")

async def publish_signal_with_retry(signal: Signal, max_retries: int = 3):
    """Publish signal with exponential backoff and jitter"""
    global kafka_producer, circuit_breaker, local_buffer
    
    if circuit_breaker and circuit_breaker.is_open():
        logger.warning("Circuit breaker is open, buffering signal locally")
        await local_buffer.store_signal(signal)
        return False
    
    for attempt in range(max_retries):
        try:
            if not kafka_producer:
                await initialize_kafka_producer()
            
            # Add idempotency key
            signal_data = signal.to_dict()
            signal_data['idempotency_key'] = signal.signal_id
            
            await kafka_producer.send_and_wait(
                KAFKA_TOPICS['signals'],
                value=signal_data,
                key=signal.symbol
            )
            
            # Record success metrics
            if metrics_collector:
                await metrics_collector.increment('signals_published_total', tags={'symbol': signal.symbol})
                await metrics_collector.record_latency('signal_publish_latency', time.time() - signal.timestamp)
            
            logger.debug(f"Published signal {signal.signal_id} for {signal.symbol}")
            return True
            
        except KafkaError as e:
            delay = backoff_strategy.calculate_delay(attempt) if backoff_strategy else (2 ** attempt)
            logger.error(f"Kafka publish attempt {attempt + 1} failed: {e}, retrying in {delay}s")
            
            if circuit_breaker:
                circuit_breaker.record_failure()
            
            if attempt == max_retries - 1:
                # Final attempt failed, buffer locally
                logger.error("Max retries exceeded, buffering signal locally")
                await local_buffer.store_signal(signal)
                return False
                
            # Add jitter to prevent thundering herd
            jitter = delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
            await asyncio.sleep(delay + jitter)
            
        except Exception as e:
            logger.error(f"Unexpected error publishing signal: {e}")
            await local_buffer.store_signal(signal)
            return False
    
    return False

async def publish_market_data(tick: MarketTick):
    """Publish market tick data"""
    try:
        if kafka_producer:
            await kafka_producer.send_and_wait(
                KAFKA_TOPICS['market_data'],
                value=tick.to_dict(),
                key=tick.symbol
            )
            
            if metrics_collector:
                await metrics_collector.increment('market_ticks_published_total', tags={'symbol': tick.symbol})
                
    except Exception as e:
        logger.error(f"Failed to publish market data for {tick.symbol}: {e}")

async def dhan_websocket_listener():
    """Main WebSocket listener for Dhan market data"""
    global technical_indicators, metrics_collector
    
    dhan_ws_url = "wss://api.dhan.co/v2/websocket"  # Replace with actual Dhan WebSocket URL
    reconnect_delay = 1.0
    max_reconnect_delay = 60.0
    
    while True:
        try:
            logger.info("Connecting to Dhan WebSocket...")
            
            async with websockets.connect(
                dhan_ws_url,
                extra_headers={
                    "Authorization": f"Bearer {settings.DHAN_ACCESS_TOKEN}",
                    "User-Agent": "InfinityAI-Engine-A/1.0"
                }
            ) as websocket:
                
                logger.info("Connected to Dhan WebSocket")
                reconnect_delay = 1.0  # Reset delay on successful connection
                
                # Subscribe to symbols
                subscribe_message = {
                    "action": "subscribe",
                    "symbols": ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK"],
                    "mode": "full"
                }
                await websocket.send(json.dumps(subscribe_message))
                
                async for raw_message in websocket:
                    try:
                        message = json.loads(raw_message)
                        
                        if message.get('type') == 'tick':
                            # Process market tick
                            tick_data = message['data']
                            
                            tick = MarketTick(
                                symbol=tick_data['symbol'],
                                timestamp=time.time(),
                                last_price=float(tick_data.get('ltp', 0)),
                                open_price=float(tick_data.get('open', 0)),
                                high_price=float(tick_data.get('high', 0)),
                                low_price=float(tick_data.get('low', 0)),
                                volume=int(tick_data.get('volume', 0)),
                                change=float(tick_data.get('change', 0)),
                                change_percent=float(tick_data.get('change_percent', 0)),
                                bid=tick_data.get('bid'),
                                ask=tick_data.get('ask')
                            )
                            
                            # Update technical indicators
                            technical_indicators.update_data(
                                tick.symbol, 
                                tick.last_price, 
                                tick.volume
                            )
                            
                            # Generate signals
                            signals = technical_indicators.generate_signals(
                                tick.symbol, 
                                tick.last_price
                            )
                            
                            # Publish market data
                            await publish_market_data(tick)
                            
                            # Publish signals
                            for signal in signals:
                                await publish_signal_with_retry(signal)
                            
                            # Record metrics
                            if metrics_collector:
                                await metrics_collector.increment('ticks_processed_total')
                                await metrics_collector.increment('signals_generated_total', 
                                                                tags={'count': str(len(signals))})
                        
                        elif message.get('type') == 'error':
                            logger.error(f"WebSocket error: {message}")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")
                        
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {e}")
                        if metrics_collector:
                            await metrics_collector.increment('websocket_errors_total')
                        
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            if metrics_collector:
                await metrics_collector.increment('websocket_connection_errors_total')
        
        # Exponential backoff for reconnection
        logger.info(f"Reconnecting in {reconnect_delay}s...")
        await asyncio.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

async def send_heartbeat():
    """Send periodic heartbeat to monitoring system"""
    while True:
        try:
            heartbeat_data = {
                'engine_name': 'ENGINE_A',
                'timestamp': time.time(),
                'status': 'healthy',
                'metrics': {
                    'kafka_connected': kafka_producer is not None,
                    'redis_connected': redis_client is not None,
                    'circuit_breaker_status': circuit_breaker.status if circuit_breaker else 'unknown'
                }
            }
            
            if kafka_producer:
                await kafka_producer.send_and_wait(
                    KAFKA_TOPICS['heartbeat'],
                    value=heartbeat_data,
                    key='ENGINE_A'
                )
                
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
        
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global kafka_producer, redis_client, postgres_pool, metrics_collector, circuit_breaker
    
    # Startup
    logger.info("Starting Engine A - Market Data Ingestion Service")
    
    try:
        # Initialize components
        await local_buffer.initialize()
        
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
        
        # Initialize circuit breaker
        circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            half_open_max_calls=3
        )
        
        # Initialize Kafka producer
        await initialize_kafka_producer()
        
        # Replay any buffered signals
        await local_buffer.replay_buffered_signals()
        
        # Start background tasks
        asyncio.create_task(dhan_websocket_listener())
        asyncio.create_task(send_heartbeat())
        
        logger.info("Engine A initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Engine A startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Engine A")
        
        if kafka_producer:
            await kafka_producer.stop()
        if redis_client:
            await redis_client.close()
        if postgres_pool:
            await postgres_pool.close()
        
        logger.info("Engine A shutdown completed")

# FastAPI app
app = FastAPI(
    title="InfinityAI Engine A - Market Data Ingestion",
    description="High-frequency market data ingestion and signal generation service",
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global kafka_producer, redis_client, circuit_breaker
    
    status = {
        "engine": "ENGINE_A",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "kafka": kafka_producer is not None,
            "redis": redis_client is not None,
            "circuit_breaker": circuit_breaker.status if circuit_breaker else "unknown"
        }
    }
    
    if circuit_breaker and circuit_breaker.is_open():
        status["status"] = "degraded"
        status["warnings"] = ["Circuit breaker is open"]
    
    return status

@app.get("/metrics")
async def get_metrics():
    """Get engine metrics"""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    return await metrics_collector.get_all_metrics()

@app.post("/circuit-breaker/reset")
async def reset_circuit_breaker():
    """Manual circuit breaker reset"""
    global circuit_breaker
    
    if not circuit_breaker:
        raise HTTPException(status_code=503, detail="Circuit breaker not initialized")
    
    circuit_breaker.reset()
    logger.info("Circuit breaker manually reset")
    
    return {"status": "Circuit breaker reset successfully"}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )