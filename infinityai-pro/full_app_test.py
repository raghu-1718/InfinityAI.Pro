#!/usr/bin/env python3
"""
InfinityAI.Pro Full Application Test
Tests all features and functionality
"""

import requests
import json
import time
import random

BACKEND_URL = "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io"

def test_trading_chatbot():
    """Test comprehensive trading chatbot functionality"""
    print("🤖 Testing Trading Chatbot...")
    
    test_commands = [
        {
            "command": "Scan NIFTY with 5 lakh capital using momentum strategy",
            "expected_keywords": ["scan", "nifty", "analysis", "price", "trend"]
        },
        {
            "command": "Start automated trading BANKNIFTY with 2 lakh",
            "expected_keywords": ["trading", "session", "setup", "broker", "capital"]
        },
        {
            "command": "Stop all trading activities",
            "expected_keywords": ["stop", "trading", "session", "summary", "p&l"]
        },
        {
            "command": "Analyze RELIANCE for swing trading",
            "expected_keywords": ["understand", "analysis", "trading", "strategy"]
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_commands, 1):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/chatbot/chat",
                json={
                    "message": test["command"],
                    "user_id": f"test_user_{i}",
                    "voice_input": False
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get("data", {}).get("response", "").lower()
                
                # Check if response contains expected keywords
                keyword_matches = sum(1 for keyword in test["expected_keywords"] 
                                    if keyword.lower() in bot_response)
                
                success = keyword_matches >= 2  # At least 2 keywords should match
                
                print(f"   {'✅' if success else '❌'} Command {i}: {test['command'][:50]}...")
                print(f"      Response: {data.get('data', {}).get('response', '')[:80]}...")
                print(f"      Keywords matched: {keyword_matches}/{len(test['expected_keywords'])}")
                
                if success:
                    success_count += 1
            else:
                print(f"   ❌ Command {i}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Command {i}: Error - {e}")
    
    overall_success = success_count >= 3
    print(f"\n   {'🎉' if overall_success else '⚠️'} Chatbot Test: {success_count}/{len(test_commands)} commands successful")
    return overall_success

def test_market_data_apis():
    """Test market data functionality"""
    print("\n📈 Testing Market Data APIs...")
    
    endpoints = [
        ("Market Indices", "/api/market/indices"),
        ("NIFTY Quote", "/api/market/quote/NIFTY"),
        ("NIFTY Historical", "/api/market/historical/NIFTY?limit=10"),
        ("NIFTY News", "/api/market/news/NIFTY?limit=5")
    ]
    
    success_count = 0
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_data = bool(data and (isinstance(data, dict) or isinstance(data, list)))
                
                print(f"   {'✅' if has_data else '⚠️'} {name}: {'Data received' if has_data else 'Empty response'}")
                
                if has_data:
                    success_count += 1
            else:
                print(f"   ❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    overall_success = success_count >= 2
    print(f"\n   {'🎉' if overall_success else '⚠️'} Market Data Test: {success_count}/{len(endpoints)} endpoints successful")
    return overall_success

def test_advanced_analysis():
    """Test advanced AI analysis features"""
    print("\n🧠 Testing Advanced AI Analysis...")
    
    # Test advanced analysis endpoint
    try:
        test_request = {
            "symbol": "NIFTY",
            "timeframe": "1D",
            "analysis_type": "comprehensive",
            "include_sentiment": True,
            "include_technical": True,
            "include_fundamental": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/advanced-analysis",
            json=test_request,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for key analysis components
            has_analysis = bool(data.get("analysis"))
            has_confidence = "confidence" in str(data).lower()
            has_recommendations = "recommendation" in str(data).lower()
            
            success = has_analysis and (has_confidence or has_recommendations)
            
            print(f"   {'✅' if success else '❌'} Advanced Analysis: {'Comprehensive results' if success else 'Limited results'}")
            print(f"      Analysis data: {has_analysis}")
            print(f"      Confidence scores: {has_confidence}")
            print(f"      Recommendations: {has_recommendations}")
            
            return success
            
        else:
            print(f"   ❌ Advanced Analysis: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Advanced Analysis: Error - {e}")
        return False

def test_dual_engine_system():
    """Test dual engine analysis system"""
    print("\n⚡ Testing Dual Engine System...")
    
    try:
        # Test dual engine analysis
        test_request = {
            "symbol": "BANKNIFTY",
            "strategy_type": "momentum",
            "timeframe": "15m",
            "capital": 200000,
            "risk_level": "medium"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/dual-engine/analyze",
            json=test_request,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            has_dual_analysis = bool(data.get("dual_engine_result"))
            has_strategy_config = bool(data.get("strategy_configuration"))
            has_performance_metrics = bool(data.get("performance_metrics"))
            
            success = has_dual_analysis or has_strategy_config
            
            print(f"   {'✅' if success else '❌'} Dual Engine Analysis: {'Working' if success else 'Issues'}")
            print(f"      Dual engine result: {has_dual_analysis}")
            print(f"      Strategy config: {has_strategy_config}")
            print(f"      Performance metrics: {has_performance_metrics}")
            
            return success
            
        else:
            print(f"   ❌ Dual Engine: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Dual Engine: Error - {e}")
        return False

def test_ultra_ai_system():
    """Test Ultra AI system with 99.8% accuracy claim"""
    print("\n🚀 Testing Ultra AI System...")
    
    try:
        test_request = {
            "symbol": "NIFTY",
            "analysis_depth": "ultra_deep",
            "use_quantum_enhancement": True,
            "target_accuracy": 99.8,
            "include_all_models": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/ultra-ai/ultra-analyze",
            json=test_request,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            
            has_ultra_analysis = bool(data.get("ultra_analysis"))
            has_accuracy_score = "accuracy" in str(data).lower()
            has_quantum_enhancement = "quantum" in str(data).lower()
            
            success = has_ultra_analysis and has_accuracy_score
            
            print(f"   {'✅' if success else '❌'} Ultra AI Analysis: {'Operational' if success else 'Limited'}")
            print(f"      Ultra analysis: {has_ultra_analysis}")
            print(f"      Accuracy metrics: {has_accuracy_score}")
            print(f"      Quantum enhancement: {has_quantum_enhancement}")
            
            return success
            
        else:
            print(f"   ❌ Ultra AI: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ultra AI: Error - {e}")
        return False

def test_system_health():
    """Test overall system health and performance"""
    print("\n💗 Testing System Health...")
    
    health_checks = [
        ("Basic Health", "/health"),
        ("Detailed Health", "/api/health/detailed"),
        ("Broker Status", "/api/health/broker-status"),
        ("GPU Models Status", "/api/dual-engine/gpu-models-status"),
        ("Ultra Models Status", "/api/ultra-ai/ultra-models-status")
    ]
    
    success_count = 0
    
    for name, endpoint in health_checks:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                operational = "operational" in str(data).lower() or "healthy" in str(data).lower()
                success = success and operational
            
            print(f"   {'✅' if success else '❌'} {name}: {'Healthy' if success else 'Issues detected'}")
            
            if success:
                success_count += 1
                
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    overall_health = success_count >= 3
    print(f"\n   {'💚' if overall_health else '🔸'} System Health: {success_count}/{len(health_checks)} checks passed")
    return overall_health

def main():
    print("🎯 InfinityAI.Pro - Full Application Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Trading Chatbot", test_trading_chatbot),
        ("Market Data APIs", test_market_data_apis),
        ("Advanced AI Analysis", test_advanced_analysis),
        ("Dual Engine System", test_dual_engine_system),
        ("Ultra AI System", test_ultra_ai_system),
        ("System Health", test_system_health)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name}: Critical Error - {e}")
            results.append((test_name, False))
    
    # Final Summary
    print("\n" + "=" * 60)
    print("📊 FULL APPLICATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("🎉 EXCELLENT! All functionality tests PASSED")
        print("   InfinityAI.Pro is fully operational and ready for production!")
    elif passed >= total * 0.8:
        print("🎯 GREAT! Most functionality tests PASSED")
        print(f"   {passed}/{total} features working correctly")
    elif passed >= total * 0.6:
        print("⚠️  GOOD! Core functionality is working")
        print(f"   {passed}/{total} features operational, some need attention")
    else:
        print("🔧 NEEDS ATTENTION! Several issues detected")
        print(f"   Only {passed}/{total} features working properly")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    main()