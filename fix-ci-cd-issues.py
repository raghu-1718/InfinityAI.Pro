#!/usr/bin/env python3
"""
InfinityAI.Pro - CI/CD Issues Fix Script
Addresses all GitHub Actions build failures and deployment issues
"""

import subprocess
import json
import os
import base64
from datetime import datetime

class CICDFixer:
    def __init__(self):
        self.project_id = "infinity-ai-5ec7c"
        self.repo_name = "raghu-1718/InfinityAI.Pro"
        self.issues_found = []
        self.fixes_applied = []
        
        print("🔧 InfinityAI.Pro CI/CD Issues Fix Script")
        print("=" * 60)
    
    def log_issue(self, description, severity="MEDIUM"):
        """Log identified issue"""
        issue = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "severity": severity
        }
        self.issues_found.append(issue)
        
        emoji = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
        print(f"{emoji} [{severity}] {description}")
    
    def log_fix(self, description, command=""):
        """Log applied fix"""
        fix = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "command": command
        }
        self.fixes_applied.append(fix)
        print(f"🔧 FIX: {description}")
        if command:
            print(f"   Command: {command}")
    
    def run_command(self, cmd, capture_output=True):
        """Run shell command"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, timeout=60)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def fix_typescript_error(self):
        """Fix TypeScript error in appStore.ts"""
        print("\n📋 Fixing TypeScript Error in appStore.ts")
        
        try:
            # Read the file
            with open("frontend/src/stores/appStore.ts", "r") as f:
                content = f.read()
            
            # Check if the error exists
            if "subscribeWithSelector((set, get) =>" in content:
                # Fix the error by removing unused 'get' parameter
                fixed_content = content.replace(
                    "subscribeWithSelector((set, get) =>",
                    "subscribeWithSelector((set) =>"
                )
                
                # Write the fixed content
                with open("frontend/src/stores/appStore.ts", "w") as f:
                    f.write(fixed_content)
                
                self.log_fix("Fixed TypeScript error: Removed unused 'get' parameter from subscribeWithSelector")
            else:
                print("✅ TypeScript error not found - already fixed")
                
        except Exception as e:
            self.log_issue(f"Failed to fix TypeScript error: {e}", "HIGH")
    
    def create_service_account_key(self):
        """Create and configure GCP service account key"""
        print("\n📋 Creating GCP Service Account Key")
        
        service_account_email = f"github-actions@{self.project_id}.iam.gserviceaccount.com"
        
        # Create service account if it doesn't exist
        success, stdout, stderr = self.run_command(
            f'gcloud iam service-accounts create github-actions --display-name="GitHub Actions" --project={self.project_id}'
        )
        
        if not success and "already exists" not in stderr:
            self.log_issue(f"Failed to create service account: {stderr}", "HIGH")
            return
        
        # Grant necessary roles
        roles = [
            "roles/run.admin",
            "roles/iam.serviceAccountUser",
            "roles/storage.admin",
            "roles/secretmanager.secretAccessor"
        ]
        
        for role in roles:
            success, stdout, stderr = self.run_command(
                f'gcloud projects add-iam-policy-binding {self.project_id} --member="serviceAccount:{service_account_email}" --role="{role}" --condition=None'
            )
            
            if success:
                print(f"✅ Granted {role}")
            else:
                self.log_issue(f"Failed to grant {role}: {stderr}", "MEDIUM")
        
        # Create service account key
        key_file = f"github-actions-key-{datetime.now().strftime('%Y%m%d')}.json"
        success, stdout, stderr = self.run_command(
            f'gcloud iam service-accounts keys create {key_file} --iam-account={service_account_email} --project={self.project_id}'
        )
        
        if success:
            # Read and encode the key
            try:
                with open(key_file, 'r') as f:
                    key_content = f.read()
                
                # Clean up the file
                os.remove(key_file)
                
                self.log_fix(f"Service account key created successfully", f"Key saved for GitHub secret")
                
                print("\n🔑 IMPORTANT: Add this to GitHub repository secrets as 'GCP_SERVICE_ACCOUNT_KEY':")
                print("─" * 60)
                print(key_content)
                print("─" * 60)
                
                return key_content
                
            except Exception as e:
                self.log_issue(f"Failed to read service account key: {e}", "HIGH")
        else:
            self.log_issue(f"Failed to create service account key: {stderr}", "HIGH")
    
    def fix_github_workflows(self):
        """Fix GitHub workflow configurations"""
        print("\n📋 Fixing GitHub Workflow Configurations")
        
        # Update GitHub workflow files with correct authentication
        workflows = [
            ".github/workflows/engine-a.yaml",
            ".github/workflows/engine-b.yaml", 
            ".github/workflows/engine-c.yaml",
            ".github/workflows/engine-d.yaml"
        ]
        
        for workflow_file in workflows:
            try:
                with open(workflow_file, 'r') as f:
                    content = f.read()
                
                # Fix the authentication step
                if 'credentials_json: "${{ secrets.GCP_SA_KEY }}"' in content:
                    # Replace with correct secret name
                    fixed_content = content.replace(
                        'credentials_json: "${{ secrets.GCP_SA_KEY }}"',
                        'credentials_json: "${{ secrets.GCP_SERVICE_ACCOUNT_KEY }}"'
                    )
                    
                    # Also fix project ID reference
                    fixed_content = fixed_content.replace(
                        'project_id: ${{ secrets.VITE_PROJECT_ID }}',
                        f'project_id: {self.project_id}'
                    )
                    
                    with open(workflow_file, 'w') as f:
                        f.write(fixed_content)
                    
                    self.log_fix(f"Fixed workflow file: {workflow_file}")
                
            except Exception as e:
                self.log_issue(f"Failed to fix workflow {workflow_file}: {e}", "MEDIUM")
    
    def create_github_secrets_script(self):
        """Create script to set up GitHub secrets"""
        print("\n📋 Creating GitHub Secrets Setup Script")
        
        script_content = f'''#!/bin/bash

# InfinityAI.Pro - GitHub Secrets Setup Script
# Run this script to configure all required GitHub repository secrets

echo "🔐 Setting up GitHub Repository Secrets for InfinityAI.Pro"
echo "Repository: {self.repo_name}"
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Please install it first:"
    echo "   https://cli.github.com/"
    exit 1
fi

# Authenticate with GitHub if needed
echo "🔍 Checking GitHub authentication..."
if ! gh auth status &> /dev/null; then
    echo "🔑 Please authenticate with GitHub:"
    gh auth login
fi

# Set repository context
gh repo set-default {self.repo_name}

echo ""
echo "📋 Setting up secrets..."

# GCP Service Account Key (this needs to be provided)
echo "⚠️  Please create the GCP_SERVICE_ACCOUNT_KEY secret manually:"
echo "   1. Go to: https://github.com/{self.repo_name}/settings/secrets/actions"
echo "   2. Click 'New repository secret'"
echo "   3. Name: GCP_SERVICE_ACCOUNT_KEY"
echo "   4. Value: [The JSON service account key created above]"
echo ""

# Get Gemini API keys from GCP Secret Manager
echo "🔍 Retrieving Gemini API keys from GCP Secret Manager..."

PRIMARY_KEY=$(gcloud secrets versions access latest --secret="gemini-api-key-primary" --project={self.project_id} 2>/dev/null)
SECONDARY_KEY=$(gcloud secrets versions access latest --secret="gemini-api-key-secondary" --project={self.project_id} 2>/dev/null)

if [ ! -z "$PRIMARY_KEY" ]; then
    echo "🔑 Setting GEMINI_API_KEY_PRIMARY..."
    echo "$PRIMARY_KEY" | gh secret set GEMINI_API_KEY_PRIMARY
    echo "✅ GEMINI_API_KEY_PRIMARY set"
else
    echo "❌ Failed to retrieve primary Gemini API key from Secret Manager"
fi

if [ ! -z "$SECONDARY_KEY" ]; then
    echo "🔑 Setting GEMINI_API_KEY_SECONDARY..."
    echo "$SECONDARY_KEY" | gh secret set GEMINI_API_KEY_SECONDARY
    echo "✅ GEMINI_API_KEY_SECONDARY set"
else
    echo "❌ Failed to retrieve secondary Gemini API key from Secret Manager"
fi

# Firebase token
echo "🔥 Setting up Firebase deploy token..."
echo "   Run: firebase login:ci"
echo "   Then set the token as FIREBASE_DEPLOY_TOKEN in GitHub secrets"

echo ""
echo "✅ GitHub secrets setup script completed!"
echo "📋 Manual steps required:"
echo "   1. Add GCP_SERVICE_ACCOUNT_KEY secret"
echo "   2. Run 'firebase login:ci' and add the token as FIREBASE_DEPLOY_TOKEN"
'''
        
        with open("scripts/setup-github-secrets.sh", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # Make executable
        os.chmod("scripts/setup-github-secrets.sh", 0o755)
        
        self.log_fix("Created GitHub secrets setup script: scripts/setup-github-secrets.sh")
    
    def verify_current_deployments(self):
        """Verify current deployment status"""
        print("\n📋 Verifying Current Deployment Status")
        
        # Check Cloud Run services
        success, stdout, stderr = self.run_command(
            f'gcloud run services list --region=us-central1 --project={self.project_id} --format="table(metadata.name,status.url,status.conditions[0].status)"'
        )
        
        if success:
            print("🌐 Current Cloud Run Services:")
            print(stdout)
        else:
            self.log_issue(f"Failed to list Cloud Run services: {stderr}", "MEDIUM")
        
        # Check Firebase Functions
        success, stdout, stderr = self.run_command(f'firebase functions:list --project={self.project_id}')
        
        if success:
            print("\n🔥 Current Firebase Functions:")
            print(stdout)
        else:
            print(f"⚠️ Firebase Functions list failed: {stderr}")
    
    def create_ci_cd_fix_summary(self):
        """Create comprehensive CI/CD fix summary"""
        print("\n📋 Creating CI/CD Fix Summary")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "project_id": self.project_id,
            "repository": self.repo_name,
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "next_steps": [
                "1. Run scripts/setup-github-secrets.sh to configure GitHub repository secrets",
                "2. Add GCP_SERVICE_ACCOUNT_KEY manually to GitHub secrets",
                "3. Run 'firebase login:ci' and add token as FIREBASE_DEPLOY_TOKEN",
                "4. Commit and push changes to trigger CI/CD pipeline",
                "5. Monitor GitHub Actions for successful deployment"
            ],
            "github_secrets_required": [
                "GCP_SERVICE_ACCOUNT_KEY (Service account JSON)",
                "GEMINI_API_KEY_PRIMARY (From GCP Secret Manager)",
                "GEMINI_API_KEY_SECONDARY (From GCP Secret Manager)", 
                "FIREBASE_DEPLOY_TOKEN (From firebase login:ci)"
            ]
        }
        
        filename = f"ci-cd-fix-summary-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log_fix(f"CI/CD fix summary saved to: {filename}")
        
        return filename, summary
    
    def run_comprehensive_fix(self):
        """Run all CI/CD fixes"""
        print("\n🚀 Running Comprehensive CI/CD Fix")
        
        try:
            # Fix TypeScript error
            self.fix_typescript_error()
            
            # Create service account key
            service_account_key = self.create_service_account_key()
            
            # Fix GitHub workflows
            self.fix_github_workflows()
            
            # Create GitHub secrets setup script
            self.create_github_secrets_script()
            
            # Verify current deployments
            self.verify_current_deployments()
            
            # Create summary report
            report_file, summary = self.create_ci_cd_fix_summary()
            
            print(f"\n{'='*80}")
            print(f"✅ CI/CD FIX COMPLETED!")
            print(f"{'='*80}")
            print(f"📊 Issues Found: {len(self.issues_found)}")
            print(f"🔧 Fixes Applied: {len(self.fixes_applied)}")
            print(f"📄 Summary Report: {report_file}")
            
            print(f"\n🚀 NEXT STEPS:")
            for i, step in enumerate(summary["next_steps"], 1):
                print(f"   {step}")
            
            print(f"\n🔑 REQUIRED GITHUB SECRETS:")
            for secret in summary["github_secrets_required"]:
                print(f"   • {secret}")
            
            return report_file, summary
            
        except Exception as e:
            self.log_issue(f"CI/CD fix failed: {e}", "HIGH")
            raise

if __name__ == "__main__":
    fixer = CICDFixer()
    fixer.run_comprehensive_fix()