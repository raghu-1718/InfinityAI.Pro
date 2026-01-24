"""
Load Testing Script for InfinityAI.Pro
Simulates 15 concurrent users performing critical operations
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import List, Dict
import random

# Service endpoints
SERVICES = {
    "engine-a": "https://engine-a-3acobgd3qa-uc.a.run.app",
    "engine-b": "https://engine-b-3acobgd3qa-uc.a.run.app",
    "engine-c": "https://engine-c-3acobgd3qa-uc.a.run.app",
    "get-latest-signals": "https://get-latest-signals-3acobgd3qa-uc.a.run.app",
}

# Test scenarios
async def user_scenario(session: aiohttp.ClientSession, user_id: int) -> Dict:
    """Simulate a single user's journey"""
    results = {
        "user_id": user_id,
        "start_time": time.time(),
        "actions": [],
        "errors": 0,
        "success": 0
    }
    
    try:
        # Action 1: Check Engine A health
        start = time.time()
        async with session.get(f"{SERVICES['engine-a']}/health", timeout=aiohttp.ClientTimeout(total=10)) as resp:
            duration = time.time() - start
            results["actions"].append({
                "action": "engine_a_health",
                "status": resp.status,
                "duration_ms": round(duration * 1000, 2)
            })
            if resp.status == 200:
                results["success"] += 1
            else:
                results["errors"] += 1
        
        # Action 2: Get latest signals
        await asyncio.sleep(random.uniform(0.5, 2))
        start = time.time()
        async with session.get(f"{SERVICES['get-latest-signals']}", timeout=aiohttp.ClientTimeout(total=15)) as resp:
            duration = time.time() - start
            results["actions"].append({
                "action": "get_signals",
                "status": resp.status,
                "duration_ms": round(duration * 1000, 2)
            })
            if resp.status == 200:
                results["success"] += 1
            else:
                results["errors"] += 1
        
        # Action 3: Check Engine C (trading)
        await asyncio.sleep(random.uniform(0.5, 2))
        start = time.time()
        async with session.get(f"{SERVICES['engine-c']}/health", timeout=aiohttp.ClientTimeout(total=10)) as resp:
            duration = time.time() - start
            results["actions"].append({
                "action": "engine_c_health",
                "status": resp.status,
                "duration_ms": round(duration * 1000, 2)
            })
            if resp.status == 200:
                results["success"] += 1
            else:
                results["errors"] += 1
        
        # Action 4: Check Engine B (ML)
        await asyncio.sleep(random.uniform(0.5, 2))
        start = time.time()
        async with session.get(f"{SERVICES['engine-b']}/health", timeout=aiohttp.ClientTimeout(total=10)) as resp:
            duration = time.time() - start
            results["actions"].append({
                "action": "engine_b_health",
                "status": resp.status,
                "duration_ms": round(duration * 1000, 2)
            })
            if resp.status == 200:
                results["success"] += 1
            else:
                results["errors"] += 1
                
    except Exception as e:
        results["errors"] += 1
        results["actions"].append({
            "action": "error",
            "error": str(e)[:100]
        })
    
    results["end_time"] = time.time()
    results["total_duration_s"] = round(results["end_time"] - results["start_time"], 2)
    return results

async def run_load_test(num_users: int = 15):
    """Run load test with specified number of concurrent users"""
    print("=" * 80)
    print(f"InfinityAI.Pro - Load Test ({num_users} Concurrent Users)")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    start_time = time.time()
    
    # Create session with connection pooling
    connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Launch all users concurrently
        tasks = [user_scenario(session, i+1) for i in range(num_users)]
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Analyze results
    total_actions = sum(len(r["actions"]) for r in results)
    total_errors = sum(r["errors"] for r in results)
    total_success = sum(r["success"] for r in results)
    
    all_durations = []
    for r in results:
        for action in r["actions"]:
            if "duration_ms" in action:
                all_durations.append(action["duration_ms"])
    
    avg_response_time = sum(all_durations) / len(all_durations) if all_durations else 0
    max_response_time = max(all_durations) if all_durations else 0
    min_response_time = min(all_durations) if all_durations else 0
    
    # Calculate percentiles
    sorted_durations = sorted(all_durations)
    p50 = sorted_durations[len(sorted_durations)//2] if sorted_durations else 0
    p95 = sorted_durations[int(len(sorted_durations)*0.95)] if sorted_durations else 0
    p99 = sorted_durations[int(len(sorted_durations)*0.99)] if sorted_durations else 0
    
    # Print results
    print()
    print("=" * 80)
    print("LOAD TEST RESULTS")
    print("=" * 80)
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Concurrent Users: {num_users}")
    print(f"Total Actions: {total_actions}")
    print(f"Successful Actions: {total_success} ({(total_success/total_actions*100):.1f}%)")
    print(f"Failed Actions: {total_errors} ({(total_errors/total_actions*100):.1f}%)")
    print()
    print("Response Time Statistics:")
    print(f"  Average: {avg_response_time:.2f}ms")
    print(f"  Min: {min_response_time:.2f}ms")
    print(f"  Max: {max_response_time:.2f}ms")
    print(f"  P50 (Median): {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")
    print()
    print(f"Throughput: {total_actions/total_duration:.2f} requests/second")
    print("=" * 80)
    
    # Save detailed results
    output = {
        "timestamp": datetime.now().isoformat(),
        "num_users": num_users,
        "total_duration_s": total_duration,
        "total_actions": total_actions,
        "total_success": total_success,
        "total_errors": total_errors,
        "success_rate": total_success/total_actions*100 if total_actions > 0 else 0,
        "response_times": {
            "avg_ms": avg_response_time,
            "min_ms": min_response_time,
            "max_ms": max_response_time,
            "p50_ms": p50,
            "p95_ms": p95,
            "p99_ms": p99
        },
        "throughput_rps": total_actions/total_duration,
        "user_results": results
    }
    
    filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Detailed results saved to: {filename}")
    print()
    
    # Pass/Fail criteria
    print("PASS/FAIL CRITERIA:")
    print(f"  Success Rate > 95%: {'[PASS]' if (total_success/total_actions*100) > 95 else '[FAIL]'}")
    print(f"  P95 Response Time < 5000ms: {'[PASS]' if p95 < 5000 else '[FAIL]'}")
    print(f"  No Errors: {'[PASS]' if total_errors == 0 else '[WARN]'}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_load_test(15))
