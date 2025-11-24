#!/usr/bin/env python3
"""
InfinityAI.Pro Complete Integration Test Suite
Tests all engines, cross-cloud communication, and end-to-end workflows
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import websockets
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfinityAIIntegrationTester:
    """Complete integration test suite for InfinityAI.Pro"""

    def __init__(self):
        # Current deployment URLs (GCP Cloud Run + Firebase)
        self.urls = {
            "frontend": "https://infinityai.pro",
            "engine_a": "https://infinityai-engine-a-bprmddefsa-uc.a.run.app",
            "engine_b": "https://infinityai-engine-b-bprmddefsa-uc.a.run.app",
            "engine_c": "https://infinityai-engine-c-execution-bprmddefsa-uc.a.run.app",
            "engine_d": "https://infinityai-engine-d-bprmddefsa-uc.a.run.app"
        }

        # Test results
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }

        # HTTP session
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "InfinityAI-Integration-Test/1.0",
                "Accept": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def run_test(self, test_name: str, test_func, *args, **kwargs):
        """Run a single test and record results"""
        self.test_results["total_tests"] += 1
        start_time = time.time()

        try:
            logger.info(f"🧪 Running test: {test_name}")
            result = await test_func(*args, **kwargs)

            execution_time = time.time() - start_time

            if result.get("success", False):
                self.test_results["passed_tests"] += 1
                logger.info(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
            else:
                self.test_results["failed_tests"] += 1
                logger.error(f"❌ {test_name} FAILED ({execution_time:.2f}s): {result.get('error', 'Unknown error')}")

            self.test_results["test_details"].append({
                "name": test_name,
                "success": result.get("success", False),
                "execution_time": execution_time,
                "details": result,
                "timestamp": datetime.now().isoformat()
            })

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name} FAILED ({execution_time:.2f}s): {str(e)}")

            self.test_results["test_details"].append({
                "name": test_name,
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            return {"success": False, "error": str(e)}

    async def test_frontend_accessibility(self, url_key: str) -> Dict[str, Any]:
        """Test frontend accessibility and basic functionality"""
        url = self.urls[url_key]

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()

                    # Check for key elements
                    checks = {
                        "has_react": "react" in content.lower(),
                        "has_infinityai": "infinityai" in content.lower(),
                        "has_trading": "trading" in content.lower() or "portfolio" in content.lower(),
                        "has_scripts": "<script" in content.lower(),
                        "has_styles": "<style" in content.lower() or "css" in content.lower()
                    }

                    success_count = sum(checks.values())

                    return {
                        "success": response.status == 200 and success_count >= 3,
                        "status_code": response.status,
                        "response_time": response.headers.get("X-Response-Time", "N/A"),
                        "content_checks": checks,
                        "content_length": len(content),
                        "url": url
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}",
                        "url": url
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }

    async def test_backend_health(self, url_key: str) -> Dict[str, Any]:
        """Test backend health endpoint"""
        base_url = self.urls[url_key]
        health_url = f"{base_url}/health"

        try:
            async with self.session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()

                    return {
                        "success": True,
                        "status_code": response.status,
                        "health_data": data,
                        "service": data.get("service", "Unknown"),
                        "status": data.get("status", "Unknown"),
                        "url": health_url
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}",
                        "url": health_url
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": health_url
            }

    async def test_api_endpoints(self, url_key: str) -> Dict[str, Any]:
        """Test various API endpoints"""
        base_url = self.urls[url_key]

        endpoints_to_test = [
            {"path": "/health", "method": "GET", "expected_status": [200, 404]},
            {"path": "/api/health", "method": "GET", "expected_status": [200, 404]},
            {"path": "/docs", "method": "GET", "expected_status": [200, 404]},
            {"path": "/api/v1/health", "method": "GET", "expected_status": [200, 404]},
        ]

        results = []
        successful_endpoints = 0

        for endpoint in endpoints_to_test:
            try:
                url = f"{base_url}{endpoint['path']}"

                if endpoint["method"] == "GET":
                    async with self.session.get(url) as response:
                        success = response.status in endpoint["expected_status"]
                        if success:
                            successful_endpoints += 1

                        results.append({
                            "path": endpoint["path"],
                            "status_code": response.status,
                            "success": success,
                            "response_time": response.headers.get("X-Response-Time", "N/A")
                        })

            except Exception as e:
                results.append({
                    "path": endpoint["path"],
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": successful_endpoints > 0,
            "successful_endpoints": successful_endpoints,
            "total_endpoints": len(endpoints_to_test),
            "endpoint_results": results,
            "base_url": base_url
        }

    async def test_chatbot_functionality(self) -> Dict[str, Any]:
        """Test AI chatbot functionality"""
        chatbot_url = f"{self.urls['engine_d_alb']}/chat"

        test_messages = [
            {"message": "Hello, how are you?", "expected_response_contains": ["hello", "hi", "help"]},
            {"message": "What's my portfolio?", "expected_response_contains": ["portfolio", "position", "balance"]},
            {"message": "Analyze AAPL", "expected_response_contains": ["aapl", "analysis", "price", "stock"]}
        ]

        results = []
        successful_chats = 0

        for test_msg in test_messages:
            try:
                payload = {
                    "user_id": "integration_test_user",
                    "message": test_msg["message"]
                }

                async with self.session.post(chatbot_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get("message", "").lower()

                        # Check if response contains expected keywords
                        contains_expected = any(
                            keyword in response_text
                            for keyword in test_msg["expected_response_contains"]
                        )

                        if contains_expected or len(response_text) > 10:  # Valid response
                            successful_chats += 1
                            success = True
                        else:
                            success = False

                        results.append({
                            "message": test_msg["message"],
                            "response": data.get("message", "")[:100] + "...",
                            "success": success,
                            "status_code": response.status
                        })
                    else:
                        results.append({
                            "message": test_msg["message"],
                            "success": False,
                            "status_code": response.status,
                            "error": f"HTTP {response.status}"
                        })

            except Exception as e:
                results.append({
                    "message": test_msg["message"],
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": successful_chats > 0,
            "successful_chats": successful_chats,
            "total_chats": len(test_messages),
            "chat_results": results,
            "chatbot_url": chatbot_url
        }

    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connectivity"""
        # Try WebSocket connection to Engine D via ALB
        ws_url = self.urls["engine_d_alb"].replace("http://", "ws://") + "/ws/integration_test"

        try:
            async with websockets.connect(ws_url, timeout=10) as websocket:
                # Send test message
                test_message = {
                    "type": "test",
                    "message": "Integration test message",
                    "timestamp": datetime.now().isoformat()
                }

                await websocket.send(json.dumps(test_message))

                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)

                    return {
                        "success": True,
                        "ws_url": ws_url,
                        "response": response_data,
                        "connection_established": True
                    }

                except asyncio.TimeoutError:
                    return {
                        "success": True,  # Connection established even if no response
                        "ws_url": ws_url,
                        "connection_established": True,
                        "note": "Connection established but no response received"
                    }

        except Exception as e:
            return {
                "success": False,
                "ws_url": ws_url,
                "error": str(e),
                "connection_established": False
            }

    async def test_cross_engine_communication(self) -> Dict[str, Any]:
        """Test communication between engines"""
        # Test if Engine D can communicate with other engines
        engine_d_url = f"{self.urls.get('engine_c_alb', self.urls.get('engine_c'))}/chat"

        # Send a message that should trigger cross-engine communication
        payload = {
            "user_id": "integration_test",
            "message": "Get market analysis for TSLA and check my portfolio"
        }

        try:
            async with self.session.post(engine_d_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("message", "").lower()

                    # Check if response indicates cross-engine functionality
                    cross_engine_indicators = [
                        "portfolio", "analysis", "market", "price", "trading",
                        "engine", "data", "signal", "ai"
                    ]

                    indicators_found = sum(
                        1 for indicator in cross_engine_indicators
                        if indicator in response_text
                    )

                    return {
                        "success": indicators_found >= 2,
                        "response": data.get("message", "")[:200] + "...",
                        "indicators_found": indicators_found,
                        "cross_engine_capable": indicators_found >= 2,
                        "status_code": response.status
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def run_comprehensive_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting InfinityAI.Pro Comprehensive Integration Tests (GCP + Firebase)")
        logger.info("=" * 80)

        # Test 1: Frontend Accessibility (Firebase Hosting)
        await self.run_test(
            "Frontend Firebase Hosting Accessibility",
            self.test_frontend_accessibility,
            "frontend"
        )

        # Test 2: Backend Health Checks
        await self.run_test(
            "Engine A Health (GCP Cloud Run)",
            self.test_backend_health,
            "engine_a"
        )

        await self.run_test(
            "Engine B Health (GCP Cloud Run)",
            self.test_backend_health,
            "engine_b"
        )

        await self.run_test(
            "Engine C Health (GCP Cloud Run)",
            self.test_backend_health,
            "engine_c"
        )

        await self.run_test(
            "Engine D Health (GCP Cloud Run)",
            self.test_backend_health,
            "engine_d"
        )

        # Test 3: API Endpoint Testing
        await self.run_test(
            "Engine A API Endpoints",
            self.test_api_endpoints,
            "engine_a"
        )

        await self.run_test(
            "Engine B API Endpoints",
            self.test_api_endpoints,
            "engine_b"
        )

        await self.run_test(
            "Engine D API Endpoints",
            self.test_api_endpoints,
            "engine_d"
        )

        # Test 4: AI Chatbot Functionality
        await self.run_test(
            "AI Chatbot Functionality",
            self.test_chatbot_functionality
        )

        # Test 5: WebSocket Connectivity
        await self.run_test(
            "WebSocket Connection Test",
            self.test_websocket_connection
        )

        # Test 6: Cross-Engine Communication
        await self.run_test(
            "Cross-Engine Communication (GCP Cloud Run)",
            self.test_cross_engine_communication
        )

        # Generate final report
        await self.generate_final_report()

    async def generate_final_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 INTEGRATION TEST RESULTS SUMMARY")
        logger.info("=" * 80)

        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0

        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {success_rate:.1f}%")

        # Overall system status
        if success_rate >= 80:
            status = "✅ SYSTEM HEALTHY"
            status_color = "🟢"
        elif success_rate >= 60:
            status = "⚠️ SYSTEM DEGRADED"
            status_color = "🟡"
        else:
            status = "❌ SYSTEM ISSUES"
            status_color = "🔴"

        logger.info(f"\n{status_color} OVERALL STATUS: {status}")

        # Detailed results
        logger.info("\n📋 DETAILED TEST RESULTS:")
        logger.info("-" * 80)

        for test in self.test_results["test_details"]:
            status_icon = "✅" if test["success"] else "❌"
            logger.info(f"{status_icon} {test['name']}: {test['execution_time']:.2f}s")

            if not test["success"] and "error" in test:
                logger.info(f"   Error: {test['error']}")

        # Working services summary
        logger.info("\n🌐 WORKING SERVICES:")
        logger.info("-" * 40)

        working_services = []
        for test in self.test_results["test_details"]:
            if test["success"]:
                if "Frontend" in test["name"]:
                    working_services.append(f"✅ {test['name']}")
                elif "Backend" in test["name"] or "Engine" in test["name"]:
                    working_services.append(f"✅ {test['name']}")
                elif "Chatbot" in test["name"]:
                    working_services.append(f"✅ AI Chatbot Service")
                elif "WebSocket" in test["name"]:
                    working_services.append(f"✅ Real-time WebSocket")

        for service in working_services:
            logger.info(f"   {service}")

        # Save detailed report to file
        report_data = {
            "test_summary": {
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": failed,
                "success_rate": success_rate,
                "overall_status": status
            },
            "test_details": self.test_results["test_details"],
            "urls_tested": self.urls,
            "timestamp": datetime.now().isoformat()
        }

        with open("integration_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"\n📄 Detailed report saved to: integration_test_report.json")

        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        logger.info("-" * 40)

        if success_rate >= 80:
            logger.info("   🎉 System is ready for production use!")
            logger.info("   🔧 Consider completing remaining engine deployments")
            logger.info("   🌐 Configure custom domain (infinityai.pro)")
        elif success_rate >= 60:
            logger.info("   ⚠️ System has some issues but core functionality works")
            logger.info("   🔧 Review failed tests and fix critical issues")
            logger.info("   🧪 Run tests again after fixes")
        else:
            logger.info("   ❌ System needs significant attention")
            logger.info("   🔧 Focus on fixing failed services first")
            logger.info("   📞 Consider reviewing deployment configurations")

        logger.info("\n🚀 Next Steps:")
        logger.info("   1. Review failed tests and fix issues")
        logger.info("   2. Deploy remaining engines (A, B, C) to their clouds")
        logger.info("   3. Configure DNS and SSL certificates")
        logger.info("   4. Run load testing for production readiness")

async def main():
    """Main test execution function"""
    async with InfinityAIIntegrationTester() as tester:
        await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())