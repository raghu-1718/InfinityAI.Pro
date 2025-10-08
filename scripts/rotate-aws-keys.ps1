param(
  [Parameter(Mandatory=$true)][string]$Repo,
  [string]$UserName,
  [switch]$DeleteOldestIfLimit
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host $msg -ForegroundColor Red }

try {
  # Determine IAM user
  if (-not $UserName) {
    $arn = aws sts get-caller-identity --query 'Arn' --output text
    Write-Info "AWS Identity ARN: $arn"
    if ($arn -notmatch ':user\/([^\/]+)$') {
      throw "Current AWS identity is not an IAM user. Specify -UserName explicitly (e.g., 'infinityai-deploy')."
    }
    $UserName = ($arn -replace '.*:user\/','')
  } else {
    Write-Info "Target IAM User: $UserName"
  }

  # Ensure GH CLI logged in
  gh auth status | Out-Null

  # Check existing keys
  $keys = aws iam list-access-keys --user-name $UserName | ConvertFrom-Json
  $keyCount = @($keys.AccessKeyMetadata).Count
  Write-Info "Existing access keys for '$UserName': $keyCount"

  if ($keyCount -ge 2) {
    if ($DeleteOldestIfLimit) {
      # Delete the oldest active key
      $sorted = $keys.AccessKeyMetadata | Sort-Object -Property CreateDate
      $oldest = $sorted | Select-Object -First 1
      Write-Warn "Key limit reached (2). Deleting oldest key: $($oldest.AccessKeyId) created $($oldest.CreateDate)"
      aws iam delete-access-key --user-name $UserName --access-key-id $oldest.AccessKeyId | Out-Null
    } else {
      throw "User already has 2 access keys. Re-run with -DeleteOldestIfLimit to delete the oldest active key automatically."
    }
  }

  # Create new access key
  $resp = aws iam create-access-key --user-name $UserName | ConvertFrom-Json
  $ak = $resp.AccessKey.AccessKeyId
  $sk = $resp.AccessKey.SecretAccessKey
  if (-not $ak -or -not $sk) { throw "Failed to obtain new access key values." }
  Write-Info "Created new access key for '$UserName': $ak"

  # Set GitHub repo secrets securely without trailing newlines
  gh secret set AWS_ACCESS_KEY_ID --repo $Repo --body "$ak" | Out-Null
  gh secret set AWS_SECRET_ACCESS_KEY --repo $Repo --body "$sk" | Out-Null
  Write-Host "✅ Updated GitHub secrets AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY for $Repo" -ForegroundColor Green

} catch {
  Write-Err ("Rotation failed: " + $_.Exception.Message)
  exit 1
}

exit 0
