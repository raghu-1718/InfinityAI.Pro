#!/usr/bin/env python3
"""
InfinityAI.Pro - Specific Issue Diagnosis and Resolution
This script diagnoses known issues by checking service health, endpoint availability,
and external service configurations.
"""

import json
import requests
import subprocess
import time
from datetime import datetime, timezone
import concurrent.futures

class InfinityAIIssueDiagnostic:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.region = "us-central1"
        self.issues_found = []
        self.fixes_applied = []
        self.fix_commands = []

        # Updated URLs based on verification results
        self.base_urls = {
            "engine_a": "https://infinityai-engine-a-26140490557.us-central1.run.app",
            "engine_b": "https://infinityai-engine-b-26140490557.us-central1.run.app",
            "engine_c_execution": "https://infinityai-engine-c-execution-26140490557.us-central1.run.app",
            "engine_d": "https://infinityai-engine-d-26140490557.us-central1.run.app",
            "frontend": "https://infinityai-frontend-26140490557.us-central1.run.app"
        }

    def log_issue(self, category: str, description: str, severity: str = "MEDIUM"):
        """Log identified issue"""
        issue = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "description": description,
            "severity": severity
        }
        self.issues_found.append(issue)

        emoji = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
        print(f"{emoji} [{severity}] {category}: {description}")

    def log_fix(self, description: str, command: str = None):
        """Log applied fix"""
        fix = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": description,
            "command": command
        }
        self.fixes_applied.append(fix)
        print(f"🔧 FIX APPLIED: {description}")
        if command:
            print(f"   Command: {command}")

    def _run_command(self, command: list[str]) -> subprocess.CompletedProcess:
        """Executes a shell command safely."""
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,  # Raises CalledProcessError on non-zero exit codes
                timeout=60
            )
        except FileNotFoundError:
            raise Exception(f"Command not found: {command[0]}. Ensure gcloud/firebase CLI is in your PATH.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Command '{' '.join(command)}' failed with exit code {e.returncode}:\n{e.stderr}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while running command: {e}")

    def diagnose_url_mismatch(self):
        """Diagnose URL mismatches between expected and actual service URLs"""
        print(f"\n{'='*80}")
        print(f"🔍 DIAGNOSING URL MISMATCHES")
        print(f"{'='*80}")

        # Get actual Cloud Run service URLs
        try:
            cmd = ["gcloud", "run", "services", "list", f"--region={self.region}", f"--project={self.project_id}", "--format=json"]
            result = self._run_command(cmd)
            services = json.loads(result.stdout)

            if services:
                print("📋 Current Cloud Run Services:")
                actual_urls = {}
                for service in services:
                    name = service.get('metadata', {}).get('name', '')
                    url = service.get('status', {}).get('url', '')
                    if name and url:
                        actual_urls[name] = url
                        print(f"   {name}: {url}")

                # Compare with expected URLs
                for service_key, service_name in [('engine_a', 'infinityai-engine-a'), ('engine_b', 'infinityai-engine-b'), ('engine_c_execution', 'infinityai-engine-c-execution'), ('engine_d', 'infinityai-engine-d'), ('frontend', 'infinityai-frontend')]:
                    if service_name in actual_urls:
                        self.base_urls[service_key] = actual_urls[service_name]
                    else:
                        self.log_issue("URL_MISMATCH", f"Service {service_name} not found in Cloud Run", "HIGH")

                print(f"\n✅ Updated service URLs:")
                for key, url in self.base_urls.items():
                    print(f"   {key}: {url}")

        except Exception as e:
            self.log_issue("GCLOUD_ERROR", f"Exception getting service URLs: {str(e)}", "HIGH")

    def diagnose_missing_endpoints(self):
        """Diagnose missing API endpoints"""
        print(f"\n{'='*80}")
        print(f"🔍 DIAGNOSING MISSING API ENDPOINTS")
        print(f"{'='*80}")

        # Test specific endpoints that were failing
        endpoints_to_test = [
            ("engine_a", "/api/market-data/NIFTY", "Market data endpoint"),
            ("engine_b", "/api/gemini/analyze", "Gemini analysis endpoint"),
            ("engine_b", "/api/ai-signals", "AI signals endpoint"),
            ("engine_d", "/api/status", "Engine D status endpoint"),
            ("frontend", "/health", "Frontend health endpoint")
        ]

        def test_endpoint(service, endpoint, description):
            url = f"{self.base_urls.get(service, '')}{endpoint}"
            if not self.base_urls.get(service):
                self.log_issue("CONFIG_ERROR", f"Base URL for service '{service}' not found.", "HIGH")
                return
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 404:
                    self.log_issue("MISSING_ENDPOINT", f"{description} returns 404: {url}", "HIGH")
                elif response.status_code >= 500:
                    self.log_issue("SERVER_ERROR", f"{description} server error ({response.status_code}): {url}", "HIGH")
                else:
                    print(f"✅ {description}: Available (Status: {response.status_code})")
            except requests.exceptions.Timeout:
                self.log_issue("TIMEOUT", f"{description} timeout: {url}", "MEDIUM")
            except Exception as e:
                self.log_issue("CONNECTION_ERROR", f"{description} connection error: {str(e)}", "MEDIUM")

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(endpoints_to_test)) as executor:
            executor.map(lambda p: test_endpoint(*p), endpoints_to_test)

    def diagnose_firebase_functions(self):
        """Diagnose Firebase Functions issues"""
        print(f"\n{'='*80}")
        print(f"🔍 DIAGNOSING FIREBASE FUNCTIONS")
        print(f"{'='*80}")

        # List actual Firebase Functions
        try:
            cmd = ["firebase", "functions:list", f"--project={self.project_id}"]
            result = self._run_command(cmd)
            if result.stdout:
                print("📋 Current Firebase Functions:")
                print(result.stdout)

                # Check if functions are deployed correctly
                functions_expected = [
                    "getGeminiAnalysis",
                    "analyzePortfolio",
                    "getDhanOverview",
                    "submitDhanCredentialsV2"
                ]

                for func_name in functions_expected:
                    if func_name not in result.stdout:
                        self.log_issue("MISSING_FUNCTION", f"Firebase Function {func_name} not found", "HIGH")
                    else:
                        print(f"✅ Function {func_name}: Found")

        except Exception as e:
            self.log_issue("FIREBASE_ERROR", f"Exception listing functions: {str(e)}", "HIGH")

    def diagnose_secret_access(self):
        """Diagnose secret access issues"""
        print(f"\n{'='*80}")
        print(f"🔍 DIAGNOSING SECRET ACCESS")
        print(f"{'='*80}")

        # Test secret access
        secrets_to_test = [
            "gemini-api-key-primary",
            "gemini-api-key-secondary",
            "firebase-deploy-token"
        ]

        for secret_name in secrets_to_test:
            try:
                cmd = ["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret_name}", f"--project={self.project_id}"]
                result = self._run_command(cmd)
                if result.stdout:
                    print(f"✅ Secret {secret_name}: Accessible (payload length: {len(result.stdout)})")
            except Exception as e:
                self.log_issue("SECRET_ACCESS", f"Exception accessing secret {secret_name}: {str(e)}", "HIGH")

    def test_corrected_endpoints(self):
        """Test endpoints with corrected URLs"""
        print(f"\n{'='*80}")
        print(f"🧪 TESTING WITH CORRECTED URLS")
        print(f"{'='*80}")

        def test_health(service, url):
            health_url = f"{url}/health"
            try:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {service} health: OK ({response.elapsed.total_seconds():.2f}s)")
                else:
                    self.log_issue("HEALTH_CHECK_FAIL", f"{service} health check failed with status {response.status_code}", "HIGH")
            except Exception as e:
                self.log_issue("HEALTH_CHECK_ERROR", f"{service} health check error: {e}", "HIGH")

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.base_urls)) as executor:
            executor.map(lambda item: test_health(item[0], item[1]), self.base_urls.items())

        # Test specific problematic endpoints
        test_cases = [
            {
                "name": "Gemini Analysis",
                "url": f"{self.base_urls['engine_b']}/api/gemini/analyze",
                "method": "POST",
                "data": {
                    "prompt": "Test analysis",
                    "userId": "diagnostic_test",
                    "context": {"test": True}
                }
            },
            {
                "name": "AI Signals",
                "url": f"{self.base_urls['engine_b']}/api/ai-signals",
                "method": "GET"
            },
            {
                "name": "Market Data NIFTY",
                "url": f"{self.base_urls['engine_a']}/api/market-data/NIFTY",
                "method": "GET"
            }
        ]

        for test in test_cases:
            try:
                if test["method"] == "POST":
                    response = requests.post(test["url"], json=test.get("data"), timeout=15)
                else:
                    response = requests.get(test["url"], timeout=10)

                print(f"🧪 {test['name']}: Status {response.status_code}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   Response: {str(data)[:100]}...")
                    except:
                        print(f"   Response: {response.text[:100]}...")

            except Exception as e:
                print(f"❌ {test['name']}: Error - {str(e)}")

    def generate_fix_commands(self):
        """Generate commands to fix identified issues"""
        print(f"\n{'='*80}")
        print(f"🔧 GENERATING FIX COMMANDS")
        print(f"{'='*80}")

        # Generate fix commands based on specific issues found
        if any(i['category'] == 'MISSING_ENDPOINT' and 'Gemini' in i['description'] for i in self.issues_found):
            self.fix_commands.append({
                "description": "Redeploy Engine B to fix missing Gemini endpoint.",
                "command": f"gcloud run deploy infinityai-engine-b --source ./engines/engine-b --region {self.region} --project {self.project_id} --allow-unauthenticated"
            })

        if any(i['category'] == 'MISSING_FUNCTION' for i in self.issues_found):
            self.fix_commands.append({
                "description": "Redeploy all Firebase Functions to fix missing ones.",
                "command": f"firebase deploy --only functions --project {self.project_id}"
            })

        if any(i['category'] == 'SECRET_ACCESS' for i in self.issues_found):
            self.fix_commands.append({
                "description": "Review IAM policies for Secret Manager.",
                "command": f"gcloud secrets get-iam-policy <SECRET_NAME> --project={self.project_id}"
            })

        if not self.fix_commands:
            print("✅ No specific fix commands generated as no critical issues were auto-diagnosed.")
            return

        print("📋 Recommended Fix Commands:")
        for i, fix in enumerate(self.fix_commands, 1):
            print(f"\n{i}. {fix['description']}:")
            print(f"   {fix['command']}")

    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        report = {
            "diagnostic_timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": self.project_id,
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "current_service_urls": self.base_urls,
            "summary": {
                "total_issues": len(self.issues_found),
                "high_severity": len([i for i in self.issues_found if i["severity"] == "HIGH"]),
                "medium_severity": len([i for i in self.issues_found if i["severity"] == "MEDIUM"]),
                "low_severity": len([i for i in self.issues_found if i["severity"] == "LOW"])
            }
        }

        filename = f"infinityai_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Diagnostic report saved to: {filename}")
        return filename, report

    def run_comprehensive_diagnosis(self):
        """Run comprehensive diagnosis"""
        print(f"\n{'='*100}")
        print(f"🔍 InfinityAI.Pro Issue Diagnosis & Resolution")
        print(f"{'='*100}")

        # Run all diagnostic steps
        self.diagnose_url_mismatch()
        self.diagnose_missing_endpoints()
        self.diagnose_firebase_functions()
        self.diagnose_secret_access()
        self.test_corrected_endpoints()
        self.generate_fix_commands()

        # Generate final report
        filename, report = self.generate_diagnostic_report()

        print(f"\n{'='*100}")
        print(f"📊 DIAGNOSTIC SUMMARY")
        print(f"{'='*100}")
        print(f"🔴 High Severity Issues: {report['summary']['high_severity']}")
        print(f"🟡 Medium Severity Issues: {report['summary']['medium_severity']}")
        print(f"🟢 Low Severity Issues: {report['summary']['low_severity']}")
        print(f"📋 Total Issues Found: {report['summary']['total_issues']}")
        print(f"\n📊 Full report saved to: {filename}")

        return filename, report

if __name__ == "__main__":
    diagnostic = InfinityAIIssueDiagnostic()
    diagnostic.run_comprehensive_diagnosis()