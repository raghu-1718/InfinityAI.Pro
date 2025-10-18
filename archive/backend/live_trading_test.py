#!/usr/bin/env python3
# 🚀 InfinityAI.Pro - Live Trading Test & Integration
# Direct execution test for crude oil trade

import asyncio
import requests
import json
from datetime import datetime

class LiveTradingTest:
    def __init__(self):
        self.dhan_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NTk4MDUzMzEsImlhdCI6MTc1OTcxODkzMSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vaW5maW5pdHlhaS1hcHAuYWdyZWVhYmxlbWVhZG93LTczNzViMWY3LmVhc3R1cy5henVyZWNvbnRhaW5lcmFwcHMuaW8vYXBpL3dlYmhvb2tzL2RoYW4iLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.SdnAubAOeObBTLmEYWTUP9lBW2MapBPeQL2b57mV8or-8tqUZwiIVmZywIzbkhRPViGKrqOH56ClQUXJL9oawA"
        self.base_url = "https://api.dhan.co/v2"
        self.client_id = "1101302170"
        self.headers = {
            "access-token": self.dhan_token,
            "Content-Type": "application/json"
        }
    
    async def test_crude_oil_exit(self):
        """Test placing a REAL crude oil exit order"""
        
        print("🔥 LIVE TRADING TEST - CRUDE OIL EXIT")
        print("=" * 50)
        
        # Get current position first
        response = requests.get(f"{self.base_url}/positions", headers=self.headers)
        
        if response.status_code == 200:
            positions = response.json()
            crude_position = None
            
            for pos in positions:
                if "CRUDE" in pos.get('tradingSymbol', ''):
                    crude_position = pos
                    break
            
            if crude_position:
                symbol = crude_position['tradingSymbol']
                quantity = crude_position['netQty']
                current_pnl = crude_position['unrealizedProfit']
                
                print(f"✅ Found Crude Position:")
                print(f"   Symbol: {symbol}")
                print(f"   Quantity: {quantity}")
                print(f"   Current P&L: ₹{current_pnl}")
                
                # Prepare order data
                order_data = {
                    "dhanClientId": self.client_id,
                    "correlationId": f"TEST_EXIT_{int(datetime.now().timestamp())}",
                    "transactionType": "SELL",
                    "exchangeSegment": "MCX_COMM",
                    "productType": "MARGIN",
                    "orderType": "MARKET",
                    "validity": "DAY",
                    "securityId": crude_position['securityId'],
                    "quantity": abs(quantity)
                }
                
                print(f"\n📋 ORDER DETAILS:")
                print(f"   Type: MARKET SELL")
                print(f"   Quantity: {abs(quantity)}")
                print(f"   Security ID: {crude_position['securityId']}")
                
                print(f"\n🚨 PLACING REAL ORDER...")
                
                try:
                    order_response = requests.post(f"{self.base_url}/orders", 
                                                 headers=self.headers, 
                                                 json=order_data)
                    
                    print(f"Response Status: {order_response.status_code}")
                    print(f"Response: {order_response.text}")
                    
                    if order_response.status_code == 200:
                        result = order_response.json()
                        order_id = result.get('orderId', 'Unknown')
                        
                        print(f"✅ ORDER PLACED SUCCESSFULLY!")
                        print(f"📋 Order ID: {order_id}")
                        print(f"💰 Profit Locked: ₹{current_pnl}")
                        
                        # Log the successful trade
                        with open("live_trade_log.txt", "a") as f:
                            f.write(f"{datetime.now()}: CRUDE EXIT - Order ID: {order_id}, P&L: ₹{current_pnl}\n")
                        
                        return True
                    else:
                        print(f"❌ ORDER FAILED: {order_response.text}")
                        return False
                        
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    return False
            else:
                print("❌ No crude oil position found")
                return False
        else:
            print(f"❌ Failed to fetch positions: {response.status_code}")
            return False

async def main():
    print("🚀 InfinityAI.Pro - Live Trading Integration Test")
    print("This will place a REAL order to exit your crude oil position")
    print("=" * 60)
    
    tester = LiveTradingTest()
    success = await tester.test_crude_oil_exit()
    
    if success:
        print("\n✅ LIVE TRADING TEST: SUCCESS")
        print("🎯 Order placement system is working!")
        print("🔄 Ready for GitHub CI/CD integration")
    else:
        print("\n❌ LIVE TRADING TEST: FAILED")
        print("🔧 Check API credentials and permissions")

if __name__ == "__main__":
    asyncio.run(main())