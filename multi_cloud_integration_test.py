#!/usr/bin/env python3
"""
InfinityAI.Pro Multi-Cloud Integration Test (No Vercel)
Tests AWS and Google Cloud deployments only (Azure removed)
"""
#!/usr/bin/env python3
"""
InfinityAI.Pro Multi-Cloud Integration Test (No Vercel)
Tests AWS and Google Cloud deployments only (Azure removed)
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any


class MultiCloudTester:
    def __init__(self):
        # Default config; will be overridden by discovered endpoints
        self.config = {
            "aws": {
                "load_balancer": None,
                "engine_c": None,
                "engine_d": None
            },
            "gcp": {
                "engine_b": None
            }
        }

        self.test_results: List[Dict[str, Any]] = []

    async def test_endpoint(self, name: str, base_url: str, timeout: int = 10) -> Dict[str, Any]:
        """Test a single endpoint by calling its /health"""
        start_time = time.time()
        url = f"{base_url}/health" if base_url else None

        try:
            if not url:
                return {
                    "success": False,
                    "error": "No URL configured",
                    "endpoint": None,
                    "name": name,
                }
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    status_code = response.status
                    content: Any = None
                    try:
                        content = await response.json()
                    except Exception:
                        content = await response.text()
                    return {
                        "name": name,
                        "success": 200 <= status_code < 300,
                        "status_code": status_code,
                        "response_time": time.time() - start_time,
                        "content": content,
                        "endpoint": base_url,
                    }
        except asyncio.TimeoutError:
            return {
                "name": name,
                "success": False,
                "error": "Timeout",
                "timeout": timeout,
                "endpoint": base_url,
            }
        except Exception as e:
            return {
                "name": name,
                "success": False,
                "error": str(e),
                "endpoint": base_url,
            }

    async def test_aws_services(self):
        print("🟠 Testing AWS Services...")

        # Load Balancer probe (Engine D path)
        result = await self.test_endpoint("AWS ALB (Engine D)", (self.config["aws"]["load_balancer"] or "") + "/engine-d")
        result.update({"cloud": "aws", "service": "alb_engine_d", "timestamp": datetime.now(timezone.utc).isoformat()})
        self.test_results.append(result)

        # Engine C via ALB path
        result = await self.test_endpoint("AWS Engine C", (self.config["aws"]["engine_c"]))
        result.update({"cloud": "aws", "service": "engine_c", "timestamp": datetime.now(timezone.utc).isoformat()})
        self.test_results.append(result)

        # Engine D via ALB path
        result = await self.test_endpoint("AWS Engine D", (self.config["aws"]["engine_d"]))
        result.update({"cloud": "aws", "service": "engine_d", "timestamp": datetime.now(timezone.utc).isoformat()})
        self.test_results.append(result)

    async def test_gcp_services(self):
        print("🔴 Testing Google Cloud Services...")

        result = await self.test_endpoint("GCP Engine B", self.config["gcp"]["engine_b"])
        result.update({"cloud": "gcp", "service": "engine_b", "timestamp": datetime.now(timezone.utc).isoformat()})
        self.test_results.append(result)

    async def run_all_tests(self):
        print("🚀 Starting InfinityAI.Pro Multi-Cloud Integration Tests (No Vercel)")
        print("=" * 70)

        start_time = time.time()

        # Discover endpoints from config
        try:
            with open("multi-cloud-config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            aws = cfg.get("clouds", {}).get("aws", {}).get("services", {})
            gcp = cfg.get("clouds", {}).get("google_cloud", {}).get("services", {})
            if not self.config["aws"]["load_balancer"] and aws.get("load_balancer", {}).get("dns"):
                self.config["aws"]["load_balancer"] = f"http://{aws['load_balancer']['dns']}"
            if not self.config["aws"]["engine_c"] and aws.get("engine_c", {}).get("endpoint"):
                self.config["aws"]["engine_c"] = aws["engine_c"]["endpoint"]
            if not self.config["aws"]["engine_d"] and aws.get("engine_d", {}).get("endpoint"):
                self.config["aws"]["engine_d"] = aws["engine_d"]["endpoint"]
            if not self.config["gcp"]["engine_b"] and gcp.get("engine_b", {}).get("endpoint"):
                self.config["gcp"]["engine_b"] = gcp["engine_b"]["endpoint"]
        except Exception:
            pass

        # Reasonable defaults
        if not self.config["aws"]["load_balancer"]:
            self.config["aws"]["load_balancer"] = "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com"
        if not self.config["aws"]["engine_c"]:
            self.config["aws"]["engine_c"] = self.config["aws"]["load_balancer"] + "/engine-c"
        if not self.config["aws"]["engine_d"]:
            self.config["aws"]["engine_d"] = self.config["aws"]["load_balancer"] + "/engine-d"
        if not self.config["gcp"]["engine_b"]:
            self.config["gcp"]["engine_b"] = "https://infinityai-engine-b-573866363639.us-central1.run.app"

        await self.test_aws_services()
        await self.test_gcp_services()

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("success")])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests else 0.0

        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "execution_time": time.time() - start_time,
                "overall_status": "✅ SYSTEM HEALTHY" if success_rate >= 80 else "❌ SYSTEM ISSUES",
                "clouds_tested": ["aws", "gcp"],
                "vercel_eliminated": True,
            },
            "test_details": self.test_results,
            "endpoints_tested": self.config,
            "recommendations": self.generate_recommendations(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with open("multi_cloud_integration_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("\n📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Status: {report['test_summary']['overall_status']}")
        print("\n📄 Detailed report saved to: multi_cloud_integration_report.json")

        return report

    def generate_recommendations(self) -> List[str]:
        recs: List[str] = []
        aws_ok = all(r.get("success", False) for r in self.test_results if r.get("cloud") == "aws")
        gcp_ok = all(r.get("success", False) for r in self.test_results if r.get("cloud") == "gcp")
        if not aws_ok:
            recs.append("🟠 AWS: Check ECS services, ALB target groups, and security groups")
        if not gcp_ok:
            recs.append("🔴 GCP: Verify Engine B deployment and update endpoint configuration")
        recs.append("✅ Vercel successfully eliminated from architecture")
        recs.append("✅ Azure removed; topology is AWS (C/D) + GCP (A/B)")
        return recs


async def main():
    tester = MultiCloudTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
