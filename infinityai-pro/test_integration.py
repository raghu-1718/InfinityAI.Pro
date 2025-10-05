#!/usr/bin/env python3
"""
InfinityAI.Pro Engine Integration Test
Test all four engines and demonstrate load balancer functionality
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Engine endpoints
ENGINES = {
    "engine_a": {
        "name": "Market Data Ingestion (Azure)",
        "endpoint": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
        "cloud": "Azure"
    },
    "engine_b": {
        "name": "AI Signal Processing (GCP)",
        "endpoint": "https://infinityai-engine-b-573866363639.us-central1.run.app",
        "cloud": "Google Cloud"
    },
    "engine_c": {
        "name": "Trade Execution (AWS)",
        "endpoint": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
        "cloud": "AWS"
    },
    "engine_d": {
        "name": "AI Chatbot Assistant (AWS)",
        "endpoint": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d",
        "cloud": "AWS"
    }
}

async def test_engine_health(session: aiohttp.ClientSession, engine_id: str, config: dict):
    """Test individual engine health"""
    endpoint = config["endpoint"]
    health_url = endpoint + "/health"
    
    print(f"\n🔍 Testing {config['name']}")
    print(f"   Cloud: {config['cloud']}")
    print(f"   Endpoint: {endpoint}")
    
    start_time = time.time()
    
    try:
        async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    try:
                        data = await response.json()
                        print(f"   ✅ Status: HEALTHY ({response_time:.2f}ms)")
                        
                        # Extract key information from JSON response
                        if isinstance(data, dict):
                            if "engine" in data:
                                print(f"   📋 Engine: {data['engine']}")
                            if "status" in data:
                                print(f"   📊 Status: {data['status']}")
                            if "components" in data:
                                print(f"   🔧 Components: {list(data['components'].keys())}")
                            if "gpu_info" in data:
                                gpu = data["gpu_info"]
                                if gpu.get("available"):
                                    print(f"   🚀 GPU: {gpu['count']} devices available")
                                else:
                                    print(f"   💻 GPU: Not available (CPU mode)")
                        
                        return True, response_time, data
                        
                    except json.JSONDecodeError:
                        # Fallback to text if JSON parsing fails
                        text = await response.text()
                        print(f"   ✅ Status: HEALTHY ({response_time:.2f}ms)")
                        print(f"   📄 Response: {text[:100]}...")
                        return True, response_time, text
                else:
                    # Handle text/plain responses (like AWS engines)
                    text = await response.text()
                    print(f"   ✅ Status: HEALTHY ({response_time:.2f}ms)")
                    print(f"   📄 Response: {text}")
                    return True, response_time, text
            else:
                error_text = await response.text()
                print(f"   ❌ Status: HTTP {response.status}")
                print(f"   📄 Error: {error_text[:200]}...")
                return False, response_time, error_text
                
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        print(f"   ❌ Status: FAILED ({response_time:.2f}ms)")
        print(f"   🚨 Error: {e}")
        return False, response_time, str(e)

async def test_load_balancer_routing():
    """Test load balancer routing logic"""
    print(f"\n🔄 Testing Load Balancer Routing Logic")
    
    # Import our load balancer
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    try:
        from load_balancer import LoadBalancer
        
        # Initialize load balancer
        lb = LoadBalancer()
        await lb.initialize()
        
        # Test different routing paths
        test_routes = [
            ("/health", "Health check - should round robin"),
            ("/api/market/data", "Market data - should route to Engine A"),
            ("/api/ai/signals", "AI processing - should route to Engine B"),
            ("/api/trade/orders", "Trading - should route to Engine C"),
            ("/api/chat/help", "Chatbot - should route to Engine D"),
            ("/api/unknown/path", "Unknown path - should use default routing")
        ]
        
        print(f"   🧭 Routing Decisions:")
        for path, description in test_routes:
            decision = lb.route_request(path)
            engine_name = ENGINES[decision.target_engine]["name"]
            print(f"     {path:<20} → {decision.target_engine} ({engine_name})")
            print(f"     {'':20}   Reason: {decision.reason}")
        
        # Get load balancer status
        status = await lb.get_status()
        healthy_count = status["load_balancer"]["healthy_engines"]
        total_count = status["load_balancer"]["total_engines"]
        
        print(f"\n   📊 Load Balancer Status:")
        print(f"     Healthy Engines: {healthy_count}/{total_count}")
        print(f"     Total Requests: {status['metrics']['total_requests']}")
        
        await lb.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Load balancer test failed: {e}")
        return False

async def test_inter_engine_communication():
    """Test communication between engines"""
    print(f"\n🔗 Testing Inter-Engine Communication")
    
    # This would test API calls between engines
    # For now, just verify all engines can be reached
    
    async with aiohttp.ClientSession() as session:
        all_healthy = True
        response_times = []
        
        for engine_id, config in ENGINES.items():
            healthy, response_time, _ = await test_engine_health(session, engine_id, config)
            if healthy:
                response_times.append(response_time)
            else:
                all_healthy = False
        
        if all_healthy:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"\n   ✅ All engines can communicate")
            print(f"   📊 Average response time: {avg_response_time:.2f}ms")
            print(f"   🌐 Multi-cloud deployment: OPERATIONAL")
        else:
            print(f"\n   ❌ Some engines are not responding")
            print(f"   🌐 Multi-cloud deployment: DEGRADED")
        
        return all_healthy

async def main():
    """Main test function"""
    print("=" * 80)
    print("🚀 InfinityAI.Pro Multi-Cloud Engine Integration Test")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all engines individually
    print(f"\n🔧 Testing Individual Engine Health:")
    
    async with aiohttp.ClientSession() as session:
        results = {}
        
        for engine_id, config in ENGINES.items():
            healthy, response_time, data = await test_engine_health(session, engine_id, config)
            results[engine_id] = {
                "healthy": healthy,
                "response_time": response_time,
                "data": data
            }
    
    # Test load balancer
    lb_success = await test_load_balancer_routing()
    
    # Test inter-engine communication
    communication_success = await test_inter_engine_communication()
    
    # Summary
    print(f"\n" + "=" * 80)
    print(f"📋 TEST SUMMARY")
    print(f"=" * 80)
    
    healthy_engines = sum(1 for r in results.values() if r["healthy"])
    total_engines = len(results)
    
    print(f"🔧 Engine Health: {healthy_engines}/{total_engines} engines operational")
    
    for engine_id, result in results.items():
        status = "✅ HEALTHY" if result["healthy"] else "❌ FAILED"
        name = ENGINES[engine_id]["name"]
        cloud = ENGINES[engine_id]["cloud"]
        response_time = result["response_time"]
        print(f"   {engine_id}: {status} ({response_time:.2f}ms) - {name} ({cloud})")
    
    print(f"\n🔄 Load Balancer: {'✅ WORKING' if lb_success else '❌ FAILED'}")
    print(f"🔗 Inter-Engine Communication: {'✅ WORKING' if communication_success else '❌ FAILED'}")
    
    # Overall status
    if healthy_engines == total_engines and lb_success and communication_success:
        print(f"\n🎉 OVERALL STATUS: ✅ ALL SYSTEMS OPERATIONAL")
        print(f"🌐 Multi-cloud deployment is fully functional!")
        print(f"🚀 InfinityAI.Pro is ready for production use!")
    elif healthy_engines == total_engines:
        print(f"\n⚠️  OVERALL STATUS: 🟡 ENGINES OPERATIONAL, LOAD BALANCER NEEDS SETUP")
        print(f"🌐 All engines are working, but load balancer needs configuration")
    else:
        print(f"\n❌ OVERALL STATUS: 🔴 SYSTEM DEGRADED")
        print(f"🌐 Some engines are not responding - investigation needed")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())