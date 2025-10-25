#!/usr/bin/env pwsh

param(
  [Parameter(Mandatory=$false)][string]$ProjectId = "infinity-ai-5ec7c",
  [Parameter(Mandatory=$false)][string]$Region = "us-central1",
  [Parameter(Mandatory=$false)][string]$ImageName = "infinityai-engine-b",
  [Parameter(Mandatory=$false)][string]$Memory = "2Gi",
  [Parameter(Mandatory=$false)][string]$CPU = "2",
  [Parameter(Mandatory=$false)][int]$TimeoutSeconds = 120,
  [Parameter(Mandatory=$false)][int]$Concurrency = 80
)

Write-Host "🚀 Deploying Engine B to Cloud Run (optimized resources)" -ForegroundColor Cyan

# Build container
$root = (Get-Location)
Set-Location "$root/engines/engine-b"
Write-Host "📦 Building container image..." -ForegroundColor Yellow

$tag = "gcr.io/$ProjectId/$ImageName"
gcloud builds submit --tag $tag --project=$ProjectId
if ($LASTEXITCODE -ne 0) {
  Write-Error "Container build failed"
  exit 1
}

# Deploy to Cloud Run with resource flags
Write-Host "🚀 Deploying to Cloud Run with memory=$Memory, cpu=$CPU, timeout=${TimeoutSeconds}s, concurrency=$Concurrency" -ForegroundColor Yellow

gcloud run deploy $ImageName `
  --image $tag `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --memory $Memory `
  --cpu $CPU `
  --timeout $TimeoutSeconds `
  --concurrency $Concurrency `
  --project=$ProjectId

if ($LASTEXITCODE -ne 0) {
  Write-Error "Cloud Run deployment failed"
  exit 1
}

Write-Host "✅ Engine B deployed successfully with optimized resources" -ForegroundColor Green
