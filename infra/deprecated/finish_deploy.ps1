#!/usr/bin/env pwsh
# InfinityAI.Pro - Finish Deployment (Firebase & Verification)
# Fixes the quoting issue and validates Engine A health.

$ErrorActionPreference = "Stop"
Write-Host "InfinityAI.Pro - Finalizing Deployment" -ForegroundColor Cyan
Write-Host "======================================"

$PROJECT_ID = "gen-lang-client-0779271931"
$REGION = "us-central1" # Define region for Cloud Run deployments

# 0. Repair Engine A (Previous Attempt Failed)
Write-Host "`n[0/3] Repairing Engine A (Increasing Memory)..." -ForegroundColor Yellow
$service = "engine-a"
$path = "backend\engine-a"
Push-Location $path
try {
    # Redeploying to EXISTING service 'engine-a'
    $tag = "gcr.io/$PROJECT_ID/$service"
    Write-Host "  > Re-building $service..."
    gcloud builds submit --tag $tag --project=$PROJECT_ID --quiet
    
    Write-Host "  > Deploying $service (2Gi Memory)..."
    gcloud run deploy $service `
        --image $tag `
        --region $REGION `
        --project $PROJECT_ID `
        --allow-unauthenticated `
        --memory "2Gi" `
        --cpu "1" `
        --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
        --quiet
    Write-Host "  > Engine A Repaired." -ForegroundColor Green
}
catch {
    Write-Host "  > Engine A Repair Failed: $_" -ForegroundColor Red
}
Pop-Location

# 1. Deploy Firebase Ecosystem (Functions + Hosting)
Write-Host "`n[1/3] Deploying Firebase Ecosystem..." -ForegroundColor Yellow
try {
    Write-Host "  > Target: Existing Firebase Project ($PROJECT_ID)"
    Write-Host "  > Pushing Functions, Hosting (web-app), and Rules..."
    # Quote the list to avoid PowerShell parsing errors
    firebase deploy --project=$PROJECT_ID --only "functions,hosting,firestore"
    Write-Host "  SUCCESS" -ForegroundColor Green
}
catch {
    Write-Host "  FAILED: $_" -ForegroundColor Red
}

# 2. Final Verification
Write-Host "`n[2/3] Final Verification..." -ForegroundColor Yellow
$Endpoints = @(
    "https://engine-a-429140669077.us-central1.run.app/health",
    "https://engine-b-429140669077.us-central1.run.app/healthz",
    "https://engine-c-429140669077.us-central1.run.app/health",
    "https://infinityai.pro"
)

foreach ($url in $Endpoints) {
    try {
        Write-Host "  Checking: $url"
        $res = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 10
        if ($res.StatusCode -eq 200) {
            Write-Host "  [OK] ($($res.StatusCode))" -ForegroundColor Green
        }
        else {
            Write-Host "  [WARN] ($($res.StatusCode))" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  [ERR] Failed to reach $url" -ForegroundColor Red
        Write-Host "    $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nDeployment Finalized." -ForegroundColor Cyan
