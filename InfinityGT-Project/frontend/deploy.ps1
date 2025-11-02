#!/usr/bin/env pwsh
# InfinityAI.Pro Frontend Deployment Script
# Deploys the React+Vite frontend to Google Cloud Run

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "after-yesterday-473512-k3",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "infinityai-frontend",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "4.0.0"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   InfinityAI.Pro Frontend Deployment   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if in correct directory
if (!(Test-Path "package.json")) {
    Write-Host "❌ Error: Must run from frontend-new directory" -ForegroundColor Red
    exit 1
}

# Step 1: Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ npm install failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 2: Build the application
Write-Host "🏗️  Building production bundle..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Build successful" -ForegroundColor Green
Write-Host ""

# Step 3: Build Docker image and push to GCR
$imageTag = "gcr.io/${ProjectId}/${ServiceName}:v${Version}"
$imageLatest = "gcr.io/${ProjectId}/${ServiceName}:latest"

Write-Host "🐳 Building and pushing Docker image..." -ForegroundColor Yellow
Write-Host "   Image: $imageTag" -ForegroundColor Cyan

gcloud builds submit --tag $imageTag --project $ProjectId
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker image built and pushed" -ForegroundColor Green
Write-Host ""

# Also tag as latest
gcloud container images add-tag $imageTag $imageLatest --project $ProjectId --quiet

# Step 4: Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "   Service: $ServiceName" -ForegroundColor Cyan
Write-Host "   Region: $Region" -ForegroundColor Cyan

gcloud run deploy $ServiceName `
    --image $imageTag `
    --platform managed `
    --region $Region `
    --project $ProjectId `
    --allow-unauthenticated `
    --port 8080 `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --set-env-vars "NODE_ENV=production"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ✅ Deployment Successful!           " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get service URL
$serviceUrl = gcloud run services describe $ServiceName `
    --platform managed `
    --region $Region `
    --project $ProjectId `
    --format 'value(status.url)'

Write-Host "🌐 Service URL: $serviceUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Check deployment status:" -ForegroundColor Yellow
Write-Host "   gcloud run services describe $ServiceName --region=$Region --project=$ProjectId" -ForegroundColor Gray
Write-Host ""
Write-Host "🔍 View logs:" -ForegroundColor Yellow
Write-Host "   gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName' --limit=50 --project=$ProjectId" -ForegroundColor Gray
Write-Host ""
