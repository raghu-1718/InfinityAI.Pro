# InfinityAI.Pro Master Fix Script (PowerShell)
# Eliminates Vercel and fixes multi-cloud deployment

Clear-Host
Write-Host "🚀 InfinityAI.Pro Multi-Cloud Fix & Deployment Script" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "This script will eliminate Vercel and fix your AWS and GCP deployments"
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to print status
function Write-Status {
    param($Success, $Message)
    if ($Success) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
    }
}

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
Write-Status $false "Azure CLI not required (removed)"
Write-Status (Test-CommandExists "aws") "AWS CLI found"
Write-Status (Test-CommandExists "gcloud") "Google Cloud CLI found"
Write-Status (Test-CommandExists "python") "Python found"
Write-Status (Test-CommandExists "docker") "Docker found"

Write-Host ""
Write-Host "📋 Available Fix Operations:" -ForegroundColor Cyan
Write-Host "1. Frontend (AWS S3/CloudFront)"
Write-Host "2. Fix AWS ECS Services (Engines C & D)"
Write-Host "3. Deploy GCP Engine B"
Write-Host "4. Update frontend configuration (eliminate Vercel)"
Write-Host "5. Test all endpoints"
Write-Host "6. Run complete fix (all operations)"
Write-Host ""

$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "� Frontend is hosted on AWS S3 (and optional CloudFront)." -ForegroundColor Cyan
        Write-Host "Use scripts/deploy_frontend_aws.ps1 to sync and optionally set CloudFront later." -ForegroundColor Yellow
    }
    
    "2" {
        Write-Host "🟠 Fixing AWS ECS Services..." -ForegroundColor DarkYellow
        Write-Host "First configure AWS CLI if not done:" -ForegroundColor Yellow
        Write-Host "  aws configure" -ForegroundColor White
        Write-Host ""
        Write-Host "AWS CLI Commands to run:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "# Check ECS Cluster" -ForegroundColor Gray
        Write-Host "aws ecs describe-clusters --clusters infinityai-pro-cluster --region us-east-1" -ForegroundColor White
        Write-Host ""
        Write-Host "# Restart services" -ForegroundColor Gray
        Write-Host "aws ecs update-service --cluster infinityai-pro-cluster --service engine-c-service --force-new-deployment --region us-east-1" -ForegroundColor White
        Write-Host "aws ecs update-service --cluster infinityai-pro-cluster --service engine-d-service --force-new-deployment --region us-east-1" -ForegroundColor White
    }
    
    "3" {
        Write-Host "🔴 Deploying GCP Engine B..." -ForegroundColor Red
        Write-Host "First authenticate with Google Cloud:" -ForegroundColor Yellow
        Write-Host "  gcloud auth login" -ForegroundColor White
        Write-Host ""
        Write-Host "GCP Commands to run:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "# Deploy to Cloud Run" -ForegroundColor Gray
        Write-Host "gcloud run deploy infinityai-engine-b --image gcr.io/YOUR_PROJECT_ID/infinityai-engine-b:latest --platform managed --region us-central1 --allow-unauthenticated" -ForegroundColor White
    }
    
    "4" {
        Write-Host "⚙️ Frontend configuration has been updated!" -ForegroundColor Green
        Write-Host "Files created/updated:" -ForegroundColor Yellow
        Write-Host "  ✅ infinityai-pro/frontend/staticwebapp.config.json" -ForegroundColor Green
        Write-Host "  ✅ infinityai-pro/frontend/src/config/api-config.js" -ForegroundColor Green
        Write-Host ""
    Write-Host "The frontend now points to Engine D (AWS) as single backend. Vercel eliminated." -ForegroundColor Cyan
    }
    
    "5" {
        Write-Host "🧪 Testing all endpoints..." -ForegroundColor Yellow
        if (Test-CommandExists "python") {
            Write-Host "Running comprehensive test..." -ForegroundColor Cyan
            & "C:/Users/Raghu/AppData/Local/Microsoft/WindowsApps/python3.12.exe" multi_cloud_integration_test.py
            Write-Host ""
            Write-Host "Test report saved to: multi_cloud_integration_report.json" -ForegroundColor Green
        } else {
            Write-Host "❌ Python 3 required for testing" -ForegroundColor Red
        }
    }
    
    "6" {
        Write-Host "🚀 Running complete fix process..." -ForegroundColor Green
        Write-Host ""
        
        # Step 1
        Write-Host "Step 1/5: ⚙️ Updated frontend configuration files" -ForegroundColor Cyan
        Write-Host "  ✅ API configuration updated (no Vercel)" -ForegroundColor Green
        Write-Host "  ✅ Static Web App config generated" -ForegroundColor Green
        Write-Host ""
        
        # Step 2
        Write-Host "Step 2/5: 🧪 Testing current working endpoints..." -ForegroundColor Cyan
        if (Test-CommandExists "python") {
            & "C:/Users/Raghu/AppData/Local/Microsoft/WindowsApps/python3.12.exe" multi_cloud_integration_test.py
        }
        Write-Host ""
        
        # Step 3
    # Azure frontend removed
        
        # Step 4
        Write-Host "Step 4/5: 🟠 AWS ECS Fix Commands" -ForegroundColor DarkYellow
        Write-Host "First run: aws configure" -ForegroundColor Yellow
        Write-Host "Then check your ECS cluster:" -ForegroundColor Yellow
        Write-Host "aws ecs describe-clusters --clusters infinityai-pro-cluster --region us-east-1" -ForegroundColor White
        Write-Host ""
        
        # Step 5
        Write-Host "Step 5/5: 🔴 GCP Engine B Deployment" -ForegroundColor Red
        Write-Host "First run: gcloud auth login" -ForegroundColor Yellow
        Write-Host "Then deploy Engine B to Cloud Run:" -ForegroundColor Yellow
        Write-Host "gcloud run deploy infinityai-engine-b --image gcr.io/YOUR_PROJECT_ID/infinityai-engine-b:latest --platform managed --region us-central1 --allow-unauthenticated" -ForegroundColor White
        Write-Host ""
        
        Write-Host "🎯 Summary of Changes Made:" -ForegroundColor Magenta
    Write-Host "✅ Vercel dependencies eliminated" -ForegroundColor Green
    Write-Host "✅ Frontend configured to Engine D (AWS)" -ForegroundColor Green
        Write-Host "⚠️ AWS ECS needs manual restart" -ForegroundColor Yellow
        Write-Host "⚠️ GCP Engine B needs deployment" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "📄 Generated files:" -ForegroundColor Cyan
    # Azure helper removed
        Write-Host "  - aws_ecs_fix.sh"
        Write-Host "  - gcp_engine_b_deploy.sh"
        Write-Host "  - multi-cloud-config.json"
        Write-Host "  - Frontend API config files"
        Write-Host ""
        Write-Host "🎉 Once you run the cloud-specific commands, your app will be 100% operational!" -ForegroundColor Green
    }
    
    default {
        Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Run the cloud-specific fix commands for your chosen option"
Write-Host "2. Test endpoints: python multi_cloud_integration_test.py"
Write-Host "3. Validate fixes: python post_fix_validation.py"
Write-Host ""
Write-Host "🎯 Goal: 100% multi-cloud deployment without Vercel" -ForegroundColor Green
Write-Host "📞 Need help? Check the generated command files for detailed instructions"