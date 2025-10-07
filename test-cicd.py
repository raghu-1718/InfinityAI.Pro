#!/usr/bin/env python3
"""
InfinityAI.Pro - AWS and Google Cloud CI/CD Automated Test Suite
This script performs automated testing of CI/CD configurations
"""

import yaml
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class CICDTester:
    def __init__(self):
        self.base_path = Path('/home/runner/work/InfinityAI.Pro/InfinityAI.Pro')
        self.workflow_path = self.base_path / 'infinityai-pro' / '.github' / 'workflows'
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def print_status(self, message: str):
        print(f"{Colors.BLUE}[TEST]{Colors.NC} {message}")
        
    def print_pass(self, message: str):
        print(f"{Colors.GREEN}[✅ PASS]{Colors.NC} {message}")
        self.passed += 1
        
    def print_fail(self, message: str):
        print(f"{Colors.RED}[❌ FAIL]{Colors.NC} {message}")
        self.failed += 1
        
    def print_warn(self, message: str):
        print(f"{Colors.YELLOW}[⚠️  WARN]{Colors.NC} {message}")
        self.warnings += 1
        
    def test_workflow_structure(self, workflow_file: Path, workflow_name: str) -> bool:
        """Test workflow file structure and syntax"""
        self.print_status(f"Testing {workflow_name} structure")
        
        try:
            with open(workflow_file, 'r') as f:
                workflow = yaml.safe_load(f)
                
            # Check required top-level keys
            # Note: 'on' in YAML can be interpreted as boolean True
            required_keys = ['name', 'jobs']
            for key in required_keys:
                if key not in workflow:
                    self.print_fail(f"{workflow_name}: Missing required key '{key}'")
                    return False
            
            # Check for 'on' or True (YAML boolean interpretation)
            if 'on' not in workflow and True not in workflow:
                self.print_fail(f"{workflow_name}: Missing workflow triggers ('on' key)")
                return False
                    
            self.print_pass(f"{workflow_name} has valid structure")
            return True
            
        except yaml.YAMLError as e:
            self.print_fail(f"{workflow_name}: Invalid YAML - {str(e)}")
            return False
        except Exception as e:
            self.print_fail(f"{workflow_name}: Error - {str(e)}")
            return False
            
    def test_aws_job_configuration(self, workflow: Dict) -> bool:
        """Test AWS deployment job configuration"""
        self.print_status("Testing AWS deployment job")
        
        if 'jobs' not in workflow:
            self.print_fail("No jobs found in workflow")
            return False
            
        if 'deploy-aws' not in workflow['jobs']:
            self.print_fail("AWS deployment job not found")
            return False
            
        aws_job = workflow['jobs']['deploy-aws']
        
        # Check required AWS steps
        required_steps = [
            'Configure AWS Credentials',
            'Login to Amazon ECR',
            'Build and Push Engine C',
            'Build and Push Engine D'
        ]
        
        if 'steps' not in aws_job:
            self.print_fail("AWS job has no steps")
            return False
            
        step_names = [step.get('name', '') for step in aws_job['steps']]
        
        for required in required_steps:
            found = any(required.lower() in name.lower() for name in step_names)
            if not found:
                self.print_fail(f"AWS job missing step: {required}")
                return False
                
        self.print_pass("AWS deployment job properly configured")
        return True
        
    def test_gcp_job_configuration(self, workflow: Dict) -> bool:
        """Test Google Cloud deployment job configuration"""
        self.print_status("Testing GCP deployment job")
        
        if 'jobs' not in workflow:
            self.print_fail("No jobs found in workflow")
            return False
            
        if 'deploy-gcp' not in workflow['jobs']:
            self.print_fail("GCP deployment job not found")
            return False
            
        gcp_job = workflow['jobs']['deploy-gcp']
        
        # Check required GCP steps
        required_steps = [
            'Authenticate to Google Cloud',
            'Set up Cloud SDK',
            'Build and Push Engine B',
            'Deploy to Cloud Run'
        ]
        
        if 'steps' not in gcp_job:
            self.print_fail("GCP job has no steps")
            return False
            
        step_names = [step.get('name', '') for step in gcp_job['steps']]
        
        for required in required_steps:
            found = any(required.lower() in name.lower() for name in step_names)
            if not found:
                self.print_fail(f"GCP job missing step: {required}")
                return False
                
        self.print_pass("GCP deployment job properly configured")
        return True
        
    def test_environment_variables(self, workflow: Dict) -> bool:
        """Test environment variables configuration"""
        self.print_status("Testing environment variables")
        
        if 'env' not in workflow:
            self.print_fail("No environment variables defined")
            return False
            
        env_vars = workflow['env']
        
        required_vars = {
            'AWS_REGION': 'us-east-1',
            'GCP_PROJECT_ID': 'after-yesterday-473512-k3'
        }
        
        all_valid = True
        for var, expected_value in required_vars.items():
            if var not in env_vars:
                self.print_fail(f"Missing environment variable: {var}")
                all_valid = False
            elif env_vars[var] != expected_value:
                self.print_warn(f"{var} = {env_vars[var]} (expected: {expected_value})")
                
        if all_valid:
            self.print_pass("All required environment variables configured")
            
        return all_valid
        
    def test_secrets_usage(self, workflow: Dict) -> bool:
        """Test that required secrets are referenced"""
        self.print_status("Testing secrets usage")
        
        workflow_str = yaml.dump(workflow)
        
        required_secrets = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'GCP_SERVICE_ACCOUNT_KEY',
            'DHAN_CLIENT_ID',
            'DHAN_ACCESS_TOKEN'
        ]
        
        all_found = True
        for secret in required_secrets:
            if f"secrets.{secret}" not in workflow_str:
                self.print_warn(f"Secret not referenced: {secret}")
                all_found = False
            else:
                self.print_pass(f"Secret referenced: {secret}")
                
        return all_found
        
    def test_job_dependencies(self, workflow: Dict) -> bool:
        """Test job dependencies and order"""
        self.print_status("Testing job dependencies")
        
        jobs = workflow.get('jobs', {})
        
        # Check that integration tests depend on all deployments
        if 'integration-tests' in jobs:
            integration_job = jobs['integration-tests']
            needs = integration_job.get('needs', [])
            
            required_deps = ['deploy-azure', 'deploy-gcp', 'deploy-aws']
            
            if isinstance(needs, list):
                for dep in required_deps:
                    if dep not in needs:
                        self.print_fail(f"Integration tests missing dependency: {dep}")
                        return False
            else:
                self.print_fail("Integration tests dependencies not properly configured")
                return False
                
            self.print_pass("Job dependencies properly configured")
            return True
        else:
            self.print_warn("No integration tests job found")
            return True
            
    def test_docker_image_tags(self, workflow: Dict) -> bool:
        """Test that Docker images are properly tagged"""
        self.print_status("Testing Docker image tagging")
        
        workflow_str = yaml.dump(workflow)
        
        # Check for proper image tagging patterns
        patterns = [
            'github.sha',
            ':latest',
            'infinityai-engine-c',
            'infinityai-engine-d',
            'infinityai-engine-b'
        ]
        
        all_found = True
        for pattern in patterns:
            if pattern not in workflow_str:
                self.print_fail(f"Image tag pattern not found: {pattern}")
                all_found = False
                
        if all_found:
            self.print_pass("Docker image tagging properly configured")
            
        return all_found
        
    def test_conditional_execution(self, workflow: Dict) -> bool:
        """Test that jobs have proper conditional execution"""
        self.print_status("Testing conditional execution")
        
        jobs = workflow.get('jobs', {})
        
        # Deployment jobs should only run on main branch
        deployment_jobs = ['deploy-aws', 'deploy-gcp', 'deploy-azure']
        
        for job_name in deployment_jobs:
            if job_name in jobs:
                job = jobs[job_name]
                if 'if' not in job:
                    self.print_warn(f"{job_name} has no conditional execution")
                elif "github.ref == 'refs/heads/main'" in str(job.get('if', '')):
                    self.print_pass(f"{job_name} only runs on main branch")
                else:
                    self.print_warn(f"{job_name} conditional may not be restrictive enough")
                    
        return True
        
    def run_all_tests(self):
        """Run all CI/CD tests"""
        print("=" * 70)
        print("🧪 InfinityAI.Pro - AWS & Google Cloud CI/CD Automated Tests")
        print("=" * 70)
        print()
        
        # Test multi-cloud workflow
        print("📋 Testing Multi-Cloud CI/CD Workflow")
        print("-" * 70)
        
        workflow_file = self.workflow_path / 'multi-cloud-cicd.yml'
        
        if not workflow_file.exists():
            self.print_fail(f"Workflow file not found: {workflow_file}")
            return False
            
        # Load workflow
        try:
            with open(workflow_file, 'r') as f:
                workflow = yaml.safe_load(f)
        except Exception as e:
            self.print_fail(f"Failed to load workflow: {str(e)}")
            return False
            
        # Run tests
        self.test_workflow_structure(workflow_file, 'multi-cloud-cicd.yml')
        self.test_aws_job_configuration(workflow)
        self.test_gcp_job_configuration(workflow)
        self.test_environment_variables(workflow)
        self.test_secrets_usage(workflow)
        self.test_job_dependencies(workflow)
        self.test_docker_image_tags(workflow)
        self.test_conditional_execution(workflow)
        
        print()
        print("-" * 70)
        
        # Test deploy-live-trading workflow
        print()
        print("📋 Testing Deploy Live Trading Workflow")
        print("-" * 70)
        
        live_trading_file = self.workflow_path / 'deploy-live-trading.yml'
        
        if live_trading_file.exists():
            self.test_workflow_structure(live_trading_file, 'deploy-live-trading.yml')
            
            with open(live_trading_file, 'r') as f:
                live_workflow = yaml.safe_load(f)
                
            # Check for AWS deployment steps
            if 'jobs' in live_workflow and 'deploy-aws-engines' in live_workflow['jobs']:
                self.print_pass("Live trading workflow includes AWS deployment")
            else:
                self.print_warn("Live trading workflow may be missing AWS deployment")
        else:
            self.print_warn("Live trading workflow not found")
            
        print()
        print("-" * 70)
        
        # Print summary
        print()
        print("=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print()
        
        if self.failed == 0:
            print(f"{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.NC}")
            print()
            print("AWS and Google Cloud CI/CD configurations are valid and ready for use.")
            return True
        else:
            print(f"{Colors.RED}⚠️  SOME TESTS FAILED!{Colors.NC}")
            print()
            print("Please review the errors above and fix the configuration.")
            return False

def main():
    """Main entry point"""
    tester = CICDTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
