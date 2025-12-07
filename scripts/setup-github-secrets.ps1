# Setup GitHub Secrets for CI/CD
# Run this script to configure the required secrets in your GitHub repository

# =====================================================
# REQUIRED GITHUB SECRETS
# =====================================================
#
# 1. GCP_WORKLOAD_IDENTITY_PROVIDER
#    Format: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
#    Get with: gcloud iam workload-identity-pools providers describe github-provider --location=global --workload-identity-pool=github-actions-pool --format="value(name)"
#
# 2. GCP_SERVICE_ACCOUNT
#    Format: SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com
#    Example: github-actions@after-yesterday-473512-k3.iam.gserviceaccount.com
#
# 3. FIREBASE_SERVICE_ACCOUNT
#    JSON key file for Firebase deployment
#    Generate at: Firebase Console > Project Settings > Service Accounts > Generate new private key
#
# =====================================================

Write-Host "=== InfinityAI.Pro GitHub Secrets Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI (gh) is not installed. Please install it first." -ForegroundColor Red
    Write-Host "Install: winget install GitHub.cli"
    exit 1
}

# Check auth status
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please authenticate with GitHub CLI first:" -ForegroundColor Yellow
    Write-Host "Run: gh auth login"
    exit 1
}

$repo = "raghu-1718/InfinityAI.Pro"
$projectId = "gen-lang-client-0779271931"
$projectNumber = "429140669077"

Write-Host "Repository: $repo" -ForegroundColor Green
Write-Host "GCP Project: $projectId" -ForegroundColor Green
Write-Host ""

# Get Workload Identity Provider
Write-Host "Fetching Workload Identity Provider..." -ForegroundColor Yellow
$wifProvider = gcloud iam workload-identity-pools providers describe github-provider `
    --location=global `
    --workload-identity-pool=github-pool `
    --format="value(name)" `
    --project=$projectId 2>$null

if ($wifProvider) {
    Write-Host "Found WIF Provider: $wifProvider" -ForegroundColor Green
    gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --repo $repo --body $wifProvider
    Write-Host "✓ GCP_WORKLOAD_IDENTITY_PROVIDER secret set" -ForegroundColor Green
} else {
    Write-Host "WIF Provider not found. Creating one..." -ForegroundColor Yellow

    # Create Workload Identity Pool if not exists
    gcloud iam workload-identity-pools create github-actions-pool `
        --location=global `
        --display-name="GitHub Actions Pool" `
        --project=$projectId 2>$null

    # Create Provider
    gcloud iam workload-identity-pools providers create-oidc github-provider `
        --location=global `
        --workload-identity-pool=github-actions-pool `
        --display-name="GitHub Provider" `
        --issuer-uri="https://token.actions.githubusercontent.com" `
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" `
        --attribute-condition="assertion.repository_owner=='raghu-1718'" `
        --project=$projectId

    $wifProvider = "projects/$projectNumber/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider"
    gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --repo $repo --body $wifProvider
}

# Set Service Account
$serviceAccount = "github-actions@$projectId.iam.gserviceaccount.com"
Write-Host "Setting GCP_SERVICE_ACCOUNT: $serviceAccount" -ForegroundColor Yellow
gh secret set GCP_SERVICE_ACCOUNT --repo $repo --body $serviceAccount
Write-Host "✓ GCP_SERVICE_ACCOUNT secret set" -ForegroundColor Green

# Check if service account has required permissions
Write-Host ""
Write-Host "Verifying Service Account permissions..." -ForegroundColor Yellow

# Grant Workload Identity User role
gcloud iam service-accounts add-iam-policy-binding $serviceAccount `
    --role="roles/iam.workloadIdentityUser" `
    --member="principalSet://iam.googleapis.com/projects/$projectNumber/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/raghu-1718/InfinityAI.Pro" `
    --project=$projectId 2>$null

# Grant Cloud Run Admin
gcloud projects add-iam-policy-binding $projectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/run.admin" 2>$null

# Grant Artifact Registry Writer
gcloud projects add-iam-policy-binding $projectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/artifactregistry.writer" 2>$null

# Grant Secret Accessor
gcloud projects add-iam-policy-binding $projectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/secretmanager.secretAccessor" 2>$null

# Grant Service Account User
gcloud projects add-iam-policy-binding $projectId `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/iam.serviceAccountUser" 2>$null

Write-Host "✓ Service account permissions configured" -ForegroundColor Green

Write-Host ""
Write-Host "=== Firebase Service Account ===" -ForegroundColor Cyan
Write-Host "To set FIREBASE_SERVICE_ACCOUNT:"
Write-Host "1. Go to: https://console.firebase.google.com/project/$projectId/settings/serviceaccounts/adminsdk"
Write-Host "2. Click 'Generate new private key'"
Write-Host "3. Run: gh secret set FIREBASE_SERVICE_ACCOUNT --repo $repo < path/to/key.json"
Write-Host ""

Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Secrets configured:" -ForegroundColor Green
Write-Host "  - GCP_WORKLOAD_IDENTITY_PROVIDER"
Write-Host "  - GCP_SERVICE_ACCOUNT"
Write-Host ""
Write-Host "Manual steps required:" -ForegroundColor Yellow
Write-Host "  - Set FIREBASE_SERVICE_ACCOUNT (see instructions above)"
Write-Host ""
Write-Host "To verify secrets, run: gh secret list --repo $repo"
