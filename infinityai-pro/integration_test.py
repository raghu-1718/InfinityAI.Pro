#!/usr/bin/env python3
"""
InfinityAI.Pro Integration Test
Tests complete frontend-backend integration
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io"
FRONTEND_URLS = [
    "https://infinity-ai-9utba60h7-infinityaipro.vercel.app",
    "https://infinityai.pro"
]

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend Health: HEALTHY")
            print(f"   Platform: {data.get('platform')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Services: {', '.join(data.get('services', {}).keys())}")
            return True
        else:
            print(f"❌ Backend Health: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Backend Health: ERROR - {e}")
        return False

def test_backend_apis():
    """Test key backend API endpoints"""
    tests = [
        {
            "name": "Chatbot Status",
            "url": f"{BACKEND_URL}/api/chatbot/chatbot-status",
            "method": "GET"
        },
        {
            "name": "Chatbot Chat",
            "url": f"{BACKEND_URL}/api/chatbot/chat",
            "method": "POST",
            "data": {
                "message": "Hello InfinityAI",
                "user_id": "integration_test",
                "voice_input": False
            }
        },
        {
            "name": "Market Indices",
            "url": f"{BACKEND_URL}/api/market/indices",
            "method": "GET"
        }
    ]
    
    results = []
    
    for test in tests:
        try:
            if test["method"] == "GET":
                response = requests.get(test["url"], timeout=10)
            else:
                response = requests.post(test["url"], json=test.get("data"), timeout=10)
            
            success = response.status_code in [200, 201]
            results.append(success)
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {status} {test['name']} ({response.status_code})")
            
            if success and "chatbot/chat" in test["url"]:
                data = response.json()
                print(f"      Response preview: {data.get('data', {}).get('response', '')[:50]}...")
                
        except Exception as e:
            results.append(False)
            print(f"   ❌ ERROR {test['name']}: {e}")
    
    return all(results)

def test_frontend_accessibility():
    """Test frontend accessibility"""
    for url in FRONTEND_URLS:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                has_title = "InfinityAI" in response.text
                has_react = "react" in response.text.lower()
                
                status = "✅ ACCESSIBLE" if has_title else "⚠️ ACCESSIBLE (No Title)"
                print(f"   {status} {url}")
                print(f"      Title found: {has_title}")
                print(f"      React app: {has_react}")
                
                if has_title:
                    return True
            else:
                print(f"   ❌ FAILED {url} ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ ERROR {url}: {e}")
    
    return False

def test_cors_integration():
    """Test CORS and integration between frontend and backend"""
    try:
        # Test CORS preflight
        response = requests.options(
            f"{BACKEND_URL}/api/chatbot/chat",
            headers={
                'Origin': 'https://infinityai.pro',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=10
        )
        
        cors_ok = response.status_code in [200, 204]
        print(f"   {'✅' if cors_ok else '❌'} CORS Preflight: {'PASSED' if cors_ok else 'FAILED'}")
        
        # Test actual API call with origin header
        response = requests.post(
            f"{BACKEND_URL}/api/chatbot/chat",
            json={
                "message": "Integration test from frontend",
                "user_id": "cors_test",
                "voice_input": False
            },
            headers={'Origin': 'https://infinityai.pro'},
            timeout=10
        )
        
        api_ok = response.status_code == 200
        print(f"   {'✅' if api_ok else '❌'} API with Origin: {'PASSED' if api_ok else 'FAILED'}")
        
        return cors_ok and api_ok
        
    except Exception as e:
        print(f"   ❌ CORS Integration ERROR: {e}")
        return False

def main():
    print("🚀 InfinityAI.Pro Integration Test")
    print("=" * 50)
    
    # Test backend
    print("\n1. Backend Health Check")
    backend_healthy = test_backend_health()
    
    print("\n2. Backend API Tests")
    apis_working = test_backend_apis()
    
    print("\n3. Frontend Accessibility")
    frontend_accessible = test_frontend_accessibility()
    
    print("\n4. CORS & Integration")
    integration_working = test_cors_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Backend Health", backend_healthy),
        ("Backend APIs", apis_working),
        ("Frontend Access", frontend_accessible),
        ("CORS Integration", integration_working)
    ]
    
    all_passed = True
    for name, passed in tests:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - InfinityAI.Pro is fully integrated!")
        print("\nYour application is ready at:")
        for url in FRONTEND_URLS:
            print(f"  🌐 {url}")
        print(f"\nBackend API: {BACKEND_URL}")
    else:
        print("⚠️  SOME TESTS FAILED - Check the details above")
    
    return all_passed

if __name__ == "__main__":
    main()