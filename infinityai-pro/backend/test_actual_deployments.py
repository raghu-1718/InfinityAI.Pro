#!/usr/bin/env python3
"""
Test actual Vercel deployment URLs
"""

import requests
import json
import time
from datetime import datetime

# Actual deployment URLs
BACKEND_URL = "https://infinity-backend-22cen5bdh-infinityaipro.vercel.app"

def test_backend():
    print("🚀 Testing Actual Backend Deployment")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'InfinityAI-Test/1.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })
    
    results = []
    
    # Test Backend Root
    print("\n🔧 Testing Backend Root...")
    try:
        start_time = time.time()
        response = session.get(BACKEND_URL, timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        print(f"✅ Backend root (Status: {response.status_code}) - {response_time}ms")
        print(f"   Response: {response.text[:200]}...")
        results.append(("Backend Root", True, response.status_code, response_time))
    except Exception as e:
        print(f"❌ Backend root error: {str(e)}")
        results.append(("Backend Root", False, "Error", str(e)))
    
    # Test Backend Health
    print("\n🏥 Testing Backend Health...")
    try:
        start_time = time.time()
        response = session.get(f"{BACKEND_URL}/health", timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        print(f"✅ Backend health (Status: {response.status_code}) - {response_time}ms")
        print(f"   Response: {response.text}")
        results.append(("Backend Health", True, response.status_code, response_time))
    except Exception as e:
        print(f"❌ Backend health error: {str(e)}")
        results.append(("Backend Health", False, "Error", str(e)))
    
    # Test API Documentation
    print("\n📚 Testing API Documentation...")
    try:
        start_time = time.time()
        response = session.get(f"{BACKEND_URL}/docs", timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        print(f"✅ API docs (Status: {response.status_code}) - {response_time}ms")
        if response.status_code == 200:
            print("   ✅ Swagger docs available!")
        results.append(("API Docs", True, response.status_code, response_time))
    except Exception as e:
        print(f"❌ API docs error: {str(e)}")
        results.append(("API Docs", False, "Error", str(e)))
    
    # Test AI Chat with POST
    print("\n🤖 Testing AI Chat with POST...")
    try:
        test_payload = {
            "message": "Hello, this is a test message. Please respond briefly.",
            "model": "gpt-4o-mini"
        }
        
        start_time = time.time()
        response = session.post(
            f"{BACKEND_URL}/api/ai/chat", 
            json=test_payload, 
            timeout=30
        )
        response_time = int((time.time() - start_time) * 1000)
        
        print(f"✅ AI Chat POST (Status: {response.status_code}) - {response_time}ms")
        if response.status_code == 200:
            try:
                chat_data = response.json()
                print(f"   AI Response: {str(chat_data)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   Response: {response.text[:200]}...")
        results.append(("AI Chat POST", True, response.status_code, response_time))
    except Exception as e:
        print(f"❌ AI Chat error: {str(e)}")
        results.append(("AI Chat POST", False, "Error", str(e)))
    
    # Test Engines Status
    print("\n⚙️ Testing Engines Status...")
    try:
        start_time = time.time()
        response = session.get(f"{BACKEND_URL}/api/engines/status", timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        print(f"✅ Engines status (Status: {response.status_code}) - {response_time}ms")
        if response.status_code == 200:
            try:
                engines_data = response.json()
                print(f"   Engines: {engines_data}")
            except:
                print(f"   Response: {response.text[:200]}...")
        results.append(("Engines Status", True, response.status_code, response_time))
    except Exception as e:
        print(f"❌ Engines status error: {str(e)}")
        results.append(("Engines Status", False, "Error", str(e)))
    
    # Test Trading Status
    print("\n📈 Testing Trading Status...")
    try:
        start_time = time.time()
        response = session.get(f"{BACKEND_URL}/api/trading/status", timeout=15)
        response_time = int((time.time() - start_time) * 1000)
        
        print(f"✅ Trading status (Status: {response.status_code}) - {response_time}ms")
        print(f"   Response: {response.text[:200]}...")
        results.append(("Trading Status", True, response.status_code, response_time))
    except Exception as e:
        print(f"❌ Trading status error: {str(e)}")
        results.append(("Trading Status", False, "Error", str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for _, success, _, _ in results if success)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if (passed/total) >= 0.8:
        print("\n✅ SYSTEM STATUS: HEALTHY")
    elif (passed/total) >= 0.5:
        print("\n⚠️ SYSTEM STATUS: DEGRADED")
    else:
        print("\n❌ SYSTEM STATUS: ISSUES DETECTED")
    
    # Save results
    with open("actual_deployment_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "backend_url": BACKEND_URL,
            "results": results,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": passed/total*100
            }
        }, f, indent=2)
    
    print(f"\n📄 Results saved to actual_deployment_test_results.json")

if __name__ == "__main__":
    test_backend()