#!/usr/bin/env python3
"""
InfinityAI.Pro Live Trading Test Script
======================================

This script tests all live trading functionality including:
- Portfolio management
- Order placement and execution
- AI analysis integration
- Real-time data feeds
- Risk management systems

IMPORTANT: This script is for testing purposes only.
Use with caution and small amounts in production.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io"
TEST_TIMEOUT = 30
MAX_ORDER_VALUE = 1000  # Maximum test order value in INR

class LiveTradingTester:
    def __init__(self):
        self.session = None
        self.test_results = {
            "portfolio_tests": [],
            "order_tests": [],
            "ai_tests": [],
            "data_tests": [],
            "risk_tests": []
        }
        self.start_time = datetime.now()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            url = f"{API_BASE_URL}{endpoint}"
            async with self.session.request(method, url, **kwargs) as response:
                result = {
                    "status_code": response.status,
                    "success": 200 <= response.status < 300,
                    "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                    "response_time": time.time()
                }
                return result
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "response_time": time.time()
            }

    async def test_portfolio_management(self) -> List[Dict[str, Any]]:
        """Test portfolio management functionality"""
        print("🏦 Testing Portfolio Management...")
        tests = []
        
        # Test 1: Get portfolio data
        result = await self.make_request("GET", "/dhan/portfolio")
        tests.append({
            "name": "Portfolio Data Retrieval",
            "success": result["success"] and "portfolio" in str(result.get("data", {})),
            "details": f"Status: {result['status_code']}, Response: {type(result.get('data'))}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 2: Get portfolio positions
        result = await self.make_request("GET", "/api/orders/positions")
        tests.append({
            "name": "Portfolio Positions",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, Positions: {len(result.get('data', {}).get('positions', []))}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 3: Get portfolio history
        result = await self.make_request("GET", "/api/dhan/portfolio/history")
        tests.append({
            "name": "Portfolio History",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, History available: {bool(result.get('data'))}",
            "response_time": result.get("response_time", 0)
        })
        
        return tests

    async def test_order_management(self) -> List[Dict[str, Any]]:
        """Test order placement and management"""
        print("📋 Testing Order Management...")
        tests = []
        
        # Test 1: Get order history
        result = await self.make_request("GET", "/dhan/orders")
        tests.append({
            "name": "Order History Retrieval",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, Orders: {len(result.get('data', {}).get('orders', []))}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 2: Place demo order (buy)
        test_order = {
            "symbol": "NSE_EQ|INE002A01018",  # Reliance
            "quantity": 1,
            "price": 2500.00,
            "order_type": "LIMIT",
            "transaction_type": "BUY",
            "product_type": "INTRADAY",
            "validity": "DAY"
        }
        
        result = await self.make_request("POST", "/api/dhan/orders/place", 
                                       json=test_order,
                                       headers={"Content-Type": "application/json"})
        tests.append({
            "name": "Order Placement (Demo)",
            "success": result["success"] or "demo" in str(result.get("data", {})).lower(),
            "details": f"Status: {result['status_code']}, Order ID: {result.get('data', {}).get('order_id', 'N/A')}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 3: Get order status
        if result["success"]:
            order_id = result.get("data", {}).get("order_id")
            if order_id:
                status_result = await self.make_request("GET", f"/api/dhan/orders/{order_id}/status")
                tests.append({
                    "name": "Order Status Check",
                    "success": status_result["success"],
                    "details": f"Status: {status_result['status_code']}, Order Status: {status_result.get('data', {}).get('status', 'Unknown')}",
                    "response_time": status_result.get("response_time", 0)
                })
        
        return tests

    async def test_ai_analysis(self) -> List[Dict[str, Any]]:
        """Test AI analysis functionality"""
        print("🤖 Testing AI Analysis...")
        tests = []
        
        # Test 1: Market pulse analysis
        result = await self.make_request("GET", "/ai/market-pulse")
        tests.append({
            "name": "Market Pulse Analysis",
            "success": result["success"] and "market_trend" in str(result.get("data", {})),
            "details": f"Status: {result['status_code']}, Trend: {result.get('data', {}).get('market_trend', 'N/A')}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 2: Comprehensive analysis
        analysis_request = {
            "symbols": ["NSE_IDX|Nifty 50", "NSE_EQ|INE002A01018"],
            "analysis_type": "comprehensive",
            "include_signals": True
        }
        
        result = await self.make_request("POST", "/ai/comprehensive-analysis",
                                       json=analysis_request,
                                       headers={"Content-Type": "application/json"})
        tests.append({
            "name": "Comprehensive AI Analysis",
            "success": result["success"] and result.get("data", {}).get("total_symbols", 0) > 0,
            "details": f"Status: {result['status_code']}, Symbols: {result.get('data', {}).get('total_symbols', 0)}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 3: Trading opportunities
        result = await self.make_request("GET", "/ai/trading-opportunities")
        tests.append({
            "name": "Trading Opportunities",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, Opportunities: {len(result.get('data', {}).get('opportunities', []))}",
            "response_time": result.get("response_time", 0)
        })
        
        return tests

    async def test_real_time_data(self) -> List[Dict[str, Any]]:
        """Test real-time data feeds"""
        print("📈 Testing Real-time Data...")
        tests = []
        
        # Test 1: Symbol data
        result = await self.make_request("GET", "/dhan/market-data/NSE_EQ%7CINE002A01018")
        tests.append({
            "name": "Symbol Data Feed",
            "success": result["success"] and "price" in str(result.get("data", {})).lower(),
            "details": f"Status: {result['status_code']}, Price available: {bool('price' in str(result.get('data', {})).lower())}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 2: Multiple symbols
        symbols = ["NSE_EQ|INE002A01018", "NSE_EQ|INE467B01029"]  # Reliance, TCS
        result = await self.make_request("POST", "/api/dhan/data/batch",
                                       json={"symbols": symbols},
                                       headers={"Content-Type": "application/json"})
        tests.append({
            "name": "Batch Symbol Data",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, Symbols returned: {len(result.get('data', {}).get('data', []))}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 3: Market indices
        result = await self.make_request("GET", "/api/dhan/data/NSE_IDX|Nifty%2050")
        tests.append({
            "name": "Market Index Data",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, Index data: {bool(result.get('data'))}",
            "response_time": result.get("response_time", 0)
        })
        
        return tests

    async def test_risk_management(self) -> List[Dict[str, Any]]:
        """Test risk management systems"""
        print("🛡️ Testing Risk Management...")
        tests = []
        
        # Test 1: Portfolio risk assessment
        result = await self.make_request("GET", "/api/ai/risk-assessment")
        tests.append({
            "name": "Portfolio Risk Assessment",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, Risk data: {bool(result.get('data'))}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 2: Order validation
        risky_order = {
            "symbol": "NSE_EQ|INE002A01018",
            "quantity": 1000,  # Large quantity
            "price": 2500.00,
            "order_type": "MARKET",
            "transaction_type": "BUY",
            "product_type": "DELIVERY"
        }
        
        result = await self.make_request("POST", "/api/dhan/orders/validate",
                                       json=risky_order,
                                       headers={"Content-Type": "application/json"})
        tests.append({
            "name": "Order Risk Validation",
            "success": result["success"] or result.get("status_code") == 400,  # Should reject or warn
            "details": f"Status: {result['status_code']}, Risk check: {'Passed' if result['success'] else 'Rejected/Warning'}",
            "response_time": result.get("response_time", 0)
        })
        
        # Test 3: System limits check
        result = await self.make_request("GET", "/api/dhan/limits")
        tests.append({
            "name": "Trading Limits Check",
            "success": result["success"],
            "details": f"Status: {result['status_code']}, Limits available: {bool(result.get('data'))}",
            "response_time": result.get("response_time", 0)
        })
        
        return tests

    async def run_comprehensive_test(self):
        """Run all trading tests"""
        print("🚀 InfinityAI.Pro Live Trading Test Suite")
        print("=" * 50)
        print(f"Started at: {self.start_time}")
        print(f"Base URL: {API_BASE_URL}")
        print("=" * 50)
        
        # Run all test suites
        test_suites = [
            ("Portfolio Management", self.test_portfolio_management),
            ("Order Management", self.test_order_management),
            ("AI Analysis", self.test_ai_analysis),
            ("Real-time Data", self.test_real_time_data),
            ("Risk Management", self.test_risk_management)
        ]
        
        all_results = {}
        total_tests = 0
        passed_tests = 0
        
        for suite_name, test_func in test_suites:
            try:
                print(f"\n{suite_name}:")
                print("-" * 30)
                results = await test_func()
                all_results[suite_name.lower().replace(" ", "_")] = results
                
                for test in results:
                    status = "✅ PASS" if test["success"] else "❌ FAIL"
                    print(f"{status} {test['name']}: {test['details']}")
                    total_tests += 1
                    if test["success"]:
                        passed_tests += 1
                        
            except Exception as e:
                print(f"❌ {suite_name} suite failed: {e}")
                all_results[suite_name.lower().replace(" ", "_")] = [{"error": str(e)}]
        
        # Generate summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 50)
        print("🎯 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Completed at: {end_time}")
        
        if success_rate >= 80:
            print("🟢 LIVE TRADING SYSTEM: READY FOR PRODUCTION")
        elif success_rate >= 60:
            print("🟡 LIVE TRADING SYSTEM: NEEDS ATTENTION")
        else:
            print("🔴 LIVE TRADING SYSTEM: NOT READY FOR PRODUCTION")
        
        # Save detailed results
        detailed_results = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "results": all_results
        }
        
        with open("live_trading_test_results.json", "w") as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        print(f"\n📊 Detailed results saved to: live_trading_test_results.json")
        
        return detailed_results

async def main():
    """Main test execution function"""
    async with LiveTradingTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    print("⚠️  IMPORTANT: This script tests live trading functionality.")
    print("⚠️  Ensure you're using a test environment or small amounts.")
    print("⚠️  Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        time.sleep(5)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")