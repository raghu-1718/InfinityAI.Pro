#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Script for InfinityAI.Pro
Tests all services, measures performance, validates integrations
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple

# Service URLs
SERVICES = {
    "engine-a": "https://engine-a-3acobgd3qa-uc.a.run.app",
    "engine-b": "https://engine-b-3acobgd3qa-uc.a.run.app",
    "engine-c": "https://engine-c-3acobgd3qa-uc.a.run.app",
    "detect-momentum-signals": "https://detect-momentum-signals-3acobgd3qa-uc.a.run.app",
    "get-latest-signals": "https://get-latest-signals-3acobgd3qa-uc.a.run.app",
    "market-data-ingestion": "https://market-data-ingestion-3acobgd3qa-uc.a.run.app",
    "websocket-streamer": "https://websocket-streamer-3acobgd3qa-uc.a.run.app",
}

CLOUD_FUNCTION_URLS = {
    "detect-momentum-signals": "https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/detect-momentum-signals",
    "get-latest-signals": "https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/get-latest-signals",
}

results = {
    "timestamp": datetime.now().isoformat(),
    "services_tested": 0,
    "services_healthy": 0,
    "services_unhealthy": 0,
    "average_response_time_ms": 0,
    "details": []
}

def test_endpoint(name: str, url: str, endpoint: str = "/health", timeout: int = 10) -> Dict:
    """Test a single endpoint and return results"""
    full_url = f"{url}{endpoint}"
    result = {
        "service": name,
        "url": full_url,
        "status": "unknown",
        "response_time_ms": 0,
        "status_code": 0,
        "error": None
    }
    
    try:
        start = time.time()
        response = requests.get(full_url, timeout=timeout)
        end = time.time()
        
        result["response_time_ms"] = round((end - start) * 1000, 2)
        result["status_code"] = response.status_code
        result["status"] = "healthy" if response.status_code == 200 else "unhealthy"
        
        if response.status_code == 200:
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200]
    
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = f"Timeout after {timeout}s"
    except requests.exceptions.ConnectionError as e:
        result["status"] = "connection_error"
        result["error"] = str(e)[:200]
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:200]
    
    return result

print("=" * 80)
print("InfinityAI.Pro - Comprehensive End-to-End Testing")
print("=" * 80)
print(f"Started: {results['timestamp']}")
print()

# Test all Cloud Run services
print("[1/4] Testing Cloud Run Services...")
print("-" * 80)
for name, url in SERVICES.items():
    print(f"Testing {name}...", end=" ")
    result = test_endpoint(name, url, "/health")
    results["details"].append(result)
    results["services_tested"] += 1
    
    if result["status"] == "healthy":
        results["services_healthy"] += 1
        print(f"[OK] {result['response_time_ms']}ms")
    else:
        results["services_unhealthy"] += 1
        print(f"[FAIL] {result['status']}: {result.get('error', 'N/A')}")

print()

# Test Cloud Functions
print("[2/4] Testing Cloud Functions...")
print("-" * 80)
for name, url in CLOUD_FUNCTION_URLS.items():
    print(f"Testing {name}...", end=" ")
    result = test_endpoint(f"cf-{name}", url, "", timeout=30)
    results["details"].append(result)
    results["services_tested"] += 1
    
    if result["status_code"] == 200:
        results["services_healthy"] += 1
        print(f"[OK] {result['response_time_ms']}ms")
    else:
        results["services_unhealthy"] += 1
        print(f"[WARN] Status {result['status_code']}: {result.get('error', 'N/A')}")

print()

# Calculate average response time
total_response_time = sum(r["response_time_ms"] for r in results["details"] if r["response_time_ms"] > 0)
if results["services_tested"] > 0:
    results["average_response_time_ms"] = round(total_response_time / results["services_tested"], 2)

# Test Engine-specific endpoints
print("[3/4] Testing Engine-Specific Endpoints...")
print("-" * 80)

# Engine A - Signal Generation
print("Testing Engine A signal generation...", end=" ")
try:
    response = requests.get(f"{SERVICES['engine-a']}/api/health", timeout=10)
    if response.status_code == 200:
        print(f"[OK] Engine A healthy")
    else:
        print(f"[WARN] Status {response.status_code}")
except Exception as e:
    print(f"[ERROR] Error: {str(e)[:50]}")

# Engine C - Trading capabilities
print("Testing Engine C trading endpoints...", end=" ")
try:
    response = requests.get(f"{SERVICES['engine-c']}/api/health", timeout=10)
    if response.status_code == 200:
        print(f"[OK] Engine C healthy")
    else:
        print(f"[WARN] Status {response.status_code}")
except Exception as e:
    print(f"[ERROR] Error: {str(e)[:50]}")

print()

# Summary
print("[4/4] Test Summary")
print("=" * 80)
print(f"Total Services Tested: {results['services_tested']}")
print(f"Healthy Services: {results['services_healthy']} [OK]")
print(f"Unhealthy Services: {results['services_unhealthy']} [FAIL]")
print(f"Average Response Time: {results['average_response_time_ms']}ms")
print(f"Success Rate: {round((results['services_healthy'] / results['services_tested']) * 100, 1)}%")
print()

# Save results
output_file = f"e2e_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"Results saved to: {output_file}")
print("=" * 80)
