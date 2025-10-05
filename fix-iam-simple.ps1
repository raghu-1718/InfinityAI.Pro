# Simple AWS IAM Fix for InfinityAI.Pro
Write-Host "Fixing AWS IAM permissions..." -ForegroundColor Green

# Create IAM policy
$policy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecs:*",
                "ecr:*",
                "elasticloadbalancing:*",
                "iam:PassRole",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
"@

# Save policy to file
$policy | Out-File -FilePath "iam-policy.json" -Encoding UTF8

# Create and attach policy
try {
    Write-Host "Creating IAM policy..." -ForegroundColor Yellow
    aws iam create-policy --policy-name "InfinityAI-ECS-Policy" --policy-document "file://iam-policy.json" --description "ECS access for InfinityAI"
    
    Write-Host "Attaching policy to user..." -ForegroundColor Yellow
    aws iam attach-user-policy --user-name "infinityai-deploy" --policy-arn "arn:aws:iam::152687308610:policy/InfinityAI-ECS-Policy"
    
    Write-Host "IAM fix completed!" -ForegroundColor Green
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Cleanup
Remove-Item "iam-policy.json" -ErrorAction SilentlyContinue