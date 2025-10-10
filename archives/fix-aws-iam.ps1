#!/usr/bin/env pwsh
# Automated AWS IAM Fix for InfinityAI.Pro
# Fixes permissions for ECS deployment

param(
    [string]$UserName = "infinityai-deploy",
    [string]$Region = "us-east-1"
)

Write-Host "🔧 Fixing AWS IAM permissions for InfinityAI.Pro deployment..." -ForegroundColor Green

# Create IAM policy JSON
$PolicyDocument = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ecs:*",
                "ecr:*", 
                "elasticloadbalancing:*",
                "iam:PassRole",
                "logs:*",
                "application-autoscaling:*"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 10

# Save policy to temp file
$PolicyFile = "$env:TEMP\infinityai-iam-policy.json"
$PolicyDocument | Out-File -FilePath $PolicyFile -Encoding UTF8

Write-Host "📄 Created IAM policy file: $PolicyFile" -ForegroundColor Yellow

try {
    # Create or update IAM policy
    Write-Host "🔐 Creating/updating IAM policy..." -ForegroundColor Cyan
    
    $PolicyArn = "arn:aws:iam::152687308610:policy/InfinityAI-ECS-FullAccess"
    
    # Try to create new policy
    try {
        aws iam create-policy --policy-name "InfinityAI-ECS-FullAccess" --policy-document "file://$PolicyFile" --description "Full ECS access for InfinityAI deployment" --region $Region
        Write-Host "✅ Created new IAM policy: $PolicyArn" -ForegroundColor Green
    }
    catch {
        # Policy exists, update it
        Write-Host "⚠️ Policy exists, updating..." -ForegroundColor Yellow
        $VersionList = aws iam list-policy-versions --policy-arn $PolicyArn --query 'Versions[?IsDefaultVersion==`false`].VersionId' --output text
        if ($VersionList) {
            aws iam delete-policy-version --policy-arn $PolicyArn --version-id $VersionList.Split()[0]
        }
        aws iam create-policy-version --policy-arn $PolicyArn --policy-document "file://$PolicyFile" --set-as-default
        Write-Host "✅ Updated IAM policy: $PolicyArn" -ForegroundColor Green
    }

    # Attach policy to user
    Write-Host "👤 Attaching policy to user: $UserName" -ForegroundColor Cyan
    aws iam attach-user-policy --user-name $UserName --policy-arn $PolicyArn --region $Region
    Write-Host "✅ Policy attached successfully" -ForegroundColor Green

    # Verify permissions
    Write-Host "🔍 Verifying permissions..." -ForegroundColor Cyan
    $UserPolicies = aws iam list-attached-user-policies --user-name $UserName --query 'AttachedPolicies[?PolicyName==`InfinityAI-ECS-FullAccess`]' --output text
    
    if ($UserPolicies) {
        Write-Host "✅ IAM permissions verified successfully!" -ForegroundColor Green
        
        # Test AWS CLI access
        Write-Host "🧪 Testing AWS CLI access..." -ForegroundColor Cyan
        $ClusterTest = aws ecs describe-clusters --clusters infinityai-pro-cluster --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ AWS CLI access working!" -ForegroundColor Green
            Write-Host "🚀 Ready to deploy engines to AWS ECS" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️ AWS CLI test failed. You may need to wait a few minutes for permissions to propagate." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "❌ Policy attachment verification failed" -ForegroundColor Red
    }

}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    # Cleanup temp file
    if (Test-Path $PolicyFile) {
        Remove-Item $PolicyFile -Force
    }
}

Write-Host "`n🎯 Next Steps:" -ForegroundColor Magenta
Write-Host "1. Wait 2-3 minutes for permissions to propagate" -ForegroundColor White
Write-Host "2. Run: .\deploy-aws-engines.ps1" -ForegroundColor White
Write-Host "3. Your engines will be deployed to AWS ECS" -ForegroundColor White