<#
Setup AWS IAM Role for GitHub OIDC deployments.
Requires: AWS CLI v2, permissions to create IAM identity provider & role.
#>
param(
  [string]$GitHubOrg = 'raghu-1718',
  [string]$Repo = 'InfinityAI.Pro',
  [string]$RoleName = 'GitHubOIDCDeployRole',
  [string]$PolicyArn = 'arn:aws:iam::aws:policy/AdministratorAccess',
  [string]$SessionDuration = '3600',
  [switch]$DryRun
)

$ProviderUrl = 'token.actions.githubusercontent.com'
$Thumbprint = '6938fd4d98bab03faadb97b34396831e3780aea1'
$Audience = 'sts.amazonaws.com'

Write-Host "[INFO] Ensuring IAM OIDC provider exists" -ForegroundColor Cyan
if(-not $DryRun){
  $existing = aws iam list-open-id-connect-providers --query 'OpenIDConnectProviderList[].Arn' --output text 2>$null | Select-String $ProviderUrl
  if(-not $existing){
    aws iam create-open-id-connect-provider `
      --url "https://$ProviderUrl" `
      --thumbprint-list $Thumbprint `
      --client-id-list $Audience | Out-Null
    Write-Host "[OK] Created OIDC provider"
  }else{ Write-Host "[SKIP] Provider already present" }
} else { Write-Host "[DRYRUN] Skipping provider creation" }

$ProviderArn = if(-not $DryRun){ aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, '$ProviderUrl')].Arn" --output text 2>$null } else { "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" }
if([string]::IsNullOrWhiteSpace($ProviderArn)){ $ProviderArn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" }

$sub = "repo:$GitHubOrg/$Repo:ref:refs/heads/main"
$AssumeDoc = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "$ProviderArn" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$ProviderUrl:aud": "$Audience"
        },
        "StringLike": {
          "$ProviderUrl:sub": "$sub"
        }
      }
    }
  ]
}
"@

if(-not $DryRun){
  $existingArn = aws iam get-role --role-name $RoleName --query 'Role.Arn' --output text 2>$null
  if([string]::IsNullOrWhiteSpace($existingArn) -or $existingArn -like '*NoSuchEntity*' -or $LASTEXITCODE -ne 0){
    Write-Host "[INFO] Creating role $RoleName" -ForegroundColor Cyan
    $tmp = New-TemporaryFile
    $AssumeDoc | Set-Content -Path $tmp -Encoding UTF8
    $createOut = aws iam create-role --role-name $RoleName --assume-role-policy-document file://$tmp 2>&1
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    if($LASTEXITCODE -ne 0){ Write-Host "[ERR] create-role failed: $createOut" -ForegroundColor Red }
    aws iam attach-role-policy --role-name $RoleName --policy-arn $PolicyArn | Out-Null
    aws iam update-role --role-name $RoleName --max-session-duration $SessionDuration | Out-Null
    Write-Host "[OK] Role created and policy attached" -ForegroundColor Green
  } else {
    Write-Host "[SKIP] Role $RoleName exists" -ForegroundColor Yellow
  }
} else { Write-Host "[DRYRUN] Skipping role creation" }

$RoleArn = if(-not $DryRun){ aws iam get-role --role-name $RoleName --query 'Role.Arn' --output text 2>$null } else { "arn:aws:iam::123456789012:role/$RoleName(DRYRUN)" }
if([string]::IsNullOrWhiteSpace($RoleArn)){
  Write-Host "[WARN] RoleArn could not be retrieved. Verify IAM permissions and try again." -ForegroundColor Yellow
}
Write-Host "[RESULT] RoleArn=$RoleArn"
