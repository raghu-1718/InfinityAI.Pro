#!/usr/bin/env python3
"""
InfinityAI.Pro Multi-Cloud Integration Test (No Vercel)
Tests AWS, Azure, and Google Cloud deployments only
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class MultiCloudTester:
    def __init__(self):
        self.config = {
            "azure": {
                "engine_a": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
                "engine_a_alt": "https://infinityai-engine-a--0000006.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
                "frontend": "https://brave-ocean-09e85cd10-preview.centralus.2.azurestaticapps.net"
            },
            "aws": {
                "load_balancer": "http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com",
                "engine_c": "http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8002",
                "engine_d": "http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8000"
            },
            "gcp": {
                "engine_b": "https://engine-b-service.infinityai.pro"  # Placeholder - need actual GCP endpoint
            }
        }
        
        self.test_results = []
        
    async def test_endpoint(self, name: str, url: str, timeout: int = 10) -> Dict:
        """Test a single endpoint"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(f"{url}/health") as response:
                    status_code = response.status
                    if status_code == 200:
                        content = await response.json()
                        return {
                            "success": True,
                            "status_code": status_code,
                            "response_time": time.time() - start_time,
                            "content": content,
                            "endpoint": url
                        }
                    else:
                        return {
                            "success": False,
                            "status_code": status_code,
                            "error": f"HTTP {status_code}",
                            "endpoint": url
                        }
                        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Timeout",
                "timeout": timeout,
                "endpoint": url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "endpoint": url
            }
    
    async def test_azure_services(self):
        """Test all Azure services"""
        print("🔵 Testing Azure Services...")
        
        # Test Engine A (main)
        result = await self.test_endpoint("Azure Engine A", self.config["azure"]["engine_a"])
        self.test_results.append({
            "name": "Azure Engine A Health",
            "cloud": "azure",
            "service": "engine_a",
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Test Engine A (alternative)
        result = await self.test_endpoint("Azure Engine A Alt", self.config["azure"]["engine_a_alt"])
        self.test_results.append({
            "name": "Azure Engine A Alternative",
            "cloud": "azure", 
            "service": "engine_a_alt",
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Test Frontend
        start_time = time.time()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(self.config["azure"]["frontend"]) as response:
                    success = response.status == 200
                    self.test_results.append({
                        "name": "Azure Frontend Accessibility", 
                        "cloud": "azure",
                        "service": "static_web_app",
                        "success": success,
                        "status_code": response.status,
                        "execution_time": time.time() - start_time,
                        "endpoint": self.config["azure"]["frontend"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
        except Exception as e:
            self.test_results.append({
                "name": "Azure Frontend Accessibility",
                "cloud": "azure",
                "service": "static_web_app", 
                "success": False,
                "error": str(e),
                "endpoint": self.config["azure"]["frontend"],
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def test_aws_services(self):
        """Test AWS services"""
        print("🟠 Testing AWS Services...")
        
        # Test Load Balancer
        result = await self.test_endpoint("AWS Load Balancer", self.config["aws"]["load_balancer"])
        self.test_results.append({
            "name": "AWS Load Balancer Health",
            "cloud": "aws",
            "service": "application_load_balancer",
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Test Engine C
        result = await self.test_endpoint("AWS Engine C", self.config["aws"]["engine_c"])
        self.test_results.append({
            "name": "AWS Engine C Health",
            "cloud": "aws",
            "service": "engine_c",
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Test Engine D  
        result = await self.test_endpoint("AWS Engine D", self.config["aws"]["engine_d"])
        self.test_results.append({
            "name": "AWS Engine D Health",
            "cloud": "aws",
            "service": "engine_d", 
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_gcp_services(self):
        """Test Google Cloud services"""
        print("🔴 Testing Google Cloud Services...")
        
        # Test Engine B
        result = await self.test_endpoint("GCP Engine B", self.config["gcp"]["engine_b"])
        self.test_results.append({
            "name": "GCP Engine B Health",
            "cloud": "gcp",
            "service": "engine_b",
            **result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_cross_cloud_communication(self):
        """Test communication between clouds"""
        print("🌐 Testing Cross-Cloud Communication...")
        
        # Test Azure to AWS communication
        try:
            async with aiohttp.ClientSession() as session:
                # Simulate Azure Engine A calling AWS Engine C
                test_payload = {"source": "azure_engine_a", "target": "aws_engine_c", "test": True}
                async with session.post(f"{self.config['aws']['engine_c']}/api/cross-cloud-test", 
                                      json=test_payload, timeout=15) as response:
                    success = response.status == 200
                    self.test_results.append({
                        "name": "Azure to AWS Communication",
                        "cloud": "multi-cloud",
                        "service": "cross_cloud_comm",
                        "success": success,
                        "status_code": response.status,
                        "route": "azure_engine_a -> aws_engine_c",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        except Exception as e:
            self.test_results.append({
                "name": "Azure to AWS Communication",
                "cloud": "multi-cloud", 
                "service": "cross_cloud_comm",
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting InfinityAI.Pro Multi-Cloud Integration Tests (No Vercel)")
        print("=" * 70)
        
        start_time = time.time()
        
        # Run tests for each cloud
        await self.test_azure_services()
        await self.test_aws_services() 
        await self.test_gcp_services()
        await self.test_cross_cloud_communication()
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("success", False)])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "execution_time": time.time() - start_time,
                "overall_status": "✅ SYSTEM HEALTHY" if success_rate >= 80 else "❌ SYSTEM ISSUES",
                "clouds_tested": ["azure", "aws", "gcp"],
                "vercel_eliminated": True
            },
            "test_details": self.test_results,
            "endpoints_tested": self.config,
            "recommendations": self.generate_recommendations(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save report
        with open("multi_cloud_integration_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Status: {report['test_summary']['overall_status']}")
        print(f"\n📄 Detailed report saved to: multi_cloud_integration_report.json")
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check each cloud
        azure_tests = [r for r in self.test_results if r.get("cloud") == "azure"]
        aws_tests = [r for r in self.test_results if r.get("cloud") == "aws"]
        gcp_tests = [r for r in self.test_results if r.get("cloud") == "gcp"]
        
        azure_success = all(r.get("success", False) for r in azure_tests)
        aws_success = all(r.get("success", False) for r in aws_tests)
        gcp_success = all(r.get("success", False) for r in gcp_tests)
        
        if not azure_success:
            recommendations.append("🔵 Azure: Fix Container Apps deployment or redeploy Static Web App")
        
        if not aws_success:
            recommendations.append("🟠 AWS: Check ECS services, Load Balancer target groups, and security groups")
            
        if not gcp_success:
            recommendations.append("🔴 GCP: Verify Engine B deployment and update endpoint configuration")
        
        # Cross-cloud communication
        cross_cloud_tests = [r for r in self.test_results if r.get("cloud") == "multi-cloud"]
        if not all(r.get("success", False) for r in cross_cloud_tests):
            recommendations.append("🌐 Multi-Cloud: Update API routing and authentication between clouds")
        
        recommendations.append("✅ Vercel successfully eliminated from architecture")
        
        return recommendations

async def main():
    tester = MultiCloudTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())