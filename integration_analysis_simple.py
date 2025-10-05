#!/usr/bin/env python3
"""
InfinityAI.Pro Complete Integration Analysis
Tests all deployed engines and provides comprehensive report
"""

import requests
import json
import time
from datetime import datetime

# Current Live URLs from deployment reports
URLS = {
    "frontend_azure": "https://brave-ocean-09e85cd10-preview.centralus.2.azurestaticapps.net",
    "backend_azure": "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
    "engine_d_vercel": "https://infinity-backend-9z59tyitb-infinityaipro.vercel.app",
    "frontend_vercel": "https://infinityai-pro-frontend-n53xfzqol-infinityaipro.vercel.app",
    "local_backend": "http://localhost:8000"
}

def test_url(name, url):
    """Test a URL"""
    print(f"\nTesting {name}: {url}")
    results = []
    
    endpoints = ["/", "/health", "/docs"]
    
    for endpoint in endpoints:
        full_url = url + endpoint
        try:
            start_time = time.time()
            response = requests.get(full_url, timeout=10, allow_redirects=True)
            response_time = int((time.time() - start_time) * 1000)
            
            status = "OK" if response.status_code == 200 else "WARN" if response.status_code in [301, 302, 404] else "FAIL"
            print(f"  {status} {endpoint}: {response.status_code} ({response_time}ms)")
            
            results.append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            })
            
        except Exception as e:
            print(f"  ERROR {endpoint}: {str(e)}")
            results.append({"endpoint": endpoint, "status_code": "ERROR", "response_time": 0, "success": False})
    
    return results

def analyze_deployment():
    """Complete deployment analysis"""
    print("InfinityAI.Pro Complete Integration Analysis")
    print("=" * 80)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    all_results = {}
    
    # Test all URLs
    for service_name, url in URLS.items():
        results = test_url(service_name, url)
        all_results[service_name] = results
    
    # Generate Summary Report
    print("\n" + "=" * 80)
    print("INTEGRATION ANALYSIS SUMMARY")
    print("=" * 80)
    
    total_tests = 0
    successful_tests = 0
    working_services = []
    
    for service, results in all_results.items():
        service_total = len(results)
        service_success = sum(1 for r in results if r.get("success", False))
        total_tests += service_total
        successful_tests += service_success
        
        success_rate = (service_success / service_total * 100) if service_total > 0 else 0
        status = "HEALTHY" if success_rate >= 50 else "DEGRADED" if success_rate >= 25 else "FAILED"
        
        print(f"{status} {service.upper()}: {service_success}/{service_total} ({success_rate:.1f}%)")
        
        if service_success > 0:
            working_services.append((service, URLS[service]))
    
    overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nOVERALL SYSTEM STATUS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Success Rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 60:
        print(f"   Status: SYSTEM HEALTHY")
    elif overall_success_rate >= 30:
        print(f"   Status: SYSTEM DEGRADED")
    else:
        print(f"   Status: SYSTEM ISSUES")
    
    # Working URLs
    print(f"\nWORKING SERVICES:")
    for service, url in working_services:
        print(f"   {service}: {url}")
    
    # Save results
    report = {
        "timestamp": datetime.now().isoformat(),
        "urls_tested": URLS,
        "results": all_results,
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": overall_success_rate,
            "working_services": working_services
        }
    }
    
    with open("integration_analysis_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: integration_analysis_report.json")
    
    return report

if __name__ == "__main__":
    analyze_deployment()