<#
apply_secrets_and_verify.ps1
Final refined version for InfinityAI.Pro
#>

param(
  [string]$Project = "gen-lang-client-0779271931",
  [string]$Region  = "us-central1",
  [string]$CollectDir = "infra/collected",
  [switch]$DryRun
)

# === Secrets and local files ===
$secrets = @{
  "encryption-key" = ".\secrets\encryption-key.txt"
}

# === Services with plaintext ENCRYPTION_KEY ===
$plaintext_services = @(
  "getaisignals","getbatchaisignals","getdhanoverview","getenginebstatus",
  "getgeminianalysis","getvertexaianalysis","savedhancredentials",
  "starttrading","stoptrading","submitdhancredentialsv2","syncholdings"
)

# === Services with existing secret refs ===
$secret_ref_services = @("engine-a","engine-b","engine-c")

# === Sensitive files ===
$sensitive_files = @("firebase-sa-key.json","firebase_users.json","logs.json","token.txt")

# === Preflight ===
function Check-Command($cmd) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Error "Missing command: $cmd"
    exit 1
  }
}
Check-Command gcloud
Check-Command git

# === Create secrets ===
foreach ($secretName in $secrets.Keys) {
  $localPath = $secrets[$secretName]
  if (Test-Path $localPath) {
    $exists = gcloud secrets list --project $Project --filter="name:$secretName" --format="value(name)"
    if (-not $exists) {
      if (-not $DryRun) { gcloud secrets create $secretName --data-file="$localPath" --project=$Project }
    } else {
      if (-not $DryRun) { gcloud secrets versions add $secretName --data-file="$localPath" --project=$Project }
    }
  }
}

# === Bind secrets to engine services ===
if (-not $DryRun) {
  gcloud run services update engine-a --project=$Project --region=$Region --update-secrets=DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_API_SECRET=dhan-api-secret:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest
  gcloud run services update engine-b --project=$Project --region=$Region --update-secrets=DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_API_SECRET=dhan-api-secret:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest,GEMINI_API_KEY=gemini-api-key:latest
  gcloud run services update engine-c --project=$Project --region=$Region --update-secrets=DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_API_SECRET=dhan-api-secret:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest,ENCRYPTION_KEY=encryption-key:latest
}

# === Bind ENCRYPTION_KEY to all plaintext services ===
foreach ($svc in $plaintext_services) {
  if (-not $DryRun) {
    gcloud run services update $svc --project=$Project --region=$Region --update-secrets=ENCRYPTION_KEY=encryption-key:latest
  }
}

# === Remove plaintext ENCRYPTION_KEY ===
foreach ($svc in $plaintext_services) {
  if (-not $DryRun) {
    gcloud run services update $svc --project=$Project --region=$Region --remove-env-vars=ENCRYPTION_KEY
  }
}

# === Collect verification ===
New-Item -ItemType Directory -Path $CollectDir -Force | Out-Null

$allServices = gcloud run services list --platform managed --project $Project --format="value(metadata.name)"
foreach ($svc in $allServices) {
  $safe = $svc -replace '[^a-zA-Z0-9._-]','_'
  gcloud run services describe $svc --project=$Project --region=$Region --format="yaml(spec.template.spec.containers[0].env)" > "$CollectDir/env_${safe}.yaml"
}

# === Remove sensitive files from Git ===
foreach ($f in $sensitive_files) {
  git rm --cached $f -q 2>$null
}

Add-Content -Path ".gitignore" -Value ($sensitive_files -join "`n")
git add .gitignore
git commit -m "chore(security): remove sensitive files and bind secrets" || Write-Host "No changes"

# === Archive ===
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path $CollectDir\* -DestinationPath "infra_collected_${timestamp}.zip" -Force

Write-Host "✅ Secret binding + cleanup complete."
Write-Host "📁 Verification stored in $CollectDir"
