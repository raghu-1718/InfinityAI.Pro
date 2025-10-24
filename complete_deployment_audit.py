#!/usr/bin/env python3
"""
InfinityAI.Pro - Complete End-to-End Deployment Audit & Verification
Comprehensive cloud resource inventory and deployment completion
"""

import json
import subprocess
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
import asyncio

class InfinityAICloudAuditor:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.region = "us-central1"
        self.audit_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "project_id": self.project_id,
            "resources": {},
            "deployment_status": {},
            "health_checks": {},
            "recommendations": []
        }

    def print_header(self, title: str):
        print(f"\n{'='*80}")
        print(f"🚀 {title}")
        print(f"{'='*80}")

    def print_status(self, message: str, status: str = "info"):
        emoji = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "🔍"}
        print(f"{emoji.get(status, '📋')} {message}")

    def run_command(self, command: str) -> dict:
        """Execute shell command and return result"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def audit_cloud_run_services(self):
        """Audit all Cloud Run services"""
        self.print_header("Cloud Run Services Audit")

        cmd = f"gcloud run services list --region={self.region} --project={self.project_id} --format=json"
        result = self.run_command(cmd)

        if result["success"]:
            services = json.loads(result["stdout"]) if result["stdout"] else []
            self.audit_results["resources"]["cloud_run"] = {
                "count": len(services),
                "services": services
            }

            for service in services:
                name = service.get("metadata", {}).get("name", "unknown")
                status = service.get("status", {})
                url = status.get("url", "")

                self.print_status(f"Service: {name}")
                self.print_status(f"  URL: {url}")
                self.print_status(f"  Ready: {status.get('conditions', [{}])[0].get('status', 'Unknown')}")

                # Test service health
                if url:
                    health_url = f"{url}/health" if "/health" not in url else url
                    try:
                        response = requests.get(health_url, timeout=10)
                        if response.status_code == 200:
                            self.print_status(f"  Health: Healthy", "success")
                        else:
                            self.print_status(f"  Health: Unhealthy ({response.status_code})", "error")
                    except Exception as e:
                        self.print_status(f"  Health: Error - {str(e)}", "error")
        else:
            self.print_status(f"Failed to list Cloud Run services: {result['stderr']}", "error")

    def audit_firebase_functions(self):
        """Audit Firebase Functions"""
        self.print_header("Firebase Functions Audit")

        # List Firebase Functions
        cmd = f"firebase functions:list --project={self.project_id}"
        result = self.run_command(cmd)

        if result["success"]:
            self.print_status("Firebase Functions listed successfully", "success")
            functions_output = result["stdout"]

            # Parse function names from output
            function_names = []
            for line in functions_output.split('\n'):
                if 'https://' in line and 'cloudfunctions.net' in line:
                    # Extract function name from URL
                    parts = line.split('/')
                    if len(parts) > 4:
                        function_names.append(parts[-1].strip())

            self.audit_results["resources"]["firebase_functions"] = {
                "count": len(function_names),
                "functions": function_names
            }

            # Test each function
            for func_name in function_names:
                func_url = f"https://us-central1-{self.project_id}.cloudfunctions.net/{func_name}"
                try:
                    response = requests.get(func_url, timeout=5)
                    if response.status_code in [200, 403]:  # 403 is expected for authenticated functions
                        self.print_status(f"Function {func_name}: Available", "success")
                    else:
                        self.print_status(f"Function {func_name}: Error ({response.status_code})", "error")
                except Exception as e:
                    self.print_status(f"Function {func_name}: Error - {str(e)}", "error")
        else:
            self.print_status(f"Failed to list Firebase Functions: {result['stderr']}", "error")

    def audit_firestore(self):
        """Audit Firestore database"""
        self.print_header("Firestore Database Audit")

        # Check Firestore indexes
        cmd = f"firebase firestore:indexes --project={self.project_id}"
        result = self.run_command(cmd)

        if result["success"]:
            self.print_status("Firestore indexes retrieved", "success")
            self.audit_results["resources"]["firestore"] = {
                "indexes": result["stdout"],
                "status": "active"
            }
        else:
            self.print_status(f"Failed to get Firestore indexes: {result['stderr']}", "error")

    def audit_secrets(self):
        """Audit GCP Secret Manager"""
        self.print_header("Secret Manager Audit")

        cmd = f"gcloud secrets list --project={self.project_id} --format=json"
        result = self.run_command(cmd)

        if result["success"]:
            secrets = json.loads(result["stdout"]) if result["stdout"] else []
            self.audit_results["resources"]["secrets"] = {
                "count": len(secrets),
                "secrets": [s.get("name", "").split("/")[-1] for s in secrets]
            }

            for secret in secrets:
                name = secret.get("name", "").split("/")[-1]
                created = secret.get("createTime", "unknown")
                self.print_status(f"Secret: {name} (Created: {created})", "success")

        else:
            self.print_status(f"Failed to list secrets: {result['stderr']}", "error")

    def audit_vertex_ai(self):
        """Audit Vertex AI resources"""
        self.print_header("Vertex AI Audit")

        # Check if Vertex AI API is enabled
        cmd = f"gcloud services list --enabled --filter='name:aiplatform.googleapis.com' --project={self.project_id}"
        result = self.run_command(cmd)

        if result["success"] and "aiplatform.googleapis.com" in result["stdout"]:
            self.print_status("Vertex AI API is enabled", "success")
            self.audit_results["resources"]["vertex_ai"] = {"status": "enabled"}

            # List Vertex AI endpoints
            cmd = f"gcloud ai endpoints list --region={self.region} --project={self.project_id} --format=json"
            endpoints_result = self.run_command(cmd)

            if endpoints_result["success"]:
                endpoints = json.loads(endpoints_result["stdout"]) if endpoints_result["stdout"] else []
                self.audit_results["resources"]["vertex_ai"]["endpoints"] = len(endpoints)
                self.print_status(f"Vertex AI Endpoints: {len(endpoints)}", "info")
        else:
            self.print_status("Vertex AI API not enabled or accessible", "warning")

    def audit_iam(self):
        """Audit IAM configuration"""
        self.print_header("IAM Configuration Audit")

        cmd = f"gcloud projects get-iam-policy {self.project_id} --format=json"
        result = self.run_command(cmd)

        if result["success"]:
            iam_policy = json.loads(result["stdout"])
            bindings = iam_policy.get("bindings", [])

            self.audit_results["resources"]["iam"] = {
                "bindings_count": len(bindings),
                "service_accounts": []
            }

            # Extract service accounts
            for binding in bindings:
                for member in binding.get("members", []):
                    if member.startswith("serviceAccount:"):
                        sa_email = member.replace("serviceAccount:", "")
                        if sa_email not in self.audit_results["resources"]["iam"]["service_accounts"]:
                            self.audit_results["resources"]["iam"]["service_accounts"].append(sa_email)

            self.print_status(f"IAM Bindings: {len(bindings)}", "info")
            self.print_status(f"Service Accounts: {len(self.audit_results['resources']['iam']['service_accounts'])}", "info")
        else:
            self.print_status(f"Failed to get IAM policy: {result['stderr']}", "error")

    def audit_storage(self):
        """Audit Cloud Storage buckets"""
        self.print_header("Cloud Storage Audit")

        cmd = f"gsutil ls -p {self.project_id}"
        result = self.run_command(cmd)

        if result["success"]:
            buckets = [line.strip() for line in result["stdout"].split('\n') if line.strip()]
            self.audit_results["resources"]["storage"] = {
                "buckets": buckets,
                "count": len(buckets)
            }

            for bucket in buckets:
                self.print_status(f"Bucket: {bucket}", "success")
        else:
            self.print_status(f"Failed to list storage buckets: {result['stderr']}", "error")

    def test_end_to_end_flow(self):
        """Test complete application flow"""
        self.print_header("End-to-End Flow Testing")

        # Test engine endpoints
        engines = [
            ("Engine A", "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app"),
            ("Engine B", "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app"),
            ("Engine C", "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app"),
            ("Engine D", "https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app")
        ]

        for name, url in engines:
            try:
                response = requests.get(f"{url}/health", timeout=10)
                if response.status_code == 200:
                    self.print_status(f"{name}: Healthy", "success")
                else:
                    self.print_status(f"{name}: Unhealthy ({response.status_code})", "error")
            except Exception as e:
                self.print_status(f"{name}: Connection failed - {str(e)}", "error")

        # Test Gemini integration
        try:
            gemini_payload = {
                "prompt": "Test Gemini integration",
                "userId": "audit_test",
                "context": {"source": "deployment_audit"}
            }

            response = requests.post(
                "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/api/gemini/analyze",
                json=gemini_payload,
                timeout=30
            )

            if response.status_code == 200:
                self.print_status("Gemini Integration: Working", "success")
            else:
                self.print_status(f"Gemini Integration: Failed ({response.status_code})", "error")
        except Exception as e:
            self.print_status(f"Gemini Integration: Error - {str(e)}", "error")

    def check_duplicates_and_cleanup(self):
        """Identify and recommend cleanup for duplicates"""
        self.print_header("Duplicate Resources Check")

        # Check for duplicate functions
        functions = self.audit_results.get("resources", {}).get("firebase_functions", {}).get("functions", [])

        # Common duplicates to check
        potential_duplicates = []
        for func in functions:
            if func.lower() in ['submitdhancredentials', 'submitdhancredentialsv2']:
                potential_duplicates.append(func)

        if potential_duplicates:
            self.print_status(f"Found potential duplicate functions: {potential_duplicates}", "warning")
            self.audit_results["recommendations"].append({
                "type": "cleanup",
                "description": f"Consider removing duplicate functions: {potential_duplicates}",
                "action": "Review and remove older versions"
            })

    def deploy_missing_components(self):
        """Deploy any missing or failed components"""
        self.print_header("Missing Components Deployment")

        # Check and deploy Engine B with latest Gemini integration
        self.print_status("Deploying Engine B with latest Gemini integration...", "info")

        deploy_cmd = f"""
        cd engines/engine-b &&
        gcloud builds submit --tag gcr.io/{self.project_id}/infinityai-engine-b --project={self.project_id} &&
        gcloud run deploy infinityai-engine-b
        --image gcr.io/{self.project_id}/infinityai-engine-b
        --region {self.region}
        --project {self.project_id}
        --allow-unauthenticated
        --memory 1Gi
        --cpu 1
        --set-env-vars="GOOGLE_CLOUD_PROJECT={self.project_id}"
        """

        result = self.run_command(deploy_cmd)
        if result["success"]:
            self.print_status("Engine B deployment successful", "success")
        else:
            self.print_status(f"Engine B deployment failed: {result['stderr']}", "error")

    def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        self.print_header("Deployment Report Generation")

        # Summary statistics
        total_resources = 0
        healthy_resources = 0

        for category, data in self.audit_results["resources"].items():
            if isinstance(data, dict) and "count" in data:
                total_resources += data["count"]

        report = {
            "deployment_summary": {
                "total_resources": total_resources,
                "project_id": self.project_id,
                "region": self.region,
                "audit_timestamp": self.audit_results["timestamp"]
            },
            "resource_inventory": self.audit_results["resources"],
            "recommendations": self.audit_results["recommendations"]
        }

        # Save report
        with open("infinityai_deployment_audit_report.json", "w") as f:
            json.dump(report, f, indent=2)

        self.print_status("Deployment report saved to: infinityai_deployment_audit_report.json", "success")

        # Print summary
        print(f"\n🎯 DEPLOYMENT SUMMARY:")
        print(f"📊 Total Cloud Resources: {total_resources}")
        print(f"🔥 Project: {self.project_id}")
        print(f"🌍 Region: {self.region}")
        print(f"⏰ Audit Time: {self.audit_results['timestamp']}")

    async def run_complete_audit(self):
        """Run complete deployment audit and verification"""
        self.print_header("InfinityAI.Pro Complete Deployment Audit")

        # Run all audits
        self.audit_cloud_run_services()
        self.audit_firebase_functions()
        self.audit_firestore()
        self.audit_secrets()
        self.audit_vertex_ai()
        self.audit_iam()
        self.audit_storage()

        # Test functionality
        self.test_end_to_end_flow()

        # Check for issues
        self.check_duplicates_and_cleanup()

        # Deploy missing components
        self.deploy_missing_components()

        # Generate report
        self.generate_deployment_report()

        self.print_header("Audit Complete!")
        return self.audit_results

if __name__ == "__main__":
    auditor = InfinityAICloudAuditor()
    asyncio.run(auditor.run_complete_audit())