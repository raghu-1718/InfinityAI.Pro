#!/usr/bin/env python3
"""
InfinityAI.Pro - Comprehensive Multi-Cloud Engine Test
Including Ultra-Aggressive Engine Validation
"""

import requests
import json
import time
from datetime import datetime
import asyncio
import aiohttp

# Complete Engine Configuration - Updated with Real Endpoints
ENGINES = {
    "gcp": {
        "engine_a": "https://infinityai-engine-a-573866363639.us-central1.run.app",
        "engine_b": "https://infinityai-engine-b-573866363639.us-central1.run.app", 
        "ultra_aggressive": "https://infinityai-ultra-aggressive-573866363639.us-central1.run.app"
    },
    "aws": {
        "engine_c": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
        "engine_d": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d"
    }
}

FRONTEND_URL = "https://infinityai.pro"

def test_engine_health(name, url):
    """Test individual engine health"""
    try:
        response = requests.get(f"{url}/health", timeout=15)
        success = response.status_code == 200
        response_time = response.elapsed.total_seconds() * 1000
        
        data = {}
        if success:
            try:
                data = response.json()
            except:
                data = {"content": response.text[:100]}
                
        return {
            "name": name,
            "url": url,
            "success": success,
            "status_code": response.status_code,
            "response_time_ms": round(response_time, 2),
            "data": data
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "success": False,
            "error": str(e),
            "response_time_ms": None
        }

def test_ultra_aggressive_specific():
    """Specific tests for ultra-aggressive engine"""
    print("\n🔥 ULTRA-AGGRESSIVE ENGINE DEEP DIVE")
    print("=" * 60)
    
    ultra_url = ENGINES["gcp"]["ultra_aggressive"]
    tests = []
    
    # Test 1: Health Check
    result = test_engine_health("Ultra-Aggressive Health", ultra_url)
    tests.append(result)
    print(f"   {'✅' if result['success'] else '❌'} Health Check: {result.get('status_code', 'ERROR')}")
    
    # Test 2: Main Dashboard
    try:
        response = requests.get(ultra_url, timeout=10)
        success = response.status_code == 200 and "Ultra Aggressive" in response.text
        tests.append({
            "name": "Ultra-Aggressive Dashboard",
            "success": success,
            "status_code": response.status_code,
            "has_content": "Ultra Aggressive" in response.text
        })
        print(f"   {'✅' if success else '❌'} Dashboard: {response.status_code} - Content: {'Found' if 'Ultra Aggressive' in response.text else 'Missing'}")
    except Exception as e:
        tests.append({"name": "Ultra-Aggressive Dashboard", "success": False, "error": str(e)})
        print(f"   ❌ Dashboard: ERROR - {e}")
    
    # Test 3: API Status
    try:
        response = requests.get(f"{ultra_url}/api/status", timeout=10)
        success = response.status_code == 200
        tests.append({
            "name": "Ultra-Aggressive API Status",
            "success": success,
            "status_code": response.status_code
        })
        print(f"   {'✅' if success else '❌'} API Status: {response.status_code}")
        
        if success:
            try:
                data = response.json()
                print(f"      Mode: {data.get('ultra_aggressive_mode', 'Unknown')}")
                print(f"      Live: {data.get('live_execution', 'Unknown')}")
            except:
                pass
                
    except Exception as e:
        tests.append({"name": "Ultra-Aggressive API Status", "success": False, "error": str(e)})
        print(f"   ❌ API Status: ERROR - {e}")
    
    return tests

def test_cross_cloud_communication():
    """Test communication between GCP and AWS engines"""
    print("\n🔄 CROSS-CLOUD COMMUNICATION TEST")
    print("=" * 50)
    
    results = []
    
    # Test GCP to AWS communication paths
    gcp_engines = ENGINES["gcp"]
    aws_engines = ENGINES["aws"]
    
    for gcp_name, gcp_url in gcp_engines.items():
        for aws_name, aws_url in aws_engines.items():
            try:
                # Simple connectivity test - check if both engines are reachable
                gcp_health = requests.get(f"{gcp_url}/health", timeout=5)
                aws_health = requests.get(aws_url, timeout=5)
                
                both_online = gcp_health.status_code == 200 and aws_health.status_code == 200
                
                result = {
                    "path": f"{gcp_name} (GCP) ↔ {aws_name} (AWS)",
                    "gcp_status": gcp_health.status_code,
                    "aws_status": aws_health.status_code,
                    "communication_possible": both_online
                }
                results.append(result)
                
                status = "✅ POSSIBLE" if both_online else "❌ BLOCKED"
                print(f"   {status} {gcp_name} (GCP) ↔ {aws_name} (AWS)")
                
            except Exception as e:
                result = {
                    "path": f"{gcp_name} (GCP) ↔ {aws_name} (AWS)",
                    "error": str(e),
                    "communication_possible": False
                }
                results.append(result)
                print(f"   ❌ ERROR {gcp_name} (GCP) ↔ {aws_name} (AWS): {e}")
    
    return results

def test_integration_resilience():
    """Test system resilience and integration"""
    print("\n🛡️ INTEGRATION RESILIENCE TEST")
    print("=" * 45)
    
    # Count operational engines
    operational_engines = 0
    total_engines = 0
    
    all_results = []
    
    for cloud, engines in ENGINES.items():
        for name, url in engines.items():
            total_engines += 1
            result = test_engine_health(f"{cloud.upper()}_{name}", url)
            all_results.append(result)
            
            if result['success']:
                operational_engines += 1
                print(f"   ✅ {cloud.upper()} {name}: OPERATIONAL")
            else:
                print(f"   ❌ {cloud.upper()} {name}: {result.get('error', 'FAILED')}")
    
    # Calculate resilience
    resilience_percentage = (operational_engines / total_engines) * 100
    
    print(f"\n   📊 RESILIENCE SUMMARY:")
    print(f"      Operational: {operational_engines}/{total_engines} engines")
    print(f"      Resilience: {resilience_percentage:.1f}%")
    
    # Determine system status
    if resilience_percentage >= 75:
        status = "🟢 RESILIENT"
    elif resilience_percentage >= 50:
        status = "🟡 DEGRADED"
    else:
        status = "🔴 CRITICAL"
        
    print(f"      Status: {status}")
    
    return {
        "operational_engines": operational_engines,
        "total_engines": total_engines,
        "resilience_percentage": resilience_percentage,
        "status": status,
        "engine_results": all_results
    }

def main():
    print("🚀 INFINITYAI.PRO - COMPREHENSIVE ENGINE ANALYSIS")
    print("GitHub Repository: https://github.com/raghu-1718/InfinityAI.Pro")
    print("=" * 65)
    
    # Test all engines
    print("\n1. ENGINE HEALTH CHECK")
    print("=" * 30)
    
    all_engine_results = []
    
    for cloud, engines in ENGINES.items():
        print(f"\n   {cloud.upper()} ENGINES:")
        for name, url in engines.items():
            result = test_engine_health(name, url)
            all_engine_results.append(result)
            
            status = "✅ HEALTHY" if result['success'] else "❌ FAILED"
            time_info = f"({result['response_time_ms']}ms)" if result.get('response_time_ms') else ""
            print(f"      {status} {name}: {url} {time_info}")
            
            if result['success'] and result.get('data'):
                if isinstance(result['data'], dict):
                    service = result['data'].get('service', result['data'].get('status', 'Unknown'))
                    print(f"         └─ Service: {service}")
    
    # Test ultra-aggressive engine specifically
    ultra_tests = test_ultra_aggressive_specific()
    
    # Test cross-cloud communication
    comm_tests = test_cross_cloud_communication()
    
    # Test integration resilience
    resilience_results = test_integration_resilience()
    
    # Test frontend
    print(f"\n🌐 FRONTEND TEST")
    print("=" * 20)
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        frontend_ok = response.status_code == 200 and "InfinityAI" in response.text
        print(f"   {'✅' if frontend_ok else '❌'} Frontend: {FRONTEND_URL} ({response.status_code})")
        print(f"      InfinityAI Branding: {'Found' if 'InfinityAI' in response.text else 'Missing'}")
    except Exception as e:
        print(f"   ❌ Frontend ERROR: {e}")
        frontend_ok = False
    
    # Final Summary
    print("\n" + "=" * 65)
    print("📋 COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 65)
    
    # Count successful engines
    successful_engines = sum(1 for r in all_engine_results if r['success'])
    total_engines = len(all_engine_results)
    
    # Ultra-aggressive specific
    ultra_successful = sum(1 for r in ultra_tests if r.get('success', False))
    ultra_total = len(ultra_tests)
    
    print(f"📊 ENGINE STATUS:")
    print(f"   Total Engines: {total_engines}")
    print(f"   Operational: {successful_engines}")
    print(f"   Success Rate: {(successful_engines/total_engines)*100:.1f}%")
    
    print(f"\n🔥 ULTRA-AGGRESSIVE ENGINE:")
    print(f"   Tests Passed: {ultra_successful}/{ultra_total}")
    print(f"   Integration: {'✅ ACTIVE' if ultra_successful > 0 else '❌ INACTIVE'}")
    
    print(f"\n🌐 FRONTEND:")
    print(f"   Status: {'✅ ACCESSIBLE' if frontend_ok else '❌ INACCESSIBLE'}")
    
    print(f"\n☁️ CLOUD DISTRIBUTION:")
    gcp_count = len(ENGINES["gcp"])
    aws_count = len(ENGINES["aws"])
    print(f"   GCP Engines: {gcp_count} (Engine A, Engine B, Ultra-Aggressive)")
    print(f"   AWS Engines: {aws_count} (Engine C, Engine D)")
    
    print(f"\n🛡️ SYSTEM RESILIENCE:")
    print(f"   {resilience_results['status']}")
    
    # Overall system status
    overall_healthy = (successful_engines >= 3 and ultra_successful > 0 and frontend_ok)
    overall_status = "🟢 FULLY OPERATIONAL" if overall_healthy else "🟡 PARTIALLY OPERATIONAL" if successful_engines >= 2 else "🔴 CRITICAL ISSUES"
    
    print(f"\n🎯 OVERALL STATUS: {overall_status}")
    
    # Next steps
    print(f"\n📋 RECOMMENDATIONS:")
    if successful_engines < total_engines:
        print("   • Fix failed engine connections")
    if ultra_successful < ultra_total:
        print("   • Verify ultra-aggressive engine configuration") 
    if not frontend_ok:
        print("   • Check frontend deployment")
    if successful_engines >= 4:
        print("   • ✅ System ready for production trading")
    
    print("\n🎉 Analysis Complete!")
    print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()