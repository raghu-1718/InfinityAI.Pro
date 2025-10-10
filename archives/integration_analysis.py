#!/usr/bin/env python3
"""
InfinityAI.Pro Complete Integration Analysis
Tests all deployed engines and provides comprehensive report
"""

import requests
import json
import time
from datetime import datetime
import sys

# Current Live URLs from deployment reports
URLS = {
    "frontend_azure": "https://brave-ocean-09e85cd10-preview.centralus.2.azurestaticapps.net",
    "backend_azure": "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
    "engine_d_vercel": "https://infinity-backend-9z59tyitb-infinityaipro.vercel.app",
    "frontend_vercel": "https://infinityai-pro-frontend-n53xfzqol-infinityaipro.vercel.app",
    "local_backend": "http://localhost:8000"
}

def test_url(name, url, endpoints=None):
    """Test a URL and its endpoints"""
    print(f"\n🔍 Testing {name}: {url}")
    results = []
    
    if endpoints is None:
        endpoints = ["/", "/health"]
    
    for endpoint in endpoints:
        full_url = url + endpoint
        try:
            start_time = time.time()
            response = requests.get(full_url, timeout=10, allow_redirects=True)
            response_time = int((time.time() - start_time) * 1000)
            
            status = "✅" if response.status_code == 200 else "⚠️" if response.status_code in [301, 302, 404] else "❌"
            print(f"  {status} {endpoint}: {response.status_code} ({response_time}ms)")
            
            # Check for specific content
            if response.status_code == 200:
                content = response.text.lower()
                if "infinityai" in content or "trading" in content or "react" in content:
                    print(f"    ✅ Contains relevant content")
                elif endpoint == "/health":
                    try:
                        health_data = response.json()
                        print(f"    ✅ Health data: {health_data}")
                    except:
                        pass
            
            results.append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            })
            
        except requests.exceptions.Timeout:
            print(f"  ⏱️ {endpoint}: TIMEOUT")
            results.append({"endpoint": endpoint, "status_code": "TIMEOUT", "response_time": 10000, "success": False})
        except requests.exceptions.ConnectionError:
            print(f"  🔌 {endpoint}: CONNECTION ERROR")
            results.append({"endpoint": endpoint, "status_code": "CONNECTION_ERROR", "response_time": 0, "success": False})
        except Exception as e:
            print(f"  ❌ {endpoint}: ERROR - {str(e)}")
            results.append({"endpoint": endpoint, "status_code": "ERROR", "response_time": 0, "success": False})
    
    return results

def test_api_endpoints(base_url):
    """Test API endpoints specifically"""
    api_endpoints = [
        "/api/health",
        "/api/v1/health", 
        "/health",
        "/docs",
        "/api/chatbot/chat",
        "/api/trading/status",
        "/api/engines/status"
    ]
    
    print(f"\n🔧 Testing API endpoints for: {base_url}")
    results = []
    
    for endpoint in api_endpoints:
        try:
            full_url = base_url + endpoint
            start_time = time.time()
            
            if "chat" in endpoint:
                # POST request for chat
                response = requests.post(
                    full_url, 
                    json={"message": "test", "user_id": "integration_test"},
                    timeout=10
                )
            else:
                # GET request for others
                response = requests.get(full_url, timeout=10)
            
            response_time = int((time.time() - start_time) * 1000)
            
            status = "✅" if response.status_code == 200 else "⚠️" if response.status_code in [404, 405, 422] else "❌"
            print(f"  {status} {endpoint}: {response.status_code} ({response_time}ms)")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"    📄 Response: {str(data)[:100]}...")
                except:
                    print(f"    📄 Response: {response.text[:100]}...")
            
            results.append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            })
            
        except Exception as e:
            print(f"  ❌ {endpoint}: ERROR - {str(e)}")
            results.append({"endpoint": endpoint, "status_code": "ERROR", "response_time": 0, "success": False})
    
    return results

def analyze_deployment():
    """Complete deployment analysis"""
    print("InfinityAI.Pro Complete Integration Analysis")
    print("=" * 80)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    all_results = {}
    
    # Test Frontend Deployments
    print("\n🌐 FRONTEND DEPLOYMENTS")
    print("-" * 40)
    
    frontend_results = test_url("Azure Static Web App", URLS["frontend_azure"])
    all_results["frontend_azure"] = frontend_results
    
    frontend_vercel_results = test_url("Vercel Frontend", URLS["frontend_vercel"])
    all_results["frontend_vercel"] = frontend_vercel_results
    
    # Test Backend Deployments
    print("\n🔧 BACKEND DEPLOYMENTS")
    print("-" * 40)
    
    backend_azure_results = test_url("Azure Container App", URLS["backend_azure"])
    all_results["backend_azure"] = backend_azure_results
    
    backend_azure_api = test_api_endpoints(URLS["backend_azure"])
    all_results["backend_azure_api"] = backend_azure_api
    
    engine_d_results = test_url("Vercel Engine D", URLS["engine_d_vercel"])
    all_results["engine_d_vercel"] = engine_d_results
    
    engine_d_api = test_api_endpoints(URLS["engine_d_vercel"])
    all_results["engine_d_api"] = engine_d_api
    
    # Test Local Backend
    print("\n🏠 LOCAL BACKEND")
    print("-" * 40)
    
    local_results = test_url("Local Docker Backend", URLS["local_backend"])
    all_results["local_backend"] = local_results
    
    local_api = test_api_endpoints(URLS["local_backend"])
    all_results["local_api"] = local_api
    
    # Generate Summary Report
    print("\n" + "=" * 80)
    print("📊 INTEGRATION ANALYSIS SUMMARY")
    print("=" * 80)
    
    total_tests = 0
    successful_tests = 0
    
    for service, results in all_results.items():
        if isinstance(results, list):
            service_total = len(results)
            service_success = sum(1 for r in results if r.get("success", False))
            total_tests += service_total
            successful_tests += service_success
            
            success_rate = (service_success / service_total * 100) if service_total > 0 else 0
            status = "✅ HEALTHY" if success_rate >= 80 else "⚠️ DEGRADED" if success_rate >= 50 else "❌ FAILED"
            
            print(f"{status} {service.upper()}: {service_success}/{service_total} ({success_rate:.1f}%)")
    
    overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 OVERALL SYSTEM STATUS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Success Rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 80:
        print(f"   Status: ✅ SYSTEM HEALTHY")
    elif overall_success_rate >= 50:
        print(f"   Status: ⚠️ SYSTEM DEGRADED")
    else:
        print(f"   Status: ❌ SYSTEM ISSUES")
    
    # Working URLs
    print(f"\n🔗 WORKING URLS:")
    working_urls = []
    
    for service, results in all_results.items():
        if isinstance(results, list) and any(r.get("success", False) for r in results):
            if "frontend_azure" in service:
                working_urls.append(f"Frontend (Azure): {URLS['frontend_azure']}")
            elif "frontend_vercel" in service:
                working_urls.append(f"Frontend (Vercel): {URLS['frontend_vercel']}")
            elif "backend_azure" in service:
                working_urls.append(f"Backend (Azure): {URLS['backend_azure']}")
            elif "engine_d" in service:
                working_urls.append(f"Engine D (Vercel): {URLS['engine_d_vercel']}")
            elif "local" in service:
                working_urls.append(f"Local Backend: {URLS['local_backend']}")
    
    for url in working_urls:
        print(f"   🌐 {url}")
    
    # Save detailed results
    report = {
        "timestamp": datetime.now().isoformat(),
        "urls_tested": URLS,
        "results": all_results,
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": overall_success_rate,
            "working_urls": working_urls
        }
    }
    
    with open("integration_analysis_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: integration_analysis_report.json")
    
    return report

if __name__ == "__main__":
    analyze_deployment()