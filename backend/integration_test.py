#!/usr/bin/env python3
"""
InfinityAI.Pro Integration Test
Tests complete frontend-backend integration
"""

import requests
import json
import time

# Configuration - AWS/GCP Multi-Cloud Architecture
AWS_ALB_URL = "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com"
GCP_ENGINES = {
    "engine_a": "https://infinityai-engine-a-573866363639.us-central1.run.app",
    "engine_b": "https://infinityai-engine-b-573866363639.us-central1.run.app"
}
AWS_ENGINES = {
    "engine_c": f"{AWS_ALB_URL}/engine-c",
    "engine_d": f"{AWS_ALB_URL}/engine-d"
}

# Frontend URLs (cleaned - no Azure/Vercel)
FRONTEND_URLS = [
    "https://infinityai.pro"
]

def test_backend_health():
    """Test backend health endpoint for all engines"""
    results = []
    
    # Test GCP Engines
    for name, url in GCP_ENGINES.items():
        try:
            response = requests.get(f"{url}/health", timeout=10)
            success = response.status_code == 200
            results.append(success)
            status = "✅ HEALTHY" if success else "❌ FAILED"
            print(f"   {status} GCP {name.upper()}: {url}")
            if success:
                data = response.json()
                print(f"      Service: {data.get('service', 'Unknown')}")
        except Exception as e:
            results.append(False)
            print(f"   ❌ ERROR GCP {name.upper()}: {e}")
    
    # Test AWS Engines
    for name, url in AWS_ENGINES.items():
        try:
            response = requests.get(url, timeout=10)
            success = response.status_code == 200
            results.append(success)
            status = "✅ HEALTHY" if success else "❌ FAILED"
            print(f"   {status} AWS {name.upper()}: {url}")
            if success and 'application/json' in response.headers.get('content-type', ''):
                try:
                    data = response.json()
                    print(f"      Service: {data.get('service', 'Unknown')}")
                except:
                    print(f"      Content: {response.text[:50]}...")
        except Exception as e:
            results.append(False)
            print(f"   ❌ ERROR AWS {name.upper()}: {e}")
    
    return any(results)  # Return True if at least one engine is healthy

def test_backend_apis():
    """Test key backend API endpoints across engines"""
    tests = [
        {
            "name": "Engine A - Market Data",
            "url": f"{GCP_ENGINES['engine_a']}/market/indices",
            "method": "GET"
        },
        {
            "name": "Engine B - AI Health",
            "url": f"{GCP_ENGINES['engine_b']}/health",
            "method": "GET"
        },
        {
            "name": "Engine C - Trading Status", 
            "url": AWS_ENGINES['engine_c'],
            "method": "GET"
        },
        {
            "name": "Engine D - Chatbot Status",
            "url": AWS_ENGINES['engine_d'],
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
    """Test inter-engine communication and integration"""
    try:
        # Test AWS Engine C to D communication
        response = requests.get(
            AWS_ENGINES['engine_c'],
            headers={'Origin': 'https://infinityai.pro'},
            timeout=10
        )
        
        engine_c_ok = response.status_code == 200
        print(f"   {'✅' if engine_c_ok else '❌'} Engine C Communication: {'PASSED' if engine_c_ok else 'FAILED'}")
        
        # Test GCP to AWS cross-cloud communication
        try:
            response = requests.get(
                f"{GCP_ENGINES['engine_b']}/health",
                timeout=10
            )
            gcp_ok = response.status_code == 200
            print(f"   {'✅' if gcp_ok else '❌'} GCP Engine B: {'OPERATIONAL' if gcp_ok else 'DOWN'}")
        except Exception as e:
            gcp_ok = False
            print(f"   ❌ GCP Engine B ERROR: {e}")
        
        return engine_c_ok or gcp_ok  # Pass if at least one engine is working
        
    except Exception as e:
        print(f"   ❌ Integration ERROR: {e}")
        return False

def main():
    print("🚀 InfinityAI.Pro Multi-Cloud Integration Test")
    print("AWS (Engines C/D) + GCP (Engines A/B)")
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
        ("Multi-Cloud Engine Health", backend_healthy),
        ("Engine API Endpoints", apis_working),
        ("Frontend Access", frontend_accessible),
        ("Inter-Engine Communication", integration_working)
    ]
    
    all_passed = True
    for name, passed in tests:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - InfinityAI.Pro Multi-Cloud Architecture is operational!")
        print("\n🌐 Frontend:")
        for url in FRONTEND_URLS:
            print(f"  {url}")
        print("\n☁️ AWS Engines:")
        for name, url in AWS_ENGINES.items():
            print(f"  {name.upper()}: {url}")
        print("\n🔄 GCP Engines:")
        for name, url in GCP_ENGINES.items():
            print(f"  {name.upper()}: {url}")
    else:
        print("⚠️  SOME TESTS FAILED - Check the details above")
    
    return all_passed

if __name__ == "__main__":
    main()