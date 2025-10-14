#!/usr/bin/env python3
"""
InfinityAI.Pro - Final System Integration Validation
Complete validation of all 5 engines across AWS and GCP
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import asyncio
import aiohttp
import ssl

class FinalSystemValidator:
    def __init__(self):
        # Engine configurations
        self.engines = {
            # GCP Cloud Run Engines
            "engine_a": {
                "name": "Engine A - Market Data Ingestion",
                "url": "https://infinityai-engine-a-573866363639.us-east1.run.app",
                "platform": "GCP Cloud Run",
                "expected_response_time": 500
            },
            "engine_b": {
                "name": "Engine B - AI/ML Processing", 
                "url": "https://infinityai-engine-b-573866363639.us-east1.run.app",
                "platform": "GCP Cloud Run",
                "expected_response_time": 600
            },
            "ultra_aggressive": {
                "name": "Ultra-Aggressive Trading Engine",
                "url": "https://infinityai-ultra-aggressive-573866363639.us-east1.run.app",
                "platform": "GCP Cloud Run",
                "expected_response_time": 400
            },
            # AWS ECS Engines - HTTPS ENABLED
            "engine_c": {
                "name": "Engine C - Trade Execution",
                "url": "https://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
                "platform": "AWS ECS/Fargate",
                "expected_response_time": 500
            },
            "engine_d": {
                "name": "Engine D - AI Chatbot Assistant",
                "url": "https://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d",
                "platform": "AWS ECS/Fargate", 
                "expected_response_time": 600
            }
        }
        
        # Frontend configuration
        self.frontend = {
            "name": "InfinityAI.Pro Frontend",
            "url": "https://infinityai.pro",
            "platform": "Cloudflare Pages"
        }
        
        self.validation_results = {}
        
        print("🚀 INFINITYAI.PRO - FINAL SYSTEM VALIDATION")
        print("=" * 70)
        print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
    
    def test_engine_health(self, engine_id: str, config: Dict) -> Dict:
        """Test individual engine health and performance"""
        results = {
            "name": config["name"],
            "platform": config["platform"],
            "connectivity": "❌ Failed",
            "health_status": "❌ Unhealthy",
            "response_time": 0,
            "performance_grade": "❌ Poor",
            "endpoints_accessible": 0,
            "ssl_valid": False,
            "integration_ready": False
        }
        
        try:
            print(f"\n🔍 VALIDATING: {config['name']}")
            print("=" * 60)
            
            # Test main endpoint
            start_time = time.time()
            response = requests.get(config["url"], timeout=10, verify=False)
            response_time = (time.time() - start_time) * 1000
            
            results["response_time"] = response_time
            
            if response.status_code == 200:
                results["connectivity"] = "✅ Connected"
                print(f"   ✅ Connectivity: Connected ({response.status_code})")
            else:
                results["connectivity"] = f"⚠️ Connected ({response.status_code})"
                print(f"   ⚠️ Connectivity: Connected but non-200 ({response.status_code})")
            
            # Test health endpoint
            health_url = f"{config['url']}/health"
            health_response = requests.get(health_url, timeout=10, verify=False)
            
            if health_response.status_code == 200:
                results["health_status"] = "✅ Healthy"
                results["integration_ready"] = True
                print(f"   ✅ Health Check: Healthy")
            else:
                results["health_status"] = f"❌ Unhealthy ({health_response.status_code})"
                print(f"   ❌ Health Check: Failed ({health_response.status_code})")
            
            # Performance validation
            if response_time < config["expected_response_time"]:
                results["performance_grade"] = "✅ Excellent"
                print(f"   ✅ Performance: {response_time:.2f}ms (Expected: <{config['expected_response_time']}ms)")
            else:
                results["performance_grade"] = "⚠️ Acceptable"
                print(f"   ⚠️ Performance: {response_time:.2f}ms (Expected: <{config['expected_response_time']}ms)")
            
            # Test additional endpoints
            endpoints = ["/health", "/metrics"]
            accessible_count = 0
            
            for endpoint in endpoints:
                try:
                    test_url = f"{config['url']}{endpoint}"
                    ep_response = requests.get(test_url, timeout=5, verify=False)
                    if ep_response.status_code in [200, 401]:  # 401 is acceptable for protected endpoints
                        accessible_count += 1
                except:
                    pass
            
            results["endpoints_accessible"] = accessible_count
            print(f"   ✅ Endpoints: {accessible_count}/{len(endpoints)} accessible")
            
            # SSL validation for HTTPS endpoints
            if config["url"].startswith("https://"):
                try:
                    ssl_response = requests.get(config["url"], timeout=5)
                    results["ssl_valid"] = True
                    print(f"   ✅ SSL Security: Valid")
                except:
                    print(f"   ❌ SSL Security: Invalid")
            else:
                print(f"   ⚠️ SSL Security: HTTP (not HTTPS)")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection Failed: {str(e)}")
        except Exception as e:
            print(f"   ❌ Validation Error: {str(e)}")
        
        return results
    
    def test_frontend_integration(self) -> Dict:
        """Test frontend connectivity and basic functionality"""
        print(f"\n🌐 VALIDATING FRONTEND")
        print("=" * 60)
        
        results = {
            "connectivity": "❌ Failed",
            "response_time": 0,
            "content_loaded": False,
            "ssl_valid": False
        }
        
        try:
            start_time = time.time()
            response = requests.get(self.frontend["url"], timeout=15)
            response_time = (time.time() - start_time) * 1000
            
            results["response_time"] = response_time
            
            if response.status_code == 200:
                results["connectivity"] = "✅ Connected"
                print(f"   ✅ Frontend Connectivity: Connected ({response.status_code})")
                
                # Check if it contains expected content
                if "InfinityAI.Pro" in response.text:
                    results["content_loaded"] = True
                    print(f"   ✅ Content Loading: InfinityAI.Pro content detected")
                else:
                    print(f"   ⚠️ Content Loading: Generic content")
                
                results["ssl_valid"] = True
                print(f"   ✅ SSL Security: Valid HTTPS")
                print(f"   ✅ Performance: {response_time:.2f}ms")
            else:
                results["connectivity"] = f"❌ Failed ({response.status_code})"
                print(f"   ❌ Frontend: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Frontend Error: {str(e)}")
        
        return results
    
    def test_cross_cloud_communication(self) -> List[Dict]:
        """Test communication paths between GCP and AWS engines"""
        print(f"\n🔄 CROSS-CLOUD COMMUNICATION VALIDATION")
        print("=" * 60)
        
        gcp_engines = ["engine_a", "engine_b", "ultra_aggressive"]
        aws_engines = ["engine_c", "engine_d"]
        
        communication_results = []
        
        for gcp_engine in gcp_engines:
            for aws_engine in aws_engines:
                gcp_config = self.engines[gcp_engine]
                aws_config = self.engines[aws_engine]
                
                # Test if both engines are accessible (prerequisite for communication)
                try:
                    gcp_response = requests.get(gcp_config["url"], timeout=5, verify=False)
                    aws_response = requests.get(aws_config["url"], timeout=5, verify=False)
                    
                    if gcp_response.status_code in [200, 404] and aws_response.status_code in [200, 404]:
                        status = "✅ POSSIBLE"
                        communication_results.append({
                            "from": gcp_engine,
                            "to": aws_engine,
                            "status": "possible",
                            "from_platform": "GCP",
                            "to_platform": "AWS"
                        })
                    else:
                        status = "❌ BLOCKED"
                        communication_results.append({
                            "from": gcp_engine,
                            "to": aws_engine,
                            "status": "blocked",
                            "from_platform": "GCP", 
                            "to_platform": "AWS"
                        })
                    
                    print(f"   {status} {gcp_engine} (GCP) ↔ {aws_engine} (AWS)")
                    
                except Exception as e:
                    print(f"   ❌ FAILED {gcp_engine} (GCP) ↔ {aws_engine} (AWS): {str(e)}")
                    communication_results.append({
                        "from": gcp_engine,
                        "to": aws_engine,
                        "status": "failed",
                        "error": str(e)
                    })
        
        return communication_results
    
    def generate_final_report(self) -> Dict:
        """Generate comprehensive system status report"""
        print(f"\n📋 FINAL SYSTEM STATUS REPORT")
        print("=" * 60)
        
        operational_engines = sum(1 for result in self.validation_results.values() 
                                 if result.get("connectivity") == "✅ Connected")
        total_engines = len(self.engines)
        success_rate = (operational_engines / total_engines) * 100
        
        critical_engines_down = sum(1 for result in self.validation_results.values()
                                  if result.get("health_status", "").startswith("❌"))
        
        # Overall system status
        if success_rate >= 100:
            overall_status = "🟢 FULLY OPERATIONAL"
        elif success_rate >= 80:
            overall_status = "🟡 MOSTLY OPERATIONAL"
        elif success_rate >= 60:
            overall_status = "🟠 PARTIALLY OPERATIONAL"
        else:
            overall_status = "🔴 CRITICAL ISSUES"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_engines": total_engines,
            "operational_engines": operational_engines,
            "success_rate": round(success_rate, 1),
            "critical_engines_down": critical_engines_down,
            "overall_status": overall_status,
            "engine_details": self.validation_results,
            "frontend_status": getattr(self, 'frontend_results', {}),
            "cross_cloud_communication": getattr(self, 'communication_results', [])
        }
        
        print(f"📊 ENGINE STATUS:")
        print(f"   Total Engines: {total_engines}")
        print(f"   Operational: {operational_engines}")
        print(f"   Success Rate: {success_rate}%")
        print(f"   Critical Engines Down: {critical_engines_down}")
        print(f"\n🎯 OVERALL SYSTEM STATUS: {overall_status}")
        
        # Save detailed report
        with open("final_system_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed validation report saved to: final_system_validation_report.json")
        
        return report
    
    def run_comprehensive_validation(self):
        """Execute complete system validation"""
        # Validate all engines
        for engine_id, config in self.engines.items():
            self.validation_results[engine_id] = self.test_engine_health(engine_id, config)
        
        # Test frontend
        self.frontend_results = self.test_frontend_integration()
        
        # Test cross-cloud communication
        self.communication_results = self.test_cross_cloud_communication()
        
        # Generate final report
        final_report = self.generate_final_report()
        
        print(f"\n🎉 Final system validation complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return final_report

if __name__ == "__main__":
    validator = FinalSystemValidator()
    final_report = validator.run_comprehensive_validation()