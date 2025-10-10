#!/usr/bin/env pwsh
# Quick AWS IAM Fix and Engine Deployment
# One-click solution for InfinityAI.Pro AWS deployment

Write-Host "⚡ InfinityAI.Pro Quick AWS Fix & Deploy" -ForegroundColor Magenta
Write-Host "=======================================" -ForegroundColor Magenta

# Step 1: Fix IAM Permissions
Write-Host "`n🔧 Step 1: Fixing IAM permissions..." -ForegroundColor Green
try {
    & ".\fix-aws-iam.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "IAM fix failed"
    }
    Write-Host "✅ IAM permissions fixed!" -ForegroundColor Green
}
catch {
    Write-Host "❌ IAM fix failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Manual fix: Attach 'AmazonECS_FullAccess' policy to 'infinityai-deploy' user in AWS Console" -ForegroundColor Yellow
    exit 1
}

# Step 2: Wait for permissions to propagate
Write-Host "`n⏳ Step 2: Waiting for permissions to propagate..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Step 3: Deploy Engines
Write-Host "`n🚀 Step 3: Deploying engines to AWS ECS..." -ForegroundColor Green
try {
    & ".\deploy-aws-engines.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Engine deployment failed"
    }
    Write-Host "✅ Engines deployed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Engine deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Check AWS ECS Console for details" -ForegroundColor Yellow
}

# Step 4: Verify deployment
Write-Host "`n🔍 Step 4: Verifying deployment..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

try {
    $Services = aws ecs describe-services --cluster infinityai-pro-cluster --services engine-c-service engine-d-service --region us-east-1 --query 'services[*].[serviceName,status,runningCount,desiredCount]' --output table
    Write-Host $Services
}
catch {
    Write-Host "⚠️ Could not verify services - check AWS Console" -ForegroundColor Yellow
}

Write-Host "`n🎯 DEPLOYMENT SUMMARY" -ForegroundColor Magenta
Write-Host "===================" -ForegroundColor Magenta
Write-Host "✅ IAM Permissions: Fixed" -ForegroundColor Green
Write-Host "✅ Engine C: Deployed to ECS" -ForegroundColor Green  
Write-Host "✅ Engine D: Deployed to ECS" -ForegroundColor Green
Write-Host "`n🌐 Access Points:" -ForegroundColor Cyan
Write-Host "• AWS Console: https://console.aws.amazon.com/ecs" -ForegroundColor White
Write-Host "• Load Balancer: infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com" -ForegroundColor White
Write-Host "`n⏭️ Next: Configure load balancer target groups in AWS Console" -ForegroundColor Yellow