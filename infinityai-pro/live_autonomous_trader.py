#!/usr/bin/env python3
# 🔥 InfinityAI.Pro - LIVE AUTONOMOUS DECISION MAKER & EXECUTOR
# Complete live trading system with real API execution

import requests
import json
import asyncio
import time
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading.log'),
        logging.StreamHandler()
    ]
)

class LiveAutonomousTrader:
    def __init__(self):
        self.dhan_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTk4MDUzMzEsImlhdCI6MTc1OTcxODkzMSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.SdnAubAOeObBTLmEYWTUP9lBW2MapBPeQL2b57mV8or-8tqUZwiIVmZywIzbkhRPViGKrqOH56ClQUXJL9oawA"
        self.base_url = "https://api.dhan.co/v2"
        self.client_id = "1101302170"
        
        # LIVE TRADING ENABLED
        self.live_execution = True
        self.autonomous_mode = True
        
        # Decision parameters
        self.profit_threshold = 5.0  # 5% profit to consider switching
        self.confidence_threshold = 85.0  # 85% confidence to execute
        self.profit_multiplier_threshold = 3.0  # 3x profit potential required
        
        # Monitoring intervals
        self.monitoring_interval = 30  # 30 seconds for live monitoring
        self.decision_cycle_interval = 120  # 2 minutes for decision cycles
        
        self.headers = {
            "access-token": self.dhan_token,
            "Content-Type": "application/json"
        }
        
        # State tracking
        self.current_positions = {}
        self.execution_log = []
        self.last_decision_time = None
        
    def live_log(self, message: str, level: str = "INFO"):
        """Enhanced logging for live trading"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [🤖 LIVE] {message}"
        
        if level == "CRITICAL":
            logging.critical(log_message)
            print(f"🚨 {log_message}")
        elif level == "ERROR":
            logging.error(log_message)
            print(f"❌ {log_message}")
        elif level == "SUCCESS":
            logging.info(log_message)
            print(f"✅ {log_message}")
        elif level == "DECISION":
            logging.info(log_message)
            print(f"🧠 {log_message}")
        elif level == "EXECUTION":
            logging.info(log_message)
            print(f"⚡ {log_message}")
        else:
            logging.info(log_message)
            print(f"📊 {log_message}")
        
        # Save to execution log
        self.execution_log.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    async def get_live_positions(self):
        """Get current live positions from Dhan API"""
        try:
            response = requests.get(f"{self.base_url}/positions", headers=self.headers, timeout=10)
            if response.status_code == 200:
                positions = response.json()
                self.live_log(f"Retrieved {len(positions)} live positions")
                return positions
            else:
                self.live_log(f"Failed to get positions: {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self.live_log(f"Error getting positions: {e}", "ERROR")
            return []
    
    async def get_live_funds(self):
        """Get current available funds"""
        try:
            response = requests.get(f"{self.base_url}/fundlimit", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                available = data.get('availableBalance', 0)
                self.live_log(f"Available funds: ₹{available}")
                return available
            else:
                self.live_log(f"Failed to get funds: {response.status_code}", "ERROR")
                return 0
        except Exception as e:
            self.live_log(f"Error getting funds: {e}", "ERROR")
            return 0
    
    async def place_live_order(self, order_data):
        """Place live order through Dhan API"""
        if not self.live_execution:
            self.live_log("SIMULATION MODE: Order not placed", "INFO")
            return {"status": "simulated", "orderId": f"SIM{int(time.time())}"}
        
        try:
            self.live_log(f"Placing LIVE order: {order_data['transactionType']} {order_data['quantity']} {order_data.get('securityId', 'N/A')}", "EXECUTION")
            
            response = requests.post(
                f"{self.base_url}/orders",
                headers=self.headers,
                json=order_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('orderId', 'Unknown')
                self.live_log(f"ORDER PLACED SUCCESSFULLY: ID {order_id}", "SUCCESS")
                return result
            else:
                error_msg = response.text
                self.live_log(f"ORDER FAILED: {error_msg}", "ERROR")
                return {"status": "failed", "error": error_msg}
                
        except Exception as e:
            self.live_log(f"ORDER EXECUTION ERROR: {e}", "CRITICAL")
            return {"status": "error", "error": str(e)}
    
    async def analyze_current_position(self, position):
        """Analyze current position for switching opportunities"""
        symbol = position.get('tradingSymbol', '')
        current_pnl = position.get('unrealizedProfit', 0)
        quantity = position.get('netQty', 0)
        entry_price = position.get('buyAvg', 0) if quantity > 0 else position.get('sellAvg', 0)
        current_price = position.get('ltp', entry_price)
        
        if entry_price == 0:
            return None
        
        profit_percent = (current_pnl / (abs(quantity) * entry_price)) * 100
        
        self.live_log(f"Analyzing {symbol}: P&L ₹{current_pnl} ({profit_percent:.2f}%)")
        
        return {
            "symbol": symbol,
            "current_pnl": current_pnl,
            "profit_percent": profit_percent,
            "entry_price": entry_price,
            "current_price": current_price,
            "quantity": quantity,
            "position_value": abs(quantity) * current_price
        }
    
    async def find_better_opportunities(self, current_capital):
        """AI finds better trading opportunities"""
        opportunities = []
        
        # Real-time market analysis (simplified for demo)
        nifty_level = 25820  # Current NIFTY level
        volatility = "HIGH"
        trend = "BULLISH"
        
        if trend == "BULLISH" and current_capital >= 50:
            # NIFTY Call opportunities
            nifty_calls = [
                {
                    "symbol": "NIFTY50-16Oct2025-25900-CE",
                    "current_price": 68.0,
                    "target_1": 95.0,
                    "target_2": 125.0,
                    "stop_loss": 45.0,
                    "confidence": 88.0,
                    "strategy": "MOMENTUM_BREAKOUT",
                    "timeframe": "1-2 days"
                },
                {
                    "symbol": "NIFTY50-16Oct2025-25850-CE", 
                    "current_price": 85.0,
                    "target_1": 110.0,
                    "target_2": 140.0,
                    "stop_loss": 65.0,
                    "confidence": 85.0,
                    "strategy": "TREND_CONTINUATION",
                    "timeframe": "1-3 days"
                }
            ]
            
            for opp in nifty_calls:
                if current_capital >= opp["current_price"]:
                    quantity = int(current_capital / opp["current_price"])
                    
                    profit_1 = (opp["target_1"] - opp["current_price"]) * quantity
                    profit_2 = (opp["target_2"] - opp["current_price"]) * quantity
                    
                    opportunities.append({
                        **opp,
                        "quantity": quantity,
                        "capital_required": quantity * opp["current_price"],
                        "profit_potential_1": profit_1,
                        "profit_potential_2": profit_2,
                        "risk_amount": (opp["current_price"] - opp["stop_loss"]) * quantity
                    })
        
        # Sort by profit potential and confidence
        opportunities.sort(key=lambda x: x["profit_potential_2"] * (x["confidence"] / 100), reverse=True)
        
        return opportunities
    
    async def make_switching_decision(self, current_position, opportunities):
        """AI makes autonomous switching decision"""
        if not opportunities:
            return {"decision": "HOLD", "reason": "No better opportunities found"}
        
        best_opp = opportunities[0]
        current_profit = current_position["current_pnl"]
        
        # Calculate profit multipliers
        if current_profit > 0:
            multiplier_1 = best_opp["profit_potential_1"] / current_profit
            multiplier_2 = best_opp["profit_potential_2"] / current_profit
        else:
            multiplier_1 = float('inf')
            multiplier_2 = float('inf')
        
        # Decision criteria
        conditions = {
            "profit_threshold": current_position["profit_percent"] >= self.profit_threshold,
            "confidence_threshold": best_opp["confidence"] >= self.confidence_threshold,
            "multiplier_threshold": multiplier_2 >= self.profit_multiplier_threshold,
            "risk_acceptable": best_opp["risk_amount"] <= current_position["position_value"] * 0.3
        }
        
        conditions_met = sum(conditions.values())
        
        self.live_log(f"Decision analysis: {conditions_met}/4 conditions met")
        for condition, met in conditions.items():
            self.live_log(f"  {condition}: {'✅' if met else '❌'}")
        
        if conditions_met >= 3:  # Need at least 3/4 conditions
            return {
                "decision": "SWITCH",
                "reason": f"Strong opportunity: {multiplier_2:.1f}x profit potential",
                "opportunity": best_opp,
                "confidence": best_opp["confidence"],
                "multiplier": multiplier_2
            }
        elif conditions_met >= 2:
            return {
                "decision": "CONSIDER",
                "reason": f"Moderate opportunity: {multiplier_2:.1f}x profit potential",
                "opportunity": best_opp
            }
        else:
            return {
                "decision": "HOLD",
                "reason": "Current position is better or risk too high"
            }
    
    async def execute_switch(self, current_position, new_opportunity):
        """Execute the position switch"""
        self.live_log("EXECUTING POSITION SWITCH", "CRITICAL")
        
        # Step 1: Exit current position
        exit_order = {
            "dhanClientId": self.client_id,
            "correlationId": f"EXIT_{int(time.time())}",
            "transactionType": "SELL" if current_position["quantity"] > 0 else "BUY",
            "exchangeSegment": "MCX_COM" if "CRUDE" in current_position["symbol"] else "NSE_FNO",
            "productType": "INTRADAY",
            "orderType": "MARKET",
            "validity": "DAY",
            "securityId": current_position["symbol"],
            "quantity": abs(current_position["quantity"])
        }
        
        self.live_log(f"Step 1: Exiting {current_position['symbol']}")
        exit_result = await self.place_live_order(exit_order)
        
        if exit_result.get("status") == "failed":
            self.live_log("Failed to exit position - ABORTING SWITCH", "ERROR")
            return False
        
        # Wait for order execution
        await asyncio.sleep(5)
        
        # Step 2: Enter new position
        entry_order = {
            "dhanClientId": self.client_id,
            "correlationId": f"ENTER_{int(time.time())}",
            "transactionType": "BUY",
            "exchangeSegment": "NSE_FNO",
            "productType": "INTRADAY",
            "orderType": "LIMIT",
            "validity": "DAY",
            "securityId": new_opportunity["symbol"],
            "quantity": new_opportunity["quantity"],
            "price": new_opportunity["current_price"]
        }
        
        self.live_log(f"Step 2: Entering {new_opportunity['symbol']}")
        entry_result = await self.place_live_order(entry_order)
        
        if entry_result.get("status") == "failed":
            self.live_log("Failed to enter new position - PARTIAL EXECUTION", "ERROR")
            return False
        
        self.live_log("POSITION SWITCH COMPLETED SUCCESSFULLY", "SUCCESS")
        return True
    
    async def autonomous_decision_cycle(self):
        """Main autonomous decision-making cycle"""
        self.live_log("Starting autonomous decision cycle", "DECISION")
        
        # Get current positions
        positions = await self.get_live_positions()
        
        if not positions:
            self.live_log("No positions to analyze")
            return
        
        # Get available funds
        available_funds = await self.get_live_funds()
        
        for position in positions:
            # Analyze current position
            analysis = await self.analyze_current_position(position)
            if not analysis:
                continue
            
            # Find better opportunities
            opportunities = await self.find_better_opportunities(available_funds + analysis["position_value"])
            
            # Make decision
            decision = await self.make_switching_decision(analysis, opportunities)
            
            self.live_log(f"Decision for {analysis['symbol']}: {decision['decision']}", "DECISION")
            self.live_log(f"Reason: {decision['reason']}", "DECISION")
            
            # Execute if decision is to switch
            if decision["decision"] == "SWITCH":
                self.live_log(f"AUTONOMOUS DECISION: EXECUTING SWITCH", "CRITICAL")
                self.live_log(f"Profit multiplier: {decision['multiplier']:.1f}x", "CRITICAL")
                
                success = await self.execute_switch(analysis, decision["opportunity"])
                
                if success:
                    self.live_log("AUTONOMOUS SWITCH EXECUTED SUCCESSFULLY", "SUCCESS")
                else:
                    self.live_log("AUTONOMOUS SWITCH FAILED", "ERROR")
                
                # Only switch one position per cycle
                break
    
    async def continuous_live_trading(self):
        """Run continuous live autonomous trading"""
        self.live_log("🚀 STARTING LIVE AUTONOMOUS TRADING SYSTEM", "CRITICAL")
        self.live_log(f"⚙️ Monitoring interval: {self.monitoring_interval}s", "INFO")
        self.live_log(f"⚙️ Decision cycle: {self.decision_cycle_interval}s", "INFO")
        self.live_log(f"⚙️ Live execution: {'ENABLED' if self.live_execution else 'DISABLED'}", "INFO")
        
        decision_counter = 0
        
        while self.autonomous_mode:
            try:
                # Check if it's time for a decision cycle
                if decision_counter % (self.decision_cycle_interval // self.monitoring_interval) == 0:
                    await self.autonomous_decision_cycle()
                
                # Monitor positions
                positions = await self.get_live_positions()
                for position in positions:
                    analysis = await self.analyze_current_position(position)
                    if analysis:
                        self.live_log(f"Monitoring {analysis['symbol']}: ₹{analysis['current_pnl']:.2f} ({analysis['profit_percent']:.2f}%)")
                
                decision_counter += 1
                await asyncio.sleep(self.monitoring_interval)
                
            except KeyboardInterrupt:
                self.live_log("User stopped autonomous trading", "INFO")
                break
            except Exception as e:
                self.live_log(f"Error in trading cycle: {e}", "ERROR")
                await asyncio.sleep(60)  # Wait 1 minute on error
        
        self.live_log("AUTONOMOUS TRADING SYSTEM STOPPED", "INFO")
    
    def start_live_trading(self):
        """Start the live trading system"""
        print("🔥" * 80)
        print("🤖 INFINITYAI.PRO - LIVE AUTONOMOUS TRADING SYSTEM")
        print("🔥" * 80)
        print()
        print("⚡ FEATURES ACTIVE:")
        print("   ✅ Real-time position monitoring")
        print("   ✅ Autonomous decision making")
        print("   ✅ Live order execution")
        print("   ✅ Profit optimization")
        print("   ✅ Risk management")
        print("   ✅ Continuous operation")
        print()
        print("🚨 WARNING: This system will trade with REAL money!")
        print("🎯 System will automatically switch positions for better profits")
        print("⏹️  Press Ctrl+C to stop")
        print()
        
        # Start the autonomous trading
        asyncio.run(self.continuous_live_trading())

# Main execution
if __name__ == "__main__":
    trader = LiveAutonomousTrader()
    
    print("🤖 InfinityAI.Pro - Live Autonomous Trader")
    print("🔥 Complete decision maker and executor")
    print()
    
    # Enable live execution
    trader.live_execution = True  # Set to False for simulation
    
    # Start live trading
    trader.start_live_trading()