#!/usr/bin/env pwsh

# InfinityAI.Pro - Verified Fresh Deployment Script
# Generated based on CLOUD_RECON_REPORT.md
# Deployment Target: gen-lang-client-0779271931 (us-central1)

$ErrorActionPreference = "Stop"

Write-Host "InifinityAI.Pro - Starting Fresh Deployment..." -ForegroundColor Cyan

# 1. Configuration
$PROJECT_ID = gcloud config get-value project
if (-not $PROJECT_ID) { $PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT }
if (-not $PROJECT_ID) { Write-Error "Project ID not set"; exit 1 }
$REGION = "us-central1"

# Service Map: Directory -> Cloud Run Service Name (Verified)
$SERVICES = @{
    "engine-a" = "engine-a"
    "engine-b" = "engine-b"
    "engine-c" = "engine-c"
}

# 2. Deploy Cloud Run Engines
Write-Host "`n[1/4] Building and Deploying Engines..." -ForegroundColor Yellow

foreach ($dir in $SERVICES.Keys) {
    $serviceName = $SERVICES[$dir]
    Write-Host "Processing $serviceName ($dir)..." -ForegroundColor White
    
    $path = "backend\$dir"
    if (-not (Test-Path $path)) {
        Write-Error "Directory not found: $path"
    }

    Push-Location $path

    # Build
    Write-Host "  > Building Container for $serviceName..."
    $tag = "gcr.io/$PROJECT_ID/$serviceName"
    gcloud builds submit --tag $tag --project=$PROJECT_ID --quiet
    
    # Deploy
    Write-Host "  > Deploying to Cloud Run..."
    gcloud run deploy $serviceName `
        --image $tag `
        --region $REGION `
        --project $PROJECT_ID `
        --allow-unauthenticated `
        --memory "1Gi" `
        --cpu "1" `
        --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
        --quiet

    Pop-Location
    Write-Host "  > $serviceName Deployed Successfully." -ForegroundColor Green
}

# 3. Deploy Frontend
Write-Host "`n[2/4] Deploying Frontend..." -ForegroundColor Yellow
$frontendDir = "frontend"
if (Test-Path $frontendDir) {
    Push-Location $frontendDir
    
    # Build
    Write-Host "  > Compiling Next.js Application..."
    npm run build
    
    # Containerize
    Write-Host "  > Building Frontend Container..."
    $frontendTag = "gcr.io/$PROJECT_ID/infinityai-frontend"
    gcloud builds submit --tag $frontendTag --project=$PROJECT_ID --quiet
    
    # Deploy
    Write-Host "  > Deploying Frontend Service..."
    gcloud run deploy infinityai-frontend `
        --image $frontendTag `
        --region $REGION `
        --project $PROJECT_ID `
        --allow-unauthenticated `
        --memory "1Gi" `
        --cpu "1" `
        --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
        --quiet
        
    Pop-Location
    Write-Host "  > Frontend Deployed Successfully." -ForegroundColor Green
}
else {
    Write-Error "Frontend directory not found!"
}

# 4. Deploy Firebase Config
Write-Host "`n[3/4] Deploying Firebase (Functions, Hosting, Rules)..." -ForegroundColor Yellow
firebase deploy --project=$PROJECT_ID --only functions, hosting, firestore:rules, firestore:indexes

# 5. Verification
Write-Host "`n[4/4] Verifying Endpoints..." -ForegroundColor Yellow
$endpoints = @(
    "https://engine-a-429140669077.us-central1.run.app/health",
    "https://engine-b-429140669077.us-central1.run.app/health",
    "https://engine-c-429140669077.us-central1.run.app/health",
    "https://infinityai-frontend-ckxt6xvshq-uc.a.run.app",
    # Custom Domains
    "https://infinityai.pro"
)

foreach ($url in $endpoints) {
    try {
        $res = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 10
        Write-Host "`nFresh Deployment Complete." -ForegroundColor Cyan
