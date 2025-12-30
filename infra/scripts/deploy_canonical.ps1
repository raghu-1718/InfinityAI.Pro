#!/usr/bin/env pwsh
# InfinityAI.Pro - Canonical Truth-Based Deployment
# Generated from LIVE_CLOUD state in infra_snapshot/infra_truth.json

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying InfinityAI.Pro (Canonical Script)" -ForegroundColor Cyan

# 1. Load Truth
if (-not (Test-Path "infra_snapshot/infra_truth.json")) {
    Write-Error "infra_snapshot/infra_truth.json not found. Run discovery first."
    exit 1
}
$truth = Get-Content "infra_snapshot/infra_truth.json" | ConvertFrom-Json

# 2. Extract Config
$PROJECT_ID = gcloud config get-value project
$REGION = $truth.cloudrun[0].region
if (-not $REGION) { $REGION = "us-central1" } # Fallback if no services exist yet

Write-Host "Target: $PROJECT_ID ($REGION)" -ForegroundColor Yellow

# 3. Deploy Cloud Run Engines
Write-Host "`n[1/3] Deploying Backend Engines..." -ForegroundColor Yellow

$engines = @("engine-a", "engine-b", "engine-c")
foreach ($engine in $engines) {
    if (Test-Path "backend/$engine") {
        Write-Host "  > Deploying $engine..."
        # Using source deploy for consistency with requested bash script
        gcloud run deploy $engine --source "backend/$engine" --region $REGION --project $PROJECT_ID --quiet
    }
}

# 4. Deploy Firebase Functions
Write-Host "`n[2/3] Deploying Firebase Functions..." -ForegroundColor Yellow
firebase deploy --only functions --project $PROJECT_ID

# 5. Deploy Frontend (Hosting)
Write-Host "`n[3/3] Deploying Frontend..." -ForegroundColor Yellow
firebase deploy --only hosting --project $PROJECT_ID

Write-Host "`n✅ Deployment Reconciliation Complete" -ForegroundColor Green
