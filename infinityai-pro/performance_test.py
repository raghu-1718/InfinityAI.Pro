#!/usr/bin/env python3
"""
InfinityAI.Pro Performance Testing Suite
Tests concurrent requests, throughput, and response times across all engines
"""

import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
from typing import Dict, List, Tuple
import json

# Engine endpoints
ENGINES = {
    "engine_a": {
        "name": "Market Data Ingestion (Azure)",
        "endpoint": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
        "test_paths": ["/health", "/metrics"]
    },
    "engine_b": {
        "name": "AI Signal Processing (GCP)",
        "endpoint": "https://infinityai-engine-b-573866363639.us-central1.run.app",
        "test_paths": ["/health", "/models/status", "/metrics"]
    },
    "engine_c": {
        "name": "Trade Execution (AWS)",
        "endpoint": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
        "test_paths": ["/health", "/metrics"]
    },
    "engine_d": {
        "name": "AI Chatbot Assistant (AWS)",
        "endpoint": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d",
        "test_paths": ["/health"]
    }
}

class PerformanceTester:
    def __init__(self):
        self.results = {}
        self.session = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def single_request(self, url: str) -> Tuple[int, float, str]:
        """Make a single request and return status, response time, and error"""
        start_time = time.perf_counter()
        try:
            async with self.session.get(url) as response:
                await response.text()  # Read response body
                end_time = time.perf_counter()
                return response.status, (end_time - start_time) * 1000, None
        except Exception as e:
            end_time = time.perf_counter()
            return 0, (end_time - start_time) * 1000, str(e)
    
    async def concurrent_requests(self, url: str, count: int) -> List[Tuple[int, float, str]]:
        """Make concurrent requests to the same URL"""
        tasks = [self.single_request(url) for _ in range(count)]
        return await asyncio.gather(*tasks)
    
    async def test_engine_performance(self, engine_id: str, config: dict, concurrent_count: int = 10) -> Dict:
        """Test performance of a single engine"""
        print(f"\n🔍 Testing {config['name']}")
        print(f"   Endpoint: {config['endpoint']}")
        print(f"   Concurrent requests: {concurrent_count}")
        
        engine_results = {
            "engine": engine_id,
            "name": config['name'],
            "endpoint": config['endpoint'],
            "tests": {}
        }
        
        for path in config['test_paths']:
            url = f"{config['endpoint']}{path}"
            print(f"   Testing {path}...")
            
            # Test concurrent requests
            start_time = time.perf_counter()
            results = await self.concurrent_requests(url, concurrent_count)
            total_time = time.perf_counter() - start_time
            
            # Analyze results
            response_times = [r[1] for r in results]
            success_count = sum(1 for r in results if r[0] == 200)
            error_count = len(results) - success_count
            
            test_result = {
                "url": url,
                "total_requests": concurrent_count,
                "successful_requests": success_count,
                "failed_requests": error_count,
                "success_rate": (success_count / concurrent_count) * 100,
                "total_time_seconds": total_time,
                "requests_per_second": concurrent_count / total_time,
                "response_times": {
                    "min_ms": min(response_times) if response_times else 0,
                    "max_ms": max(response_times) if response_times else 0,
                    "avg_ms": statistics.mean(response_times) if response_times else 0,
                    "median_ms": statistics.median(response_times) if response_times else 0,
                    "std_dev_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0
                }
            }
            
            engine_results["tests"][path] = test_result
            
            # Print summary
            print(f"     ✅ Success Rate: {test_result['success_rate']:.1f}% ({success_count}/{concurrent_count})")
            print(f"     ⚡ Requests/sec: {test_result['requests_per_second']:.2f}")
            print(f"     📊 Avg Response: {test_result['response_times']['avg_ms']:.1f}ms")
            print(f"     📈 Min/Max: {test_result['response_times']['min_ms']:.1f}ms / {test_result['response_times']['max_ms']:.1f}ms")
        
        return engine_results
    
    async def run_full_performance_test(self, concurrent_count: int = 10):
        """Run performance tests on all engines"""
        print("=" * 80)
        print("🚀 InfinityAI.Pro Performance Testing Suite")
        print("=" * 80)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔄 Concurrent requests per test: {concurrent_count}")
        
        all_results = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "concurrent_requests": concurrent_count,
                "total_engines": len(ENGINES)
            },
            "engines": {}
        }
        
        # Test each engine
        for engine_id, config in ENGINES.items():
            try:
                result = await self.test_engine_performance(engine_id, config, concurrent_count)
                all_results["engines"][engine_id] = result
            except Exception as e:
                print(f"   ❌ Error testing {engine_id}: {e}")
                all_results["engines"][engine_id] = {
                    "error": str(e),
                    "engine": engine_id,
                    "name": config['name']
                }
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 80)
        
        summary_stats = {
            "total_engines_tested": len([e for e in all_results["engines"].values() if "tests" in e]),
            "avg_response_times": {},
            "throughput_summary": {},
            "success_rates": {}
        }
        
        for engine_id, result in all_results["engines"].items():
            if "tests" in result:
                # Calculate average metrics across all endpoints for this engine
                all_response_times = []
                all_rps = []
                all_success_rates = []
                
                for path, test in result["tests"].items():
                    all_response_times.append(test["response_times"]["avg_ms"])
                    all_rps.append(test["requests_per_second"])
                    all_success_rates.append(test["success_rate"])
                
                if all_response_times:
                    summary_stats["avg_response_times"][engine_id] = statistics.mean(all_response_times)
                    summary_stats["throughput_summary"][engine_id] = statistics.mean(all_rps)
                    summary_stats["success_rates"][engine_id] = statistics.mean(all_success_rates)
                
                print(f"🔧 {result['name']}")
                print(f"   📊 Avg Response Time: {summary_stats['avg_response_times'][engine_id]:.1f}ms")
                print(f"   ⚡ Avg Throughput: {summary_stats['throughput_summary'][engine_id]:.2f} req/sec")
                print(f"   ✅ Success Rate: {summary_stats['success_rates'][engine_id]:.1f}%")
        
        # Overall platform performance
        if summary_stats["avg_response_times"]:
            overall_avg_response = statistics.mean(summary_stats["avg_response_times"].values())
            overall_throughput = sum(summary_stats["throughput_summary"].values())
            overall_success_rate = statistics.mean(summary_stats["success_rates"].values())
            
            print(f"\n🌟 OVERALL PLATFORM PERFORMANCE:")
            print(f"   📊 Average Response Time: {overall_avg_response:.1f}ms")
            print(f"   ⚡ Total Throughput: {overall_throughput:.2f} req/sec")
            print(f"   ✅ Overall Success Rate: {overall_success_rate:.1f}%")
            
            summary_stats["overall"] = {
                "avg_response_time_ms": overall_avg_response,
                "total_throughput_rps": overall_throughput,
                "overall_success_rate": overall_success_rate
            }
        
        all_results["summary"] = summary_stats
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return all_results

async def main():
    """Main performance testing function"""
    async with PerformanceTester() as tester:
        # Test with different concurrency levels
        results = {}
        
        # Light load test
        print("🧪 Running LIGHT LOAD test (5 concurrent requests)...")
        results["light_load"] = await tester.run_full_performance_test(5)
        
        # Medium load test  
        print("\n🧪 Running MEDIUM LOAD test (15 concurrent requests)...")
        results["medium_load"] = await tester.run_full_performance_test(15)
        
        # Save results
        with open("performance_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: performance_test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())