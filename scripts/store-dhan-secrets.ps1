<# 
  store-dhan-secrets.ps1
  Usage:
    # AWS only:
    .\store-dhan-secrets.ps1 -Mode aws -SecretName "prod/dhan/api" -DhanApiKey "<KEY>" -DhanApiSecret "<SECRET>" -DhanAccessToken "<ACCESS_TOKEN>"

    # AWS + GCP:
    .\store-dhan-secrets.ps1 -Mode all -SecretName "prod/dhan/api" -GcpSecretName "prod-dhan-api" -DhanApiKey "<KEY>" -DhanApiSecret "<SECRET>" -DhanAccessToken "<ACCESS_TOKEN>"

  Requirements:
    - AWS CLI configured with IAM user/role that can call Secrets Manager
    - If using GCP: gcloud CLI configured with permissions to create secrets
    - Do NOT run on CI with secrets in plain text; run locally with secure environment variables or prompt input.
#>

param(
  [Parameter(Mandatory=$true)][ValidateSet("aws","gcp","all")] [string]$Mode,
  [Parameter(Mandatory=$true)] [string]$SecretName,
  [string]$GcpSecretName = "prod-dhan-api",
  [Parameter(Mandatory=$false)] [string]$DhanApiKey,
  [Parameter(Mandatory=$false)] [string]$DhanApiSecret,
  [Parameter(Mandatory=$false)] [string]$DhanAccessToken,
  [switch]$PromptForSecrets
)

function Read-SecretIfNeeded {
  param($value, $prompt)
  if ($PromptForSecrets -and -not $value) {
    Write-Host "$prompt (input hidden): "
    $secure = Read-Host -AsSecureString
    return [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
  }
  return $value
}

# Optionally prompt if values not provided
$DhanApiKey = Read-SecretIfNeeded $DhanApiKey "Dhan API Key"
$DhanApiSecret = Read-SecretIfNeeded $DhanApiSecret "Dhan API Secret"
$DhanAccessToken = Read-SecretIfNeeded $DhanAccessToken "Dhan Access Token (daily token)"

# Build payload JSON (do NOT include empty values)
$payload = @{}
if ($DhanApiKey) { $payload.dhan_api_key = $DhanApiKey }
if ($DhanApiSecret) { $payload.dhan_api_secret = $DhanApiSecret }
if ($DhanAccessToken) { $payload.dhan_access_token = $DhanAccessToken }
$secretString = ($payload | ConvertTo-Json -Compress)

if ($Mode -in @("aws","all")) {
  Write-Host "`n== AWS Secrets Manager ($SecretName) =="
  try {
    # If secret exists -> update via put-secret-value, else create-secret
    $exists = & aws secretsmanager describe-secret --secret-id $SecretName 2>$null
    if ($LASTEXITCODE -eq 0) {
      Write-Host "Secret exists — adding new version via PutSecretValue..."
      & aws secretsmanager put-secret-value --secret-id $SecretName --secret-string $secretString
      if ($LASTEXITCODE -ne 0) { throw "aws put-secret-value failed (exit $LASTEXITCODE)" }
      Write-Host "AWS SecretsManager: Updated secret value for $SecretName"
    } else {
      Write-Host "Secret not found — creating via CreateSecret..."
      & aws secretsmanager create-secret --name $SecretName --secret-string $secretString
      if ($LASTEXITCODE -ne 0) { throw "aws create-secret failed (exit $LASTEXITCODE)" }
      Write-Host "AWS SecretsManager: Created secret $SecretName"
    }
  } catch {
    Write-Error "AWS SecretsManager operation failed: $_"
  }
}

if ($Mode -in @("gcp","all")) {
  Write-Host "`n== GCP Secret Manager ($GcpSecretName) =="
  try {
    # create secret if not exists
    $exists = & gcloud secrets describe $GcpSecretName --format="value(name)" 2>$null
    if ($LASTEXITCODE -eq 0) {
      Write-Host "GCP secret exists — adding a new secret version..."
      # Add secret version
      $tempFile = New-TemporaryFile
      $secretString | Out-File -Encoding utf8 -FilePath $tempFile
      & gcloud secrets versions add $GcpSecretName --data-file=$tempFile
      Remove-Item $tempFile
      Write-Host "GCP Secret Manager: Added new version to $GcpSecretName"
    } else {
      Write-Host "GCP secret not found — creating secret and adding initial version..."
      & gcloud secrets create $GcpSecretName --replication-policy="automatic"
      $tempFile = New-TemporaryFile
      $secretString | Out-File -Encoding utf8 -FilePath $tempFile
      & gcloud secrets versions add $GcpSecretName --data-file=$tempFile
      Remove-Item $tempFile
      Write-Host "GCP Secret Manager: Created $GcpSecretName and added initial version"
    }
  } catch {
    Write-Error "GCP Secret Manager operation failed: $_"
  }
}

Write-Host "`nDone. IMPORTANT: Do not commit secrets to git. Rotate keys immediately after storing."
