"""
Mock Market Data Manager for InfinityAI.Pro
Minimal implementation for testing backend functionality
"""
import asyncio
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataManager:
    def __init__(self):
        self.initialized = False
        self.symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK"]
        
    async def initialize(self):
        """Initialize market data manager"""
        logger.info("📊 Initializing Market Data Manager...")
        await asyncio.sleep(0.1)  # Simulate initialization
        self.initialized = True
        logger.info("✅ Market Data Manager initialized")
        
    async def get_real_time_quote(self, symbol: str):
        """Mock real-time quote data"""
        if not self.initialized:
            await self.initialize()
            
        # Generate mock data
        base_price = 1000 + random.randint(-500, 500)
        change = random.uniform(-5.0, 5.0)
        
        return {
            "symbol": symbol,
            "price": round(base_price + change, 2),
            "change": round(change, 2),
            "change_percent": round((change / base_price) * 100, 2),
            "volume": random.randint(10000, 1000000),
            "high": round(base_price + abs(change) + random.uniform(0, 10), 2),
            "low": round(base_price - abs(change) - random.uniform(0, 10), 2),
            "timestamp": datetime.now().isoformat(),
            "market_status": "OPEN" if 9 <= datetime.now().hour <= 15 else "CLOSED"
        }
        
    async def get_market_overview(self):
        """Mock market overview"""
        return {
            "market_status": "OPEN",
            "indices": {
                "NIFTY": await self.get_real_time_quote("NIFTY"),
                "BANKNIFTY": await self.get_real_time_quote("BANKNIFTY")
            },
            "top_gainers": [await self.get_real_time_quote(s) for s in self.symbols[:3]],
            "top_losers": [await self.get_real_time_quote(s) for s in self.symbols[3:]]
        }
        
    async def close(self):
        """Close market data manager"""
        logger.info("🛑 Closing Market Data Manager")
        self.initialized = False

# Global instance
market_data_manager = MarketDataManager()