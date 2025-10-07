param(
  [string]$UserName = "infinityai-deploy",
  [string]$PolicyName = "InfinityAI-ECS-Deploy-Policy",
  [string]$Region = "us-east-1"
)

$account = (aws sts get-caller-identity --query Account --output text)
$policyDoc = Get-Content -Raw -Path "$PSScriptRoot\ecs-deploy-policy.json"

# Create or update customer managed policy
try {
  $existing = aws iam get-policy --policy-arn "arn:aws:iam::$account:policy/$PolicyName" 2>$null
  if ($LASTEXITCODE -eq 0) {
    Write-Host "Updating existing policy $PolicyName" -ForegroundColor Yellow
    $versionArn = (aws iam create-policy-version --policy-arn "arn:aws:iam::$account:policy/$PolicyName" --policy-document "$policyDoc" --set-as-default --query 'PolicyVersion.Arn' --output text)
  } else {
    Write-Host "Creating policy $PolicyName" -ForegroundColor Cyan
    aws iam create-policy --policy-name $PolicyName --policy-document "$policyDoc" | Out-Null
  }
} catch {
  Write-Host "Policy create/update failed: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}

# Attach to user
try {
  aws iam attach-user-policy --user-name $UserName --policy-arn "arn:aws:iam::$account:policy/$PolicyName"
  Write-Host "✅ Attached policy $PolicyName to user $UserName" -ForegroundColor Green
} catch {
  Write-Host "Attach failed: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}
