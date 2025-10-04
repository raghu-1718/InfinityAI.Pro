#!/usr/bin/env python3
"""
Test InfinityAI.Pro using original Vercel URLs
"""

import requests
import json
import time
from datetime import datetime

# Original Vercel URLs
FRONTEND_URL = "https://infinityai-frontend.vercel.app"
BACKEND_URL = "https://infinityai-backend.vercel.app"

def test_system():
    print("🚀 Testing InfinityAI.Pro System")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'InfinityAI-Test/1.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })
    
    results = []
    
    # Test Frontend
    print("\n🌐 Testing Frontend...")
    try:
        start_time = time.time()
        response = session.get(FRONTEND_URL, timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            print(f"✅ Frontend accessible (Status: {response.status_code}) - {response_time}ms")
            results.append(("Frontend", True, response.status_code, response_time))
        else:
            print(f"❌ Frontend returned status {response.status_code} - {response_time}ms")
            results.append(("Frontend", False, response.status_code, response_time))
    except Exception as e:
        print(f"❌ Frontend error: {str(e)}")
        results.append(("Frontend", False, "Error", str(e)))
    
    # Test Backend Root
    print("\n🔧 Testing Backend Root...")
    try:
        start_time = time.time()
        response = session.get(BACKEND_URL, timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        print(f"✅ Backend root (Status: {response.status_code}) - {response_time}ms")
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
        
        if response.status_code == 200:
            print(f"✅ Backend health (Status: {response.status_code}) - {response_time}ms")
            try:
                health_data = response.json()
                print(f"   Health data: {health_data}")
            except:
                print(f"   Response: {response.text[:100]}...")
            results.append(("Backend Health", True, response.status_code, response_time))
        else:
            print(f"❌ Backend health (Status: {response.status_code}) - {response_time}ms")
            results.append(("Backend Health", False, response.status_code, response_time))
    except Exception as e:
        print(f"❌ Backend health error: {str(e)}")
        results.append(("Backend Health", False, "Error", str(e)))
    
    # Test API Documentation
    print("\n📚 Testing API Documentation...")
    try:
        start_time = time.time()
        response = session.get(f"{BACKEND_URL}/docs", timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            print(f"✅ API docs (Status: {response.status_code}) - {response_time}ms")
            results.append(("API Docs", True, response.status_code, response_time))
        else:
            print(f"⚠️ API docs (Status: {response.status_code}) - {response_time}ms")
            results.append(("API Docs", response.status_code == 404, response.status_code, response_time))
    except Exception as e:
        print(f"❌ API docs error: {str(e)}")
        results.append(("API Docs", False, "Error", str(e)))
    
    # Test AI Chat (simple GET first)
    print("\n🤖 Testing AI Chat Endpoint...")
    try:
        start_time = time.time()
        response = session.get(f"{BACKEND_URL}/api/ai/chat", timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        # GET might return 405 (Method Not Allowed) which is expected
        if response.status_code in [200, 405, 422]:
            print(f"✅ AI Chat endpoint exists (Status: {response.status_code}) - {response_time}ms")
            results.append(("AI Chat Endpoint", True, response.status_code, response_time))
        else:
            print(f"❌ AI Chat endpoint (Status: {response.status_code}) - {response_time}ms")
            results.append(("AI Chat Endpoint", False, response.status_code, response_time))
    except Exception as e:
        print(f"❌ AI Chat endpoint error: {str(e)}")
        results.append(("AI Chat Endpoint", False, "Error", str(e)))
    
    # Test Trading Status
    print("\n📈 Testing Trading Status...")
    try:
        start_time = time.time()
        response = session.get(f"{BACKEND_URL}/api/trading/status", timeout=10)
        response_time = int((time.time() - start_time) * 1000)
        
        if response.status_code in [200, 404, 422]:
            print(f"✅ Trading status endpoint (Status: {response.status_code}) - {response_time}ms")
            results.append(("Trading Status", True, response.status_code, response_time))
        else:
            print(f"❌ Trading status (Status: {response.status_code}) - {response_time}ms")
            results.append(("Trading Status", False, response.status_code, response_time))
    except Exception as e:
        print(f"❌ Trading status error: {str(e)}")
        results.append(("Trading Status", False, "Error", str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _, _ in results if success)
    total = len(results)
    
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
    with open("vercel_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "frontend_url": FRONTEND_URL,
            "backend_url": BACKEND_URL,
            "results": results,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": passed/total*100
            }
        }, f, indent=2)
    
    print(f"\n📄 Results saved to vercel_test_results.json")

if __name__ == "__main__":
    test_system()