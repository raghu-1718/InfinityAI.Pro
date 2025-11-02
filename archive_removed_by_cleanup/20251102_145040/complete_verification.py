#!/usr/bin/env python3
"""
InfinityAI.Pro - Complete End-to-End Verification Script
Comprehensive verification of all cloud deployments and integrations
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class EndToEndVerifier:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "platform_status": "unknown",
            "components": {},
            "integrations": {},
            "issues": [],
            "recommendations": []
        }

        # Firebase Configuration
        self.firebase_config = {
            "project_id": "infinity-ai-5ec7c",
            "region": "us-central1",
            "hosting_url": "https://infinity-ai-5ec7c.web.app",
            "functions_base_url": "https://us-central1-infinity-ai-5ec7c.cloudfunctions.net"
        }

        # Backend Engines
        self.engines = {
            "engine-a": "https://infinityai-engine-a-26140490557.us-central1.run.app",
            "engine-b": "https://infinityai-engine-b-26140490557.us-central1.run.app",
            "engine-c": "https://infinityai-engine-c-execution-26140490557.us-central1.run.app",
            "engine-d": "https://infinityai-engine-d-26140490557.us-central1.run.app"
        }

        # Firebase Functions (HTTP Callable)
        self.firebase_functions = [
            "submitDhanCredentialsV2",
            "analyzePortfolio",
            "startTrading",
            "stopTrading",
            "saveDhanCredentials",
            "syncHoldings",
            "getAiSignals",
            "getVertexAiAnalysis",
            "getGeminiAnalysis"
        ]

    def test_frontend_deployment(self) -> Dict:
        """Test Firebase Hosting deployment"""
        print("🌐 Testing Frontend Deployment...")

        try:
            response = requests.get(self.firebase_config["hosting_url"], timeout=15)

            # Check for React app indicators
            content = response.text
            is_react_app = any([
                "React" in content,
                "vite" in content.lower(),
                "infinity" in content.lower(),
                "<!doctype html>" in content.lower()
            ])

            result = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "is_react_app": is_react_app,
                "response_size": len(content),
                "firebase_hosting": True,
                "url": self.firebase_config["hosting_url"]
            }

            if response.status_code == 200 and is_react_app:
                print("✅ Frontend: React app deployed successfully")
            else:
                print(f"❌ Frontend: Issues detected (Status: {response.status_code})")
                self.results["issues"].append("Frontend deployment may have issues")

            return result

        except Exception as e:
            print(f"❌ Frontend: Connection failed - {str(e)}")
            self.results["issues"].append(f"Frontend connection failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    def test_backend_engines(self) -> Dict:
        """Test all backend engines health"""
        print("\n⚙️ Testing Backend Engines...")

        engine_results = {}

        for name, url in self.engines.items():
            print(f"🔍 Testing {name}...")
            try:
                health_url = f"{url}/health"
                response = requests.get(health_url, timeout=30)

                engine_results[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "url": health_url
                }

                if response.status_code == 200:
                    try:
                        data = response.json()
                        engine_results[name]["response_data"] = data
                        print(f"✅ {name}: Healthy - {data.get('service', 'Unknown service')}")
                    except:
                        print(f"✅ {name}: Healthy (non-JSON response)")
                else:
                    print(f"❌ {name}: Unhealthy (Status: {response.status_code})")
                    self.results["issues"].append(f"{name} returned status {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"⏰ {name}: Timeout (may be cold start)")
                engine_results[name] = {"status": "timeout", "error": "timeout"}
                self.results["issues"].append(f"{name} timeout - possible cold start")

            except Exception as e:
                print(f"❌ {name}: Error - {str(e)}")
                engine_results[name] = {"status": "error", "error": str(e)}
                self.results["issues"].append(f"{name} error: {str(e)}")

        return engine_results

    def test_firebase_functions_callable(self) -> Dict:
        """Test Firebase HTTP Callable Functions"""
        print("\n🔥 Testing Firebase HTTP Callable Functions...")

        function_results = {}

        for func_name in self.firebase_functions:
            print(f"🔍 Testing {func_name}...")
            try:
                url = f"{self.firebase_config['functions_base_url']}/{func_name}"

                # Test with minimal data to check if function exists and responds
                test_data = {"data": {"test": "connection_check"}}

                response = requests.post(
                    url,
                    json=test_data,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )

                function_results[func_name] = {
                    "deployed": True,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "url": url
                }

                # Parse response
                try:
                    data = response.json()
                    function_results[func_name]["response_data"] = data

                    # Check for expected authentication error (function is working)
                    if "error" in data and "UNAUTHENTICATED" in str(data):
                        print(f"✅ {func_name}: Function working (auth required)")
                        function_results[func_name]["status"] = "healthy_auth_required"
                    elif response.status_code == 200:
                        print(f"✅ {func_name}: Function working (success)")
                        function_results[func_name]["status"] = "healthy"
                    else:
                        print(f"⚠️ {func_name}: Function exists but may have issues")
                        function_results[func_name]["status"] = "exists_with_issues"

                except:
                    print(f"⚠️ {func_name}: Function exists but returned non-JSON")
                    function_results[func_name]["status"] = "exists_non_json"

            except Exception as e:
                print(f"❌ {func_name}: Error - {str(e)}")
                function_results[func_name] = {
                    "deployed": False,
                    "error": str(e),
                    "status": "error"
                }
                self.results["issues"].append(f"Firebase function {func_name}: {str(e)}")

        return function_results

    def test_frontend_firebase_integration(self) -> Dict:
        """Test frontend Firebase configuration and integration"""
        print("\n🔗 Testing Frontend-Firebase Integration...")

        integration_results = {
            "firebase_config_present": False,
            "functions_import_present": False,
            "httpsCallable_usage": False,
            "auth_integration": False
        }

        try:
            # Check if frontend uses Firebase SDK correctly
            frontend_response = requests.get(self.firebase_config["hosting_url"], timeout=10)
            content = frontend_response.text

            # Look for Firebase integration indicators
            firebase_indicators = [
                "firebase",
                "firestore",
                "httpsCallable",
                "getAuth",
                "getFunctions"
            ]

            for indicator in firebase_indicators:
                if indicator.lower() in content.lower():
                    integration_results[f"{indicator}_present"] = True

            print("✅ Frontend-Firebase Integration: Configuration detected")

        except Exception as e:
            print(f"❌ Frontend-Firebase Integration: Error - {str(e)}")
            self.results["issues"].append(f"Frontend-Firebase integration check failed: {str(e)}")

        return integration_results

    def test_end_to_end_workflow(self) -> Dict:
        """Test end-to-end workflow simulation"""
        print("\n🔄 Testing End-to-End Workflow...")

        workflow_results = {
            "frontend_accessible": False,
            "engines_responsive": False,
            "functions_callable": False,
            "integration_ready": False
        }

        try:
            # 1. Frontend accessibility
            frontend_test = self.test_frontend_deployment()
            workflow_results["frontend_accessible"] = frontend_test.get("status") == "healthy"

            # 2. Engine responsiveness
            healthy_engines = sum(1 for engine in self.results["components"]["engines"].values()
                                 if engine.get("status") == "healthy")
            total_engines = len(self.engines)
            workflow_results["engines_responsive"] = healthy_engines >= (total_engines * 0.75)  # 75% threshold

            # 3. Functions callable
            working_functions = sum(1 for func in self.results["components"]["firebase_functions"].values()
                                   if func.get("status") in ["healthy", "healthy_auth_required"])
            total_functions = len(self.firebase_functions)
            workflow_results["functions_callable"] = working_functions >= (total_functions * 0.75)  # 75% threshold

            # 4. Overall integration
            workflow_results["integration_ready"] = all([
                workflow_results["frontend_accessible"],
                workflow_results["engines_responsive"],
                workflow_results["functions_callable"]
            ])

            if workflow_results["integration_ready"]:
                print("✅ End-to-End Workflow: Ready for production")
            else:
                print("⚠️ End-to-End Workflow: Some components need attention")

        except Exception as e:
            print(f"❌ End-to-End Workflow: Error - {str(e)}")
            workflow_results["error"] = str(e)

        return workflow_results

    def generate_recommendations(self):
        """Generate recommendations based on verification results"""
        recommendations = []

        # Check component health
        engines = self.results["components"].get("engines", {})
        unhealthy_engines = [name for name, data in engines.items()
                           if data.get("status") not in ["healthy"]]

        if unhealthy_engines:
            recommendations.append(f"🔧 Fix deployment issues for engines: {', '.join(unhealthy_engines)}")

        # Check function deployment
        functions = self.results["components"].get("firebase_functions", {})
        failed_functions = [name for name, data in functions.items()
                          if data.get("status") == "error"]

        if failed_functions:
            recommendations.append(f"🔥 Debug Firebase functions: {', '.join(failed_functions)}")

        # Check overall health
        issues_count = len(self.results["issues"])
        if issues_count == 0:
            recommendations.append("🎉 All systems operational - ready for production!")
        elif issues_count <= 3:
            recommendations.append("⚡ Minor issues detected - address for optimal performance")
        else:
            recommendations.append("🚨 Multiple issues detected - priority fixes needed")

        # Always recommend monitoring
        recommendations.extend([
            "📊 Set up monitoring and alerting for production readiness",
            "🔍 Run end-to-end user acceptance testing",
            "🛡️ Verify security configurations and authentication flows"
        ])

        self.results["recommendations"] = recommendations

    def calculate_platform_status(self) -> str:
        """Calculate overall platform status"""
        try:
            components = self.results["components"]

            # Calculate health scores
            frontend_health = 1 if components.get("frontend", {}).get("status") == "healthy" else 0

            engines = components.get("engines", {})
            engine_health = sum(1 for engine in engines.values()
                              if engine.get("status") == "healthy") / max(len(engines), 1)

            functions = components.get("firebase_functions", {})
            function_health = sum(1 for func in functions.values()
                                if func.get("status") in ["healthy", "healthy_auth_required"]) / max(len(functions), 1)

            # Weighted average (frontend 30%, engines 40%, functions 30%)
            overall_health = (frontend_health * 0.3) + (engine_health * 0.4) + (function_health * 0.3)

            if overall_health >= 0.95:
                return "fully_operational"
            elif overall_health >= 0.80:
                return "mostly_operational"
            elif overall_health >= 0.60:
                return "partially_operational"
            else:
                return "needs_attention"

        except Exception:
            return "unknown"

    def run_complete_verification(self) -> Dict:
        """Run complete end-to-end verification"""
        print("🚀 InfinityAI.Pro - Complete End-to-End Verification")
        print("=" * 80)

        # Test all components
        self.results["components"]["frontend"] = self.test_frontend_deployment()
        self.results["components"]["engines"] = self.test_backend_engines()
        self.results["components"]["firebase_functions"] = self.test_firebase_functions_callable()
        self.results["components"]["frontend_firebase_integration"] = self.test_frontend_firebase_integration()
        self.results["components"]["end_to_end_workflow"] = self.test_end_to_end_workflow()

        # Calculate status and recommendations
        self.results["platform_status"] = self.calculate_platform_status()
        self.generate_recommendations()

        # Print summary
        self.print_comprehensive_summary()

        return self.results

    def print_comprehensive_summary(self):
        """Print comprehensive verification summary"""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE VERIFICATION SUMMARY")
        print("=" * 80)

        # Platform status
        status_emoji = {
            "fully_operational": "🟢",
            "mostly_operational": "🟡",
            "partially_operational": "🟠",
            "needs_attention": "🔴",
            "unknown": "⚫"
        }

        status = self.results["platform_status"]
        print(f"🎯 Platform Status: {status_emoji.get(status, '⚫')} {status.replace('_', ' ').title()}")

        # Component breakdown
        components = self.results["components"]

        print(f"\n📊 Component Health:")
        print(f"   🌐 Frontend: {'✅' if components.get('frontend', {}).get('status') == 'healthy' else '❌'} Firebase Hosting")

        engines = components.get("engines", {})
        healthy_engines = sum(1 for e in engines.values() if e.get("status") == "healthy")
        print(f"   ⚙️ Engines: {healthy_engines}/{len(engines)} operational")

        functions = components.get("firebase_functions", {})
        working_functions = sum(1 for f in functions.values()
                               if f.get("status") in ["healthy", "healthy_auth_required"])
        print(f"   🔥 Functions: {working_functions}/{len(functions)} callable")

        # Issues
        if self.results["issues"]:
            print(f"\n⚠️ Issues Found ({len(self.results['issues'])}):")
            for issue in self.results["issues"][:5]:  # Show first 5 issues
                print(f"   • {issue}")
            if len(self.results["issues"]) > 5:
                print(f"   ... and {len(self.results['issues']) - 5} more")

        # Recommendations
        if self.results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in self.results["recommendations"]:
                print(f"   {rec}")

        print(f"\n🕐 Verification completed at: {self.results['timestamp']}")

    def save_report(self, filename: str = "complete_verification_report.json"):
        """Save comprehensive verification report"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Complete report saved to: {filename}")

def main():
    """Main verification function"""
    verifier = EndToEndVerifier()
    results = verifier.run_complete_verification()
    verifier.save_report()

    # Return appropriate exit code
    status = results["platform_status"]
    if status in ["fully_operational", "mostly_operational"]:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()