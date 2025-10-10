#!/usr/bin/env python3
# 🚀 InfinityAI.Pro - Integrated Live Trading System
# Complete integration with backend application

import asyncio
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class Position:
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    entry_time: datetime
    position_type: str  # 'LONG' or 'SHORT'

@dataclass
class TradingSignal:
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    target_price: float
    stop_loss: float
    reasoning: str
    priority: int  # 1-10, 10 being highest

class IntegratedLiveTrader:
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
        
        # Trading Configuration
        self.live_trading_enabled = True
        self.risk_per_trade = 0.02  # 2% of portfolio per trade
        self.max_positions = 5
        self.trailing_stop_distance = 0.03  # 3%
        
        # Internal State
        self.positions: Dict[str, Position] = {}
        self.active_orders: List[Dict] = []
        self.trading_log: List[Dict] = []
        
        self.logger.info("🤖 InfinityAI Live Trading System Initialized")
    
    async def get_current_positions(self) -> List[Dict]:
        """Fetch current positions from Dhan API"""
        try:
            response = requests.get(f"{self.base_url}/positions", headers=self.headers)
            if response.status_code == 200:
                positions = response.json()
                self.logger.info(f"📊 Fetched {len(positions)} positions")
                return positions
            else:
                self.logger.error(f"❌ Failed to fetch positions: {response.status_code}")
                return []
        except Exception as e:
            self.logger.error(f"❌ Error fetching positions: {e}")
            return []
    
    async def get_account_balance(self) -> float:
        """Get available trading balance"""
        try:
            response = requests.get(f"{self.base_url}/fundlimit", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                balance = data.get('availableBalance', 0)
                self.logger.info(f"💰 Available Balance: ₹{balance}")
                return balance
            return 0
        except Exception as e:
            self.logger.error(f"❌ Error fetching balance: {e}")
            return 0
    
    async def place_order_live(self, symbol: str, quantity: int, price: float, 
                               transaction_type: str, order_type: str = "LIMIT") -> Dict:
        """Place LIVE order via Dhan API"""
        
        if not self.live_trading_enabled:
            self.logger.warning("🚫 Live trading disabled - order not placed")
            return {"status": "disabled", "message": "Live trading disabled"}
        
        order_data = {
            "dhanClientId": self.client_id,
            "correlationId": f"LIVE_{int(datetime.now().timestamp())}",
            "transactionType": transaction_type,
            "exchangeSegment": "MCX_COM" if "CRUDE" in symbol else "NSE_FNO",
            "productType": "INTRADAY",
            "orderType": order_type,
            "validity": "DAY",
            "securityId": symbol,
            "quantity": quantity,
            "price": price if order_type == "LIMIT" else 0
        }
        
        try:
            self.logger.info(f"🔥 PLACING LIVE ORDER: {transaction_type} {quantity} {symbol} @ ₹{price}")
            
            response = requests.post(f"{self.base_url}/orders", 
                                   headers=self.headers, 
                                   json=order_data)
            
            if response.status_code == 200:
                result = response.json()
                order_id = result.get('orderId', 'Unknown')
                
                self.logger.info(f"✅ ORDER PLACED SUCCESSFULLY: ID {order_id}")
                
                # Log the trade
                trade_log = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "action": transaction_type,
                    "quantity": quantity,
                    "price": price,
                    "order_id": order_id,
                    "status": "PLACED"
                }
                self.trading_log.append(trade_log)
                
                return {"status": "success", "order_id": order_id, "response": result}
            else:
                error_msg = response.text
                self.logger.error(f"❌ ORDER FAILED: {error_msg}")
                return {"status": "failed", "error": error_msg}
                
        except Exception as e:
            self.logger.error(f"❌ Order placement error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def analyze_crude_oil_exit(self) -> TradingSignal:
        """Analyze current crude oil position for exit"""
        positions = await self.get_current_positions()
        
        for pos in positions:
            if "CRUDE" in pos.get('tradingSymbol', ''):
                symbol = pos.get('tradingSymbol')
                current_pnl = pos.get('unrealizedProfit', 0)
                current_price = pos.get('ltp', 0)
                quantity = pos.get('netQty', 0)
                
                # AI Decision Logic
                if current_pnl > 5:  # Profit > ₹5
                    confidence = 85.0
                    action = "SELL"
                    reasoning = f"Profitable position (₹{current_pnl}), good time to exit and switch to NIFTY momentum"
                    priority = 9
                else:
                    confidence = 60.0
                    action = "HOLD"
                    reasoning = f"Current P&L: ₹{current_pnl}, waiting for better exit opportunity"
                    priority = 5
                
                return TradingSignal(
                    symbol=symbol,
                    action=action,
                    confidence=confidence,
                    target_price=current_price,
                    stop_loss=current_price * 0.95,  # 5% stop loss
                    reasoning=reasoning,
                    priority=priority
                )
        
        return None
    
    async def analyze_nifty_entry(self) -> TradingSignal:
        """Analyze NIFTY opportunities for entry"""
        
        # Real-time NIFTY analysis (simplified for demo)
        nifty_opportunities = [
            {
                "symbol": "NIFTY50-16Oct2025-25900-CE",
                "entry_price": 70.0,
                "target": 125.0,
                "confidence": 87.0,
                "reasoning": "Strong bullish momentum, high volume breakout expected"
            },
            {
                "symbol": "NIFTY50-16Oct2025-25850-CE", 
                "entry_price": 90.0,
                "target": 140.0,
                "confidence": 85.0,
                "reasoning": "Support level bounce with RSI oversold recovery"
            }
        ]
        
        # Select best opportunity
        best_opp = max(nifty_opportunities, key=lambda x: x['confidence'])
        
        return TradingSignal(
            symbol=best_opp['symbol'],
            action="BUY",
            confidence=best_opp['confidence'],
            target_price=best_opp['entry_price'],
            stop_loss=best_opp['entry_price'] * 0.9,  # 10% stop loss
            reasoning=best_opp['reasoning'],
            priority=8
        )
    
    async def execute_crude_oil_exit_test(self) -> bool:
        """Execute REAL crude oil exit for testing"""
        
        self.logger.info("🔥 TESTING REAL CRUDE OIL EXIT")
        
        # Get current crude position
        signal = await self.analyze_crude_oil_exit()
        
        if signal and signal.action == "SELL":
            self.logger.info(f"📊 Exit Signal: {signal.reasoning}")
            self.logger.info(f"📊 Confidence: {signal.confidence}%")
            
            # Place REAL exit order
            result = await self.place_order_live(
                symbol=signal.symbol,
                quantity=1,  # Assuming 1 lot
                price=signal.target_price,
                transaction_type="SELL",
                order_type="MARKET"  # Market order for immediate execution
            )
            
            if result['status'] == 'success':
                self.logger.info("✅ CRUDE OIL EXIT ORDER PLACED SUCCESSFULLY!")
                self.logger.info(f"📋 Order ID: {result['order_id']}")
                return True
            else:
                self.logger.error(f"❌ Exit order failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            self.logger.info("📊 No exit signal generated - holding position")
            return False
    
    async def execute_strategy_switch(self) -> bool:
        """Execute complete strategy switch: Crude Oil → NIFTY"""
        
        self.logger.info("🚀 EXECUTING COMPLETE STRATEGY SWITCH")
        
        # Step 1: Exit Crude Oil
        crude_exit_success = await self.execute_crude_oil_exit_test()
        
        if crude_exit_success:
            self.logger.info("✅ Step 1 Complete: Crude oil position exited")
            
            # Wait for settlement
            await asyncio.sleep(5)
            
            # Step 2: Enter NIFTY position
            nifty_signal = await self.analyze_nifty_entry()
            
            if nifty_signal:
                self.logger.info(f"🎯 NIFTY Entry Signal: {nifty_signal.reasoning}")
                
                result = await self.place_order_live(
                    symbol=nifty_signal.symbol,
                    quantity=1,
                    price=nifty_signal.target_price,
                    transaction_type="BUY",
                    order_type="LIMIT"
                )
                
                if result['status'] == 'success':
                    self.logger.info("✅ STRATEGY SWITCH COMPLETE!")
                    self.logger.info(f"📋 NIFTY Order ID: {result['order_id']}")
                    return True
                else:
                    self.logger.error(f"❌ NIFTY entry failed: {result.get('error')}")
                    return False
            else:
                self.logger.warning("⚠️ No NIFTY entry signal generated")
                return False
        else:
            self.logger.warning("⚠️ Crude oil exit failed - strategy switch aborted")
            return False
    
    async def generate_trading_report(self) -> Dict:
        """Generate comprehensive trading report"""
        
        positions = await self.get_current_positions()
        balance = await self.get_account_balance()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "account_balance": balance,
            "active_positions": len(positions),
            "total_pnl": sum(pos.get('unrealizedProfit', 0) for pos in positions),
            "positions_detail": positions,
            "trading_log": self.trading_log[-10:],  # Last 10 trades
            "system_status": {
                "live_trading_enabled": self.live_trading_enabled,
                "max_positions": self.max_positions,
                "risk_per_trade": self.risk_per_trade
            }
        }
        
        return report
    
    async def run_live_trading_cycle(self):
        """Main live trading cycle"""
        
        self.logger.info("🤖 Starting Live Trading Cycle")
        
        try:
            # Generate trading report
            report = await self.generate_trading_report()
            
            self.logger.info(f"💰 Account Balance: ₹{report['account_balance']}")
            self.logger.info(f"📊 Active Positions: {report['active_positions']}")
            self.logger.info(f"📈 Total P&L: ₹{report['total_pnl']}")
            
            # Analyze crude oil for exit opportunity
            crude_signal = await self.analyze_crude_oil_exit()
            
            if crude_signal:
                self.logger.info(f"🎯 Crude Signal: {crude_signal.action} (Confidence: {crude_signal.confidence}%)")
                self.logger.info(f"💡 Reasoning: {crude_signal.reasoning}")
                
                # If high confidence exit signal, execute strategy switch
                if crude_signal.action == "SELL" and crude_signal.confidence >= 80:
                    self.logger.info("🔥 HIGH CONFIDENCE EXIT SIGNAL - EXECUTING STRATEGY SWITCH")
                    await self.execute_strategy_switch()
            
            # Save report to file
            with open("live_trading_report.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info("✅ Live Trading Cycle Complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error in trading cycle: {e}")

# Integration with FastAPI backend
class TradingAPI:
    def __init__(self):
        self.trader = IntegratedLiveTrader()
    
    async def get_live_status(self):
        """API endpoint for live trading status"""
        return await self.trader.generate_trading_report()
    
    async def execute_trade_test(self):
        """API endpoint to test real trade execution"""
        return await self.trader.execute_crude_oil_exit_test()
    
    async def execute_strategy_switch(self):
        """API endpoint for complete strategy switch"""
        return await self.trader.execute_strategy_switch()

# Command line interface
async def main():
    print("🚀 InfinityAI.Pro - Integrated Live Trading System")
    print("=" * 60)
    
    trader = IntegratedLiveTrader()
    
    # Test options
    print("1. 📊 Generate Trading Report")
    print("2. 🔥 Test REAL Crude Oil Exit")
    print("3. 🚀 Execute Complete Strategy Switch")
    print("4. 🔄 Run Continuous Live Trading")
    
    choice = input("\nSelect option (1-4): ")
    
    if choice == "1":
        print("\n📊 Generating Trading Report...")
        report = await trader.generate_trading_report()
        print(json.dumps(report, indent=2, default=str))
        
    elif choice == "2":
        print("\n🔥 TESTING REAL CRUDE OIL EXIT...")
        print("⚠️  WARNING: This will place a REAL order!")
        confirm = input("Type 'CONFIRM' to proceed: ")
        
        if confirm == 'CONFIRM':
            success = await trader.execute_crude_oil_exit_test()
            if success:
                print("✅ REAL ORDER PLACED SUCCESSFULLY!")
            else:
                print("❌ Order placement failed")
        else:
            print("❌ Test cancelled")
            
    elif choice == "3":
        print("\n🚀 EXECUTING COMPLETE STRATEGY SWITCH...")
        print("⚠️  WARNING: This will place REAL orders!")
        confirm = input("Type 'EXECUTE LIVE' to proceed: ")
        
        if confirm == 'EXECUTE LIVE':
            success = await trader.execute_strategy_switch()
            if success:
                print("✅ STRATEGY SWITCH EXECUTED!")
            else:
                print("❌ Strategy switch failed")
        else:
            print("❌ Execution cancelled")
            
    elif choice == "4":
        print("\n🔄 Starting Continuous Live Trading...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                await trader.run_live_trading_cycle()
                await asyncio.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\n⏹️ Live trading stopped")

if __name__ == "__main__":
    asyncio.run(main())