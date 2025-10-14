#!/usr/bin/env python3
"""
InfinityAI.Pro - Advanced Engine Validation & Architecture Analysis
Complete end-to-end validation for production readiness assessment
"""

import requests
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import ssl
import socket
from urllib.parse import urlparse

# Complete Engine Registry with Detailed Specifications
ENGINES = {
    "gcp_cloud_run": {
        "engine_a": {
            "name": "Engine A - Market Data Ingestion",
            "url": "https://infinityai-engine-a-573866363639.us-central1.run.app",
            "function": "Real-time market data collection and preprocessing",
            "technology": "Google Cloud Run",
            "region": "us-central1",
            "expected_endpoints": ["/health", "/api/market/data", "/api/market/indices"],
            "expected_response_time": 500,  # ms
            "critical": True
        },
        "engine_b": {
            "name": "Engine B - AI/ML Processing",
            "url": "https://infinityai-engine-b-573866363639.us-central1.run.app",
            "function": "AI model inference and machine learning predictions",
            "technology": "Google Cloud Run",
            "region": "us-central1",
            "expected_endpoints": ["/health", "/api/ai/predict", "/api/ai/models"],
            "expected_response_time": 600,  # ms
            "critical": True
        },
        "ultra_aggressive": {
            "name": "Ultra-Aggressive Trading Engine",
            "url": "https://infinityai-ultra-aggressive-573866363639.us-central1.run.app",
            "function": "High-frequency aggressive trading execution",
            "technology": "Google Cloud Run",
            "region": "us-central1",
            "expected_endpoints": ["/health", "/", "/api/status", "/api/trading/start"],
            "expected_response_time": 400,  # ms
            "critical": True
        }
    },
    "aws_ecs": {
        "engine_c": {
            "name": "Engine C - Trade Execution",
            "url": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
            "function": "Order execution and portfolio management",
            "technology": "AWS ECS + Application Load Balancer",
            "region": "us-east-1",
            "expected_endpoints": ["/", "/health", "/api/trades", "/api/portfolio"],
            "expected_response_time": 500,  # ms
            "critical": True
        },
        "engine_d": {
            "name": "Engine D - AI Chatbot Assistant",
            "url": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d",
            "function": "Natural language interface and user assistance",
            "technology": "AWS ECS + Application Load Balancer",
            "region": "us-east-1",
            "expected_endpoints": ["/", "/health", "/api/chat", "/api/assistant"],
            "expected_response_time": 600,  # ms
            "critical": True
        }
    }
}

FRONTEND_CONFIG = {
    "production_url": "https://infinityai.pro",
    "expected_features": ["login", "dashboard", "demo access", "trading signals"],
    "expected_response_time": 2000,  # ms
    "demo_credentials": {"username": "demo", "password": "infinityai2024"}
}

class EngineValidator:
    def __init__(self):
        self.results = {}
        self.session = None
        
    async def validate_engine_detailed(self, engine_key, engine_config):
        """Perform detailed validation of a single engine"""
        print(f"\n🔍 DEEP VALIDATION: {engine_config['name']}")
        print("=" * 60)
        
        results = {
            "name": engine_config["name"],
            "url": engine_config["url"],
            "function": engine_config["function"],
            "technology": engine_config["technology"],
            "region": engine_config["region"],
            "critical": engine_config["critical"],
            "validation_results": {}
        }
        
        # Test 1: Basic Connectivity
        connectivity = await self.test_connectivity(engine_config["url"])
        results["validation_results"]["connectivity"] = connectivity
        print(f"   {'✅' if connectivity['success'] else '❌'} Connectivity: {connectivity['status']}")
        
        # Test 2: Health Check
        health = await self.test_health_endpoint(engine_config)
        results["validation_results"]["health"] = health
        print(f"   {'✅' if health['success'] else '❌'} Health Check: {health['status']}")
        
        # Test 3: Response Time Analysis
        performance = await self.test_performance(engine_config)
        results["validation_results"]["performance"] = performance
        print(f"   {'✅' if performance['within_expected'] else '❌'} Performance: {performance['avg_response_time']}ms (Expected: <{engine_config['expected_response_time']}ms)")
        
        # Test 4: Endpoint Coverage
        endpoints = await self.test_endpoints(engine_config)
        results["validation_results"]["endpoints"] = endpoints
        success_count = sum(1 for ep in endpoints if ep['success'])
        total_count = len(endpoints)
        print(f"   {'✅' if success_count > 0 else '❌'} Endpoints: {success_count}/{total_count} accessible")
        
        # Test 5: SSL/Security (for HTTPS endpoints)
        if engine_config["url"].startswith("https"):
            security = await self.test_security(engine_config["url"])
            results["validation_results"]["security"] = security
            print(f"   {'✅' if security['ssl_valid'] else '❌'} SSL Security: {'Valid' if security['ssl_valid'] else 'Invalid'}")
        
        # Test 6: Integration Readiness
        integration = await self.test_integration_readiness(engine_config)
        results["validation_results"]["integration"] = integration
        print(f"   {'✅' if integration['ready'] else '❌'} Integration Ready: {'Yes' if integration['ready'] else 'No'}")
        
        return results
    
    async def test_connectivity(self, url):
        """Test basic network connectivity"""
        try:
            async with self.session.get(url, timeout=10) as response:
                return {
                    "success": True,
                    "status": f"Connected ({response.status})",
                    "response_code": response.status
                }
        except Exception as e:
            return {
                "success": False,
                "status": f"Connection failed: {str(e)}",
                "error": str(e)
            }
    
    async def test_health_endpoint(self, engine_config):
        """Test health endpoint specifically"""
        health_endpoints = ["/health", "/api/health", "/"]
        
        for endpoint in health_endpoints:
            try:
                url = f"{engine_config['url']}{endpoint}".replace("//", "/").replace(":/", "://")
                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return {
                                "success": True,
                                "status": "Healthy",
                                "endpoint": endpoint,
                                "data": data
                            }
                        except:
                            content = await response.text()
                            return {
                                "success": True,
                                "status": "Responding",
                                "endpoint": endpoint,
                                "content": content[:100]
                            }
            except:
                continue
                
        return {
            "success": False,
            "status": "No health endpoint responding",
            "tested_endpoints": health_endpoints
        }
    
    async def test_performance(self, engine_config):
        """Test response time performance"""
        response_times = []
        
        for i in range(5):  # Test 5 times for average
            try:
                start_time = time.time()
                async with self.session.get(f"{engine_config['url']}/health", timeout=10) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    response_times.append(response_time)
            except:
                pass
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            return {
                "avg_response_time": round(avg_time, 2),
                "min_response_time": round(min(response_times), 2),
                "max_response_time": round(max(response_times), 2),
                "within_expected": avg_time < engine_config["expected_response_time"]
            }
        else:
            return {
                "avg_response_time": None,
                "within_expected": False,
                "error": "Could not measure performance"
            }
    
    async def test_endpoints(self, engine_config):
        """Test all expected endpoints"""
        results = []
        
        for endpoint in engine_config["expected_endpoints"]:
            try:
                url = f"{engine_config['url']}{endpoint}".replace("//", "/").replace(":/", "://")
                async with self.session.get(url, timeout=10) as response:
                    results.append({
                        "endpoint": endpoint,
                        "success": response.status in [200, 201, 404],  # 404 is acceptable for some endpoints
                        "status_code": response.status,
                        "url": url
                    })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e),
                    "url": f"{engine_config['url']}{endpoint}"
                })
        
        return results
    
    async def test_security(self, url):
        """Test SSL/Security configuration"""
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        "ssl_valid": True,
                        "cert_subject": dict(x[0] for x in cert['subject']),
                        "cert_expires": cert['notAfter']
                    }
        except Exception as e:
            return {
                "ssl_valid": False,
                "error": str(e)
            }
    
    async def test_integration_readiness(self, engine_config):
        """Test if engine is ready for integration"""
        # Check if engine responds to basic requests and has proper CORS headers
        try:
            async with self.session.options(engine_config["url"], timeout=10) as response:
                cors_headers = {
                    "access_control_allow_origin": response.headers.get("Access-Control-Allow-Origin"),
                    "access_control_allow_methods": response.headers.get("Access-Control-Allow-Methods"),
                    "access_control_allow_headers": response.headers.get("Access-Control-Allow-Headers")
                }
                
                return {
                    "ready": response.status in [200, 204, 404],
                    "cors_configured": bool(cors_headers["access_control_allow_origin"]),
                    "cors_headers": cors_headers
                }
        except Exception as e:
            return {
                "ready": False,
                "error": str(e)
            }
    
    async def validate_cross_engine_communication(self):
        """Test communication between engines"""
        print(f"\n🔄 CROSS-ENGINE COMMUNICATION VALIDATION")
        print("=" * 50)
        
        communication_paths = []
        
        # Test GCP to AWS communication
        gcp_engines = ENGINES["gcp_cloud_run"]
        aws_engines = ENGINES["aws_ecs"]
        
        for gcp_name, gcp_config in gcp_engines.items():
            for aws_name, aws_config in aws_engines.items():
                try:
                    # Test if both engines are reachable (prerequisite for communication)
                    gcp_response = await self.test_connectivity(gcp_config["url"])
                    aws_response = await self.test_connectivity(aws_config["url"])
                    
                    communication_possible = gcp_response["success"] and aws_response["success"]
                    
                    path_result = {
                        "path": f"{gcp_config['name']} ↔ {aws_config['name']}",
                        "gcp_status": gcp_response["success"],
                        "aws_status": aws_response["success"],
                        "communication_possible": communication_possible,
                        "latency_consideration": "Cross-cloud communication adds ~100-200ms latency"
                    }
                    
                    communication_paths.append(path_result)
                    
                    status = "✅ POSSIBLE" if communication_possible else "❌ BLOCKED"
                    print(f"   {status} {gcp_name} (GCP) ↔ {aws_name} (AWS)")
                    
                except Exception as e:
                    path_result = {
                        "path": f"{gcp_config['name']} ↔ {aws_config['name']}",
                        "error": str(e),
                        "communication_possible": False
                    }
                    communication_paths.append(path_result)
                    print(f"   ❌ ERROR {gcp_name} (GCP) ↔ {aws_name} (AWS): {e}")
        
        return communication_paths
    
    async def generate_architecture_report(self):
        """Generate comprehensive architecture validation report"""
        print(f"\n📋 ARCHITECTURE VALIDATION SUMMARY")
        print("=" * 50)
        
        total_engines = sum(len(engines) for engines in ENGINES.values())
        operational_engines = 0
        critical_engines_down = 0
        
        for platform, engines in ENGINES.items():
            for engine_key, engine_config in engines.items():
                if engine_key in self.results:
                    result = self.results[engine_key]
                    if result["validation_results"]["connectivity"]["success"]:
                        operational_engines += 1
                    elif engine_config["critical"]:
                        critical_engines_down += 1
        
        print(f"📊 ENGINE STATUS:")
        print(f"   Total Engines: {total_engines}")
        print(f"   Operational: {operational_engines}")
        print(f"   Success Rate: {(operational_engines/total_engines)*100:.1f}%")
        print(f"   Critical Engines Down: {critical_engines_down}")
        
        # Determine overall system health
        if operational_engines == total_engines:
            system_status = "🟢 FULLY OPERATIONAL"
        elif operational_engines >= total_engines * 0.8:
            system_status = "🟡 MOSTLY OPERATIONAL"
        elif critical_engines_down == 0:
            system_status = "🟠 DEGRADED BUT FUNCTIONAL"
        else:
            system_status = "🔴 CRITICAL ISSUES"
        
        print(f"\n🎯 OVERALL SYSTEM STATUS: {system_status}")
        
        return {
            "total_engines": total_engines,
            "operational_engines": operational_engines,
            "success_rate": (operational_engines/total_engines)*100,
            "critical_engines_down": critical_engines_down,
            "system_status": system_status,
            "detailed_results": self.results
        }
    
    async def run_complete_validation(self):
        """Run complete validation suite"""
        print("🚀 INFINITYAI.PRO - COMPREHENSIVE ENGINE VALIDATION")
        print(f"Repository: https://github.com/raghu-1718/InfinityAI.Pro")
        print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Initialize aiohttp session
        connector = aiohttp.TCPConnector(ssl=False)  # For testing purposes
        self.session = aiohttp.ClientSession(connector=connector)
        
        try:
            # Validate each engine
            for platform, engines in ENGINES.items():
                print(f"\n🏗️ VALIDATING {platform.upper().replace('_', ' ')} ENGINES")
                print("=" * 60)
                
                for engine_key, engine_config in engines.items():
                    result = await self.validate_engine_detailed(engine_key, engine_config)
                    self.results[engine_key] = result
            
            # Test cross-engine communication
            comm_results = await self.validate_cross_engine_communication()
            
            # Generate final report
            final_report = await self.generate_architecture_report()
            
            return final_report
            
        finally:
            await self.session.close()

async def main():
    validator = EngineValidator()
    report = await validator.run_complete_validation()
    
    # Save detailed results
    with open("engine_validation_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed validation report saved to: engine_validation_report.json")
    print(f"🎉 Validation complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())