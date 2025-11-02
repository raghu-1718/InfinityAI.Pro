Param(
    [string]$ProjectId = "infinity-ai-5ec7c",
    [string]$Region = "us-central1",
    [string]$Repo = "raghu-1718/InfinityAI.Pro",
    [string]$GithubSaJsonPath,
    [string]$GithubEnv = "",
    [switch]$NonInteractive
)

# Utility: require a command
function Test-RequireCommand($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "'$name' not found. Please install it and re-run."; exit 1
    }
}

# Prereqs
Test-RequireCommand gcloud
$FirebaseCli = Get-Command firebase -ErrorAction SilentlyContinue
if (-not $FirebaseCli) { Write-Warning "firebase CLI not found. Firebase config step will be skipped." }
$GhCli = Get-Command gh -ErrorAction SilentlyContinue
if (-not $GhCli) { Write-Warning "gh CLI not found. GitHub secrets step will be skipped." }

# Out folder
$OutDir = Join-Path $PSScriptRoot "out"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "Using Project: $ProjectId | Region: $Region"

# Set gcloud project
& gcloud config set project $ProjectId | Out-Null

# Fetch project number
$ProjectNumber = (& gcloud projects describe $ProjectId --format "value(projectNumber)").Trim()
if (-not $ProjectNumber) { Write-Error "Unable to fetch project number"; exit 1 }

# Service Accounts
$ComputeSA = "$ProjectNumber-compute@developer.gserviceaccount.com"
$AppEngineSA = "$ProjectId@appspot.gserviceaccount.com"

# 1) Billing status
Write-Host "Checking billing status..."
$BillingEnabled = (& gcloud beta billing projects describe $ProjectId --format "value(billingEnabled)" 2>$null)
Write-Host "Billing enabled: $BillingEnabled"
if ($BillingEnabled -ne "True" -and $BillingEnabled -ne "TRUE") {
    Write-Warning "Billing is not enabled. Please enable billing for project $ProjectId and re-run."
}

# 2) Enable required APIs
$apis = @(
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "eventarc.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "appengine.googleapis.com"
)
Write-Host "Enabling required APIs (best-effort)..."
foreach ($api in $apis) {
    & gcloud services enable $api --project $ProjectId 2>$null | Out-Null
}

# 3) Ensure App Engine app exists (one-time)
Write-Host "Ensuring App Engine app exists..."
& gcloud app describe --project $ProjectId 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $AppEngineRegion = $env:APP_ENGINE_REGION
    if (-not $AppEngineRegion -or $AppEngineRegion.Trim() -eq "") { $AppEngineRegion = "us-central" }
    & gcloud app create --project $ProjectId --region $AppEngineRegion
}

# 4) Grant IAM roles to deploy and runtime SAs (best-effort)
function Grant-Role($member, $role) {
    & gcloud projects add-iam-policy-binding $ProjectId `
        --member $member `
        --role $role `
        --condition=None 2>$null | Out-Null
}

# GitHub Actions deployer SA (from JSON or prompt)
if (-not $GithubSaJsonPath) {
    if (-not $NonInteractive) {
        $GithubSaJsonPath = Read-Host "Path to GitHub Actions Service Account JSON (leave blank to skip)"
    }
}
$DeploySaEmail = ""
if ($GithubSaJsonPath -and (Test-Path $GithubSaJsonPath)) {
    $DeploySaEmail = (Get-Content $GithubSaJsonPath | ConvertFrom-Json).client_email
    Write-Host "Using deployer SA: $DeploySaEmail"
}

$DeployMembers = @()
if ($DeploySaEmail) { $DeployMembers += "serviceAccount:$DeploySaEmail" }

$RuntimeMembers = @(
    "serviceAccount:$ComputeSA",
    "serviceAccount:$AppEngineSA"
)

$DeployerRoles = @(
    "roles/cloudfunctions.developer",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/eventarc.admin",
    "roles/cloudbuild.builds.editor"
)
$RuntimeRoles = @(
    "roles/secretmanager.secretAccessor"
)

Write-Host "Granting deployer roles (best-effort)..."
foreach ($m in $DeployMembers) { foreach ($r in $DeployerRoles) { Grant-Role $m $r } }
Write-Host "Granting runtime roles (best-effort)..."
foreach ($m in $RuntimeMembers) { foreach ($r in $RuntimeRoles) { Grant-Role $m $r } }

# 5) Create / update GSM secrets
function Invoke-EnsureSecret($name) {
    $exists = (& gcloud secrets list --filter "name:$name" --format "value(name)" 2>$null)
    if (-not $exists) {
        & gcloud secrets create $name --replication-policy="automatic" | Out-Null
        Write-Host "Created secret: $name"
    }
}
function Add-Secret-Version($name, $value) {
    if (-not $value) { return }
    $tmp = New-TemporaryFile
    Set-Content -Path $tmp -Value $value -NoNewline
    & gcloud secrets versions add $name --data-file $tmp | Out-Null
    Remove-Item $tmp -Force
}

$SecretNames = @(
    "gemini-api-key-primary",
    "gemini-api-key-secondary",
    "dhan-api-key",
    "huggingface-token",
    "trading-engine-secret",
    "webhook-verification-token",
    "telegram-bot-token"
)

Write-Host "Ensuring secrets exist..."
foreach ($s in $SecretNames) { Invoke-EnsureSecret $s }

# Collect values (from env or prompt if interactive)
function Read-SecretValue($envName, $prompt) {
    $v = [Environment]::GetEnvironmentVariable($envName)
    if ($v) { return $v }
    if ($NonInteractive) { return $null }
    return (Read-Host -AsSecureString $prompt | `
        ForEach-Object { (New-Object System.Net.NetworkCredential "", $_).Password })
}

$Map = @{
    "gemini-api-key-primary" = Read-SecretValue "GEMINI_API_KEY_PRIMARY" "Enter GEMINI_API_KEY_PRIMARY";
    "gemini-api-key-secondary" = Read-SecretValue "GEMINI_API_KEY_SECONDARY" "Enter GEMINI_API_KEY_SECONDARY";
    "dhan-api-key" = Read-SecretValue "DHAN_API_KEY" "Enter DHAN_API_KEY";
    "huggingface-token" = Read-SecretValue "HUGGINGFACE_TOKEN" "Enter HUGGINGFACE_TOKEN";
    "trading-engine-secret" = Read-SecretValue "TRADING_ENGINE_SECRET" "Enter TRADING_ENGINE_SECRET";
    "webhook-verification-token" = Read-SecretValue "WEBHOOK_VERIFICATION_TOKEN" "Enter WEBHOOK_VERIFICATION_TOKEN";
    "telegram-bot-token" = Read-SecretValue "TELEGRAM_BOT_TOKEN" "Enter TELEGRAM_BOT_TOKEN";
}

Write-Host "Adding secret versions (where values provided)..."
foreach ($k in $Map.Keys) { Add-Secret-Version $k $Map[$k] }

# 6) Firebase Functions config (encryption key)
$EncryptionKey = [Environment]::GetEnvironmentVariable("ENCRYPTION_KEY")
if (-not $EncryptionKey -and -not $NonInteractive) {
    $EncryptionKey = (Read-Host -AsSecureString "Enter ENCRYPTION_KEY for functions config" | `
        ForEach-Object { (New-Object System.Net.NetworkCredential "", $_).Password })
}
if ($EncryptionKey) {
    if ($FirebaseCli) {
        & firebase functions:config:set secrets.encryption_key="$EncryptionKey" --project $ProjectId | Out-Null
    } else {
        Write-Warning "Skipping Firebase functions config: firebase CLI not installed."
    }
}

# 7) Dump current state
Write-Host "Dumping current state to $OutDir ..."
& gcloud secrets list --format json > (Join-Path $OutDir "secrets_list.json")
& gcloud services list --enabled --format json > (Join-Path $OutDir "services_enabled.json")
& gcloud projects get-iam-policy $ProjectId --format json > (Join-Path $OutDir "project_iam_policy.json")
& gcloud run services list --region $Region --format json > (Join-Path $OutDir "cloud_run_services.json")

# Describe known services if they exist
$services = @("infinityai-engine-a","infinityai-engine-b","infinityai-engine-c-execution","infinityai-engine-d","infinityai-frontend")
foreach ($svc in $services) {
    & gcloud run services describe $svc --region $Region --format json 2>$null > (Join-Path $OutDir "$svc.json")
}

# 8) Optionally set GitHub Actions secrets via gh
if ($GhCli) {
    if ($GithubSaJsonPath -and (Test-Path $GithubSaJsonPath)) {
        Write-Host "Setting GitHub Actions repository secrets (gh)..."
        $json = Get-Content -Raw -Path $GithubSaJsonPath
        & gh secret set GCP_SERVICE_ACCOUNT_KEY --repo $Repo -b $json
    }
    if ($Map["gemini-api-key-primary"]) { & gh secret set GEMINI_API_KEY_PRIMARY --repo $Repo -b $Map["gemini-api-key-primary"] }
    if ($Map["gemini-api-key-secondary"]) { & gh secret set GEMINI_API_KEY_SECONDARY --repo $Repo -b $Map["gemini-api-key-secondary"] }
    if ($EncryptionKey) { & gh secret set ENCRYPTION_KEY --repo $Repo -b $EncryptionKey }
} else {
    Write-Warning "Skipping GitHub secrets step: gh CLI not installed."
}

Write-Host "\n✅ Completed. Outputs in $OutDir. Review IAM bindings and rerun CI/CD."
