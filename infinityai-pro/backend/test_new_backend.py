#!/usr/bin/env python3
"""
Test new backend deployment
"""

import requests
import json
import time
from datetime import datetime

# New deployment URL
BACKEND_URL = "https://infinity-backend-31890u5wl-infinityaipro.vercel.app"

def test_backend():
    print("🚀 Testing New Backend Deployment")
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
        print(f"   Response: {response.text[:300]}...")
        results.append(("Backend Root", response.status_code in [200, 307], response.status_code, response_time))
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
        if response.status_code == 200:
            try:
                health_data = response.json()
                print(f"   ✅ Health data: {health_data}")
            except:
                print(f"   Response: {response.text}")
        else:
            print(f"   Response: {response.text[:200]}...")
        results.append(("Backend Health", response.status_code == 200, response.status_code, response_time))
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
            print("   ✅ Swagger documentation is working!")
        results.append(("API Docs", response.status_code == 200, response.status_code, response_time))
    except Exception as e:
        print(f"❌ API docs error: {str(e)}")
        results.append(("API Docs", False, "Error", str(e)))
    
    # Test AI Chat with POST
    print("\n🤖 Testing AI Chat with POST...")
    try:
        test_payload = {
            "message": "Hello! This is a test. Please respond briefly to confirm the AI is working.",
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
                print(f"   🤖 AI Response: {str(chat_data)[:300]}...")
                results.append(("AI Chat", True, response.status_code, response_time))
            except:
                print(f"   Response (non-JSON): {response.text[:200]}...")
                results.append(("AI Chat", False, response.status_code, response_time))
        else:
            print(f"   ❌ Error response: {response.text[:200]}...")
            results.append(("AI Chat", False, response.status_code, response_time))
    except Exception as e:
        print(f"❌ AI Chat error: {str(e)}")
        results.append(("AI Chat", False, "Error", str(e)))
    
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
    
    if (passed/total) >= 0.75:
        print("\n✅ SYSTEM STATUS: HEALTHY")
        print("🎉 Backend API is working!")
    elif (passed/total) >= 0.5:
        print("\n⚠️ SYSTEM STATUS: DEGRADED")
    else:
        print("\n❌ SYSTEM STATUS: ISSUES DETECTED")

if __name__ == "__main__":
    test_backend()