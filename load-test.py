#!/usr/bin/env python3
"""
InfinityAI.Pro - Comprehensive Load Testing Script
Tests: 10 concurrent users, 3 minutes, 1000+ API calls
Author: Automated Testing System
Date: January 19, 2026
"""

import concurrent.futures
import requests
import time
import json
import statistics
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urljoin
import sys

# Configuration
CONCURRENT_USERS = 10
DURATION_SECONDS = 180  # 3 minutes
TARGET_CALLS = 1000

# Engine URLs (current production)
ENGINES = {
    "Engine-A": "https://engine-a-3acobgd3qa-uc.a.run.app",
    "Engine-B": "https://engine-b-3acobgd3qa-uc.a.run.app",
    "Engine-C": "https://engine-c-3acobgd3qa-uc.a.run.app",
}

# Endpoints to test
ENDPOINTS = [
    {"engine": "Engine-A", "path": "/health", "method": "GET"},
    {"engine": "Engine-B", "path": "/health", "method": "GET"},
    {"engine": "Engine-C", "path": "/health", "method": "GET"},
    {"engine": "Engine-B", "path": "/api/v1/market/status", "method": "GET"},
    {"engine": "Engine-C", "path": "/api/dhan/health", "method": "GET"},
]

class LoadTestResults:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors = []
        self.by_endpoint = defaultdict(lambda: {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "response_times": []
        })
        self.start_time = None
        self.end_time = None

    def add_request(self, endpoint, success, response_time, error_msg=None):
        self.total_requests += 1
        self.response_times.append(response_time)

        endpoint_key = f"{endpoint['engine']} {endpoint['path']}"
        self.by_endpoint[endpoint_key]["requests"] += 1
        self.by_endpoint[endpoint_key]["response_times"].append(response_time)

        if success:
            self.successful_requests += 1
            self.by_endpoint[endpoint_key]["successes"] += 1
        else:
            self.failed_requests += 1
            self.by_endpoint[endpoint_key]["failures"] += 1
            if error_msg:
                self.errors.append({
                    "endpoint": endpoint_key,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })

def make_request(engine_url, endpoint_path, method="GET", timeout=10):
    """Make HTTP request to endpoint"""
    url = urljoin(engine_url, endpoint_path)
    try:
        start_time = time.time()

        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, timeout=timeout, json={})
        else:
            response = requests.request(method, url, timeout=timeout)

        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        if response.status_code >= 200 and response.status_code < 300:
            return True, elapsed, None
        else:
            return False, elapsed, f"HTTP {response.status_code}"

    except requests.Timeout:
        elapsed = (time.time() - start_time) * 1000
        return False, elapsed, "Timeout"
    except requests.ConnectionError as e:
        elapsed = (time.time() - start_time) * 1000
        return False, elapsed, f"Connection Error: {str(e)}"
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return False, elapsed, f"Error: {str(e)}"

def worker(user_id, duration_seconds, results):
    """Worker function for each concurrent user"""
    end_time = time.time() + duration_seconds
    local_request_count = 0

    while time.time() < end_time:
        for endpoint in ENDPOINTS:
            engine_url = ENGINES[endpoint["engine"]]
            success, response_time, error = make_request(
                engine_url,
                endpoint["path"],
                endpoint["method"]
            )

            results.add_request(endpoint, success, response_time, error)
            local_request_count += 1

            # Small delay to avoid overwhelming the services
            time.sleep(0.01)

    return local_request_count

def print_summary(results, elapsed_time):
    """Print test results summary"""

    print("\n" + "="*70)
    print("📊 LOAD TEST RESULTS SUMMARY")
    print("="*70)

    # Overall stats
    print(f"\n⏱️  Test Duration: {elapsed_time:.2f} seconds")
    print(f"👥 Concurrent Users: {CONCURRENT_USERS}")
    print(f"📍 Total API Calls: {results.total_requests}")
    print(f"✅ Successful: {results.successful_requests} ({100*results.successful_requests/results.total_requests:.1f}%)")
    print(f"❌ Failed: {results.failed_requests} ({100*results.failed_requests/results.total_requests:.1f}%)")

    # Response time stats
    if results.response_times:
        print(f"\n⚡ Response Time Statistics:")
        print(f"   Average: {statistics.mean(results.response_times):.2f} ms")
        print(f"   Median:  {statistics.median(results.response_times):.2f} ms")
        print(f"   Min:     {min(results.response_times):.2f} ms")
        print(f"   Max:     {max(results.response_times):.2f} ms")

        if len(results.response_times) > 1:
            stdev = statistics.stdev(results.response_times)
            print(f"   StdDev:  {stdev:.2f} ms")

            # Calculate percentiles
            sorted_times = sorted(results.response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            print(f"   P95:     {sorted_times[p95_idx]:.2f} ms")
            print(f"   P99:     {sorted_times[p99_idx]:.2f} ms")

    # Throughput
    throughput = results.total_requests / elapsed_time if elapsed_time > 0 else 0
    print(f"\n🚀 Throughput: {throughput:.2f} requests/second")

    # By endpoint breakdown
    print(f"\n📋 Results by Endpoint:")
    print(f"\n{'Endpoint':<40} {'Requests':<10} {'Success':<10} {'Failed':<10} {'Avg Time':<10}")
    print("-"*70)

    for endpoint, stats in sorted(results.by_endpoint.items()):
        req_count = stats["requests"]
        success = stats["successes"]
        failed = stats["failures"]
        avg_time = statistics.mean(stats["response_times"]) if stats["response_times"] else 0

        print(f"{endpoint:<40} {req_count:<10} {success:<10} {failed:<10} {avg_time:>8.2f} ms")

    # Errors
    if results.errors:
        print(f"\n⚠️  Error Details (Sample - Last 10):")
        for error in results.errors[-10:]:
            print(f"   [{error['timestamp']}] {error['endpoint']}: {error['error']}")

    print("\n" + "="*70)

    # Success criteria
    print(f"\n✓ Test Criteria:")
    success_rate = 100 * results.successful_requests / results.total_requests if results.total_requests > 0 else 0
    print(f"  ✅ Total Calls: {results.total_requests} (target: {TARGET_CALLS}+) - {'PASS' if results.total_requests >= TARGET_CALLS else 'FAIL'}")
    print(f"  ✅ Success Rate: {success_rate:.1f}% (target: >95%) - {'PASS' if success_rate > 95 else 'FAIL'}")
    print(f"  ✅ Avg Response: {statistics.mean(results.response_times):.2f}ms (target: <500ms) - {'PASS' if statistics.mean(results.response_times) < 500 else 'FAIL'}")

def export_results_json(results, filename="load-test-results.json"):
    """Export results to JSON file"""
    export_data = {
        "metadata": {
            "test_date": datetime.now().isoformat(),
            "concurrent_users": CONCURRENT_USERS,
            "duration_seconds": DURATION_SECONDS,
            "target_calls": TARGET_CALLS,
        },
        "summary": {
            "total_requests": results.total_requests,
            "successful_requests": results.successful_requests,
            "failed_requests": results.failed_requests,
            "success_rate_percent": 100 * results.successful_requests / results.total_requests if results.total_requests > 0 else 0,
        },
        "response_times": {
            "mean": statistics.mean(results.response_times) if results.response_times else 0,
            "median": statistics.median(results.response_times) if results.response_times else 0,
            "min": min(results.response_times) if results.response_times else 0,
            "max": max(results.response_times) if results.response_times else 0,
            "stdev": statistics.stdev(results.response_times) if len(results.response_times) > 1 else 0,
        },
        "by_endpoint": dict(results.by_endpoint),
        "errors": results.errors[:100],  # Limit to first 100 errors
    }

    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"\n💾 Results exported to: {filename}")

def main():
    print("🚀 InfinityAI.Pro - Comprehensive Load Test")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Configuration:")
    print(f"  - Concurrent Users: {CONCURRENT_USERS}")
    print(f"  - Duration: {DURATION_SECONDS} seconds ({DURATION_SECONDS/60:.1f} minutes)")
    print(f"  - Target Calls: {TARGET_CALLS}+")
    print(f"  - Endpoints: {len(ENDPOINTS)}")
    print(f"  - Total Expected Calls: ~{CONCURRENT_USERS * len(ENDPOINTS) * (DURATION_SECONDS // 2)}")
    print("="*70)
    print("\n⏳ Starting load test...\n")

    # Create shared results object
    results = LoadTestResults()
    results.start_time = time.time()

    # Run load test with thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = []

        for user_id in range(1, CONCURRENT_USERS + 1):
            print(f"  Starting User {user_id}...", end=" ")
            future = executor.submit(worker, user_id, DURATION_SECONDS, results)
            futures.append(future)
            print("✓")

        print(f"\n⏳ Waiting for all workers to complete...")

        # Wait for all to complete
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                call_count = future.result()
                print(f"  ✓ User {i} completed: {call_count} calls")
            except Exception as e:
                print(f"  ✗ User {i} failed: {e}")

    results.end_time = time.time()
    elapsed_time = results.end_time - results.start_time

    # Print results
    print_summary(results, elapsed_time)

    # Export to JSON
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    export_results_json(results, f"load-test-results-{timestamp}.json")

    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

if __name__ == "__main__":
    main()
