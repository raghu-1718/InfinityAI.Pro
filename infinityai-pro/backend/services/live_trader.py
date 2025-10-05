"""
Mock Live Trader for InfinityAI.Pro
Minimal implementation for testing backend functionality
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

class LiveTrader:
    def __init__(self):
        self.initialized = False
        self.connected_brokers = []
        
    async def initialize_components(self):
        """Initialize trading components"""
        logger.info("💹 Initializing Live Trading Components...")
        await asyncio.sleep(0.1)  # Simulate initialization
        
        # Mock broker connections
        self.connected_brokers = ["dhan", "zerodha", "upstox"]
        self.initialized = True
        
        logger.info("✅ Live Trading Components initialized")
        logger.info(f"📡 Connected brokers: {', '.join(self.connected_brokers)}")
        
    async def place_order(self, order_data: dict):
        """Mock order placement"""
        if not self.initialized:
            await self.initialize_components()
            
        # Simulate order processing
        await asyncio.sleep(0.05)
        
        return {
            "status": "success",
            "order_id": f"ORD_{hash(str(order_data)) % 1000000:06d}",
            "symbol": order_data.get("symbol", "UNKNOWN"),
            "quantity": order_data.get("quantity", 0),
            "price": order_data.get("price", 0),
            "side": order_data.get("side", "BUY"),
            "order_type": order_data.get("order_type", "MARKET"),
            "timestamp": asyncio.get_event_loop().time(),
            "broker": "dhan"
        }
        
    async def get_positions(self):
        """Mock positions data"""
        return {
            "positions": [
                {
                    "symbol": "NIFTY",
                    "quantity": 50,
                    "avg_price": 19500.0,
                    "current_price": 19550.0,
                    "pnl": 2500.0,
                    "pnl_percent": 1.28
                },
                {
                    "symbol": "BANKNIFTY", 
                    "quantity": -25,
                    "avg_price": 44000.0,
                    "current_price": 43900.0,
                    "pnl": 2500.0,
                    "pnl_percent": 0.23
                }
            ],
            "total_pnl": 5000.0,
            "day_pnl": 1200.0
        }
        
    async def close(self):
        """Close live trader"""
        logger.info("🛑 Closing Live Trader")
        self.initialized = False
        self.connected_brokers = []

# Global instance
live_trader = LiveTrader()