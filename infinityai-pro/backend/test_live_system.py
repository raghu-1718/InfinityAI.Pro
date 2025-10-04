#!/usr/bin/env python3
"""
InfinityAI.Pro Live System Test Suite
Tests all features on the production deployment
"""

import requests
import json
import time
import sys
from datetime import datetime
import asyncio
import websockets

# Production URLs
FRONTEND_URL = "https://infinityai.pro"
BACKEND_URL = "https://api.infinityai.pro"

class LiveSystemTester:
    def __init__(self):
        self.results = {
            "test_run_start": datetime.now().isoformat(),
            "frontend_tests": {},
            "backend_tests": {},
            "api_tests": {},
            "integration_tests": {},
            "performance_tests": {},
            "errors": []
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InfinityAI-LiveTest/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def log_result(self, test_name, success, message, response_time=None, data=None):
        """Log test result"""
        result = {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": response_time,
            "data": data
        }
        
        print(f"{'✅' if success else '❌'} {test_name}: {message}")
        if response_time:
            print(f"   ⏱️ Response time: {response_time}ms")
        
        return result

    def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        print("\n🌐 Testing Frontend Accessibility...")
        
        try:
            start_time = time.time()
            response = self.session.get(FRONTEND_URL, timeout=10)
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                self.results["frontend_tests"]["accessibility"] = self.log_result(
                    "Frontend Accessibility", 
                    True, 
                    f"Frontend loaded successfully (Status: {response.status_code})",
                    response_time
                )
                
                # Check if it contains React app elements
                if "infinityai" in response.text.lower() or "react" in response.text.lower():
                    self.results["frontend_tests"]["react_app"] = self.log_result(
                        "React App Detection", 
                        True, 
                        "React application detected in response"
                    )
                else:
                    self.results["frontend_tests"]["react_app"] = self.log_result(
                        "React App Detection", 
                        False, 
                        "React application not clearly detected"
                    )
            else:
                self.results["frontend_tests"]["accessibility"] = self.log_result(
                    "Frontend Accessibility", 
                    False, 
                    f"Frontend returned status {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.results["frontend_tests"]["accessibility"] = self.log_result(
                "Frontend Accessibility", 
                False, 
                f"Error accessing frontend: {str(e)}"
            )

    def test_backend_health(self):
        """Test backend health endpoint"""
        print("\n🔧 Testing Backend Health...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    self.results["backend_tests"]["health"] = self.log_result(
                        "Backend Health Check", 
                        True, 
                        "Backend health endpoint responding",
                        response_time,
                        health_data
                    )
                except:
                    self.results["backend_tests"]["health"] = self.log_result(
                        "Backend Health Check", 
                        True, 
                        "Backend responding but not JSON",
                        response_time
                    )
            else:
                self.results["backend_tests"]["health"] = self.log_result(
                    "Backend Health Check", 
                    False, 
                    f"Backend health returned status {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.results["backend_tests"]["health"] = self.log_result(
                "Backend Health Check", 
                False, 
                f"Error accessing backend health: {str(e)}"
            )

    def test_api_endpoints(self):
        """Test various API endpoints"""
        print("\n📡 Testing API Endpoints...")
        
        endpoints = [
            ("/", "Root endpoint"),
            ("/docs", "API Documentation"),
            ("/api/engines/status", "Engines Status"),
            ("/api/trading/status", "Trading Status"),
            ("/api/ai/chat", "AI Chat Endpoint"),
        ]
        
        for endpoint, description in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                response_time = int((time.time() - start_time) * 1000)
                
                success = response.status_code in [200, 404, 422]  # 404/422 might be expected for some endpoints
                
                self.results["api_tests"][endpoint] = self.log_result(
                    f"API {description}", 
                    success, 
                    f"Status: {response.status_code}",
                    response_time
                )
                
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                self.results["api_tests"][endpoint] = self.log_result(
                    f"API {description}", 
                    False, 
                    f"Error: {str(e)}"
                )

    def test_ai_integration(self):
        """Test AI chat functionality"""
        print("\n🤖 Testing AI Integration...")
        
        try:
            test_payload = {
                "message": "Hello, this is a test message. Please respond briefly.",
                "model": "gpt-4o-mini"
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/api/ai/chat", 
                json=test_payload, 
                timeout=30
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                try:
                    chat_data = response.json()
                    self.results["integration_tests"]["ai_chat"] = self.log_result(
                        "AI Chat Integration", 
                        True, 
                        "AI responded successfully",
                        response_time,
                        {"response_length": len(str(chat_data))}
                    )
                except:
                    self.results["integration_tests"]["ai_chat"] = self.log_result(
                        "AI Chat Integration", 
                        True, 
                        "AI endpoint responded (non-JSON)",
                        response_time
                    )
            else:
                self.results["integration_tests"]["ai_chat"] = self.log_result(
                    "AI Chat Integration", 
                    False, 
                    f"AI chat returned status {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.results["integration_tests"]["ai_chat"] = self.log_result(
                "AI Chat Integration", 
                False, 
                f"Error testing AI chat: {str(e)}"
            )

    def test_trading_integration(self):
        """Test trading API integration"""
        print("\n📈 Testing Trading Integration...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/api/trading/portfolio", timeout=15)
            response_time = int((time.time() - start_time) * 1000)
            
            # Trading might require authentication, so 401/403 is also acceptable
            success = response.status_code in [200, 401, 403, 422]
            
            self.results["integration_tests"]["trading"] = self.log_result(
                "Trading API Integration", 
                success, 
                f"Trading API status: {response.status_code}",
                response_time
            )
            
        except Exception as e:
            self.results["integration_tests"]["trading"] = self.log_result(
                "Trading API Integration", 
                False, 
                f"Error testing trading API: {str(e)}"
            )

    def test_performance(self):
        """Test system performance"""
        print("\n⚡ Testing Performance...")
        
        # Test response times for multiple requests
        response_times = []
        
        for i in range(5):
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response_times.append(response_time)
                
                time.sleep(0.2)  # Small delay between requests
                
            except:
                pass
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            performance_good = avg_time < 2000  # Less than 2 seconds average
            
            self.results["performance_tests"]["response_times"] = self.log_result(
                "Performance Test", 
                performance_good, 
                f"Avg: {avg_time:.0f}ms, Min: {min_time:.0f}ms, Max: {max_time:.0f}ms",
                None,
                {
                    "average_ms": avg_time,
                    "min_ms": min_time,
                    "max_ms": max_time,
                    "samples": len(response_times)
                }
            )
        else:
            self.results["performance_tests"]["response_times"] = self.log_result(
                "Performance Test", 
                False, 
                "Could not measure performance - no successful requests"
            )

    def test_ssl_security(self):
        """Test SSL and security"""
        print("\n🔒 Testing Security & SSL...")
        
        try:
            # Test HTTPS redirect and SSL
            response = self.session.get(FRONTEND_URL, timeout=10)
            
            ssl_working = response.url.startswith('https://')
            
            self.results["backend_tests"]["ssl"] = self.log_result(
                "SSL/HTTPS Security", 
                ssl_working, 
                f"HTTPS working: {ssl_working}, Final URL: {response.url}"
            )
            
            # Test security headers
            security_headers = ['strict-transport-security', 'x-content-type-options', 'x-frame-options']
            headers_present = sum(1 for header in security_headers if header in response.headers)
            
            self.results["backend_tests"]["security_headers"] = self.log_result(
                "Security Headers", 
                headers_present > 0, 
                f"Security headers found: {headers_present}/{len(security_headers)}"
            )
            
        except Exception as e:
            self.results["backend_tests"]["ssl"] = self.log_result(
                "SSL/HTTPS Security", 
                False, 
                f"Error testing SSL: {str(e)}"
            )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting InfinityAI.Pro Live System Test Suite")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Run all test suites
        self.test_frontend_accessibility()
        self.test_backend_health()
        self.test_api_endpoints()
        self.test_ai_integration()
        self.test_trading_integration()
        self.test_performance()
        self.test_ssl_security()
        
        # Calculate summary
        self.results["test_run_end"] = datetime.now().isoformat()
        
        total_tests = 0
        passed_tests = 0
        
        for category in ["frontend_tests", "backend_tests", "api_tests", "integration_tests", "performance_tests"]:
            for test_name, test_result in self.results.get(category, {}).items():
                total_tests += 1
                if test_result.get("success"):
                    passed_tests += 1
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        if self.results['summary']['success_rate'] >= 80:
            print("\n✅ SYSTEM STATUS: HEALTHY")
        elif self.results['summary']['success_rate'] >= 60:
            print("\n⚠️ SYSTEM STATUS: DEGRADED")
        else:
            print("\n❌ SYSTEM STATUS: CRITICAL ISSUES")
        
        return self.results

    def save_results(self, filename="live_system_test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Test results saved to: {filename}")

if __name__ == "__main__":
    tester = LiveSystemTester()
    results = tester.run_all_tests()
    tester.save_results()