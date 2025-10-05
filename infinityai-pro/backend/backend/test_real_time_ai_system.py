#!/usr/bin/env python3
"""
Real-time AI Trading System - Comprehensive Test Suite
Tests Dhan integration, AI analysis, and live data processing
"""

import requests
import json
import time
import asyncio
from typing import Dict, Any
from datetime import datetime

# Configuration
API_BASE_URL = "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io"
FRONTEND_URL = "https://infinity-ai-9utba60h7-infinityaipro.vercel.app"

class InfinityAITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params, timeout=30)
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "data": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_system_health(self) -> Dict[str, Any]:
        """Test basic system health"""
        
        print("\n🏥 Testing System Health...")
        print("=" * 50)
        
        tests = [
            {"name": "Health Check", "endpoint": "/health", "method": "GET"},
            {"name": "Root Info", "endpoint": "/", "method": "GET"},
            {"name": "Dhan Integration Status", "endpoint": "/dhan/status", "method": "GET"},
            {"name": "AI Analysis Status", "endpoint": "/ai/health", "method": "GET"}
        ]
        
        results = []
        
        for test in tests:
            print(f"  Testing: {test['name']}")
            result = self.make_request(test["method"], test["endpoint"])
            
            if result["success"]:
                print(f"    ✅ PASS")
            else:
                print(f"    ❌ FAIL - {result.get('error', 'Unknown error')}")
            
            results.append({
                "test": test["name"],
                "success": result["success"],
                "details": result
            })
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        print(f"\n📊 Health Check Results: {success_rate:.1%} pass rate")
        
        return {"tests": results, "success_rate": success_rate}
    
    def test_dhan_integration(self) -> Dict[str, Any]:
        """Test Dhan API integration and market data"""
        
        print("\n🔗 Testing Dhan Integration...")
        print("=" * 50)
        
        tests = [
            {
                "name": "Market Data - NIFTY",
                "endpoint": "/dhan/market-data/NSE_IDX|Nifty 50",
                "method": "GET"
            },
            {
                "name": "Market Data - Multiple Symbols",
                "endpoint": "/dhan/market-data",
                "method": "POST",
                "data": {"symbols": ["NSE_IDX|Nifty 50", "NSE_IDX|Nifty Bank", "NSE_EQ|INE002A01018"]}
            },
            {
                "name": "Supported Symbols",
                "endpoint": "/dhan/supported-symbols",
                "method": "GET"
            }
        ]
        
        results = []
        
        for test in tests:
            print(f"  Testing: {test['name']}")
            result = self.make_request(
                test["method"], 
                test["endpoint"], 
                test.get("data")
            )
            
            if result["success"]:
                print(f"    ✅ PASS")
                if result["data"]:
                    data = result["data"]
                    if "quotes" in data:
                        print(f"    📊 Symbols: {len(data['quotes'])}")
                    elif "symbol" in data:
                        print(f"    📈 {data['symbol']}: ₹{data.get('data', {}).get('ltp', 'N/A')}")
            else:
                print(f"    ❌ FAIL - Status: {result.get('status_code')}")
            
            results.append({
                "test": test["name"],
                "success": result["success"],
                "details": result
            })
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        print(f"\n📊 Dhan Integration Results: {success_rate:.1%} pass rate")
        
        return {"tests": results, "success_rate": success_rate}
    
    def test_ai_analysis_engine(self) -> Dict[str, Any]:
        """Test AI analysis capabilities"""
        
        print("\n🧠 Testing AI Analysis Engine...")
        print("=" * 50)
        
        # Test comprehensive analysis
        print("  Testing: Comprehensive AI Analysis")
        comprehensive_result = self.make_request(
            "POST",
            "/ai/comprehensive-analysis",
            {
                "symbols": ["NSE_IDX|Nifty 50", "NSE_IDX|Nifty Bank", "NSE_EQ|INE002A01018", "NSE_EQ|INE062A01020", "NSE_EQ|INE040A01034"],
                "analysis_type": "comprehensive",
                "include_opportunities": True
            }
        )
        
        if comprehensive_result["success"]:
            data = comprehensive_result["data"]
            print(f"    ✅ PASS")
            print(f"    📊 Total Symbols: {data.get('total_symbols', 0)}")
            print(f"    🎯 Results Found: {len(data.get('results', []))}")
            print(f"    📈 Analysis Type: {data.get('analysis_type', 'N/A')}")
            print(f"    🔄 Status: {data.get('status', 'Unknown')}")
            print(f"    ⚡ Timestamp: {data.get('timestamp', 'N/A')[:19]}")
        else:
            print(f"    ❌ FAIL - {comprehensive_result.get('error')}")
        
        # Test market pulse
        print("  Testing: Market Pulse")
        pulse_result = self.make_request("GET", "/ai/market-pulse")
        
        if pulse_result["success"]:
            pulse_data = pulse_result["data"]["data"]
            print(f"    ✅ PASS")
            print(f"    💓 Market Trend: {pulse_data.get('market_trend', 'N/A')}")
            print(f"    📊 Overall Sentiment: {pulse_data.get('overall_sentiment', 0):.3f}")
            print(f"    🎯 Buy Signals: {pulse_data.get('signals_summary', {}).get('buy_signals', 0)}")
        else:
            print(f"    ❌ FAIL - {pulse_result.get('error')}")
        
        # Test opportunities
        print("  Testing: Trading Opportunities")
        opportunities_result = self.make_request("GET", "/ai/trading-opportunities")
        
        if opportunities_result["success"]:
            opp_data = opportunities_result["data"]
            print(f"    ✅ PASS")
            print(f"    💰 Opportunities Found: {opp_data.get('total_opportunities', 0)}")
            print(f"    📊 Min Confidence Filter: {opp_data.get('min_confidence_filter', 0):.2f}")
            
            # Show top opportunity if available
            top_opps = opp_data.get('opportunities', [])
            if top_opps:
                top_opp = top_opps[0]
                print(f"    🔥 Top Opportunity: {top_opp.get('symbol')} - {top_opp.get('action')} ({top_opp.get('confidence', 0):.2f} confidence)")
        else:
            print(f"    ❌ FAIL - {opportunities_result.get('error')}")
        
        # Test single symbol analysis
        print("  Testing: Single Symbol Analysis")
        symbol_result = self.make_request("POST", "/ai/analyze-symbol", {"symbol": "NSE_EQ|INE002A01018", "analysis_depth": "detailed"})
        
        if symbol_result["success"]:
            symbol_data = symbol_result["data"]
            analysis = symbol_data.get("analysis", {})
            recommendation = analysis.get("recommendation", {})
            print(f"    ✅ PASS")
            print(f"    📈 RELIANCE Analysis Complete")
            print(f"    🎯 Recommendation: {recommendation.get('action', 'N/A')}")
            print(f"    📊 Confidence: {recommendation.get('confidence', 0):.2f}")
            print(f"    💭 Reasoning: {recommendation.get('reasoning', 'N/A')[:50]}...")
        else:
            print(f"    ❌ FAIL - {symbol_result.get('error')}")
        
        results = [
            {"test": "Comprehensive Analysis", "success": comprehensive_result["success"]},
            {"test": "Market Pulse", "success": pulse_result["success"]},
            {"test": "Trading Opportunities", "success": opportunities_result["success"]},
            {"test": "Single Symbol", "success": symbol_result["success"]}
        ]
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        print(f"\n📊 AI Analysis Results: {success_rate:.1%} pass rate")
        
        return {"tests": results, "success_rate": success_rate}
    
    def test_chatbot_integration(self) -> Dict[str, Any]:
        """Test enhanced chatbot with trading commands"""
        
        print("\n🤖 Testing Enhanced Chatbot...")
        print("=" * 50)
        
        test_commands = [
            "help",
            "analyze NIFTY",
            "show portfolio",
            "scan market for opportunities",
            "integrate broker",
            "start trading with 50000 capital"
        ]
        
        results = []
        
        for command in test_commands:
            print(f"  Testing: '{command}'")
            result = self.make_request(
                "POST",
                "/api/chatbot/chat",
                {
                    "message": command,
                    "user_id": "test_ai_system"
                }
            )
            
            if result["success"]:
                data = result["data"]
                print(f"    ✅ PASS")
                print(f"    💬 Response: {data.get('message', 'No message')[:60]}...")
                print(f"    🔄 Type: {data.get('type', 'unknown')}")
            else:
                print(f"    ❌ FAIL - {result.get('error')}")
            
            results.append({
                "command": command,
                "success": result["success"],
                "details": result
            })
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        print(f"\n📊 Chatbot Results: {success_rate:.1%} pass rate")
        
        return {"tests": results, "success_rate": success_rate}
    
    def test_real_time_performance(self) -> Dict[str, Any]:
        """Test real-time performance and response times"""
        
        print("\n⚡ Testing Real-time Performance...")
        print("=" * 50)
        
        # Test response times for key endpoints
        performance_tests = [
            {"name": "Market Data", "endpoint": "/dhan/market-data/NSE_IDX|Nifty 50", "method": "GET"},
            {"name": "AI Analysis", "endpoint": "/ai/market-pulse", "method": "GET"},
            {"name": "Chatbot Response", "endpoint": "/api/chatbot/chat", "method": "POST", 
             "data": {"message": "help", "user_id": "perf_test"}}
        ]
        
        results = []
        
        for test in performance_tests:
            print(f"  Testing: {test['name']}")
            
            start_time = time.time()
            result = self.make_request(test["method"], test["endpoint"], test.get("data"))
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if result["success"]:
                print(f"    ✅ PASS - Response time: {response_time:.0f}ms")
            else:
                print(f"    ❌ FAIL - Response time: {response_time:.0f}ms")
            
            results.append({
                "test": test["name"],
                "success": result["success"],
                "response_time_ms": response_time
            })
        
        avg_response_time = sum(r["response_time_ms"] for r in results) / len(results)
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        print(f"\n📊 Performance Results:")
        print(f"    ⚡ Average Response Time: {avg_response_time:.0f}ms")
        print(f"    ✅ Success Rate: {success_rate:.1%}")
        
        return {"tests": results, "avg_response_time": avg_response_time, "success_rate": success_rate}
    
    def run_comprehensive_test(self):
        """Run all test suites"""
        
        print("🚀 InfinityAI.Pro - Real-time AI Trading System Test Suite")
        print("=" * 70)
        print(f"🕒 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 API Base URL: {self.base_url}")
        print(f"🖥️  Frontend URL: {FRONTEND_URL}")
        
        # Run all test suites
        health_results = self.test_system_health()
        dhan_results = self.test_dhan_integration()
        ai_results = self.test_ai_analysis_engine()
        chatbot_results = self.test_chatbot_integration()
        performance_results = self.test_real_time_performance()
        
        # Overall summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        all_success_rates = [
            ("System Health", health_results["success_rate"]),
            ("Dhan Integration", dhan_results["success_rate"]),
            ("AI Analysis", ai_results["success_rate"]),
            ("Chatbot", chatbot_results["success_rate"]),
            ("Performance", performance_results["success_rate"])
        ]
        
        for test_name, success_rate in all_success_rates:
            status = "✅ EXCELLENT" if success_rate >= 0.8 else "⚠️ NEEDS ATTENTION" if success_rate >= 0.5 else "❌ CRITICAL"
            print(f"  {test_name:<20} {success_rate:>6.1%} {status}")
        
        overall_success = sum(rate for _, rate in all_success_rates) / len(all_success_rates)
        
        print(f"\n🎯 OVERALL SYSTEM HEALTH: {overall_success:.1%}")
        
        if overall_success >= 0.8:
            status_msg = "🎉 EXCELLENT - System is production ready!"
        elif overall_success >= 0.6:
            status_msg = "⚠️ GOOD - Minor issues to address"
        else:
            status_msg = "🚨 ATTENTION NEEDED - Critical issues found"
        
        print(f"📈 STATUS: {status_msg}")
        
        print(f"\n🔧 Key Features Status:")
        features = [
            "✅ Real-time Market Data Integration" if dhan_results["success_rate"] > 0.5 else "❌ Market Data Issues",
            "✅ AI-Powered Analysis Engine" if ai_results["success_rate"] > 0.7 else "❌ AI Engine Issues", 
            "✅ Enhanced Trading Chatbot" if chatbot_results["success_rate"] > 0.7 else "❌ Chatbot Issues",
            f"✅ Average Response Time: {performance_results['avg_response_time']:.0f}ms" if performance_results['avg_response_time'] < 3000 else "❌ Slow Response Times"
        ]
        
        for feature in features:
            print(f"   {feature}")
        
        print(f"\n🔗 Next Steps:")
        if overall_success >= 0.8:
            print("   1. ✅ Deploy Enhanced React Dashboard")  
            print("   2. ✅ Complete Dhan OAuth Flow Setup")
            print("   3. ✅ Test Live Trading Functionality")
            print("   4. ✅ Launch Production System")
        else:
            print("   1. 🔧 Address failing test cases")
            print("   2. 🔧 Improve system reliability") 
            print("   3. 🔧 Optimize performance issues")
            print("   4. ⚠️ Re-run tests before deployment")
        
        print(f"\n🎊 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            "overall_success_rate": overall_success,
            "individual_results": dict(all_success_rates),
            "avg_response_time": performance_results["avg_response_time"],
            "status": status_msg
        }

def main():
    """Run the comprehensive test suite"""
    
    tester = InfinityAITester()
    results = tester.run_comprehensive_test()
    
    return results

if __name__ == "__main__":
    main()