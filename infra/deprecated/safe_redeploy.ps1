#!/usr/bin/env pwsh
# InfinityAI.Pro - Safe Redeploy Protocol
# Architecture: 3 Cloud Run Engines + Static Frontend (Hosting) + Firebase Functions

$ErrorActionPreference = "Stop"
Write-Host "InfinityAI.Pro - Master Validation and Redeploy" -ForegroundColor Cyan
Write-Host "============================================="

$PROJECT_ID = "gen-lang-client-0779271931"
$REGION = "us-central1"

# 1. Deploy Engines (Cloud Run)
$ENGINES = @{
    "engine-a" = "engine-a"
    "engine-b" = "engine-b"
    "engine-c" = "engine-c"
}

Write-Host "`n[1/4] Processing Core Engines..." -ForegroundColor Yellow
foreach ($dir in $ENGINES.Keys) {
    $service = $ENGINES[$dir]
    Write-Host "  Processing: $service ($dir)" -ForegroundColor White
    
    $path = "backend\$dir"
    if (-not (Test-Path $path)) { Write-Error "Missing path: $path" }
    
    Push-Location $path
    
    # Build & Deploy
    $tag = "gcr.io/$PROJECT_ID/$service"
    
    try {
        Write-Host "    - Building..."
        gcloud builds submit --tag $tag --project=$PROJECT_ID --quiet
        
        Write-Host "    - Deploying..."
        gcloud run deploy $service `
            --image $tag `
            --region $REGION `
            --project $PROJECT_ID `
            --allow-unauthenticated `
            --memory "1Gi" `
            --cpu "1" `
            --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
            --quiet
            
        Write-Host "    - SUCCESS" -ForegroundColor Green
    }
    catch {
        Write-Host "    - FAILED: $_" -ForegroundColor Red
    }
    
    Pop-Location
}

# 2. Deploy Frontend (Static -> Firebase Hosting)
Write-Host "`n[2/4] Processing Frontend..." -ForegroundColor Yellow
Push-Location "frontend/web-app"

try {
    Write-Host "  Building Static Export..."
    npm install
    npm run build
    
    if (-not (Test-Path "out")) {
        throw "Build failed: 'out' directory not created."
    }
    
    Write-Host "  SUCCESS: Static build complete." -ForegroundColor Green
}
catch {
    Write-Error "Frontend Build Failed: $_"
}
Pop-Location

# 3. Firebase Deployment (Functions, Hosting, Firestore)
Write-Host "`n[3/4] Deploying Firebase Ecosystem..." -ForegroundColor Yellow
try {
    Write-Host "  Pushing Functions, Hosting, and Rules..."
    firebase deploy --project=$PROJECT_ID --only functions, hosting, firestore
    Write-Host "  SUCCESS" -ForegroundColor Green
}
catch {
    Write-Host "  FAILED: $_" -ForegroundColor Red
}

# 4. Final Verification
Write-Host "`n[4/4] Final Verification..." -ForegroundColor Yellow
$Endpoints = @(
    "https://engine-a-429140669077.us-central1.run.app/health",
    "https://engine-b-429140669077.us-central1.run.app/health",
    "https://engine-c-429140669077.us-central1.run.app/health",
    "https://infinityai.pro"
)

foreach ($url in $Endpoints) {
    try {
        $res = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 5
        if ($res.StatusCode -eq 200) {
            Write-Host "  [OK] $url" -ForegroundColor Green
        }
        else {
            Write-Host "  [WARN] $url ($($res.StatusCode))" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  [ERR] $url" -ForegroundColor Red
    }
}

Write-Host "`nMission Complete." -ForegroundColor Cyan
