#!/usr/bin/env python3
# 🔥 InfinityAI.Pro - REAL Trading Execution System
# Updated with actual position: ₹130 price, ₹6.20 profit

import requests
import json
import asyncio
from datetime import datetime

class RealTradeExecutor:
    def __init__(self):
        self.dhan_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTk4MDUzMzEsImlhdCI6MTc1OTcxODkzMSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.SdnAubAOeObBTLmEYWTUP9lBW2MapBPeQL2b57mV8or-8tqUZwiIVmZywIzbkhRPViGKrqOH56ClQUXJL9oawA"
        self.base_url = "https://api.dhan.co/v2"
        self.client_id = "1101302170"
        
        # ACTUAL POSITION DATA
        self.crude_entry = 123.70
        self.crude_current = 130.00
        self.crude_profit = 6.20  # Actual current profit
        
        self.headers = {
            "access-token": self.dhan_token,
            "Content-Type": "application/json"
        }
    
    def log(self, message: str, level: str = "REAL"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [🔥 {level}] {message}")
    
    async def analyze_real_opportunity(self):
        """Analyze the REAL opportunity with current profit levels"""
        
        print("\n" + "🔥" * 60)
        print("REAL TRADING ANALYSIS - UPDATED POSITION")
        print("🔥" * 60)
        
        print(f"\n📊 CURRENT CRUDE OIL POSITION:")
        print(f"Entry Price: ₹{self.crude_entry}")
        print(f"Current Price: ₹{self.crude_current}")
        print(f"Current Profit: ₹{self.crude_profit}")
        print(f"Profit %: {((self.crude_current - self.crude_entry) / self.crude_entry * 100):.2f}%")
        
        # Updated NIFTY opportunity analysis
        nifty_opportunities = {
            "NIFTY_MOMENTUM": {
                "symbol": "NIFTY50-16Oct2025-25900-CE",
                "current_price": 68.0,  # Updated market price
                "entry_target": 70.0,
                "target_1": 95.0,
                "target_2": 125.0,
                "stop_loss": 50.0,
                "confidence": 87.0
            },
            "NIFTY_BREAKOUT": {
                "symbol": "NIFTY50-16Oct2025-25850-CE", 
                "current_price": 88.0,
                "entry_target": 90.0,
                "target_1": 115.0,
                "target_2": 140.0,
                "stop_loss": 70.0,
                "confidence": 85.0
            }
        }
        
        print(f"\n🎯 NIFTY OPPORTUNITIES:")
        
        best_opportunity = None
        best_multiplier = 0
        
        for name, opp in nifty_opportunities.items():
            # Calculate potential with crude oil exit capital
            available_capital = self.crude_current  # ₹130 after exit
            quantity = int(available_capital / opp["entry_target"])
            
            profit_1 = (opp["target_1"] - opp["entry_target"]) * quantity
            profit_2 = (opp["target_2"] - opp["entry_target"]) * quantity
            
            multiplier_1 = profit_1 / self.crude_profit
            multiplier_2 = profit_2 / self.crude_profit
            
            print(f"\n{name}:")
            print(f"  Symbol: {opp['symbol']}")
            print(f"  Entry: ₹{opp['entry_target']}")
            print(f"  Quantity: {quantity} lots")
            print(f"  Target 1: ₹{opp['target_1']} → Profit: ₹{profit_1:.2f} ({multiplier_1:.1f}x current)")
            print(f"  Target 2: ₹{opp['target_2']} → Profit: ₹{profit_2:.2f} ({multiplier_2:.1f}x current)")
            print(f"  Stop Loss: ₹{opp['stop_loss']}")
            print(f"  Confidence: {opp['confidence']:.1f}%")
            
            if multiplier_2 > best_multiplier:
                best_multiplier = multiplier_2
                best_opportunity = {
                    "name": name,
                    "data": opp,
                    "quantity": quantity,
                    "profit_1": profit_1,
                    "profit_2": profit_2,
                    "multiplier_1": multiplier_1,
                    "multiplier_2": multiplier_2
                }
        
        return best_opportunity
    
    async def generate_execution_plan(self, opportunity):
        """Generate real execution plan"""
        
        print(f"\n🚀 RECOMMENDED EXECUTION PLAN:")
        print("=" * 50)
        
        print(f"🎯 BEST OPPORTUNITY: {opportunity['name']}")
        print(f"📊 Profit Multiplier: {opportunity['multiplier_2']:.1f}x")
        
        print(f"\n📋 EXECUTION STEPS:")
        print(f"1. EXIT CRUDE: Sell CRUDEOIL-16Oct2025-5500-CE @ ₹{self.crude_current}")
        print(f"   → Lock profit: ₹{self.crude_profit}")
        print(f"   → Receive capital: ₹{self.crude_current}")
        
        print(f"\n2. ENTER NIFTY: Buy {opportunity['data']['symbol']}")
        print(f"   → Entry price: ₹{opportunity['data']['entry_target']}")
        print(f"   → Quantity: {opportunity['quantity']} lots")
        print(f"   → Capital used: ₹{opportunity['quantity'] * opportunity['data']['entry_target']}")
        
        print(f"\n3. PROFIT TARGETS:")
        print(f"   → Target 1: ₹{opportunity['data']['target_1']} (Profit: ₹{opportunity['profit_1']:.2f})")
        print(f"   → Target 2: ₹{opportunity['data']['target_2']} (Profit: ₹{opportunity['profit_2']:.2f})")
        
        print(f"\n4. RISK MANAGEMENT:")
        print(f"   → Stop Loss: ₹{opportunity['data']['stop_loss']}")
        print(f"   → Max Risk: ₹{(opportunity['data']['entry_target'] - opportunity['data']['stop_loss']) * opportunity['quantity']:.2f}")
        
        print(f"\n💰 PROFIT COMPARISON:")
        print(f"Current Crude Profit: ₹{self.crude_profit}")
        print(f"NIFTY Target 1 Profit: ₹{opportunity['profit_1']:.2f} ({opportunity['multiplier_1']:.1f}x)")
        print(f"NIFTY Target 2 Profit: ₹{opportunity['profit_2']:.2f} ({opportunity['multiplier_2']:.1f}x)")
        
        confidence_score = opportunity['data']['confidence']
        if confidence_score >= 85:
            recommendation = "STRONG EXECUTE"
            color = "🟢"
        elif confidence_score >= 80:
            recommendation = "EXECUTE"
            color = "🟡"
        else:
            recommendation = "CONSIDER"
            color = "🟠"
        
        print(f"\n{color} AI RECOMMENDATION: {recommendation}")
        print(f"📊 Confidence: {confidence_score:.1f}%")
        
        return opportunity
    
    async def create_real_orders(self, opportunity, execute_real=False):
        """Create actual order commands"""
        
        print(f"\n🔥 REAL ORDER GENERATION:")
        print("=" * 40)
        
        # Order 1: Exit Crude Oil
        crude_exit_order = {
            "dhanClientId": self.client_id,
            "correlationId": f"EXIT_CRUDE_{int(datetime.now().timestamp())}",
            "transactionType": "SELL",
            "exchangeSegment": "MCX_COM",
            "productType": "INTRADAY",
            "orderType": "MARKET",
            "validity": "DAY",
            "securityId": "CRUDEOIL-16Oct2025-5500-CE",
            "quantity": 1,
        }
        
        # Order 2: Enter NIFTY
        nifty_entry_order = {
            "dhanClientId": self.client_id,
            "correlationId": f"ENTER_NIFTY_{int(datetime.now().timestamp())}",
            "transactionType": "BUY",
            "exchangeSegment": "NSE_FNO", 
            "productType": "INTRADAY",
            "orderType": "LIMIT",
            "validity": "DAY",
            "securityId": opportunity['data']['symbol'],
            "quantity": opportunity['quantity'],
            "price": opportunity['data']['entry_target']
        }
        
        print("📋 GENERATED ORDERS:")
        print(f"\n1. CRUDE EXIT ORDER:")
        print(f"   Symbol: CRUDEOIL-16Oct2025-5500-CE")
        print(f"   Type: MARKET SELL")
        print(f"   Quantity: 1")
        print(f"   Expected Price: ~₹{self.crude_current}")
        
        print(f"\n2. NIFTY ENTRY ORDER:")
        print(f"   Symbol: {opportunity['data']['symbol']}")
        print(f"   Type: LIMIT BUY")
        print(f"   Quantity: {opportunity['quantity']}")
        print(f"   Price: ₹{opportunity['data']['entry_target']}")
        
        if execute_real:
            self.log("🚨 EXECUTING REAL ORDERS...", "LIVE")
            
            try:
                # Execute crude exit
                response1 = requests.post(f"{self.base_url}/orders", 
                                        headers=self.headers, 
                                        json=crude_exit_order)
                
                if response1.status_code == 200:
                    self.log("✅ CRUDE EXIT ORDER PLACED", "SUCCESS")
                    print(f"Order Response: {response1.json()}")
                    
                    # Wait a moment then execute NIFTY entry
                    await asyncio.sleep(3)
                    
                    response2 = requests.post(f"{self.base_url}/orders",
                                            headers=self.headers,
                                            json=nifty_entry_order)
                    
                    if response2.status_code == 200:
                        self.log("✅ NIFTY ENTRY ORDER PLACED", "SUCCESS")
                        print(f"Order Response: {response2.json()}")
                        return True
                    else:
                        self.log(f"❌ NIFTY ORDER FAILED: {response2.text}", "ERROR")
                else:
                    self.log(f"❌ CRUDE EXIT FAILED: {response1.text}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ ORDER EXECUTION ERROR: {e}", "ERROR")
                
        return False
    
    async def run_real_analysis(self, execute_orders=False):
        """Run complete real analysis"""
        
        self.log("🔥 STARTING REAL TRADING ANALYSIS", "SYSTEM")
        
        # Analyze opportunities
        best_opportunity = await self.analyze_real_opportunity()
        
        if best_opportunity:
            # Generate execution plan
            plan = await self.generate_execution_plan(best_opportunity)
            
            # Show order generation
            await self.create_real_orders(plan, execute_real=execute_orders)
            
            print(f"\n🎯 FINAL DECISION:")
            if best_opportunity['multiplier_2'] >= 5.0 and best_opportunity['data']['confidence'] >= 85:
                print(f"🚀 STRONG RECOMMENDATION: EXECUTE SWITCH")
                print(f"💰 Potential: {best_opportunity['multiplier_2']:.1f}x profit multiplication")
            elif best_opportunity['multiplier_2'] >= 3.0:
                print(f"🤔 MODERATE RECOMMENDATION: Consider switch")
            else:
                print(f"✋ HOLD CRUDE: Current opportunity not compelling enough")
            
            return best_opportunity
        
        return None

# Main execution
async def main():
    print("🔥 InfinityAI.Pro - REAL Trading Analysis")
    print("📊 Updated with your actual position: ₹130 @ ₹6.20 profit")
    print("=" * 60)
    
    executor = RealTradeExecutor()
    
    # Run analysis
    opportunity = await executor.run_real_analysis(execute_orders=False)
    
    if opportunity and opportunity['multiplier_2'] >= 5.0:
        print(f"\n🚨 HIGH PROFIT OPPORTUNITY DETECTED!")
        print(f"⚡ Ready to execute real orders?")
        
        print(f"\n⚠️  WARNING: This will place REAL orders with REAL money!")
        print(f"🎯 Profit potential: {opportunity['multiplier_2']:.1f}x current profit")
        
        # Uncomment the line below to enable real execution
        # await executor.run_real_analysis(execute_orders=True)

if __name__ == "__main__":
    asyncio.run(main())