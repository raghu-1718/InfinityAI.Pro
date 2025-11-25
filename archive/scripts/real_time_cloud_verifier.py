#!/usr/bin/env python3
"""
InfinityAI.Pro - Real-Time Cloud Deployment Verification
Comprehensive check of all GCP resources and their status
"""

import json
import requests
import subprocess
import time
from datetime import datetime, timezone
import sys
import os

class InfinityAICloudVerifier:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.region = "us-central1"

        # Results storage
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cloud_run_services": {},
            "firebase_status": {},
            "firestore_status": {},
            "secrets_status": {},
            "domain_status": {},
            "issues": [],
            "fixes_applied": [],
            "summary": {}
        }

        print(f"🚀 InfinityAI.Pro Cloud Verification Suite")
        print(f"Project: {self.project_id} | Region: {self.region}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*80}")

    def run_command(self, cmd: str, timeout: int = 30) -> tuple:
        """Run shell command and return (success, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, encoding='utf-8', errors='ignore'
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def log_issue(self, category: str, description: str, severity: str = "MEDIUM"):
        """Log an issue"""
        issue = {
            "category": category,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.results["issues"].append(issue)

        emoji = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
        print(f"{emoji} [{severity}] {category}: {description}")

    def log_fix(self, description: str, command: str = ""):
        """Log a fix applied"""
        fix = {
            "description": description,
            "command": command,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.results["fixes_applied"].append(fix)
        print(f"🔧 FIX: {description}")

    def verify_cloud_run_services(self):
        """Verify all Cloud Run services"""
        print(f"\n📊 VERIFYING CLOUD RUN SERVICES")
        print(f"-" * 50)

        # List Cloud Run services
        success, stdout, stderr = self.run_command(
            f"gcloud run services list --region={self.region} --project={self.project_id} --format=json"
        )

        if not success:
            self.log_issue("GCLOUD_ERROR", f"Failed to list services: {stderr}", "HIGH")
            return

        try:
            services = json.loads(stdout)
            print(f"Found {len(services)} Cloud Run services:")

            for service in services:
                name = service.get('metadata', {}).get('name', 'unknown')
                url = service.get('status', {}).get('url', '')

                print(f"  🔗 {name}")
                print(f"     URL: {url}")

                # Test health endpoint
                health_status = self.test_service_health(url)

                self.results["cloud_run_services"][name] = {
                    "url": url,
                    "health_status": health_status["status"],
                    "response_time": health_status.get("response_time", 0),
                    "last_tested": datetime.now(timezone.utc).isoformat()
                }

        except json.JSONDecodeError as e:
            self.log_issue("JSON_ERROR", f"Failed to parse services JSON: {e}", "HIGH")

    def test_service_health(self, url: str) -> dict:
        """Test service health endpoint"""
        if not url:
            return {"status": "no_url", "response_time": 0}

        start_time = time.time()
        try:
            health_url = f"{url}/health"
            response = requests.get(health_url, timeout=10)
            response_time = round((time.time() - start_time) * 1000, 2)

            if response.status_code == 200:
                print(f"     ✅ Health: OK ({response_time}ms)")
                return {"status": "healthy", "response_time": response_time}
            else:
                print(f"     ❌ Health: HTTP {response.status_code} ({response_time}ms)")
                self.log_issue("SERVICE_UNHEALTHY", f"Service health check failed: HTTP {response.status_code}")
                return {"status": "unhealthy", "response_time": response_time, "http_code": response.status_code}

        except requests.exceptions.Timeout:
            response_time = round((time.time() - start_time) * 1000, 2)
            print(f"     ⏰ Health: Timeout ({response_time}ms)")
            self.log_issue("SERVICE_TIMEOUT", "Service health check timeout")
            return {"status": "timeout", "response_time": response_time}

        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            print(f"     ❌ Health: Error - {str(e)[:50]}")
            self.log_issue("SERVICE_ERROR", f"Service health check error: {str(e)}")
            return {"status": "error", "response_time": response_time, "error": str(e)}

    def verify_firebase_status(self):
        """Verify Firebase project status"""
        print(f"\n🔥 VERIFYING FIREBASE STATUS")
        print(f"-" * 50)

        # Check Firebase project
        success, stdout, stderr = self.run_command(f"firebase projects:list")

        if success:
            print("✅ Firebase CLI accessible")
            print("Projects found:")
            print(stdout)
            self.results["firebase_status"]["cli_access"] = True
            self.results["firebase_status"]["projects"] = stdout
        else:
            print("❌ Firebase CLI not accessible")
            self.log_issue("FIREBASE_ERROR", f"Firebase CLI error: {stderr}", "HIGH")
            self.results["firebase_status"]["cli_access"] = False

    def verify_secrets(self):
        """Verify GCP Secret Manager secrets"""
        print(f"\n🔐 VERIFYING SECRETS")
        print(f"-" * 50)

        # List secrets
        success, stdout, stderr = self.run_command(
            f"gcloud secrets list --project={self.project_id} --format=json"
        )

        if success:
            try:
                secrets = json.loads(stdout)
                print(f"Found {len(secrets)} secrets:")

                for secret in secrets:
                    name = secret.get('name', '').split('/')[-1]
                    print(f"  🔑 {name}")

                    # Test secret access
                    access_result = self.test_secret_access(name)
                    self.results["secrets_status"][name] = access_result

            except json.JSONDecodeError:
                self.log_issue("JSON_ERROR", "Failed to parse secrets JSON", "MEDIUM")
        else:
            self.log_issue("SECRETS_ERROR", f"Failed to list secrets: {stderr}", "HIGH")

    def test_secret_access(self, secret_name: str) -> dict:
        """Test if secret can be accessed"""
        success, stdout, stderr = self.run_command(
            f"gcloud secrets versions access latest --secret={secret_name} --project={self.project_id}"
        )

        if success and stdout.strip():
            print(f"     ✅ Accessible")
            return {"accessible": True, "length": len(stdout.strip())}
        else:
            print(f"     ❌ Access failed")
            self.log_issue("SECRET_ACCESS", f"Cannot access secret {secret_name}")
            return {"accessible": False, "error": stderr}

    def verify_domains(self):
        """Verify domain mappings"""
        print(f"\n🌐 VERIFYING DOMAIN MAPPINGS")
        print(f"-" * 50)

        # List domain mappings
        success, stdout, stderr = self.run_command(
            f"gcloud run domain-mappings list --region={self.region} --project={self.project_id} --format=json"
        )

        if success:
            try:
                mappings = json.loads(stdout)
                print(f"Found {len(mappings)} domain mappings:")

                for mapping in mappings:
                    domain_spec = mapping.get('spec', {})
                    domain = domain_spec.get('routeSpec', {}).get('url', 'unknown')
                    print(f"  🔗 {domain}")

                    # Test HTTPS connectivity
                    https_result = self.test_https_connectivity(domain)
                    self.results["domain_status"][domain] = https_result

            except json.JSONDecodeError:
                self.log_issue("JSON_ERROR", "Failed to parse domain mappings", "MEDIUM")
        else:
            print("No domain mappings found or error accessing them")
            self.results["domain_status"] = {"error": stderr}

    def test_https_connectivity(self, domain: str) -> dict:
        """Test HTTPS connectivity to domain"""
        try:
            url = f"https://{domain}"
            response = requests.get(url, timeout=10)

            if response.status_code < 400:
                print(f"     ✅ HTTPS: OK (Status: {response.status_code})")
                return {"https_accessible": True, "status_code": response.status_code}
            else:
                print(f"     ⚠️ HTTPS: HTTP {response.status_code}")
                return {"https_accessible": True, "status_code": response.status_code}

        except Exception as e:
            print(f"     ❌ HTTPS: Error - {str(e)[:50]}")
            self.log_issue("DOMAIN_ERROR", f"Domain connectivity error: {str(e)}")
            return {"https_accessible": False, "error": str(e)}

    def check_for_issues(self):
        """Analyze results and identify issues"""
        print(f"\n🔍 ANALYZING RESULTS")
        print(f"-" * 50)

        # Count healthy services
        healthy_services = 0
        total_services = len(self.results["cloud_run_services"])

        for name, service in self.results["cloud_run_services"].items():
            if service["health_status"] == "healthy":
                healthy_services += 1

        # Count accessible secrets
        accessible_secrets = 0
        total_secrets = len(self.results["secrets_status"])

        for name, secret in self.results["secrets_status"].items():
            if secret.get("accessible"):
                accessible_secrets += 1

        # Generate summary
        self.results["summary"] = {
            "services": {
                "total": total_services,
                "healthy": healthy_services,
                "health_percentage": round((healthy_services / total_services * 100) if total_services > 0 else 0, 1)
            },
            "secrets": {
                "total": total_secrets,
                "accessible": accessible_secrets,
                "access_percentage": round((accessible_secrets / total_secrets * 100) if total_secrets > 0 else 0, 1)
            },
            "issues": {
                "total": len(self.results["issues"]),
                "high": len([i for i in self.results["issues"] if i["severity"] == "HIGH"]),
                "medium": len([i for i in self.results["issues"] if i["severity"] == "MEDIUM"])
            },
            "overall_status": "HEALTHY" if len([i for i in self.results["issues"] if i["severity"] == "HIGH"]) == 0 else "NEEDS_ATTENTION"
        }

        print(f"📊 SUMMARY:")
        print(f"   Services: {healthy_services}/{total_services} healthy ({self.results['summary']['services']['health_percentage']}%)")
        print(f"   Secrets: {accessible_secrets}/{total_secrets} accessible ({self.results['summary']['secrets']['access_percentage']}%)")
        print(f"   Issues: {self.results['summary']['issues']['total']} total ({self.results['summary']['issues']['high']} high, {self.results['summary']['issues']['medium']} medium)")
        print(f"   Overall: {self.results['summary']['overall_status']}")

    def save_report(self):
        """Save verification report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cloud_verification_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Report saved to: {filename}")
        return filename

    def run_verification(self):
        """Run complete verification"""
        self.verify_cloud_run_services()
        self.verify_firebase_status()
        self.verify_secrets()
        self.verify_domains()
        self.check_for_issues()

        report_file = self.save_report()

        print(f"\n{'='*80}")
        if self.results["summary"]["overall_status"] == "HEALTHY":
            print("🎉 VERIFICATION COMPLETE: All systems healthy!")
        else:
            print("⚠️ VERIFICATION COMPLETE: Issues found that need attention")
        print(f"{'='*80}")

        return report_file, self.results

if __name__ == "__main__":
    verifier = InfinityAICloudVerifier()
    report_file, results = verifier.run_verification()