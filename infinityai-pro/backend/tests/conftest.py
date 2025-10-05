"""
Test configuration for InfinityAI.Pro Trading Platform
Pytest configuration with fixtures for testing engines and infrastructure
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
import aioredis
import asyncpg
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer

from backend.engines.engine_a.utils.config import get_settings
from backend.engines.engine_a.utils.metrics import MetricsCollector

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container for testing"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
async def redis_container():
    """Start Redis container for testing"""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis

@pytest.fixture(scope="session") 
async def kafka_container():
    """Start Kafka container for testing"""
    with KafkaContainer() as kafka:
        yield kafka

@pytest_asyncio.fixture
async def redis_client(redis_container) -> AsyncGenerator[aioredis.Redis, None]:
    """Redis client fixture"""
    client = aioredis.from_url(redis_container.get_connection_url())
    try:
        yield client
    finally:
        await client.close()

@pytest_asyncio.fixture
async def postgres_pool(postgres_container) -> AsyncGenerator[asyncpg.Pool, None]:
    """PostgreSQL connection pool fixture"""
    pool = await asyncpg.create_pool(postgres_container.get_connection_url())
    try:
        yield pool
    finally:
        await pool.close()

@pytest_asyncio.fixture
async def metrics_collector(redis_client) -> MetricsCollector:
    """Metrics collector fixture"""
    return MetricsCollector(redis_client, retention_days=1)

@pytest.fixture
def test_settings():
    """Test settings fixture"""
    settings = get_settings()
    settings.ENVIRONMENT = "testing"
    settings.LOG_LEVEL = "DEBUG"
    return settings

@pytest.fixture
def sample_market_data() -> Dict[str, Any]:
    """Sample market data for testing"""
    return {
        "symbol": "RELIANCE",
        "timestamp": 1609459200.0,  # 2021-01-01 00:00:00
        "open": 100.0,
        "high": 105.0,
        "low": 98.0,
        "close": 103.0,
        "volume": 10000,
        "indicators": {
            "rsi": 65.5,
            "ema_20": 102.0,
            "ema_50": 101.0,
            "bb_upper": 108.0,
            "bb_lower": 96.0,
            "macd": 1.2,
            "adx": 45.0
        }
    }

@pytest.fixture
def sample_signal() -> Dict[str, Any]:
    """Sample trading signal for testing"""
    return {
        "signal_id": "test-signal-001",
        "symbol": "RELIANCE", 
        "timestamp": 1609459200.0,
        "signal_type": "BUY",
        "confidence": 0.85,
        "price": 103.0,
        "volume": 1000,
        "indicators": {
            "rsi": 65.5,
            "ema_20": 102.0,
            "bb_position": 0.7
        },
        "metadata": {
            "engine": "ENGINE_A",
            "strategy": "momentum"
        }
    }

@pytest.fixture
def sample_trade_request() -> Dict[str, Any]:
    """Sample trade request for testing"""
    return {
        "idempotency_key": "test-trade-001",
        "symbol": "RELIANCE",
        "order_type": "MARKET",
        "side": "BUY", 
        "quantity": 100,
        "account_id": "test_account",
        "strategy_id": "momentum_001"
    }

# Test data fixtures
@pytest.fixture
def historical_data_sample():
    """Sample historical data for backtesting"""
    import pandas as pd
    
    data = []
    base_price = 100.0
    for i in range(100):
        data.append({
            'timestamp': 1609459200.0 + i * 60,  # 1 minute intervals
            'open': base_price + (i % 10) * 0.5,
            'high': base_price + (i % 10) * 0.5 + 1.0,
            'low': base_price + (i % 10) * 0.5 - 1.0,
            'close': base_price + (i % 10) * 0.5 + 0.2,
            'volume': 1000 + (i % 50) * 100
        })
    
    return pd.DataFrame(data)

# Mock fixtures for external services
@pytest.fixture
def mock_dhan_api(monkeypatch):
    """Mock Dhan API responses"""
    class MockDhanAPI:
        def __init__(self):
            self.orders = []
            
        async def submit_order(self, order_data):
            order_id = f"MOCK_{len(self.orders) + 1:06d}"
            self.orders.append({
                "order_id": order_id,
                **order_data
            })
            return {
                "status": "success",
                "order_id": order_id,
                "message": "Order placed successfully"
            }
    
    mock_api = MockDhanAPI()
    return mock_api

@pytest.fixture
def mock_websocket_data():
    """Mock WebSocket market data stream"""
    def generate_tick_data(symbol="RELIANCE", count=10):
        import random
        import time
        
        base_price = 100.0
        for i in range(count):
            yield {
                "symbol": symbol,
                "timestamp": time.time(),
                "ltp": base_price + random.uniform(-2, 2),
                "volume": random.randint(100, 1000),
                "bid": base_price - 0.1,
                "ask": base_price + 0.1,
                "high": base_price + 5,
                "low": base_price - 5,
                "open": base_price
            }
    
    return generate_tick_data

# Performance testing fixtures
@pytest.fixture
def performance_test_config():
    """Configuration for performance tests"""
    return {
        "duration_seconds": 60,
        "messages_per_second": 100,
        "concurrent_connections": 10,
        "symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    }

# Integration test helpers
@pytest_asyncio.fixture
async def setup_test_database(postgres_pool):
    """Setup test database with schema"""
    async with postgres_pool.acquire() as conn:
        # Create test schema
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_trades (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                side VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10,2),
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        yield conn
        
        # Cleanup
        await conn.execute("DROP TABLE IF EXISTS test_trades")

# Utility functions for tests
def assert_metric_exists(metrics: Dict[str, Any], metric_name: str):
    """Assert that a metric exists in metrics collection"""
    assert metric_name in metrics or any(
        metric_name in str(key) for key in metrics.keys()
    ), f"Metric '{metric_name}' not found in metrics"

def assert_signal_valid(signal: Dict[str, Any]):
    """Assert that a trading signal has valid structure"""
    required_fields = ["symbol", "timestamp", "signal_type", "confidence", "price"]
    for field in required_fields:
        assert field in signal, f"Signal missing required field: {field}"
    
    assert 0 <= signal["confidence"] <= 1, "Signal confidence must be between 0 and 1"
    assert signal["price"] > 0, "Signal price must be positive"
    assert signal["signal_type"] in ["BUY", "SELL", "HOLD"], "Invalid signal type"