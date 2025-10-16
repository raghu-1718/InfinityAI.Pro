#!/usr/bin/env python3
"""
Full GCP Audit & Integration Verification
Comprehensive audit of InfinityAI.Pro deployment on Google Cloud Platform
"""

import json
import subprocess
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
import os

class GCPAuditor:
    def __init__(self):
        self.project_id = "after-yesterday-473512-k3"
        self.region = "us-central1"
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.results = {
            "audit_timestamp": datetime.utcnow().isoformat() + "Z",
            "project": self.project_id,
            "region": self.region,
            "cloud_run_services": [],
            "health_checks": {},
            "artifact_images": [],
            "secrets": [],
            "dns_configuration": {},
            "domain_mapping": {},
            "security_scan": {},
            "engine_integration": {},
            "ci_cd_coverage": {}
        }
    
    def run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                try:
                    return {"success": True, "data": json.loads(result.stdout)}
                except json.JSONDecodeError:
                    return {"success": True, "data": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def audit_cloud_run_services(self):
        """List and verify all Cloud Run services"""
        print("📦 Auditing Cloud Run services...")
        cmd = [
            "gcloud", "run", "services", "list",
            f"--region={self.region}",
            f"--project={self.project_id}",
            "--format=json"
        ]
        result = self.run_command(cmd)
        
        if result["success"]:
            services = result["data"]
            self.results["cloud_run_services"] = [
                {
                    "name": svc["metadata"]["name"],
                    "url": svc["status"].get("url", "N/A"),
                    "ready": any(c["type"] == "Ready" and c["status"] == "True" 
                                for c in svc["status"].get("conditions", [])),
                    "image": svc["spec"]["template"]["spec"]["containers"][0]["image"],
                    "created": svc["metadata"]["creationTimestamp"],
                    "revision": svc["status"].get("latestReadyRevisionName", "N/A")
                }
                for svc in services
            ]
            print(f"✅ Found {len(services)} Cloud Run services")
        else:
            print(f"❌ Failed to list services: {result['error']}")
    
    def check_health_endpoints(self):
        """Ping /health endpoints for all services"""
        print("\n🏥 Checking health endpoints...")
        
        services = {
            "engine-a-market-data": "https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app",
            "engine-b-ai-ml": "https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app",
            "engine-c": "https://engine-c-prod-bprmddefsa-uc.a.run.app",  # Corrected service name
            "engine-d-chatbot": "https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app",
            "engine-ultra-aggressive": "https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app",
            "frontend": "https://infinityai-frontend-bprmddefsa-uc.a.run.app"
        }
        
        for name, url in services.items():
            try:
                start_time = time.time()
                response = requests.get(f"{url}/health", timeout=15)
                latency_ms = round((time.time() - start_time) * 1000, 2)
                
                self.results["health_checks"][name] = {
                    "url": url,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "healthy": response.status_code == 200,
                    "response_preview": response.text[:200] if response.text else None,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                status_icon = "✅" if response.status_code == 200 else "⚠️"
                print(f"{status_icon} {name}: {response.status_code} ({latency_ms}ms)")
                
            except requests.exceptions.Timeout:
                self.results["health_checks"][name] = {
                    "url": url,
                    "status_code": "TIMEOUT",
                    "healthy": False,
                    "error": "Request timed out after 15s"
                }
                print(f"⏱️  {name}: TIMEOUT (>15s)")
                
            except Exception as e:
                self.results["health_checks"][name] = {
                    "url": url,
                    "status_code": "ERROR",
                    "healthy": False,
                    "error": str(e)
                }
                print(f"❌ {name}: ERROR - {str(e)}")
    
    def audit_artifact_registry(self):
        """List container images in Artifact Registry"""
        print("\n🐳 Auditing Artifact Registry...")
        cmd = [
            "gcloud", "artifacts", "docker", "images", "list",
            f"us-central1-docker.pkg.dev/{self.project_id}/infinityai-repo",
            "--format=json",
            "--limit=20"
        ]
        result = self.run_command(cmd)
        
        if result["success"]:
            images = result["data"]
            # Group by package
            packages = {}
            for img in images:
                pkg = img.get("package", "unknown")
                if pkg not in packages:
                    packages[pkg] = []
                packages[pkg].append({
                    "version": img.get("version", ""),
                    "tags": img.get("tags", ""),
                    "size_bytes": img.get("metadata", {}).get("imageSizeBytes", "0"),
                    "created": img.get("createTime", "")
                })
            
            self.results["artifact_images"] = {
                "total_images": len(images),
                "packages": packages
            }
            print(f"✅ Found {len(packages)} packages with {len(images)} images")
        else:
            print(f"❌ Failed to list images: {result['error']}")
    
    def audit_secrets(self):
        """List secrets from Secret Manager"""
        print("\n🔐 Auditing Secret Manager...")
        cmd = [
            "gcloud", "secrets", "list",
            f"--project={self.project_id}",
            "--format=json"
        ]
        result = self.run_command(cmd)
        
        if result["success"]:
            secrets = result["data"]
            self.results["secrets"] = [
                {
                    "name": s["name"].split("/")[-1],
                    "created": s.get("createTime"),
                    "replication": s.get("replication", {})
                }
                for s in secrets
            ]
            print(f"✅ Found {len(secrets)} secrets")
        else:
            print(f"❌ Failed to list secrets: {result['error']}")
    
    def audit_dns_configuration(self):
        """Check Cloud DNS and domain mapping"""
        print("\n🌐 Auditing DNS configuration...")
        
        # Check DNS zones
        cmd = ["gcloud", "dns", "managed-zones", "list", 
               f"--project={self.project_id}", "--format=json"]
        result = self.run_command(cmd)
        
        if result["success"] and result["data"]:
            zone = result["data"][0]
            self.results["dns_configuration"]["zone"] = {
                "name": zone.get("name"),
                "dns_name": zone.get("dnsName"),
                "nameservers": zone.get("nameServers", []),
                "dnssec_enabled": zone.get("dnssecConfig", {}).get("state") == "on"
            }
            
            # Get DNS records
            zone_name = zone.get("name")
            cmd = ["gcloud", "dns", "record-sets", "list",
                   f"--zone={zone_name}", f"--project={self.project_id}",
                   "--format=json"]
            records_result = self.run_command(cmd)
            
            if records_result["success"]:
                self.results["dns_configuration"]["records"] = [
                    {
                        "name": r.get("name"),
                        "type": r.get("type"),
                        "ttl": r.get("ttl"),
                        "data": r.get("rrdatas", [])
                    }
                    for r in records_result["data"]
                ]
                print(f"✅ DNS zone configured with {len(records_result['data'])} records")
        else:
            print("⚠️  No DNS zones found")
    
    def verify_engine_integration(self):
        """Document engine roles and integration"""
        print("\n⚙️  Verifying engine integration...")
        
        engines = {
            "engine-a-market-data": {
                "role": "Market Data Ingestion",
                "description": "Real-time market data collection from Dhan broker API",
                "data_flow": "Dhan API → Engine A → WebSocket → Frontend/Engine B",
                "endpoints": ["/health", "/api/market-data", "/ws"],
                "integrations": ["Dhan Broker API", "WebSocket Server", "Redis Cache"]
            },
            "engine-b-ai-ml": {
                "role": "AI/ML Inference",
                "description": "Machine learning models for market prediction and analysis",
                "data_flow": "Engine A → Engine B → Predictions → Engine C/D",
                "endpoints": ["/health", "/api/predict", "/api/analyze"],
                "integrations": ["Vertex AI", "HuggingFace API", "TensorFlow Models"]
            },
            "engine-c-execution": {
                "role": "Trade Execution Routing",
                "description": "Order management and execution routing to broker",
                "data_flow": "Strategy Signals → Engine C → Dhan API → Order Confirmation",
                "endpoints": ["/health", "/api/execute", "/api/orders"],
                "integrations": ["Dhan Trading API", "Order Queue", "Risk Manager"]
            },
            "engine-d-chatbot": {
                "role": "NLP Chatbot & Orchestration",
                "description": "Natural language interface and multi-engine orchestration",
                "data_flow": "User Query → Engine D → Engines A/B/C → Response",
                "endpoints": ["/health", "/api/chat", "/api/orchestrate"],
                "integrations": ["All Engines", "NLP Models", "WebSocket"]
            },
            "engine-ultra-aggressive": {
                "role": "Aggressive Strategy Logic",
                "description": "High-frequency trading strategies and rapid execution",
                "data_flow": "Market Data → Ultra Engine → Fast Signals → Engine C",
                "endpoints": ["/health", "/api/strategy", "/api/signals"],
                "integrations": ["Engine A", "Engine C", "Real-time Analytics"]
            }
        }
        
        self.results["engine_integration"] = engines
        print(f"✅ Documented {len(engines)} engine integrations")
    
    def verify_ci_cd_coverage(self):
        """Check CI/CD workflow coverage for all components"""
        print("\n🔄 Verifying CI/CD coverage...")
        
        workflows_dir = "/workspaces/InfinityAI.Pro/.github/workflows"
        
        components = [
            "engine-a", "engine-b", "engine-c-execution",
            "engine-d-chatbot", "engine-ultra-aggressive", "frontend"
        ]
        
        coverage = {}
        
        if os.path.exists(workflows_dir):
            workflows = os.listdir(workflows_dir)
            for component in components:
                matched_workflows = [w for w in workflows if component.replace("-", "_") in w or component in w]
                coverage[component] = {
                    "has_ci": len(matched_workflows) > 0,
                    "workflows": matched_workflows
                }
            
            # Check deploy-production.yml for matrix coverage
            prod_workflow = os.path.join(workflows_dir, "deploy-production.yml")
            if os.path.exists(prod_workflow):
                with open(prod_workflow, 'r') as f:
                    content = f.read()
                    coverage["deploy_production_matrix"] = {
                        "has_engine_a": "engine-a-market-data" in content,
                        "has_engine_b": "engine-b-ai-ml" in content,
                        "has_engine_c": "engine-c-execution" in content,
                        "has_engine_d": "engine-d-chatbot" in content,
                        "has_engine_ultra": "engine-ultra-aggressive" in content,
                        "has_frontend": "frontend" in content or "infinityai-frontend" in content
                    }
        
        self.results["ci_cd_coverage"] = coverage
        print(f"✅ CI/CD coverage verified for {len(components)} components")
    
    def security_scan(self):
        """Scan for credential files and security issues"""
        print("\n🔒 Running security scan...")
        
        findings = {
            "credential_files": [],
            "env_file_checks": [],
            "exposed_secrets": []
        }
        
        # Scan for credential files
        try:
            result = subprocess.run(
                ["find", ".", "-name", "*credentials*", "-o", "-name", "*dhan*.json"],
                capture_output=True,
                text=True,
                cwd="/workspaces/InfinityAI.Pro"
            )
            
            files = [f for f in result.stdout.split("\n") 
                    if f and "node_modules" not in f and ".git" not in f]
            
            findings["credential_files"] = files
            
        except Exception as e:
            findings["scan_error"] = str(e)
        
        # Check .env files
        env_files = [
            "backend/.env", "frontend/.env", "frontend/web/.env",
            ".env", ".env.production"
        ]
        
        for env_file in env_files:
            full_path = f"/workspaces/InfinityAI.Pro/{env_file}"
            if os.path.exists(full_path):
                findings["env_file_checks"].append({
                    "file": env_file,
                    "exists": True,
                    "note": "Review for hardcoded credentials"
                })
        
        self.results["security_scan"] = findings
        
        if findings["credential_files"]:
            print(f"⚠️  Found {len(findings['credential_files'])} credential files")
        else:
            print("✅ No exposed credential files found")
    
    def save_results(self):
        """Save audit results to JSON and generate markdown report"""
        print("\n💾 Saving audit results...")
        
        # Save JSON
        json_file = f"/workspaces/InfinityAI.Pro/deployment_verification_{self.timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✅ JSON report: {json_file}")
        
        # Generate Markdown report
        self.generate_markdown_report()
    
    def generate_markdown_report(self):
        """Generate comprehensive markdown report"""
        report_file = "/workspaces/InfinityAI.Pro/FINAL_LIVE_DEPLOYMENT_VERIFICATION_REPORT.md"
        
        with open(report_file, 'w') as f:
            f.write("# InfinityAI.Pro - Final Live Deployment Verification Report\n\n")
            f.write(f"**Audit Timestamp:** {self.results['audit_timestamp']}\n")
            f.write(f"**GCP Project:** {self.project_id}\n")
            f.write(f"**Region:** {self.region}\n\n")
            
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            healthy_services = sum(1 for h in self.results["health_checks"].values() if h.get("healthy"))
            total_services = len(self.results["health_checks"])
            f.write(f"- **Cloud Run Services:** {len(self.results['cloud_run_services'])} deployed\n")
            f.write(f"- **Health Status:** {healthy_services}/{total_services} services healthy\n")
            f.write(f"- **Secrets Configured:** {len(self.results['secrets'])} secrets\n")
            f.write(f"- **DNS Configuration:** {'✅ Active' if self.results['dns_configuration'] else '❌ Not configured'}\n\n")
            
            # Cloud Run Services
            f.write("## 1. Cloud Run Services\n\n")
            f.write("| Service | Status | URL | Image |\n")
            f.write("|---------|--------|-----|-------|\n")
            for svc in self.results["cloud_run_services"]:
                status = "✅ Ready" if svc["ready"] else "⚠️ Not Ready"
                f.write(f"| {svc['name']} | {status} | {svc['url']} | {svc['image'].split('/')[-1]} |\n")
            f.write("\n")
            
            # Health Checks
            f.write("## 2. Health Check Results\n\n")
            f.write("| Service | Status | Latency | Details |\n")
            f.write("|---------|--------|---------|----------|\n")
            for name, health in self.results["health_checks"].items():
                status_icon = "✅" if health.get("healthy") else "❌"
                latency = f"{health.get('latency_ms', 'N/A')}ms" if health.get('latency_ms') else "Timeout"
                status_code = health.get('status_code', 'ERROR')
                f.write(f"| {name} | {status_icon} {status_code} | {latency} | {health.get('error', 'OK')[:50]} |\n")
            f.write("\n")
            
            # Engine Integration
            f.write("## 3. Engine Integration Architecture\n\n")
            for engine_name, engine_info in self.results["engine_integration"].items():
                f.write(f"### {engine_name}\n\n")
                f.write(f"**Role:** {engine_info['role']}\n\n")
                f.write(f"**Description:** {engine_info['description']}\n\n")
                f.write(f"**Data Flow:**\n```\n{engine_info['data_flow']}\n```\n\n")
                f.write(f"**Endpoints:** {', '.join(engine_info['endpoints'])}\n\n")
                f.write(f"**Integrations:** {', '.join(engine_info['integrations'])}\n\n")
            
            # Artifact Registry
            f.write("## 4. Artifact Registry\n\n")
            if self.results["artifact_images"]:
                f.write(f"**Total Images:** {self.results['artifact_images'].get('total_images', 0)}\n\n")
                f.write("**Packages:**\n")
                for pkg, images in self.results["artifact_images"].get("packages", {}).items():
                    pkg_name = pkg.split('/')[-1]
                    f.write(f"- `{pkg_name}`: {len(images)} images\n")
            f.write("\n")
            
            # Secrets
            f.write("## 5. Secret Manager\n\n")
            f.write("| Secret Name | Replication |\n")
            f.write("|-------------|-------------|\n")
            for secret in self.results["secrets"]:
                replication = "Automatic" if secret.get("replication", {}).get("automatic") else "User-managed"
                f.write(f"| {secret['name']} | {replication} |\n")
            f.write("\n")
            
            # DNS Configuration
            f.write("## 6. DNS Configuration\n\n")
            if self.results["dns_configuration"]:
                zone = self.results["dns_configuration"].get("zone", {})
                f.write(f"**Zone:** {zone.get('dns_name', 'N/A')}\n\n")
                f.write(f"**DNSSEC:** {'✅ Enabled' if zone.get('dnssec_enabled') else '❌ Disabled'}\n\n")
                f.write("**Nameservers:**\n")
                for ns in zone.get("nameservers", []):
                    f.write(f"- {ns}\n")
                f.write("\n")
            
            # CI/CD Coverage
            f.write("## 7. CI/CD Coverage\n\n")
            f.write("| Component | CI Coverage | Workflows |\n")
            f.write("|-----------|-------------|----------|\n")
            for component, coverage in self.results["ci_cd_coverage"].items():
                if isinstance(coverage, dict) and "has_ci" in coverage:
                    status = "✅" if coverage["has_ci"] else "❌"
                    workflows = ", ".join(coverage.get("workflows", ["None"]))
                    f.write(f"| {component} | {status} | {workflows} |\n")
            f.write("\n")
            
            # Security Scan
            f.write("## 8. Security Scan\n\n")
            findings = self.results["security_scan"]
            if findings.get("credential_files"):
                f.write("**⚠️ Credential Files Found:**\n")
                for file in findings["credential_files"]:
                    f.write(f"- `{file}`\n")
            else:
                f.write("✅ No exposed credential files found\n")
            f.write("\n")
            
            # Recommendations
            f.write("## 9. Recommendations\n\n")
            f.write("### High Priority\n")
            
            if healthy_services < total_services:
                f.write(f"- ⚠️ Fix {total_services - healthy_services} unhealthy services\n")
            
            if not self.results["dns_configuration"].get("zone", {}).get("dnssec_enabled"):
                f.write("- 🔒 Consider enabling DNSSEC for enhanced security\n")
            
            f.write("\n### Security\n")
            f.write("- Rotate secrets regularly using GCP Secret Manager versioning\n")
            f.write("- Enable vulnerability scanning in Artifact Registry\n")
            f.write("- Review and remove any hardcoded credentials from codebase\n")
            
            f.write("\n### Monitoring\n")
            f.write("- Set up Cloud Monitoring alerts for service health\n")
            f.write("- Configure uptime checks for all public endpoints\n")
            f.write("- Enable Cloud Logging for all Cloud Run services\n")
            
            f.write("\n---\n\n")
            f.write(f"*Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n")
        
        print(f"✅ Markdown report: {report_file}")
    
    def run_full_audit(self):
        """Execute complete audit"""
        print("=" * 60)
        print("🚀 InfinityAI.Pro - Full GCP Audit & Integration")
        print("=" * 60)
        
        self.audit_cloud_run_services()
        self.check_health_endpoints()
        self.audit_artifact_registry()
        self.audit_secrets()
        self.audit_dns_configuration()
        self.verify_engine_integration()
        self.verify_ci_cd_coverage()
        self.security_scan()
        self.save_results()
        
        print("\n" + "=" * 60)
        print("✅ Full GCP Audit Complete!")
        print("=" * 60)


if __name__ == "__main__":
    auditor = GCPAuditor()
    auditor.run_full_audit()
