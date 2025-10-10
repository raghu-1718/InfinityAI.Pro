# 🎯 Dhan Sandbox Integration Test Script

import requests
import json
import time
from datetime import datetime

# Your Application URLs
BASE_URL = "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d"
DHAN_CLIENT_ID = "2508215064"

# Test endpoints
ENDPOINTS = {
    "health": f"{BASE_URL}/health",
    "dashboard": f"{BASE_URL}/dashboard",
    "api_docs": f"{BASE_URL}/docs",
    "dhan_webhook": f"{BASE_URL}/api/webhooks/dhan",
    "trading_webhook": f"{BASE_URL}/api/webhooks/trading",
    "market_data": f"{BASE_URL}/api/market-data/nifty",
    "portfolio": f"{BASE_URL}/api/portfolio/holdings"
}

def test_endpoint(name, url, method="GET", data=None):
    """Test an endpoint and return results"""
    try:
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
            
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS: {name} is working!")
            try:
                content = response.json()
                print(f"Response: {json.dumps(content, indent=2)}")
            except:
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ FAILED: {name} returned {response.status_code}")
            print(f"Error: {response.text[:200]}...")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ ERROR: {name} failed with exception: {str(e)}")
        return False

def main():
    print("🚀 INFINITYAI.PRO DHAN SANDBOX INTEGRATION TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Dhan Client ID: {DHAN_CLIENT_ID}")
    
    results = {}
    
    # Test 1: Health Check
    results["health"] = test_endpoint("Health Check", ENDPOINTS["health"])
    
    # Test 2: Dashboard Access
    results["dashboard"] = test_endpoint("Dashboard", ENDPOINTS["dashboard"])
    
    # Test 3: API Documentation
    results["api_docs"] = test_endpoint("API Documentation", ENDPOINTS["api_docs"])
    
    # Test 4: Dhan Webhook Test
    webhook_data = {
        "client_id": DHAN_CLIENT_ID,
        "action": "test_connection",
        "timestamp": datetime.now().isoformat()
    }
    results["dhan_webhook"] = test_endpoint(
        "Dhan Webhook", 
        ENDPOINTS["dhan_webhook"], 
        "POST", 
        webhook_data
    )
    
    # Test 5: Trading Webhook Test
    trading_data = {
        "symbol": "NIFTY",
        "action": "BUY",
        "quantity": 1,
        "price": "market",
        "client_id": DHAN_CLIENT_ID
    }
    results["trading_webhook"] = test_endpoint(
        "Trading Webhook", 
        ENDPOINTS["trading_webhook"], 
        "POST", 
        trading_data
    )
    
    # Test 6: Market Data
    results["market_data"] = test_endpoint("Market Data", ENDPOINTS["market_data"])
    
    # Test 7: Portfolio Holdings
    results["portfolio"] = test_endpoint("Portfolio Holdings", ENDPOINTS["portfolio"])
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your Dhan Sandbox integration is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    # Recommendations
    print("\n🔧 NEXT STEPS:")
    if results["health"]:
        print("✅ Your application is healthy and running")
    if results["dashboard"]:
        print("✅ Dashboard is accessible - you can start trading!")
    if results["dhan_webhook"]:
        print("✅ Dhan webhooks are working - live data integration ready")
    
    print(f"\n🌐 Access your app: {BASE_URL}")
    print("🗣️ Try voice commands: 'Start momentum trading on NIFTY'")

if __name__ == "__main__":
    main()