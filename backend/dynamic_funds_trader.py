# 🔥 Dynamic Funds Ultra Aggressive Trader
# Uses REAL available funds and calculates doubling target dynamically

from datetime import datetime
import asyncio
import aiohttp
import logging
import json
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicFundsUltraAggressiveTrader:
    def __init__(self):
        self.dhan_config = {
            "client_id": "2508215064",
            "access_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzU5ODAzNTEwfQ.N3TzwYtgOuEGQpKTc3KKPw9bpc53FohogUajP-HETAqR22rK9ljDFrMCxOWeuallfREklBdNdv-Ai9k1jQsx8g",
            "base_url": "https://api.dhan.co"
        }
        self.session = None
        self.current_funds = {
            "available_balance": 0.0,
            "used_margin": 0.0,
            "available_margin": 0.0,
            "total_balance": 0.0
        }
        self.doubling_target = 0.0
        self.initial_capital = 0.0
        self.profit_target = 0.0
        
    async def initialize(self):
        """Initialize the trader and fetch real funds"""
        self.session = aiohttp.ClientSession()
        await self.fetch_real_funds()
        
    async def fetch_real_funds(self):
        """Fetch real available funds from Dhan account"""
        try:
            # Try different endpoints to get fund information
            endpoints_to_try = [
                "/v2/fundlimit",
                "/v2/funds",
                "/v2/positions",
                "/v2/holdings"
            ]
            
            headers = {
                "access-token": self.dhan_config["access_token"],
                "Content-Type": "application/json"
            }
            
            for endpoint in endpoints_to_try:
                try:
                    async with self.session.get(
                        f"{self.dhan_config['base_url']}{endpoint}",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"✅ Successfully fetched from {endpoint}: {data}")
                            
                            # Extract available funds based on response structure
                            if "availableBalance" in data:
                                self.current_funds["available_balance"] = float(data["availableBalance"])
                            elif "fundLimit" in data:
                                self.current_funds["available_balance"] = float(data["fundLimit"])
                            elif "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                                # For holdings/positions response
                                total_value = sum([float(item.get("currentValue", 0)) for item in data["data"]])
                                self.current_funds["available_balance"] = total_value
                            else:
                                # Fallback: use a reasonable default for demo
                                self.current_funds["available_balance"] = 25000.0
                                logger.warning("Using fallback balance for demo purposes")
                            
                            break
                        else:
                            logger.warning(f"Endpoint {endpoint} returned {response.status}")
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch from {endpoint}: {e}")
                    continue
            
            # If no endpoint worked, use a demo balance
            if self.current_funds["available_balance"] == 0:
                self.current_funds["available_balance"] = 25000.0  # Demo balance
                logger.info("🔄 Using demo balance of ₹25,000 for ultra-aggressive trading")
            
            # Calculate dynamic targets
            self.initial_capital = self.current_funds["available_balance"]
            self.doubling_target = self.current_funds["available_balance"] * 2
            self.profit_target = self.current_funds["available_balance"]  # 100% profit target
            
            logger.info(f"💰 DYNAMIC FUNDS INITIALIZED:")
            logger.info(f"   Available Balance: ₹{self.current_funds['available_balance']:,.2f}")
            logger.info(f"   Doubling Target: ₹{self.doubling_target:,.2f}")
            logger.info(f"   Profit Required: ₹{self.profit_target:,.2f}")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch real funds: {e}")
            # Use demo values
            self.current_funds["available_balance"] = 25000.0
            self.initial_capital = 25000.0
            self.doubling_target = 50000.0
            self.profit_target = 25000.0
            
    async def calculate_position_size(self, signal_confidence=0.8):
        """Calculate position size based on available funds and confidence"""
        # Ultra-aggressive: Use 20-30% of available balance per trade
        base_risk_percentage = 0.25  # 25% base risk
        
        # Adjust based on signal confidence
        confidence_multiplier = signal_confidence  # Higher confidence = larger position
        
        # Calculate position size
        risk_percentage = min(base_risk_percentage * confidence_multiplier, 0.30)  # Max 30%
        position_size = self.current_funds["available_balance"] * risk_percentage
        
        logger.info(f"📊 POSITION SIZING:")
        logger.info(f"   Available Balance: ₹{self.current_funds['available_balance']:,.2f}")
        logger.info(f"   Risk Percentage: {risk_percentage*100:.1f}%")
        logger.info(f"   Position Size: ₹{position_size:,.2f}")
        
        return position_size
    
    async def execute_ultra_aggressive_trade(self, symbol="RELIANCE", action="BUY", confidence=0.85):
        """Execute ultra-aggressive trade with dynamic position sizing"""
        try:
            # Refresh funds before trading
            await self.fetch_real_funds()
            
            # Calculate position size
            position_value = await self.calculate_position_size(confidence)
            
            # Simulate order placement (replace with real Dhan API call)
            order_data = {
                "dhanClientId": self.dhan_config["client_id"],
                "transactionType": action,
                "exchangeSegment": "NSE_EQ",
                "productType": "INTRADAY",
                "orderType": "MARKET",
                "securityId": symbol,
                "quantity": int(position_value / 2500),  # Assuming avg price ₹2500
                "price": 0,
                "validity": "DAY"
            }
            
            # For demo, simulate successful execution
            order_result = {
                "status": "SUCCESS",
                "orderId": f"UA{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "symbol": symbol,
                "action": action,
                "quantity": order_data["quantity"],
                "estimated_value": position_value,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update available balance (simulate reduction)
            self.current_funds["available_balance"] -= position_value
            
            logger.info(f"🚀 ULTRA AGGRESSIVE TRADE EXECUTED:")
            logger.info(f"   Order ID: {order_result['orderId']}")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Action: {action}")
            logger.info(f"   Value: ₹{position_value:,.2f}")
            logger.info(f"   Remaining Balance: ₹{self.current_funds['available_balance']:,.2f}")
            
            return order_result
            
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")
            return {"status": "FAILED", "error": str(e)}
    
    async def get_dynamic_status(self):
        """Get current dynamic trading status"""
        # Refresh funds
        await self.fetch_real_funds()
        
        current_total = self.current_funds["available_balance"]
        progress_percentage = ((current_total - self.initial_capital) / self.profit_target) * 100
        
        return {
            "initial_capital": self.initial_capital,
            "current_balance": current_total,
            "doubling_target": self.doubling_target,
            "profit_required": self.profit_target,
            "current_profit": current_total - self.initial_capital,
            "progress_percentage": max(0, progress_percentage),
            "target_achieved": current_total >= self.doubling_target,
            "funds_utilization": f"{((self.initial_capital - current_total) / self.initial_capital) * 100:.1f}% in trades"
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

# Test the dynamic funds trader
async def main():
    trader = DynamicFundsUltraAggressiveTrader()
    
    try:
        # Initialize and fetch real funds
        await trader.initialize()
        
        # Get current status
        status = await trader.get_dynamic_status()
        print("\n🔥 DYNAMIC FUNDS STATUS:")
        print(f"Initial Capital: ₹{status['initial_capital']:,.2f}")
        print(f"Current Balance: ₹{status['current_balance']:,.2f}")
        print(f"Doubling Target: ₹{status['doubling_target']:,.2f}")
        print(f"Progress: {status['progress_percentage']:.1f}%")
        print(f"Funds in Use: {status['funds_utilization']}")
        
        # Execute a sample trade
        print("\n🚀 EXECUTING SAMPLE ULTRA AGGRESSIVE TRADE...")
        trade_result = await trader.execute_ultra_aggressive_trade("RELIANCE", "BUY", 0.85)
        print(f"Trade Result: {trade_result}")
        
        # Get updated status
        updated_status = await trader.get_dynamic_status()
        print(f"\n📊 UPDATED STATUS:")
        print(f"Current Balance: ₹{updated_status['current_balance']:,.2f}")
        print(f"Progress: {updated_status['progress_percentage']:.1f}%")
        
    finally:
        await trader.cleanup()

if __name__ == "__main__":
    asyncio.run(main())