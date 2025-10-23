#!/usr/bin/env python3
"""
InfinityAI.Pro - Comprehensive Platform Diagnostics
==================================================
This script performs end-to-end diagnostics equivalent to Gemini MCP commands
to identify and resolve platform issues including Engine D errors and AI analysis failures.
"""

import requests
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any

class InfinityAIDiagnostics:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.api_key = "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU"
        self.frontend_url = "https://infinity-ai-5ec7c.web.app"
        self.engines = {
            "engine-a": "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app",
            "engine-b": "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app",
            "engine-c": "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app",
            "engine-d": "https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app"
        }
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "diagnostics": {},
            "issues_found": [],
            "recommendations": []
        }

    def log_issue(self, category: str, issue: str, severity: str = "MEDIUM"):
        """Log an issue found during diagnostics"""
        self.results["issues_found"].append({
            "category": category,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })

    def add_recommendation(self, category: str, recommendation: str):
        """Add a recommendation for fixing issues"""
        self.results["recommendations"].append({
            "category": category,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        })

    def test_engine_health(self, engine_name: str, engine_url: str) -> Dict[str, Any]:
        """Test individual engine health and specific APIs"""
        print(f"\n🔍 Testing {engine_name.upper()} Health & APIs")
        print("-" * 50)

        result = {
            "name": engine_name,
            "url": engine_url,
            "health": "UNKNOWN",
            "latency": None,
            "apis": {},
            "errors": []
        }

        try:
            # Test health endpoint
            start_time = time.time()
            health_response = requests.get(f"{engine_url}/health", timeout=10)
            latency = (time.time() - start_time) * 1000

            result["latency"] = f"{latency:.2f}ms"

            if health_response.status_code == 200:
                health_data = health_response.json()
                result["health"] = "HEALTHY"
                print(f"✅ {engine_name}: {health_data.get('status', 'healthy')} ({latency:.2f}ms)")
            else:
                result["health"] = "UNHEALTHY"
                result["errors"].append(f"Health endpoint returned {health_response.status_code}")
                print(f"❌ {engine_name}: Health check failed - {health_response.status_code}")
                self.log_issue("ENGINE_HEALTH", f"{engine_name} health check failed", "HIGH")

        except Exception as e:
            result["health"] = "ERROR"
            result["errors"].append(str(e))
            print(f"❌ {engine_name}: Connection failed - {str(e)}")
            self.log_issue("ENGINE_CONNECTIVITY", f"{engine_name} connection failed: {str(e)}", "HIGH")

        # Test specific engine APIs based on engine type
        if engine_name == "engine-a":
            self.test_engine_a_apis(engine_url, result)
        elif engine_name == "engine-b":
            self.test_engine_b_apis(engine_url, result)
        elif engine_name == "engine-c":
            self.test_engine_c_apis(engine_url, result)
        elif engine_name == "engine-d":
            self.test_engine_d_apis(engine_url, result)

        return result

    def test_engine_a_apis(self, engine_url: str, result: Dict[str, Any]):
        """Test Engine A - Market Data APIs"""
        try:
            # Test market data endpoint
            market_response = requests.get(f"{engine_url}/api/market-data/NIFTY", timeout=10)
            if market_response.status_code == 200:
                result["apis"]["market_data"] = "WORKING"
                print("   📈 Market Data API: Working")
            else:
                result["apis"]["market_data"] = "FAILED"
                print(f"   ❌ Market Data API: Failed ({market_response.status_code})")
                self.log_issue("ENGINE_A_API", "Market data API not responding", "HIGH")
        except Exception as e:
            result["apis"]["market_data"] = "ERROR"
            print(f"   ❌ Market Data API: Error - {str(e)}")

    def test_engine_b_apis(self, engine_url: str, result: Dict[str, Any]):
        """Test Engine B - AI/ML APIs"""
        try:
            # Test AI signals endpoint
            ai_response = requests.get(f"{engine_url}/api/ai-signals", timeout=10)
            if ai_response.status_code == 200:
                result["apis"]["ai_signals"] = "WORKING"
                print("   🤖 AI Signals API: Working")
            else:
                result["apis"]["ai_signals"] = "FAILED"
                print(f"   ❌ AI Signals API: Failed ({ai_response.status_code})")
                self.log_issue("ENGINE_B_API", "AI signals API not responding", "HIGH")
        except Exception as e:
            result["apis"]["ai_signals"] = "ERROR"
            print(f"   ❌ AI Signals API: Error - {str(e)}")

    def test_engine_c_apis(self, engine_url: str, result: Dict[str, Any]):
        """Test Engine C - Trade Execution APIs"""
        try:
            # Test orders status endpoint
            orders_response = requests.get(f"{engine_url}/api/orders/status", timeout=10)
            if orders_response.status_code == 200:
                result["apis"]["orders"] = "WORKING"
                print("   💰 Orders API: Working")
            else:
                result["apis"]["orders"] = "FAILED"
                print(f"   ❌ Orders API: Failed ({orders_response.status_code})")
                self.log_issue("ENGINE_C_API", "Orders API not responding", "HIGH")

            # Test Dhan OAuth connectivity
            dhan_response = requests.get(f"{engine_url}/api/dhan/status", timeout=10)
            if dhan_response.status_code == 200:
                result["apis"]["dhan_oauth"] = "WORKING"
                print("   🔐 Dhan OAuth: Connected")
            else:
                result["apis"]["dhan_oauth"] = "FAILED"
                print(f"   ❌ Dhan OAuth: Failed ({dhan_response.status_code})")
                self.log_issue("DHAN_OAUTH", "Dhan OAuth connectivity issues", "HIGH")
                self.add_recommendation("DHAN_OAUTH", "Check OAuth tokens in Secret Manager and verify redirect URIs")
        except Exception as e:
            result["apis"]["dhan_oauth"] = "ERROR"
            print(f"   ❌ Dhan OAuth: Error - {str(e)}")

    def test_engine_d_apis(self, engine_url: str, result: Dict[str, Any]):
        """Test Engine D - Orchestration APIs"""
        try:
            # Test orchestration status
            orchestration_response = requests.get(f"{engine_url}/api/orchestration/status", timeout=10)
            if orchestration_response.status_code == 200:
                result["apis"]["orchestration"] = "WORKING"
                print("   🎭 Orchestration API: Working")
            else:
                result["apis"]["orchestration"] = "FAILED"
                print(f"   ❌ Orchestration API: Failed ({orchestration_response.status_code})")
                self.log_issue("ENGINE_D_API", "Engine D orchestration failing", "CRITICAL")

            # Test WebSocket connectivity
            ws_response = requests.get(f"{engine_url}/api/websocket/status", timeout=10)
            if ws_response.status_code == 200:
                result["apis"]["websocket"] = "WORKING"
                print("   🔌 WebSocket API: Working")
            else:
                result["apis"]["websocket"] = "FAILED"
                print(f"   ❌ WebSocket API: Failed ({ws_response.status_code})")
                self.log_issue("WEBSOCKET", "WebSocket connectivity issues affecting real-time updates", "HIGH")
        except Exception as e:
            result["apis"]["websocket"] = "ERROR"
            print(f"   ❌ Engine D APIs: Error - {str(e)}")
            self.log_issue("ENGINE_D_CRITICAL", f"Engine D critical failure: {str(e)}", "CRITICAL")

    def test_firebase_functions(self) -> Dict[str, Any]:
        """Test Firebase Functions connectivity"""
        print("\n⚡ Testing Firebase Functions")
        print("-" * 50)

        functions = [
            "submitDhanCredentialsV2",
            "analyzePortfolio",
            "startTrading",
            "stopTrading",
            "getAiSignals",
            "getVertexAiAnalysis",
            "getGeminiAnalysis"
        ]

        result = {"functions_tested": len(functions), "working": 0, "failed": 0, "details": {}}

        for function_name in functions:
            try:
                function_url = f"https://us-central1-{self.project_id}.cloudfunctions.net/{function_name}"
                response = requests.post(function_url, json={"data": {"test": True}}, timeout=10)

                if response.status_code in [200, 401, 403]:  # 401/403 means function exists but needs auth
                    result["working"] += 1
                    result["details"][function_name] = "WORKING"
                    print(f"   ✅ {function_name}: Available")
                else:
                    result["failed"] += 1
                    result["details"][function_name] = f"FAILED_{response.status_code}"
                    print(f"   ❌ {function_name}: Failed ({response.status_code})")

                    if function_name in ["getVertexAiAnalysis", "getGeminiAnalysis"]:
                        self.log_issue("AI_ANALYSIS", f"{function_name} failing - causing dashboard AI analysis errors", "HIGH")

            except Exception as e:
                result["failed"] += 1
                result["details"][function_name] = f"ERROR_{str(e)}"
                print(f"   ❌ {function_name}: Error - {str(e)}")

        return result

    def test_firestore_connectivity(self) -> Dict[str, Any]:
        """Test Firestore database connectivity"""
        print("\n🔥 Testing Firestore Connectivity")
        print("-" * 50)

        result = {"status": "UNKNOWN", "rules": "UNKNOWN", "collections": {}}

        try:
            # Test Firestore REST API
            firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"
            response = requests.get(firestore_url, timeout=10)

            if response.status_code in [200, 401, 403]:
                result["status"] = "ACCESSIBLE"
                print("   ✅ Firestore Database: Accessible")
            else:
                result["status"] = "FAILED"
                print(f"   ❌ Firestore Database: Failed ({response.status_code})")
                self.log_issue("FIRESTORE", "Firestore database connectivity issues", "HIGH")

        except Exception as e:
            result["status"] = "ERROR"
            print(f"   ❌ Firestore Database: Error - {str(e)}")

        return result

    def test_gcp_cloud_run_services(self) -> Dict[str, Any]:
        """Test GCP Cloud Run services status"""
        print("\n☁️ Testing GCP Cloud Run Services")
        print("-" * 50)

        result = {"services_tested": 4, "healthy": 0, "unhealthy": 0, "details": {}}

        for engine_name, engine_url in self.engines.items():
            engine_result = self.test_engine_health(engine_name, engine_url)

            if engine_result["health"] == "HEALTHY":
                result["healthy"] += 1
            else:
                result["unhealthy"] += 1

            result["details"][engine_name] = engine_result

        return result

    def analyze_dashboard_issues(self) -> Dict[str, Any]:
        """Analyze frontend dashboard issues based on screenshots"""
        print("\n📊 Analyzing Dashboard Issues")
        print("-" * 50)

        issues = {
            "engine_d_error": {
                "description": "Engine D shows Error status in Engines management page",
                "impact": "Orchestration and real-time updates affected",
                "severity": "CRITICAL"
            },
            "gemini_ai_analysis_failed": {
                "description": "Gemini AI Analysis showing 'Failed to load AI insights'",
                "impact": "AI insights and analysis features not working",
                "severity": "HIGH"
            },
            "loading_states": {
                "description": "Multiple components showing persistent loading states",
                "impact": "Poor user experience and functionality gaps",
                "severity": "MEDIUM"
            }
        }

        for issue_key, issue_data in issues.items():
            self.log_issue("DASHBOARD_UI", issue_data["description"], issue_data["severity"])
            print(f"   ❌ {issue_data['description']}")

        return issues

    def generate_recommendations(self):
        """Generate specific recommendations based on found issues"""
        print("\n🔧 Generating Recommendations")
        print("-" * 50)

        # Engine D specific recommendations
        self.add_recommendation("ENGINE_D_FIX",
            "Restart Engine D Cloud Run service and check orchestration logs")
        self.add_recommendation("ENGINE_D_FIX",
            "Verify Engine D WebSocket configuration and real-time data pipeline")

        # AI Analysis recommendations
        self.add_recommendation("AI_ANALYSIS_FIX",
            "Check getGeminiAnalysis and getVertexAiAnalysis Firebase Functions logs")
        self.add_recommendation("AI_ANALYSIS_FIX",
            "Verify AI service API keys and quotas in Secret Manager")

        # OAuth recommendations
        self.add_recommendation("DHAN_OAUTH_FIX",
            "Refresh Dhan OAuth tokens in Secret Manager")
        self.add_recommendation("DHAN_OAUTH_FIX",
            "Verify redirect URIs match Dhan API settings")

        # Monitoring recommendations
        self.add_recommendation("MONITORING",
            "Implement continuous health monitoring with alerts")
        self.add_recommendation("MONITORING",
            "Set up automated recovery scripts for common failures")

        # UI improvements
        self.add_recommendation("UI_ENHANCEMENT",
            "Add error boundaries and retry mechanisms for failed components")
        self.add_recommendation("UI_ENHANCEMENT",
            "Implement Zustand state management and React Query for better data handling")

    def run_comprehensive_diagnostics(self):
        """Run all diagnostic tests"""
        print("🔍 InfinityAI.Pro - Comprehensive Platform Diagnostics")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test GCP Cloud Run services
        self.results["diagnostics"]["cloud_run"] = self.test_gcp_cloud_run_services()

        # Test Firebase Functions
        self.results["diagnostics"]["firebase_functions"] = self.test_firebase_functions()

        # Test Firestore
        self.results["diagnostics"]["firestore"] = self.test_firestore_connectivity()

        # Analyze dashboard issues
        self.results["diagnostics"]["dashboard_issues"] = self.analyze_dashboard_issues()

        # Generate recommendations
        self.generate_recommendations()

        # Print summary
        self.print_summary()

        # Save results
        with open("comprehensive_diagnostics_report.json", "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Full diagnostic report saved to: comprehensive_diagnostics_report.json")

        return self.results

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE DIAGNOSTICS SUMMARY")
        print("=" * 60)

        # Count issues by severity
        critical_issues = len([i for i in self.results["issues_found"] if i["severity"] == "CRITICAL"])
        high_issues = len([i for i in self.results["issues_found"] if i["severity"] == "HIGH"])
        medium_issues = len([i for i in self.results["issues_found"] if i["severity"] == "MEDIUM"])

        print(f"🚨 Critical Issues: {critical_issues}")
        print(f"⚠️ High Priority Issues: {high_issues}")
        print(f"📋 Medium Priority Issues: {medium_issues}")
        print(f"💡 Recommendations Generated: {len(self.results['recommendations'])}")

        # Print top priority issues
        if critical_issues > 0:
            print(f"\n🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for issue in self.results["issues_found"]:
                if issue["severity"] == "CRITICAL":
                    print(f"   ❌ {issue['category']}: {issue['issue']}")

        # Print key recommendations
        print(f"\n🔧 TOP PRIORITY RECOMMENDATIONS:")
        for i, rec in enumerate(self.results["recommendations"][:5], 1):
            print(f"   {i}. {rec['category']}: {rec['recommendation']}")

        print(f"\n🕐 Diagnostics completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    diagnostics = InfinityAIDiagnostics()
    try:
        results = diagnostics.run_comprehensive_diagnostics()
    except KeyboardInterrupt:
        print("\n⚠️ Diagnostics interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnostics failed with error: {str(e)}")