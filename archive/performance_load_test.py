#!/usr/bin/env python3
"""
InfinityAI.Pro - Production Performance Load Testing
Comprehensive performance benchmarking with concurrent load testing
"""

import asyncio
import aiohttp
import time
import statistics
import json
from datetime import datetime
from typing import List, Dict, Any

class PerformanceLoadTester:
    def __init__(self):
        self.services = {
            'Frontend': 'https://infinityai-pro-frontend-573866363639.us-central1.run.app',
            'Engine A': 'https://engine-a-573866363639-573866363639.us-central1.run.app',
            'Engine B': 'https://engine-b-573866363639-573866363639.us-central1.run.app', 
            'Engine C': 'https://engine-c-573866363639-573866363639.us-central1.run.app',
            'Engine D': 'https://engine-d-573866363639-573866363639.us-central1.run.app',
            'Engine Ultra': 'https://engine-ultra-573866363639-573866363639.us-central1.run.app'
        }
        
    async def run_load_test(self, service_name: str, base_url: str, duration: int = 30, concurrent_requests: int = 10):
        """Run intensive load test on a service"""
        print(f"🚀 Load testing {service_name} - {duration}s, {concurrent_requests} concurrent requests")
        
        response_times = []
        status_codes = []
        errors = 0
        total_requests = 0
        
        connector = aiohttp.TCPConnector(limit=100)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            start_time = time.time()
            end_time = start_time + duration
            
            # Semaphore to control concurrent requests
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def make_request():
                nonlocal errors, total_requests
                async with semaphore:
                    request_start = time.time()
                    try:
                        async with session.get(f"{base_url}/health") as response:
                            request_time = (time.time() - request_start) * 1000
                            response_times.append(request_time)
                            status_codes.append(response.status)
                            total_requests += 1
                            
                            if response.status >= 400:
                                errors += 1
                    except Exception as e:
                        errors += 1
                        total_requests += 1
                        response_times.append(30000)  # 30s timeout
            
            # Generate continuous load
            tasks = []
            while time.time() < end_time:
                # Create batch of requests
                batch_size = min(concurrent_requests, 50)  # Cap batch size
                batch_tasks = [make_request() for _ in range(batch_size)]
                tasks.extend(batch_tasks)
                
                # Small delay between batches
                await asyncio.sleep(0.05)
                
                # Execute completed batches
                if len(tasks) >= concurrent_requests * 2:
                    await asyncio.gather(*tasks[:concurrent_requests], return_exceptions=True)
                    tasks = tasks[concurrent_requests:]
            
            # Execute remaining tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate performance metrics
        actual_duration = time.time() - start_time
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times, default=0)
        p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times, default=0)
        
        rps = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = ((total_requests - errors) / total_requests * 100) if total_requests > 0 else 0
        error_rate = (errors / total_requests * 100) if total_requests > 0 else 0
        
        results = {
            'service': service_name,
            'duration_seconds': actual_duration,
            'total_requests': total_requests,
            'successful_requests': total_requests - errors,
            'failed_requests': errors,
            'requests_per_second': round(rps, 2),
            'success_rate_percent': round(success_rate, 2),
            'error_rate_percent': round(error_rate, 2),
            'avg_response_time_ms': round(avg_response_time, 2),
            'p95_response_time_ms': round(p95_response_time, 2),
            'p99_response_time_ms': round(p99_response_time, 2),
            'min_response_time_ms': round(min(response_times), 2) if response_times else 0,
            'max_response_time_ms': round(max(response_times), 2) if response_times else 0
        }
        
        print(f"   📊 {service_name}: {rps:.1f} RPS, {avg_response_time:.0f}ms avg, {success_rate:.1f}% success, {errors} errors")
        
        return results

    async def run_comprehensive_load_test(self):
        """Run load test on all services"""
        print("🎯 Starting Comprehensive Performance Load Testing")
        print("=" * 70)
        
        all_results = {}
        
        for service_name, base_url in self.services.items():
            try:
                results = await self.run_load_test(service_name, base_url, duration=30, concurrent_requests=10)
                all_results[service_name] = results
                
                # Brief pause between service tests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Load test failed for {service_name}: {str(e)}")
                all_results[service_name] = {
                    'service': service_name,
                    'error': str(e),
                    'status': 'failed'
                }
        
        return all_results

async def main():
    tester = PerformanceLoadTester()
    
    print("🚀 InfinityAI.Pro - Performance Load Testing Suite")
    print("Testing all services with concurrent load...")
    
    # Run comprehensive load testing
    results = await tester.run_comprehensive_load_test()
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE LOAD TESTING RESULTS")
    print("=" * 70)
    
    total_rps = 0
    total_avg_response = 0
    healthy_services = 0
    
    for service_name, metrics in results.items():
        if 'error' not in metrics:
            total_rps += metrics['requests_per_second']
            total_avg_response += metrics['avg_response_time_ms']
            healthy_services += 1
            
            print(f"✅ {service_name}:")
            print(f"   RPS: {metrics['requests_per_second']}")
            print(f"   Avg Response: {metrics['avg_response_time_ms']}ms")
            print(f"   Success Rate: {metrics['success_rate_percent']}%")
            print(f"   P95 Response: {metrics['p95_response_time_ms']}ms")
            print(f"   Total Requests: {metrics['total_requests']}")
        else:
            print(f"❌ {service_name}: {metrics['error']}")
    
    print(f"\n🎯 SYSTEM TOTALS:")
    print(f"Total System RPS: {total_rps:.2f}")
    print(f"Average Response Time: {total_avg_response/healthy_services:.2f}ms" if healthy_services > 0 else "N/A")
    print(f"Healthy Services: {healthy_services}/{len(results)}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"performance_load_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_config': {
                'duration_per_service': 30,
                'concurrent_requests': 10,
                'services_tested': len(results)
            },
            'results': results,
            'system_summary': {
                'total_system_rps': total_rps,
                'average_response_time_ms': total_avg_response/healthy_services if healthy_services > 0 else 0,
                'healthy_services': f"{healthy_services}/{len(results)}"
            }
        }, f, indent=2)
    
    print(f"\n📋 Detailed results saved: {filename}")
    
if __name__ == "__main__":
    asyncio.run(main())