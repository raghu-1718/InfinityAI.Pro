# Grant Firebase/RuntimeConfig IAM Permissions
# This fixes 403 errors blocking Firebase Functions deployment
# Date: November 3, 2025

$ErrorActionPreference = "Stop"

$PROJECT_ID = "after-yesterday-473512-k3"

# Get GitHub deployer service account email
# Replace with your actual GitHub deployer SA email from GitHub secrets
$GITHUB_SA_EMAIL = if ($env:GITHUB_SA_EMAIL) { 
    $env:GITHUB_SA_EMAIL 
} else { 
    "github-deployer@${PROJECT_ID}.iam.gserviceaccount.com" 
}

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "Granting Firebase IAM Permissions" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Service Account: $GITHUB_SA_EMAIL"
Write-Host ""

# Set project context
gcloud config set project $PROJECT_ID

Write-Host "1. Granting Cloud Functions Admin..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:${GITHUB_SA_EMAIL}" `
    --role="roles/cloudfunctions.admin" `
    --quiet

Write-Host "2. Granting Cloud Functions Service Agent..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:${GITHUB_SA_EMAIL}" `
    --role="roles/cloudfunctions.serviceAgent" `
    --quiet

Write-Host "3. Granting Runtime Config Admin..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:${GITHUB_SA_EMAIL}" `
    --role="roles/runtimeconfig.admin" `
    --quiet

Write-Host "4. Granting Viewer (for log streaming)..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:${GITHUB_SA_EMAIL}" `
    --role="roles/viewer" `
    --quiet

Write-Host "5. Granting Service Usage Consumer..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:${GITHUB_SA_EMAIL}" `
    --role="roles/serviceusage.serviceUsageConsumer" `
    --quiet

Write-Host ""
Write-Host "===================================================================" -ForegroundColor Green
Write-Host "IAM Permissions Granted Successfully" -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Verifying permissions..." -ForegroundColor Cyan
gcloud projects get-iam-policy $PROJECT_ID `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:${GITHUB_SA_EMAIL}" `
    --format="table(bindings.role)"

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Trigger new deployment: git commit --allow-empty -m 'trigger: redeploy with IAM fixes' && git push"
Write-Host "2. Monitor deployment: gh run watch"
Write-Host "3. Verify all engines and functions deploy successfully"
