# =====================================================================
# InfinityAI.Pro - Deploy Engine B with Vertex AI Enhanced Integration
# v3.7.7-vertexai - Uses Gemini with function calling for auto-execution
# =====================================================================

param(
    [switch]$DryRun = $false,
    [switch]$SkipBuild = $false,
    [string]$Version = "v3.7.7-vertexai"
)

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "after-yesterday-473512-k3"
$REGION = "us-central1"
$SERVICE_NAME = "engine-b"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/${SERVICE_NAME}:$Version"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host " InfinityAI.Pro - Engine B Deployment ($Version)" -ForegroundColor Cyan
Write-Host " Enhanced with Vertex AI Function Calling" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Step 1: Verify gcloud authentication
Write-Host "`n📋 Step 1: Verifying GCP authentication..." -ForegroundColor Yellow
try {
    $account = gcloud auth list --filter="status:ACTIVE" --format="value(account)" 2>$null
    if (-not $account) {
        Write-Host "❌ No active GCP account. Please run: gcloud auth login" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Authenticated as: $account" -ForegroundColor Green
}
catch {
    Write-Host "❌ gcloud not available. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}

# Step 2: Set project
Write-Host "`n📋 Step 2: Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID 2>$null
Write-Host "✅ Project set to: $PROJECT_ID" -ForegroundColor Green

# Step 3: Build Docker image
if (-not $SkipBuild) {
    Write-Host "`n📋 Step 3: Building Docker image..." -ForegroundColor Yellow
    Write-Host "   Image: $IMAGE_NAME" -ForegroundColor Cyan

    $buildPath = Join-Path $PSScriptRoot "..\backend\engine-core"

    if ($DryRun) {
        Write-Host "[DRY RUN] Would build: docker build -t $IMAGE_NAME $buildPath" -ForegroundColor Magenta
    }
    else {
        Push-Location $buildPath
        try {
            # Build with Cloud Build for faster push
            Write-Host "   Using Cloud Build for faster deployment..." -ForegroundColor Cyan
            gcloud builds submit --tag $IMAGE_NAME --quiet
            if ($LASTEXITCODE -ne 0) {
                throw "Cloud Build failed"
            }
            Write-Host "✅ Image built and pushed: $IMAGE_NAME" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    }
}
else {
    Write-Host "`n📋 Step 3: Skipping build (using existing image)..." -ForegroundColor Yellow
    Write-Host "   Image: $IMAGE_NAME" -ForegroundColor Cyan
}

# Step 4: Deploy to Cloud Run
Write-Host "`n📋 Step 4: Deploying to Cloud Run..." -ForegroundColor Yellow

$deployCmd = @(
    "gcloud", "run", "deploy", $SERVICE_NAME,
    "--image", $IMAGE_NAME,
    "--region", $REGION,
    "--platform", "managed",
    "--allow-unauthenticated",
    "--memory", "4Gi",
    "--cpu", "2",
    "--min-instances", "1",
    "--max-instances", "10",
    "--timeout", "300s",
    "--set-env-vars", "GCP_PROJECT_ID=$PROJECT_ID,ENABLE_VERTEX_AI=true,GEMINI_MODEL=gemini-2.0-flash",
    "--set-secrets", "DHAN_ACCESS_TOKEN=dhan-access-token:latest,GEMINI_API_KEY=gemini-api-key:latest",
    "--labels", "version=$Version,engine=b,features=vertexai-function-calling"
)

if ($DryRun) {
    Write-Host "[DRY RUN] Would run:" -ForegroundColor Magenta
    Write-Host "  $($deployCmd -join ' ')" -ForegroundColor Magenta
}
else {
    Write-Host "   Deploying with Vertex AI enhanced features..." -ForegroundColor Cyan
    & $deployCmd[0] $deployCmd[1..$deployCmd.Length]

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
        exit 1
    }
}

# Step 5: Get service URL
Write-Host "`n📋 Step 5: Getting service URL..." -ForegroundColor Yellow

if (-not $DryRun) {
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>$null
    Write-Host "✅ Service URL: $serviceUrl" -ForegroundColor Green

    # Step 6: Health check
    Write-Host "`n📋 Step 6: Running health check..." -ForegroundColor Yellow

    try {
        $healthResponse = Invoke-RestMethod -Uri "$serviceUrl/health" -Method GET -TimeoutSec 30
        Write-Host "✅ Health check passed!" -ForegroundColor Green
        Write-Host "   Status: $($healthResponse.status)" -ForegroundColor Cyan
        Write-Host "   Version: $($healthResponse.version)" -ForegroundColor Cyan
    }
    catch {
        Write-Host "⚠️ Health check failed (service may still be starting): $_" -ForegroundColor Yellow
    }
}

# Summary
Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host " DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host "`n✅ Engine B deployed successfully!" -ForegroundColor Green
Write-Host @"

Configuration:
  - Project: $PROJECT_ID
  - Region: $REGION
  - Version: $Version
  - Memory: 4GB
  - CPU: 2 vCPU
  - Min Instances: 1

Features Enabled:
  - Vertex AI integration with service account auth
  - Function calling for real-time market data
  - Auto-execution trading signals
  - News sentiment analysis
  - Technical indicator calculation
  - Option chain analysis

Domain Mapping:
  - engine-b.infinityai.pro → $SERVICE_NAME

Next Steps:
  1. Test the Vertex AI integration: GET /api/gemini/test
  2. Generate a trading signal: POST /api/gemini/signal
  3. Get market summary: GET /api/gemini/market-summary

Credits:
  Using GenAI App Builder trial credits (87,000 available)

"@ -ForegroundColor White

Write-Host "🎉 Deployment complete!" -ForegroundColor Green
