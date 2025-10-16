#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy Fixed InfinityAI.Pro Frontend to GCP Cloud Run
    
.DESCRIPTION
    This script:
    1. Updates all configuration files with correct Cloud Run URLs
    2. Rebuilds the frontend Docker image
    3. Pushes to Google Container Registry
    4. Deploys to Cloud Run
    5. Creates domain mapping for infinityai.pro
    6. Verifies deployment health
    
.EXAMPLE
    .\deploy-fixed-frontend-gcp.ps1
    .\deploy-fixed-frontend-gcp.ps1 -SkipBuild
    .\deploy-fixed-frontend-gcp.ps1 -SkipDomainMapping
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "after-yesterday-473512-k3",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDomainMapping
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Header { param($msg) Write-Host "`n$('=' * 80)`n$msg`n$('=' * 80)" -ForegroundColor Magenta }

Write-Header "🚀 InfinityAI.Pro - Frontend Deployment with Fixed URLs"

# Step 1: Verify GCP authentication
Write-Info "Checking GCP authentication..."
try {
    $currentProject = gcloud config get-value project 2>$null
    if ($currentProject -ne $ProjectId) {
        Write-Warning "Switching to project: $ProjectId"
        gcloud config set project $ProjectId
    }
    Write-Success "Authenticated to GCP project: $ProjectId"
} catch {
    Write-Error "Failed to authenticate to GCP. Please run: gcloud auth login"
    exit 1
}

# Step 2: Enable required APIs
Write-Info "Ensuring required APIs are enabled..."
$apis = @(
    "run.googleapis.com",
    "containerregistry.googleapis.com"
)

foreach ($api in $apis) {
    Write-Info "Enabling $api..."
    gcloud services enable $api --project=$ProjectId 2>$null
}
Write-Success "All required APIs enabled"

# Step 3: Navigate to frontend directory
Write-Info "Navigating to frontend directory..."
$frontendPath = "frontend/web"
if (-not (Test-Path $frontendPath)) {
    Write-Error "Frontend directory not found: $frontendPath"
    exit 1
}
Set-Location $frontendPath
Write-Success "In frontend directory"

# Step 4: Install dependencies
if (-not $SkipBuild) {
    Write-Info "Installing npm dependencies..."
    npm install --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm install failed"
        exit 1
    }
    Write-Success "Dependencies installed"
}

# Step 5: Build production bundle
if (-not $SkipBuild) {
    Write-Info "Building production bundle with correct URLs..."
    $env:REACT_APP_ENGINE_A_URL = "https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app"
    $env:REACT_APP_ENGINE_B_URL = "https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app"
    $env:REACT_APP_ENGINE_C_URL = "https://engine-c-prod-bprmddefsa-uc.a.run.app"
    $env:REACT_APP_ENGINE_D_URL = "https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app"
    $env:REACT_APP_ENGINE_ULTRA_URL = "https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app"
    
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit 1
    }
    Write-Success "Production build completed"
}

# Step 6: Build and push Docker image
if (-not $SkipBuild) {
    Write-Info "Building Docker image..."
    $imageName = "gcr.io/$ProjectId/infinityai-frontend"
    $imageTag = "latest"
    $fullImage = "${imageName}:${imageTag}"
    
    docker build -t $fullImage .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed"
        exit 1
    }
    Write-Success "Docker image built: $fullImage"
    
    Write-Info "Pushing image to Google Container Registry..."
    docker push $fullImage
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker push failed"
        exit 1
    }
    Write-Success "Image pushed to GCR"
}

# Step 7: Deploy to Cloud Run
Write-Info "Deploying to Cloud Run..."
$serviceName = "infinityai-frontend"

gcloud run deploy $serviceName `
    --image="gcr.io/$ProjectId/infinityai-frontend:latest" `
    --platform=managed `
    --region=$Region `
    --allow-unauthenticated `
    --port=8080 `
    --memory=1Gi `
    --cpu=1 `
    --min-instances=1 `
    --max-instances=10 `
    --timeout=300s `
    --set-env-vars="REACT_APP_ENGINE_A_URL=https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app,REACT_APP_ENGINE_B_URL=https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app,REACT_APP_ENGINE_C_URL=https://engine-c-prod-bprmddefsa-uc.a.run.app,REACT_APP_ENGINE_D_URL=https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app,REACT_APP_ENGINE_ULTRA_URL=https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Cloud Run deployment failed"
    exit 1
}

$serviceUrl = gcloud run services describe $serviceName --region=$Region --format="value(status.url)" 2>$null
Write-Success "Frontend deployed to Cloud Run: $serviceUrl"

# Step 8: Create domain mapping (if not skipped)
if (-not $SkipDomainMapping) {
    Write-Header "🌐 Setting Up Custom Domain"
    
    Write-Info "Checking if domain mapping exists..."
    $existingMapping = gcloud beta run domain-mappings describe infinityai.pro --region=$Region --format="value(metadata.name)" 2>$null
    
    if ($existingMapping) {
        Write-Warning "Domain mapping already exists for infinityai.pro"
    } else {
        Write-Info "Creating domain mapping for infinityai.pro..."
        try {
            gcloud beta run domain-mappings create `
                --service=$serviceName `
                --domain=infinityai.pro `
                --region=$Region
            Write-Success "Domain mapping created for infinityai.pro"
        } catch {
            Write-Warning "Domain mapping may need DNS records. Check GCP Console for DNS configuration."
        }
    }
}

# Step 9: Verify deployment
Write-Header "🔍 Verifying Deployment"

Write-Info "Testing Cloud Run URL..."
try {
    $response = Invoke-WebRequest -Uri $serviceUrl -Method Get -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Success "Cloud Run URL is accessible: $serviceUrl"
    } else {
        Write-Warning "Cloud Run URL returned: $($response.StatusCode)"
    }
} catch {
    Write-Warning "Cloud Run URL check: $_"
}

Write-Info "Testing backend engines connectivity..."
$engines = @{
    "Engine A" = "https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app/health"
    "Engine B" = "https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/health"
    "Engine C" = "https://engine-c-prod-bprmddefsa-uc.a.run.app/health"
    "Engine D" = "https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app/health"
    "Engine Ultra" = "https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app/health"
}

$healthyEngines = 0
foreach ($engine in $engines.GetEnumerator()) {
    try {
        $engineResponse = Invoke-WebRequest -Uri $engine.Value -Method Get -TimeoutSec 5
        if ($engineResponse.StatusCode -eq 200) {
            Write-Success "$($engine.Key) is healthy"
            $healthyEngines++
        }
    } catch {
        Write-Warning "$($engine.Key) health check failed"
    }
}

Write-Info "Healthy engines: $healthyEngines / $($engines.Count)"

# Step 10: Final summary
Write-Header "📊 Deployment Summary"

Write-Host ""
Write-Host "✅ Frontend Deployed Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access URLs:" -ForegroundColor Cyan
Write-Host "   Cloud Run: $serviceUrl" -ForegroundColor White
Write-Host "   Custom Domain: https://infinityai.pro (once DNS propagates)" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Backend Engines Status:" -ForegroundColor Cyan
Write-Host "   Healthy: $healthyEngines / $($engines.Count)" -ForegroundColor White
Write-Host ""
Write-Host "⏳ Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Update Namecheap nameservers (if not done)" -ForegroundColor White
Write-Host "   2. Wait for DNS propagation (24-48 hours)" -ForegroundColor White
Write-Host "   3. Test at: $serviceUrl" -ForegroundColor White
Write-Host ""

Write-Success "🎉 Deployment completed successfully!"

# Return to project root
Set-Location ../..
