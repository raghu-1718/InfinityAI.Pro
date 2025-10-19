#!/usr/bin/env python3
"""
InfinityAI.Pro - Complete Production Deployment Script
Deploy all components with OAuth integration, security hardening, and GitHub version tracking
"""

import subprocess
import sys
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PRODUCTION-DEPLOY - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionDeployer:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.region = "us-central1"
        self.domain = "infinityai.pro"
        
        self.services = {
            'infinityai-engine-a': {
                'path': 'backend/engines/engine-a',
                'description': 'Market Data Engine - Real-time NIFTY/BANKNIFTY data',
                'port': 8080
            },
            'infinityai-engine-b': {
                'path': 'backend/engines/engine-b',
                'description': 'AI/ML Engine - Predictions and signals',
                'port': 8080
            },
            'infinityai-engine-c-execution': {
                'path': 'backend/engines/engine-c-execution',
                'description': 'Trading Engine - Secure OAuth & order execution',
                'port': 8080
            },
            'infinityai-engine-d': {
                'path': 'backend/engines/engine-d',
                'description': 'Chatbot Engine - Multi-engine orchestration',
                'port': 8080
            },
            'infinityai-frontend': {
                'path': 'frontend-new',
                'description': 'Dashboard Frontend - Real-time UI & data aggregation',
                'port': 8080
            }
        }

    def run_command(self, command: str, cwd: str = None) -> bool:
        """Execute command and return success status"""
        try:
            logger.info(f"Executing: {command}")
            if cwd:
                logger.info(f"Working directory: {cwd}")
                
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Command succeeded: {command}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout[:200]}...")
                return True
            else:
                logger.error(f"❌ Command failed: {command}")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception running command '{command}': {e}")
            return False

    def update_version_info(self) -> str:
        """Update version information across all services"""
        logger.info("📝 Updating version information...")
        
        version = datetime.now().strftime("v%Y.%m.%d-%H%M%S")
        build_info = {
            'version': version,
            'build_timestamp': datetime.now().isoformat(),
            'commit_hash': self.get_git_commit_hash(),
            'oauth_integration': 'enabled',
            'security_hardened': True,
            'cloud_platform': 'Google Cloud Run',
            'region': self.region,
            'domain': self.domain
        }
        
        # Save build info
        with open('build_info.json', 'w') as f:
            json.dump(build_info, f, indent=2)
            
        logger.info(f"✅ Version updated: {version}")
        return version

    def get_git_commit_hash(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                'git rev-parse --short HEAD',
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'

    def setup_secrets(self) -> bool:
        """Setup Google Secret Manager secrets"""
        logger.info("🔐 Setting up Google Secret Manager secrets...")
        
        try:
            # Run the secret setup script
            return self.run_command("python setup_secrets.py")
        except Exception as e:
            logger.error(f"❌ Error setting up secrets: {e}")
            return False

    def commit_to_github(self) -> bool:
        """Commit all changes to GitHub with version tracking"""
        logger.info("📤 Committing to GitHub with version tracking...")
        
        version = self.update_version_info()
        
        # Git operations
        commands = [
            "git add .",
            f'git commit -m "🔐 Production deployment {version} - OAuth integration + security hardening + Secret Manager"',
            "git push origin main"
        ]
        
        for command in commands:
            if not self.run_command(command):
                logger.error(f"❌ Git operation failed: {command}")
                return False
                
        logger.info("✅ Successfully committed to GitHub")
        return True

    def deploy_service(self, service_name: str, service_config: Dict[str, Any]) -> bool:
        """Deploy individual service to Google Cloud Run"""
        logger.info(f"🚀 Deploying {service_name}...")
        
        service_path = service_config['path']
        description = service_config['description']
        port = service_config['port']
        
        # Build the deployment command
        deploy_command = (
            f"gcloud run deploy {service_name} "
            f"--source={service_path} "
            f"--region={self.region} "
            f"--project={self.project_id} "
            f"--platform=managed "
            f"--allow-unauthenticated "
            f"--port={port} "
            f"--memory=1Gi "
            f"--cpu=1 "
            f"--timeout=300 "
            f"--max-instances=10 "
            f"--concurrency=80 "
            f'--set-env-vars="GOOGLE_CLOUD_PROJECT={self.project_id}" '
            f'--description="{description}"'
        )
        
        if self.run_command(deploy_command):
            logger.info(f"✅ {service_name} deployed successfully")
            return True
        else:
            logger.error(f"❌ {service_name} deployment failed")
            return False

    def configure_dns_mapping(self) -> bool:
        """Configure DNS domain mapping"""
        logger.info("🌐 Configuring DNS domain mapping...")
        
        # Map frontend service to domain
        domain_mapping_command = (
            f"gcloud run domain-mappings create "
            f"--service=infinityai-frontend "
            f"--domain={self.domain} "
            f"--region={self.region} "
            f"--project={self.project_id}"
        )
        
        return self.run_command(domain_mapping_command)

    def run_post_deployment_verification(self) -> bool:
        """Run post-deployment verification"""
        logger.info("🔍 Running post-deployment verification...")
        
        try:
            # Run OAuth verification
            oauth_result = self.run_command("python verify_oauth_integration.py")
            
            # Run comprehensive production verification
            production_result = self.run_command("python production_verification_suite.py")
            
            return oauth_result and production_result
        except Exception as e:
            logger.error(f"❌ Post-deployment verification failed: {e}")
            return False

    def deploy_all_services(self) -> Dict[str, bool]:
        """Deploy all services to Google Cloud Run"""
        logger.info("🚀 Starting deployment of all services...")
        
        deployment_results = {}
        
        for service_name, service_config in self.services.items():
            deployment_results[service_name] = self.deploy_service(service_name, service_config)
            
        return deployment_results

    def generate_deployment_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        
        successful_deployments = sum(1 for success in results.get('deployments', {}).values() if success)
        total_services = len(self.services)
        deployment_success_rate = (successful_deployments / total_services) * 100 if total_services > 0 else 0
        
        report = {
            'deployment_timestamp': datetime.now().isoformat(),
            'version': results.get('version', 'unknown'),
            'platform': 'InfinityAI.Pro Multi-Cloud AI Trading Platform',
            'cloud_provider': 'Google Cloud Run',
            'region': self.region,
            'domain': self.domain,
            'deployment_results': {
                'total_services': total_services,
                'successful_deployments': successful_deployments,
                'success_rate': deployment_success_rate,
                'service_results': results.get('deployments', {})
            },
            'integration_status': {
                'oauth_configured': results.get('oauth_setup', False),
                'secrets_managed': results.get('secrets_setup', False),
                'github_committed': results.get('github_commit', False),
                'dns_mapped': results.get('dns_mapping', False)
            },
            'verification_passed': results.get('verification_passed', False),
            'production_ready': (
                deployment_success_rate >= 90 and
                results.get('oauth_setup', False) and
                results.get('secrets_setup', False) and
                results.get('verification_passed', False)
            )
        }
        
        return report

    def run_complete_deployment(self) -> Dict[str, Any]:
        """Run complete production deployment"""
        
        print("🚀 InfinityAI.Pro - Complete Production Deployment")
        print("=" * 70)
        print(f"Starting deployment at {datetime.now().isoformat()}")
        print("=" * 70)
        
        deployment_results = {}
        
        # Step 1: Update version and commit to GitHub
        print("\n📤 STEP 1: GitHub Version Tracking")
        print("-" * 50)
        deployment_results['version'] = self.update_version_info()
        deployment_results['github_commit'] = self.commit_to_github()
        
        # Step 2: Setup Google Secret Manager
        print("\n🔐 STEP 2: Google Secret Manager Setup")
        print("-" * 50)
        deployment_results['secrets_setup'] = self.setup_secrets()
        
        # Step 3: Deploy all services
        print("\n🚀 STEP 3: Service Deployment to Google Cloud Run")
        print("-" * 50)
        deployment_results['deployments'] = self.deploy_all_services()
        
        # Step 4: Configure DNS mapping
        print("\n🌐 STEP 4: DNS Domain Mapping")
        print("-" * 50)
        deployment_results['dns_mapping'] = self.configure_dns_mapping()
        
        # Step 5: OAuth and security verification
        print("\n🔍 STEP 5: Post-Deployment Verification")
        print("-" * 50)
        deployment_results['verification_passed'] = self.run_post_deployment_verification()
        
        # Generate comprehensive report
        report = self.generate_deployment_report(deployment_results)
        
        # Display results
        print("\n" + "=" * 70)
        print("🎯 PRODUCTION DEPLOYMENT RESULTS")
        print("=" * 70)
        
        print(f"Platform: {report['platform']}")
        print(f"Version: {report['version']}")
        print(f"Success Rate: {report['deployment_results']['success_rate']:.1f}%")
        print(f"Services Deployed: {report['deployment_results']['successful_deployments']}/{report['deployment_results']['total_services']}")
        print(f"OAuth Configured: {'✅ YES' if report['integration_status']['oauth_configured'] else '❌ NO'}")
        print(f"Secrets Managed: {'✅ YES' if report['integration_status']['secrets_managed'] else '❌ NO'}")
        print(f"GitHub Committed: {'✅ YES' if report['integration_status']['github_committed'] else '❌ NO'}")
        print(f"DNS Mapped: {'✅ YES' if report['integration_status']['dns_mapped'] else '❌ NO'}")
        print(f"Production Ready: {'✅ YES' if report['production_ready'] else '❌ NO'}")
        
        # Save deployment report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"production_deployment_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Deployment report saved: {filename}")
        
        if report['production_ready']:
            print("\n🎉 DEPLOYMENT SUCCESSFUL! InfinityAI.Pro is production-ready!")
            print(f"🌐 Platform URL: https://{self.domain}")
            print(f"🚀 Demo Access: https://{self.domain}/demo")
        else:
            print("\n⚠️ Deployment completed with issues. Review the report for details.")
        
        return report

def main():
    """Main deployment function"""
    
    deployer = ProductionDeployer()
    
    try:
        deployment_report = deployer.run_complete_deployment()
        return deployment_report
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return None

if __name__ == "__main__":
    main()