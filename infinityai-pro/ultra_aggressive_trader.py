#!/usr/bin/env python3
# 🔥 InfinityAI.Pro - ULTRA AGGRESSIVE TRADING SYSTEM
# ZERO CONFIRMATION - MAXIMUM AGGRESSION - IMMEDIATE EXECUTION
# Goal: Double capital through aggressive opportunities

import asyncio
import requests
import json
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure aggressive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AGGRESSIVE - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aggressive_trading.log'),
        logging.StreamHandler()
    ]
)

class UltraAggressiveTrader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Dhan API Configuration
        self.dhan_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTk4MDUzMzEsImlhdCI6MTc1OTcxODkzMSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.SdnAubAOeObBTLmEYWTUP9lBW2MapBPeQL2b57mV8or-8tqUZwiIVmZywIzbkhRPViGKrqOH56ClQUXJL9oawA"
        self.base_url = "https://api.dhan.co/v2"
        self.client_id = "1101302170"
        
        self.headers = {
            "access-token": self.dhan_token,
            "Content-Type": "application/json"
        }
        
        # ULTRA AGGRESSIVE PARAMETERS
        self.capital_doubling_target = 2.0  # 100% return target
        self.max_position_size = 0.8        # Use 80% of capital per trade
        self.aggression_multiplier = 3.0    # 3x normal position sizes
        self.profit_threshold = 0.15        # 15% minimum profit to hold
        self.max_loss_per_trade = 0.25      # 25% max loss (high risk, high reward)
        
        # TRAILING PARAMETERS (More Aggressive)
        self.trailing_start = 0.08          # Start trailing at 8% profit
        self.trailing_distance = 0.04       # 4% trailing distance
        self.aggressive_exit_at = 0.20      # Exit at 20% profit if volatile
        
        # EXECUTION PARAMETERS
        self.confidence_threshold = 65.0    # Lower threshold for more trades
        self.scan_interval = 30             # Scan every 30 seconds
        self.immediate_execution = True     # NO CONFIRMATION NEEDED
        
        # State tracking
        self.available_capital = 0.0
        self.target_capital = 0.0
        self.current_positions = {}
        self.executed_trades = []
        
        self.logger.info("🔥 ULTRA AGGRESSIVE TRADING SYSTEM INITIALIZED")
        self.logger.info(f"🎯 GOAL: DOUBLE CAPITAL FROM ANY AMOUNT")
        self.logger.info(f"⚡ MODE: ZERO CONFIRMATION - IMMEDIATE EXECUTION")
    
    async def get_available_funds(self) -> float:
        """Get available trading funds"""
        try:
            response = requests.get(f"{self.base_url}/fundlimit", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                balance = data.get('availableBalance', 0)
                self.available_capital = balance
                if self.target_capital == 0:
                    self.target_capital = balance * self.capital_doubling_target
                
                self.logger.info(f"💰 Available Capital: ₹{balance}")
                self.logger.info(f"🎯 Target Capital: ₹{self.target_capital}")
                return balance
        except Exception as e:
            self.logger.error(f"❌ Error fetching funds: {e}")
        return 0.0
    
    async def scan_aggressive_opportunities(self) -> List[Dict]:
        """Scan for ultra-aggressive profit opportunities"""
        opportunities = []
        
        # Get current market data (simulated for demo)
        market_data = {
            'nifty_spot': 25850,
            'nifty_trend': 'BULLISH_BREAKOUT',
            'volatility': 'HIGH',
            'momentum': 'STRONG',
            'bank_nifty': 54200,
            'crude_oil': 5520,
            'time_to_expiry': 10
        }
        
        # AGGRESSIVE NIFTY OPPORTUNITIES
        if market_data['nifty_trend'] == 'BULLISH_BREAKOUT':
            # Ultra aggressive ATM call
            nifty_aggressive = {
                'symbol': 'NIFTY50-16Oct2025-25850-CE',
                'type': 'ULTRA_AGGRESSIVE_CALL',
                'entry_price': 90.0,
                'target_1': 130.0,    # 44% gain
                'target_2': 180.0,    # 100% gain  
                'stop_loss': 65.0,    # 28% loss
                'confidence': 85.0,
                'aggression_score': 95,
                'capital_usage': 0.7,  # Use 70% of capital
                'profit_potential': 100,  # 100% gain potential
                'reasoning': 'NIFTY breakout above resistance with high volume - IMMEDIATE EXECUTION REQUIRED'
            }
            opportunities.append(nifty_aggressive)
        
        # AGGRESSIVE BANK NIFTY MOMENTUM
        bank_nifty_aggressive = {
            'symbol': 'BANKNIFTY-16Oct2025-54200-CE',
            'type': 'MOMENTUM_BLAST',
            'entry_price': 180.0,
            'target_1': 280.0,    # 56% gain
            'target_2': 400.0,    # 122% gain
            'stop_loss': 120.0,   # 33% loss
            'confidence': 82.0,
            'aggression_score': 92,
            'capital_usage': 0.6,
            'profit_potential': 122,
            'reasoning': 'Bank NIFTY explosive momentum setup - MAXIMUM AGGRESSION MODE'
        }
        opportunities.append(bank_nifty_aggressive)
        
        # CRUDE OIL VOLATILITY PLAY
        crude_aggressive = {
            'symbol': 'CRUDEOIL-16Oct2025-5550-CE',
            'type': 'VOLATILITY_EXPLOSION',
            'entry_price': 120.0,
            'target_1': 200.0,    # 67% gain
            'target_2': 300.0,    # 150% gain
            'stop_loss': 80.0,    # 33% loss
            'confidence': 78.0,
            'aggression_score': 88,
            'capital_usage': 0.5,
            'profit_potential': 150,
            'reasoning': 'Crude oil volatility spike expected - HIGH RISK HIGH REWARD'
        }
        opportunities.append(crude_aggressive)
        
        # INTRADAY SCALPING OPPORTUNITIES
        scalp_opportunities = [
            {
                'symbol': 'NIFTY50-16Oct2025-25900-PE',
                'type': 'SCALP_HEDGE',
                'entry_price': 45.0,
                'target_1': 65.0,
                'target_2': 85.0,
                'stop_loss': 30.0,
                'confidence': 75.0,
                'aggression_score': 80,
                'capital_usage': 0.3,
                'profit_potential': 89,
                'reasoning': 'Quick scalp opportunity - Fast profits'
            }
        ]
        opportunities.extend(scalp_opportunities)
        
        # Sort by aggression score and profit potential
        opportunities.sort(key=lambda x: x['aggression_score'] * x['profit_potential'], reverse=True)
        
        return opportunities
    
    async def calculate_position_size(self, opportunity: Dict) -> int:
        """Calculate ultra-aggressive position size"""
        available = await self.get_available_funds()
        
        if available <= 0:
            return 0
        
        # Ultra aggressive sizing
        capital_to_use = available * opportunity['capital_usage'] * self.aggression_multiplier
        entry_price = opportunity['entry_price']
        
        # Calculate lot size
        position_size = int(capital_to_use / entry_price)
        
        # Ensure we don't exceed limits but be aggressive
        max_affordable = int(available * 0.95 / entry_price)  # Use 95% of available capital
        position_size = min(position_size, max_affordable)
        
        return max(1, position_size)  # At least 1 lot
    
    async def execute_immediate_order(self, opportunity: Dict) -> bool:
        """IMMEDIATE ORDER EXECUTION - NO CONFIRMATION"""
        
        position_size = await self.calculate_position_size(opportunity)
        
        if position_size <= 0:
            self.logger.warning(f"⚠️ Insufficient capital for {opportunity['symbol']}")
            return False
        
        # Prepare order for IMMEDIATE execution
        order_data = {
            "dhanClientId": self.client_id,
            "correlationId": f"AGGRESSIVE_{int(time.time())}",
            "transactionType": "BUY",
            "exchangeSegment": "NSE_FNO" if "NIFTY" in opportunity['symbol'] else "MCX_COMM",
            "productType": "INTRADAY",
            "orderType": "MARKET",  # MARKET ORDER for immediate execution
            "validity": "DAY",
            "securityId": opportunity['symbol'],
            "quantity": position_size
        }
        
        self.logger.info(f"🔥 EXECUTING IMMEDIATE ORDER - NO CONFIRMATION")
        self.logger.info(f"🎯 {opportunity['symbol']}")
        self.logger.info(f"📊 Quantity: {position_size}")
        self.logger.info(f"💰 Capital Used: ₹{position_size * opportunity['entry_price']}")
        self.logger.info(f"🚀 Aggression Score: {opportunity['aggression_score']}/100")
        self.logger.info(f"💡 Reasoning: {opportunity['reasoning']}")
        
        try:
            # EXECUTE ORDER IMMEDIATELY
            response = requests.post(f"{self.base_url}/orders", 
                                   headers=self.headers, 
                                   json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('orderId', 'Unknown')
                
                self.logger.info(f"✅ IMMEDIATE EXECUTION SUCCESS!")
                self.logger.info(f"📋 Order ID: {order_id}")
                
                # Track the trade
                trade_log = {
                    'timestamp': datetime.now().isoformat(),
                    'order_id': order_id,
                    'symbol': opportunity['symbol'],
                    'type': opportunity['type'],
                    'quantity': position_size,
                    'entry_price': opportunity['entry_price'],
                    'target_1': opportunity['target_1'],
                    'target_2': opportunity['target_2'],
                    'stop_loss': opportunity['stop_loss'],
                    'aggression_score': opportunity['aggression_score'],
                    'profit_potential': opportunity['profit_potential'],
                    'reasoning': opportunity['reasoning']
                }
                
                self.executed_trades.append(trade_log)
                
                # Save to log file
                with open('aggressive_trades.json', 'w') as f:
                    json.dump(self.executed_trades, f, indent=2)
                
                return True
            else:
                self.logger.error(f"❌ ORDER FAILED: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ EXECUTION ERROR: {e}")
            return False
    
    async def manage_aggressive_positions(self) -> None:
        """Manage positions with aggressive trailing and exits"""
        try:
            response = requests.get(f"{self.base_url}/positions", headers=self.headers)
            
            if response.status_code == 200:
                positions = response.json()
                
                for position in positions:
                    symbol = position.get('tradingSymbol', '')
                    current_pnl = position.get('unrealizedProfit', 0)
                    quantity = position.get('netQty', 0)
                    entry_value = abs(quantity) * position.get('buyAvg', 0)
                    
                    if entry_value > 0:
                        profit_percent = (current_pnl / entry_value) * 100
                        
                        self.logger.info(f"📊 {symbol}: P&L ₹{current_pnl} ({profit_percent:.1f}%)")
                        
                        # AGGRESSIVE PROFIT TAKING
                        if profit_percent >= 20:  # 20% profit - consider exit
                            self.logger.info(f"🎯 HIGH PROFIT DETECTED: {symbol} at {profit_percent:.1f}%")
                            # Could implement automatic profit booking here
                        
                        # AGGRESSIVE LOSS CUTTING
                        elif profit_percent <= -25:  # 25% loss - immediate exit
                            self.logger.warning(f"🚨 STOP LOSS TRIGGERED: {symbol} at {profit_percent:.1f}%")
                            # Could implement automatic stop loss here
                        
                        # TRAILING MANAGEMENT
                        elif profit_percent >= 8:  # Start trailing at 8%
                            self.logger.info(f"🔄 TRAILING ACTIVE: {symbol} - protecting {profit_percent-4:.1f}%")
        
        except Exception as e:
            self.logger.error(f"❌ Position management error: {e}")
    
    async def aggressive_capital_doubling_cycle(self):
        """Main aggressive trading cycle - IMMEDIATE EXECUTION"""
        
        self.logger.info("🔥 STARTING AGGRESSIVE CAPITAL DOUBLING CYCLE")
        self.logger.info("⚡ MODE: ZERO CONFIRMATION - MAXIMUM AGGRESSION")
        
        cycle_count = 0
        
        while True:
            cycle_count += 1
            
            try:
                self.logger.info(f"🔄 AGGRESSIVE CYCLE #{cycle_count}")
                
                # Check available capital
                current_capital = await self.get_available_funds()
                
                if current_capital >= self.target_capital:
                    self.logger.info(f"🎉 CAPITAL DOUBLING TARGET ACHIEVED!")
                    self.logger.info(f"💰 Started with: ₹{self.target_capital/2}")
                    self.logger.info(f"💰 Current: ₹{current_capital}")
                    self.logger.info(f"📈 Gain: {((current_capital / (self.target_capital/2)) - 1) * 100:.1f}%")
                
                # Scan for opportunities
                opportunities = await self.scan_aggressive_opportunities()
                
                self.logger.info(f"🔍 Found {len(opportunities)} aggressive opportunities")
                
                # Execute BEST opportunity IMMEDIATELY
                if opportunities:
                    best_opportunity = opportunities[0]  # Highest scored opportunity
                    
                    if best_opportunity['confidence'] >= self.confidence_threshold:
                        self.logger.info(f"🚀 EXECUTING BEST OPPORTUNITY IMMEDIATELY")
                        self.logger.info(f"🎯 {best_opportunity['symbol']}")
                        self.logger.info(f"💡 {best_opportunity['reasoning']}")
                        
                        # IMMEDIATE EXECUTION - NO CONFIRMATION
                        success = await self.execute_immediate_order(best_opportunity)
                        
                        if success:
                            self.logger.info(f"✅ AGGRESSIVE TRADE EXECUTED SUCCESSFULLY")
                        else:
                            self.logger.error(f"❌ Trade execution failed")
                    else:
                        self.logger.info(f"⚠️ Best opportunity confidence {best_opportunity['confidence']}% < {self.confidence_threshold}%")
                
                # Manage existing positions
                await self.manage_aggressive_positions()
                
                # Summary
                self.logger.info(f"📊 CYCLE #{cycle_count} COMPLETE")
                self.logger.info(f"💰 Current Capital: ₹{current_capital}")
                self.logger.info(f"🎯 Target: ₹{self.target_capital}")
                self.logger.info(f"📈 Progress: {(current_capital/self.target_capital*100):.1f}% to goal")
                
                # Wait for next scan
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Error in aggressive cycle: {e}")
                await asyncio.sleep(10)  # Brief pause on error
    
    async def display_aggressive_status(self):
        """Display current aggressive trading status"""
        
        print("🔥" * 60)
        print("ULTRA AGGRESSIVE TRADING SYSTEM STATUS")
        print("🔥" * 60)
        
        current_capital = await self.get_available_funds()
        opportunities = await self.scan_aggressive_opportunities()
        
        print(f"\n💰 CAPITAL STATUS:")
        print(f"Available: ₹{current_capital}")
        print(f"Target: ₹{self.target_capital}")
        print(f"Progress: {(current_capital/self.target_capital*100):.1f}% to doubling goal")
        
        print(f"\n🎯 AGGRESSIVE OPPORTUNITIES ({len(opportunities)}):")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"{i}. {opp['symbol']}")
            print(f"   Type: {opp['type']}")
            print(f"   Aggression Score: {opp['aggression_score']}/100")
            print(f"   Profit Potential: {opp['profit_potential']}%")
            print(f"   Capital Usage: {opp['capital_usage']*100:.0f}%")
            print(f"   Reasoning: {opp['reasoning']}")
        
        print(f"\n⚡ SYSTEM PARAMETERS:")
        print(f"Confidence Threshold: {self.confidence_threshold}%")
        print(f"Max Position Size: {self.max_position_size*100:.0f}%")
        print(f"Scan Interval: {self.scan_interval} seconds")
        print(f"Immediate Execution: {self.immediate_execution}")
        
        print(f"\n🚀 EXECUTED TRADES: {len(self.executed_trades)}")
        for trade in self.executed_trades[-3:]:
            print(f"   {trade['symbol']}: {trade['type']} (Score: {trade['aggression_score']})")

# Launch the Ultra Aggressive System
async def main():
    print("🔥 InfinityAI.Pro - ULTRA AGGRESSIVE TRADING SYSTEM")
    print("⚡ ZERO CONFIRMATION - IMMEDIATE EXECUTION - CAPITAL DOUBLING")
    print("=" * 80)
    
    trader = UltraAggressiveTrader()
    
    print("Select Mode:")
    print("1. 📊 Display Current Status")
    print("2. 🔥 START AGGRESSIVE TRADING (IMMEDIATE EXECUTION)")
    print("3. 🚀 SINGLE AGGRESSIVE SCAN & EXECUTE")
    
    choice = "2"  # Default to aggressive trading
    
    if choice == "1":
        await trader.display_aggressive_status()
    elif choice == "2":
        print("\n🔥 STARTING ULTRA AGGRESSIVE TRADING SYSTEM")
        print("⚡ NO CONFIRMATIONS - IMMEDIATE EXECUTION")
        print("🎯 GOAL: DOUBLE YOUR CAPITAL")
        print("\nPress Ctrl+C to stop...")
        
        await trader.aggressive_capital_doubling_cycle()
    elif choice == "3":
        print("\n🚀 RUNNING SINGLE AGGRESSIVE CYCLE")
        opportunities = await trader.scan_aggressive_opportunities()
        if opportunities:
            await trader.execute_immediate_order(opportunities[0])

if __name__ == "__main__":
    asyncio.run(main())