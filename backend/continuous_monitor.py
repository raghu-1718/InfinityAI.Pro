# 🔄 InfinityAI.Pro - Continuous Monitoring & Auto-Trading System

import asyncio
import requests
import json
from datetime import datetime, timedelta
import time

class ContinuousMonitoringSystem:
    def __init__(self):
        self.dhan_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTk4MDUzMzEsImlhdCI6MTc1OTcxODkzMSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.SdnAubAOeObBTLmEYWTUP9lBW2MapBPeQL2b57mV8or-8tqUZwiIVmZywIzbkhRPViGKrqOH56ClQUXJL9oawA"
        self.base_url = "https://api.dhan.co/v2"
        self.monitoring_interval = 300  # 5 minutes
        self.auto_trade_enabled = True
        self.risk_threshold = 100  # Max loss threshold
        
    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def get_current_positions(self):
        try:
            headers = {
                "access-token": self.dhan_token,
                "Content-Type": "application/json"
            }
            response = requests.get(f"{self.base_url}/positions", headers=headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.log_message(f"Error fetching positions: {e}", "ERROR")
            return []
    
    async def analyze_position_risk(self, position):
        """Advanced risk analysis for each position"""
        symbol = position.get('tradingSymbol', '')
        current_pnl = float(position.get('unrealizedProfit', 0))
        quantity = int(position.get('netQty', 0))
        buy_avg = float(position.get('buyAvg', 0))
        
        # Calculate position value
        position_value = buy_avg * quantity * position.get('multiplier', 1)
        
        # Risk assessment
        risk_level = "LOW"
        if abs(current_pnl) > 50:
            risk_level = "MEDIUM"
        if abs(current_pnl) > self.risk_threshold:
            risk_level = "HIGH"
        
        # Time-based analysis
        expiry_date = position.get('drvExpiryDate')
        if expiry_date:
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            days_to_expiry = (expiry - datetime.now().date()).days
            
            if days_to_expiry <= 2:
                risk_level = "CRITICAL"
        
        return {
            "symbol": symbol,
            "current_pnl": current_pnl,
            "position_value": position_value,
            "risk_level": risk_level,
            "days_to_expiry": days_to_expiry if expiry_date else "N/A",
            "action_required": self.determine_action(current_pnl, risk_level, days_to_expiry if expiry_date else 10)
        }
    
    def determine_action(self, pnl, risk_level, days_to_expiry):
        """AI-based action determination"""
        if risk_level == "CRITICAL" and pnl < -50:
            return "IMMEDIATE_EXIT"
        elif risk_level == "HIGH" and pnl < -self.risk_threshold:
            return "CONSIDER_EXIT"
        elif pnl > 50 and days_to_expiry < 5:
            return "BOOK_PROFITS"
        elif pnl > 30:
            return "PARTIAL_PROFIT_BOOKING"
        else:
            return "MONITOR"
    
    async def execute_auto_trade(self, action, position):
        """Simulate automatic trade execution"""
        if not self.auto_trade_enabled:
            return {"status": "disabled", "message": "Auto-trading disabled"}
        
        symbol = position.get('tradingSymbol', '')
        quantity = position.get('netQty', 0)
        
        if action == "IMMEDIATE_EXIT":
            self.log_message(f"🚨 CRITICAL: Executing immediate exit for {symbol}", "CRITICAL")
            # In production: Place sell order for full quantity
            return {"status": "executed", "action": f"Sold {quantity} of {symbol}"}
        
        elif action == "PARTIAL_PROFIT_BOOKING":
            partial_qty = max(1, quantity // 2)
            self.log_message(f"💰 PROFIT: Booking partial profits for {symbol}", "SUCCESS")
            # In production: Place sell order for partial quantity
            return {"status": "executed", "action": f"Sold {partial_qty} of {symbol}"}
        
        elif action == "BOOK_PROFITS":
            self.log_message(f"🎯 PROFITS: Full profit booking for {symbol}", "SUCCESS")
            # In production: Place sell order for full quantity
            return {"status": "executed", "action": f"Sold {quantity} of {symbol}"}
        
        return {"status": "monitoring", "action": "Continue monitoring"}
    
    async def get_market_sentiment(self):
        """Get overall market sentiment"""
        # Simulated market sentiment analysis
        # In production, this would fetch real market data
        return {
            "nifty_sentiment": "BULLISH",
            "bank_nifty_sentiment": "NEUTRAL", 
            "vix_level": "MEDIUM",
            "fii_activity": "BUYING",
            "global_markets": "POSITIVE",
            "recommendation": "CAUTIOUS_OPTIMISM"
        }
    
    async def monitor_and_trade(self):
        """Main monitoring loop"""
        self.log_message("🚀 Starting continuous monitoring system", "INFO")
        
        while True:
            try:
                self.log_message("🔍 Running position analysis...", "INFO")
                
                # Get current positions
                positions = await self.get_current_positions()
                
                if not positions:
                    self.log_message("📝 No active positions to monitor", "INFO")
                else:
                    self.log_message(f"📊 Monitoring {len(positions)} positions", "INFO")
                    
                    for position in positions:
                        analysis = await self.analyze_position_risk(position)
                        
                        self.log_message(f"Position: {analysis['symbol']}", "INFO")
                        self.log_message(f"  P&L: ₹{analysis['current_pnl']}", "INFO")
                        self.log_message(f"  Risk: {analysis['risk_level']}", "INFO")
                        self.log_message(f"  Action: {analysis['action_required']}", "INFO")
                        
                        # Execute automatic trades if required
                        if analysis['action_required'] in ['IMMEDIATE_EXIT', 'BOOK_PROFITS', 'PARTIAL_PROFIT_BOOKING']:
                            result = await self.execute_auto_trade(analysis['action_required'], position)
                            self.log_message(f"🤖 Auto-trade result: {result}", "SUCCESS")
                
                # Get market sentiment
                sentiment = await self.get_market_sentiment()
                self.log_message(f"🌐 Market sentiment: {sentiment['recommendation']}", "INFO")
                
                # Wait for next iteration
                self.log_message(f"😴 Sleeping for {self.monitoring_interval} seconds...", "INFO")
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.log_message(f"❌ Error in monitoring loop: {e}", "ERROR")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def run_single_analysis(self):
        """Run a single analysis cycle"""
        self.log_message("🎯 Running single analysis cycle", "INFO")
        
        positions = await self.get_current_positions()
        
        if positions:
            for position in positions:
                analysis = await self.analyze_position_risk(position)
                
                print(f"\n📊 POSITION ANALYSIS:")
                print(f"Symbol: {analysis['symbol']}")
                print(f"Current P&L: ₹{analysis['current_pnl']}")
                print(f"Position Value: ₹{analysis['position_value']:.2f}")
                print(f"Risk Level: {analysis['risk_level']}")
                print(f"Days to Expiry: {analysis['days_to_expiry']}")
                print(f"Recommended Action: {analysis['action_required']}")
                
                if analysis['action_required'] != "MONITOR":
                    print(f"🚨 ACTION REQUIRED: {analysis['action_required']}")
        
        sentiment = await self.get_market_sentiment()
        print(f"\n🌐 MARKET SENTIMENT:")
        print(f"NIFTY: {sentiment['nifty_sentiment']}")
        print(f"Bank NIFTY: {sentiment['bank_nifty_sentiment']}")
        print(f"VIX: {sentiment['vix_level']}")
        print(f"Overall: {sentiment['recommendation']}")

# Configuration for different modes
if __name__ == "__main__":
    import sys
    
    monitor = ContinuousMonitoringSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        # Run continuous monitoring
        print("🔄 Starting continuous monitoring mode...")
        asyncio.run(monitor.monitor_and_trade())
    else:
        # Run single analysis
        print("📊 Running single analysis...")
        asyncio.run(monitor.run_single_analysis())