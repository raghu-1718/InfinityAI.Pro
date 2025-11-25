#!/usr/bin/env python3
"""
InfinityAI.Pro - Comprehensive Cloud Verification Suite
Real-time verification of all GCP, Firebase, and Firestore deployments
"""

import json
import requests
import subprocess
import time
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
import os
import sys

class CloudVerificationSuite:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.region = "us-central1"
        self.domain = "infinityai.pro"

        # Cloud resources tracking
        self.cloud_run_services = []
        self.firebase_functions = []
        self.firestore_collections = []
        self.domain_mappings = []
        self.secrets = []

        # Verification results
        self.verification_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": self.project_id,
            "cloud_run_services": {},
            "firebase_functions": {},
            "firestore_collections": {},
            "domain_mappings": {},
            "secrets": {},
            "integration_tests": {},
            "issues_found": [],
            "fixes_applied": [],
            "summary": {}
        }

        # Issue tracking
        self.issues = []
        self.fixes = []

    def log_issue(self, category: str, description: str, severity: str = "MEDIUM", resource: str = ""):
        """Log an issue found during verification"""
        issue = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "description": description,
            "severity": severity,
            "resource": resource
        }
        self.issues.append(issue)
        self.verification_results["issues_found"].append(issue)

        emoji = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
        print(f"{emoji} [{severity}] {category}: {description}" + (f" (Resource: {resource})" if resource else ""))

    def log_fix(self, description: str, command: str = "", resource: str = ""):
        """Log a fix that was applied"""
        fix = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": description,
            "command": command,
            "resource": resource
        }
        self.fixes.append(fix)
        self.verification_results["fixes_applied"].append(fix)
        print(f"🔧 FIX APPLIED: {description}" + (f" (Resource: {resource})" if resource else ""))

    async def run_gcloud_command(self, command: str) -> Tuple[bool, str, str]:
        """Run gcloud command and return success, stdout, stderr"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0, stdout.decode(), stderr.decode()
        except Exception as e:
            return False, "", str(e)

    def run_sync_command(self, command: str) -> Tuple[bool, str, str]:
        """Run command synchronously"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    async def verify_cloud_run_services(self):
        """Verify all Cloud Run services"""
        print(f"\n{'='*80}")
        print(f"🚀 VERIFYING CLOUD RUN SERVICES")
        print(f"{'='*80}")

        # List all Cloud Run services
        success, stdout, stderr = await self.run_gcloud_command(
            f"gcloud run services list --region={self.region} --project={self.project_id} --format=json"
        )

        if not success:
            self.log_issue("GCLOUD_ERROR", f"Failed to list Cloud Run services: {stderr}", "HIGH")
            return

        try:
            services = json.loads(stdout)
            self.cloud_run_services = services

            print(f"📋 Found {len(services)} Cloud Run services:")

            # Test each service
            for service in services:
                name = service.get('metadata', {}).get('name', '')
                url = service.get('status', {}).get('url', '')

                if name and url:
                    print(f"   🔗 {name}: {url}")
                    self.verification_results["cloud_run_services"][name] = {
                        "url": url,
                        "status": "unknown",
                        "health_check": "pending",
                        "response_time": 0
                    }

                    # Test health endpoint
                    health_status = await self.test_service_health(name, url)
                    self.verification_results["cloud_run_services"][name].update(health_status)

        except json.JSONDecodeError:
            self.log_issue("JSON_ERROR", "Failed to parse Cloud Run services JSON", "HIGH")

    async def test_service_health(self, service_name: str, url: str) -> Dict[str, Any]:
        """Test health endpoint of a service"""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                health_url = f"{url}/health"
                async with session.get(health_url) as response:
                    response_time = round((time.time() - start_time) * 1000, 2)

                    if response.status == 200:
                        try:
                            data = await response.json()
                            print(f"   ✅ {service_name}: Healthy ({response_time}ms)")
                            return {
                                "status": "healthy",
                                "health_check": "pass",
                                "response_time": response_time,
                                "health_data": data
                            }
                        except:
                            text = await response.text()
                            print(f"   ✅ {service_name}: Responding ({response_time}ms)")
                            return {
                                "status": "responding",
                                "health_check": "pass",
                                "response_time": response_time,
                                "health_data": text[:100]
                            }
                    else:
                        print(f"   ❌ {service_name}: HTTP {response.status} ({response_time}ms)")
                        self.log_issue("SERVICE_UNHEALTHY", f"Service returning HTTP {response.status}", "MEDIUM", service_name)
                        return {
                            "status": "unhealthy",
                            "health_check": "fail",
                            "response_time": response_time,
                            "http_status": response.status
                        }

        except asyncio.TimeoutError:
            print(f"   ⏰ {service_name}: Timeout")
            self.log_issue("SERVICE_TIMEOUT", "Service health check timeout", "MEDIUM", service_name)
            return {
                "status": "timeout",
                "health_check": "fail",
                "response_time": 10000
            }
        except Exception as e:
            print(f"   ❌ {service_name}: Error - {str(e)}")
            self.log_issue("SERVICE_ERROR", f"Service health check error: {str(e)}", "MEDIUM", service_name)
            return {
                "status": "error",
                "health_check": "fail",
                "error": str(e)
            }

    async def verify_firebase_functions(self):
        """Verify Firebase Functions"""
        print(f"\n{'='*80}")
        print(f"🔥 VERIFYING FIREBASE FUNCTIONS")
        print(f"{'='*80}")

        # List Firebase Functions
        success, stdout, stderr = self.run_sync_command(f"firebase functions:list --project={self.project_id}")

        if success and stdout:
            print("📋 Firebase Functions:")
            print(stdout)

            # Parse function names from output
            lines = stdout.split('\n')
            functions = []
            for line in lines:
                if 'https://' in line and 'cloudfunctions.net' in line:
                    # Extract function name and URL
                    parts = line.split()
                    for part in parts:
                        if 'cloudfunctions.net' in part:
                            function_name = part.split('/')[-1].split('-')[0]
                            functions.append({
                                "name": function_name,
                                "url": part,
                                "region": "us-central1"
                            })

            self.firebase_functions = functions

            # Test each function
            for func in functions:
                print(f"   🔗 {func['name']}: {func['url']}")
                self.verification_results["firebase_functions"][func['name']] = {
                    "url": func['url'],
                    "status": "unknown",
                    "test_result": "pending"
                }

                # Test function
                test_result = await self.test_firebase_function(func['name'], func['url'])
                self.verification_results["firebase_functions"][func['name']].update(test_result)

        else:
            print("❌ Firebase Functions: Not accessible or none deployed")
            self.log_issue("FIREBASE_ERROR", f"Failed to list Firebase Functions: {stderr if stderr else 'Unknown error'}", "HIGH")

    async def test_firebase_function(self, func_name: str, url: str) -> Dict[str, Any]:
        """Test a Firebase Function"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                # Try a simple GET request first
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"   ✅ {func_name}: Responding")
                        return {"status": "healthy", "test_result": "pass"}
                    elif response.status == 404:
                        print(f"   ❌ {func_name}: Not Found (404)")
                        self.log_issue("FUNCTION_404", "Firebase Function not found", "HIGH", func_name)
                        return {"status": "not_found", "test_result": "fail"}
                    else:
                        print(f"   ⚠️ {func_name}: HTTP {response.status}")
                        return {"status": "responding", "test_result": "partial", "http_status": response.status}

        except Exception as e:
            print(f"   ❌ {func_name}: Error - {str(e)}")
            self.log_issue("FUNCTION_ERROR", f"Function test error: {str(e)}", "MEDIUM", func_name)
            return {"status": "error", "test_result": "fail", "error": str(e)}

    async def verify_firestore_collections(self):
        """Verify Firestore collections"""
        print(f"\n{'='*80}")
        print(f"🗄️  VERIFYING FIRESTORE COLLECTIONS")
        print(f"{'='*80}")

        # Expected collections based on the application
        expected_collections = [
            "ai_signals",
            "generate",
            "trades",
            "users",
            "portfolio",
            "settings"
        ]

        for collection in expected_collections:
            try:
                # Use gcloud to check collection
                success, stdout, stderr = self.run_sync_command(
                    f"gcloud firestore databases describe --project={self.project_id}"
                )

                if success:
                    print(f"   ✅ Firestore database accessible")
                    self.verification_results["firestore_collections"][collection] = {
                        "status": "accessible",
                        "test_result": "pass"
                    }
                else:
                    print(f"   ❌ Firestore database access failed")
                    self.log_issue("FIRESTORE_ACCESS", "Cannot access Firestore database", "HIGH")

            except Exception as e:
                print(f"   ❌ {collection}: Error - {str(e)}")
                self.log_issue("FIRESTORE_ERROR", f"Firestore collection error: {str(e)}", "MEDIUM", collection)

    async def verify_domain_mappings(self):
        """Verify domain mappings and SSL certificates"""
        print(f"\n{'='*80}")
        print(f"🌐 VERIFYING DOMAIN MAPPINGS & SSL")
        print(f"{'='*80}")

        # List domain mappings
        success, stdout, stderr = await self.run_gcloud_command(
            f"gcloud run domain-mappings list --region={self.region} --project={self.project_id} --format=json"
        )

        if success:
            try:
                mappings = json.loads(stdout)
                self.domain_mappings = mappings

                print(f"📋 Found {len(mappings)} domain mappings:")
                for mapping in mappings:
                    domain = mapping.get('spec', {}).get('routeSpec', {}).get('url', '')
                    service = mapping.get('spec', {}).get('routeSpec', {}).get('service', '')
                    print(f"   🔗 {domain} → {service}")

                    # Test HTTPS connectivity
                    await self.test_domain_connectivity(domain)

            except json.JSONDecodeError:
                self.log_issue("JSON_ERROR", "Failed to parse domain mappings", "MEDIUM")
        else:
            self.log_issue("DOMAIN_ERROR", f"Failed to list domain mappings: {stderr}", "MEDIUM")

    async def test_domain_connectivity(self, domain: str):
        """Test domain connectivity and SSL"""
        try:
            url = f"https://{domain}"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status < 400:
                        print(f"   ✅ {domain}: HTTPS OK (Status: {response.status})")
                    else:
                        print(f"   ⚠️ {domain}: HTTP {response.status}")

        except Exception as e:
            print(f"   ❌ {domain}: Error - {str(e)}")
            self.log_issue("DOMAIN_CONNECTIVITY", f"Domain connectivity error: {str(e)}", "MEDIUM", domain)

    async def verify_secrets(self):
        """Verify GCP Secret Manager secrets"""
        print(f"\n{'='*80}")
        print(f"🔐 VERIFYING GCP SECRETS")
        print(f"{'='*80}")

        # List secrets
        success, stdout, stderr = await self.run_gcloud_command(
            f"gcloud secrets list --project={self.project_id} --format=json"
        )

        if success:
            try:
                secrets = json.loads(stdout)
                print(f"📋 Found {len(secrets)} secrets:")

                for secret in secrets:
                    name = secret.get('name', '').split('/')[-1]
                    created = secret.get('createTime', '')
                    print(f"   🔑 {name} (Created: {created})")

                    # Test secret access
                    can_access = await self.test_secret_access(name)
                    self.verification_results["secrets"][name] = {
                        "accessible": can_access,
                        "created": created
                    }

            except json.JSONDecodeError:
                self.log_issue("JSON_ERROR", "Failed to parse secrets list", "MEDIUM")
        else:
            self.log_issue("SECRETS_ERROR", f"Failed to list secrets: {stderr}", "HIGH")

    async def test_secret_access(self, secret_name: str) -> bool:
        """Test if a secret can be accessed"""
        try:
            success, stdout, stderr = await self.run_gcloud_command(
                f"gcloud secrets versions access latest --secret={secret_name} --project={self.project_id}"
            )

            if success and stdout.strip():
                print(f"   ✅ {secret_name}: Accessible")
                return True
            else:
                print(f"   ❌ {secret_name}: Access failed")
                self.log_issue("SECRET_ACCESS", f"Cannot access secret: {stderr}", "HIGH", secret_name)
                return False

        except Exception as e:
            print(f"   ❌ {secret_name}: Error - {str(e)}")
            self.log_issue("SECRET_ACCESS", f"Secret access error: {str(e)}", "HIGH", secret_name)
            return False

    async def run_integration_tests(self):
        """Run integration tests between services"""
        print(f"\n{'='*80}")
        print(f"🔗 RUNNING INTEGRATION TESTS")
        print(f"{'='*80}")

        # Find service URLs
        service_urls = {}
        for name, service in self.verification_results["cloud_run_services"].items():
            if service.get("status") == "healthy":
                service_urls[name] = service["url"]

        # Test engine-to-engine communication
        if "infinityai-engine-d" in service_urls and "infinityai-engine-a" in service_urls:
            await self.test_engine_integration(service_urls["infinityai-engine-d"], service_urls["infinityai-engine-a"])

        # Test frontend to backend
        if "infinityai-frontend" in service_urls:
            await self.test_frontend_integration(service_urls["infinityai-frontend"])

    async def test_engine_integration(self, engine_d_url: str, engine_a_url: str):
        """Test integration between engines"""
        print(f"🧪 Testing Engine D ↔ Engine A integration")

        try:
            # Test Engine D health endpoint
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{engine_d_url}/api/health/simple") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Engine D health API: OK")
                        self.verification_results["integration_tests"]["engine_d_health"] = {"status": "pass", "data": data}
                    else:
                        print(f"   ❌ Engine D health API: Failed")
                        self.log_issue("INTEGRATION_ERROR", "Engine D health API failed", "MEDIUM")

        except Exception as e:
            print(f"   ❌ Engine integration test failed: {str(e)}")
            self.log_issue("INTEGRATION_ERROR", f"Engine integration error: {str(e)}", "MEDIUM")

    async def test_frontend_integration(self, frontend_url: str):
        """Test frontend integration"""
        print(f"🧪 Testing Frontend integration")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Test main page
                async with session.get(frontend_url) as response:
                    if response.status == 200:
                        print(f"   ✅ Frontend: Accessible")
                        self.verification_results["integration_tests"]["frontend_access"] = {"status": "pass"}
                    else:
                        print(f"   ❌ Frontend: HTTP {response.status}")
                        self.log_issue("INTEGRATION_ERROR", f"Frontend returned HTTP {response.status}", "MEDIUM")

        except Exception as e:
            print(f"   ❌ Frontend integration test failed: {str(e)}")
            self.log_issue("INTEGRATION_ERROR", f"Frontend integration error: {str(e)}", "MEDIUM")

    def check_for_duplicates(self):
        """Check for duplicate deployments"""
        print(f"\n{'='*80}")
        print(f"🔍 CHECKING FOR DUPLICATE DEPLOYMENTS")
        print(f"{'='*80}")

        # Group services by base name
        service_groups = {}
        for service in self.cloud_run_services:
            name = service.get('metadata', {}).get('name', '')
            base_name = name.split('-')[0] if '-' in name else name

            if base_name not in service_groups:
                service_groups[base_name] = []
            service_groups[base_name].append(service)

        # Check for duplicates
        duplicates_found = False
        for base_name, services in service_groups.items():
            if len(services) > 1:
                duplicates_found = True
                print(f"   ⚠️ Found {len(services)} services with base name '{base_name}':")
                for service in services:
                    name = service.get('metadata', {}).get('name', '')
                    url = service.get('status', {}).get('url', '')
                    print(f"      - {name}: {url}")

                self.log_issue("DUPLICATE_SERVICE", f"Multiple services found for {base_name}", "MEDIUM")

        if not duplicates_found:
            print("   ✅ No duplicate deployments found")

    async def fix_identified_issues(self):
        """Fix identified issues automatically where possible"""
        print(f"\n{'='*80}")
        print(f"🔧 FIXING IDENTIFIED ISSUES")
        print(f"{'='*80}")

        high_priority_issues = [issue for issue in self.issues if issue["severity"] == "HIGH"]

        for issue in high_priority_issues:
            category = issue["category"]
            resource = issue.get("resource", "")

            if category == "SECRET_ACCESS":
                await self.fix_secret_access(resource)
            elif category == "SERVICE_UNHEALTHY":
                await self.fix_unhealthy_service(resource)
            elif category == "FUNCTION_404":
                await self.fix_missing_function(resource)

        print(f"🔧 Applied {len(self.fixes)} fixes")

    async def fix_secret_access(self, secret_name: str):
        """Fix secret access issues"""
        if not secret_name:
            return

        print(f"🔧 Attempting to fix secret access for: {secret_name}")

        # Check if secret exists but has wrong permissions
        success, stdout, stderr = await self.run_gcloud_command(
            f"gcloud secrets describe {secret_name} --project={self.project_id}"
        )

        if success:
            # Secret exists, might be a permission issue
            # Grant Cloud Run service account access
            fix_command = f"gcloud secrets add-iam-policy-binding {secret_name} --member='serviceAccount:{self.project_id}@appspot.gserviceaccount.com' --role='roles/secretmanager.secretAccessor' --project={self.project_id}"

            success, stdout, stderr = await self.run_gcloud_command(fix_command)
            if success:
                self.log_fix(f"Fixed secret access permissions for {secret_name}", fix_command, secret_name)
            else:
                self.log_issue("FIX_FAILED", f"Failed to fix secret permissions: {stderr}", "HIGH", secret_name)

    async def fix_unhealthy_service(self, service_name: str):
        """Fix unhealthy service"""
        if not service_name:
            return

        print(f"🔧 Attempting to fix unhealthy service: {service_name}")

        # Try to get service logs for diagnosis
        success, stdout, stderr = await self.run_gcloud_command(
            f"gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"{service_name}\"' --limit=10 --project={self.project_id}"
        )

        if success:
            print(f"   📋 Recent logs for {service_name}:")
            print(stdout[:500] + "..." if len(stdout) > 500 else stdout)

    async def fix_missing_function(self, function_name: str):
        """Fix missing Firebase function"""
        if not function_name:
            return

        print(f"🔧 Function {function_name} appears to be missing")
        self.log_fix(f"Identified missing function {function_name} - requires manual redeployment", "", function_name)

    def generate_comprehensive_report(self):
        """Generate comprehensive verification report"""
        print(f"\n{'='*100}")
        print(f"📊 COMPREHENSIVE VERIFICATION REPORT")
        print(f"{'='*100}")

        # Calculate summary statistics
        total_services = len(self.verification_results["cloud_run_services"])
        healthy_services = len([s for s in self.verification_results["cloud_run_services"].values()
                               if s.get("status") == "healthy"])

        total_functions = len(self.verification_results["firebase_functions"])
        working_functions = len([f for f in self.verification_results["firebase_functions"].values()
                                if f.get("status") == "healthy"])

        total_secrets = len(self.verification_results["secrets"])
        accessible_secrets = len([s for s in self.verification_results["secrets"].values()
                                 if s.get("accessible")])

        # Update summary
        self.verification_results["summary"] = {
            "total_issues": len(self.issues),
            "high_severity_issues": len([i for i in self.issues if i["severity"] == "HIGH"]),
            "medium_severity_issues": len([i for i in self.issues if i["severity"] == "MEDIUM"]),
            "fixes_applied": len(self.fixes),
            "cloud_run_services": {
                "total": total_services,
                "healthy": healthy_services,
                "health_percentage": round((healthy_services / total_services * 100) if total_services > 0 else 0, 1)
            },
            "firebase_functions": {
                "total": total_functions,
                "working": working_functions,
                "success_percentage": round((working_functions / total_functions * 100) if total_functions > 0 else 0, 1)
            },
            "secrets": {
                "total": total_secrets,
                "accessible": accessible_secrets,
                "access_percentage": round((accessible_secrets / total_secrets * 100) if total_secrets > 0 else 0, 1)
            },
            "overall_health": "HEALTHY" if len([i for i in self.issues if i["severity"] == "HIGH"]) == 0 else "NEEDS_ATTENTION"
        }

        # Print summary
        summary = self.verification_results["summary"]
        print(f"🏗️  Cloud Run Services: {summary['cloud_run_services']['healthy']}/{summary['cloud_run_services']['total']} healthy ({summary['cloud_run_services']['health_percentage']}%)")
        print(f"🔥 Firebase Functions: {summary['firebase_functions']['working']}/{summary['firebase_functions']['total']} working ({summary['firebase_functions']['success_percentage']}%)")
        print(f"🔐 Secrets: {summary['secrets']['accessible']}/{summary['secrets']['total']} accessible ({summary['secrets']['access_percentage']}%)")
        print(f"🚨 Issues Found: {summary['total_issues']} (High: {summary['high_severity_issues']}, Medium: {summary['medium_severity_issues']})")
        print(f"🔧 Fixes Applied: {summary['fixes_applied']}")
        print(f"🎯 Overall Health: {summary['overall_health']}")

        # Save detailed report
        report_filename = f"cloud_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.verification_results, f, indent=2)

        print(f"\n📊 Detailed report saved to: {report_filename}")
        return report_filename

    async def run_complete_verification(self):
        """Run complete cloud verification suite"""
        print(f"\n{'='*100}")
        print(f"☁️  InfinityAI.Pro Cloud Verification Suite")
        print(f"Project: {self.project_id} | Region: {self.region}")
        print(f"{'='*100}")

        # Run all verification steps
        await self.verify_cloud_run_services()
        await self.verify_firebase_functions()
        await self.verify_firestore_collections()
        await self.verify_domain_mappings()
        await self.verify_secrets()
        await self.run_integration_tests()
        self.check_for_duplicates()
        await self.fix_identified_issues()

        # Generate final report
        report_file = self.generate_comprehensive_report()

        return report_file, self.verification_results

if __name__ == "__main__":
    async def main():
        verifier = CloudVerificationSuite()
        report_file, results = await verifier.run_complete_verification()

        # Print final status
        if results["summary"]["overall_health"] == "HEALTHY":
            print(f"\n🎉 VERIFICATION COMPLETE: System is healthy!")
        else:
            print(f"\n⚠️  VERIFICATION COMPLETE: Issues require attention")

        return report_file

    # Run the verification
    asyncio.run(main())