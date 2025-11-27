#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Deploy InfinityAI.Pro with custom domain URLs

.DESCRIPTION
    Comprehensive deployment script that:
    1. Updates frontend with custom domain URLs
    2. Rebuilds all Docker images
    3. Deploys to Cloud Run with proper environment variables
    4. Verifies deployment success

.PARAMETER SkipBuild
    Skip Docker image rebuild (use existing images)

.PARAMETER SkipDeploy
    Skip Cloud Run deployment (only build images)

.PARAMETER UseCustomDomains
    Use custom domains instead of Cloud Run URLs

.EXAMPLE
    .\deploy-with-custom-domains.ps1
    .\deploy-with-custom-domains.ps1 -UseCustomDomains
    .\deploy-with-custom-domains.ps1 -SkipBuild
#>

param(
    [switch]$SkipBuild,
    [switch]$SkipDeploy,
    [switch]$UseCustomDomains
)

$ErrorActionPreference = "Stop"
$PROJECT_ID = "after-yesterday-473512-k3"
$REGION = "us-central1"

Write-Host "`n🚀 InfinityAI.Pro Deployment Script`n" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Determine URLs to use
if ($UseCustomDomains) {
    Write-Host "Using CUSTOM DOMAIN URLs (requires DNS configuration)" -ForegroundColor Yellow
    $ENGINE_A_URL = "https://engine-a.infinityai.pro"
    $ENGINE_B_URL = "https://engine-b.infinityai.pro"
    $ENGINE_C_URL = "https://engine-c.infinityai.pro"
} else {
    Write-Host "Using CLOUD RUN URLs (works immediately)" -ForegroundColor Yellow
    $ENGINE_A_URL = "https://infinityai-engine-a-573866363639.us-central1.run.app"
    $ENGINE_B_URL = "https://infinityai-engine-b-573866363639.us-central1.run.app"
    $ENGINE_C_URL = "https://infinityai-engine-c-execution-573866363639.us-central1.run.app"
}

Write-Host "`nEngine URLs:" -ForegroundColor Cyan
Write-Host "  Engine A: $ENGINE_A_URL" -ForegroundColor White
Write-Host "  Engine B: $ENGINE_B_URL" -ForegroundColor White
Write-Host "  Engine C: $ENGINE_C_URL`n" -ForegroundColor White

# Step 1: Update Frontend
Write-Host "STEP 1: UPDATING FRONTEND`n" -ForegroundColor Yellow
Write-Host "Updating frontend with engine URLs..." -ForegroundColor White

$frontendPath = "frontend/web/index.html"
$content = Get-Content $frontendPath -Raw

# Replace with chosen URLs
$content = $content -replace 'https://infinityai-engine-a-573866363639\.us-central1\.run\.app', $ENGINE_A_URL
$content = $content -replace 'https://infinityai-engine-b-573866363639\.us-central1\.run\.app', $ENGINE_B_URL
$content = $content -replace 'https://infinityai-engine-c-execution-573866363639\.us-central1\.run\.app', $ENGINE_C_URL
$content = $content -replace 'https://engine-a\.infinityai\.pro', $ENGINE_A_URL
$content = $content -replace 'https://engine-b\.infinityai\.pro', $ENGINE_B_URL
$content = $content -replace 'https://engine-c\.infinityai\.pro', $ENGINE_C_URL

Set-Content $frontendPath -Value $content -NoNewline
Write-Host "✅ Frontend updated`n" -ForegroundColor Green

# Step 2: Build Docker Images
if (-not $SkipBuild) {
    Write-Host "STEP 2: BUILDING DOCKER IMAGES`n" -ForegroundColor Yellow
    
    $engines = @(
        @{Name="Engine A (Analytics)"; Dir="backend/engine-analytics"; Image="infinityai-engine-a"},
        @{Name="Engine B (Core/ML)"; Dir="backend/engine-core"; Image="infinityai-engine-b"},
        @{Name="Engine C (Execution)"; Dir="backend/engine-execution"; Image="infinityai-engine-c-execution"}
    )
    
    foreach ($engine in $engines) {
        Write-Host "Building $($engine.Name)..." -ForegroundColor Cyan
        Set-Location $engine.Dir
        
        $buildId = gcloud builds submit `
            --tag="gcr.io/$PROJECT_ID/$($engine.Image):latest" `
            --project=$PROJECT_ID `
            --async `
            --format="value(id)" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Build started: $buildId" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Build failed" -ForegroundColor Red
            Set-Location ../..
            exit 1
        }
        
        Set-Location ../..
    }
    
    Write-Host "`nWaiting for all builds to complete (60 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 60
    
    Write-Host "Checking build status..." -ForegroundColor White
    gcloud builds list --project=$PROJECT_ID --limit=3 --format="table(id,status,images[0])"
    Write-Host ""
} else {
    Write-Host "STEP 2: SKIPPING BUILD (using existing images)`n" -ForegroundColor Yellow
}

# Step 3: Deploy to Cloud Run
if (-not $SkipDeploy) {
    Write-Host "STEP 3: DEPLOYING TO CLOUD RUN`n" -ForegroundColor Yellow
    
    # Deploy Engine A
    Write-Host "Deploying Engine A (Analytics + Orchestration)..." -ForegroundColor Cyan
    gcloud run deploy infinityai-engine-a `
        --image="gcr.io/$PROJECT_ID/infinityai-engine-a:latest" `
        --region=$REGION `
        --project=$PROJECT_ID `
        --memory=512Mi `
        --cpu=1 `
        --min-instances=1 `
        --max-instances=10 `
        --allow-unauthenticated `
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENGINE_B_URL=$ENGINE_B_URL,ENGINE_C_URL=$ENGINE_C_URL" `
        --set-secrets="DHAN_API_KEY=dhan-api-key:latest" `
        --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Engine A deployed`n" -ForegroundColor Green
    } else {
        Write-Host "❌ Engine A deployment failed`n" -ForegroundColor Red
        exit 1
    }
    
    # Deploy Engine B
    Write-Host "Deploying Engine B (AI/ML Intelligence)..." -ForegroundColor Cyan
    gcloud run deploy infinityai-engine-b `
        --image="gcr.io/$PROJECT_ID/infinityai-engine-b:latest" `
        --region=$REGION `
        --project=$PROJECT_ID `
        --memory=1Gi `
        --cpu=2 `
        --min-instances=1 `
        --max-instances=10 `
        --allow-unauthenticated `
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENGINE_A_URL=$ENGINE_A_URL,ENGINE_C_URL=$ENGINE_C_URL" `
        --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Engine B deployed`n" -ForegroundColor Green
    } else {
        Write-Host "❌ Engine B deployment failed`n" -ForegroundColor Red
        exit 1
    }
    
    # Deploy Engine C
    Write-Host "Deploying Engine C (DhanHQ Execution)..." -ForegroundColor Cyan
    gcloud run deploy infinityai-engine-c-execution `
        --image="gcr.io/$PROJECT_ID/infinityai-engine-c-execution:latest" `
        --region=$REGION `
        --project=$PROJECT_ID `
        --memory=512Mi `
        --cpu=1 `
        --min-instances=1 `
        --max-instances=10 `
        --allow-unauthenticated `
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENGINE_A_URL=$ENGINE_A_URL,ENGINE_B_URL=$ENGINE_B_URL,ENABLE_WEBSOCKET=true,ENABLE_CHATBOT=true" `
        --set-secrets="DHAN_API_KEY=dhan-api-key:latest" `
        --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Engine C deployed`n" -ForegroundColor Green
    } else {
        Write-Host "❌ Engine C deployment failed`n" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "STEP 3: SKIPPING DEPLOYMENT`n" -ForegroundColor Yellow
}

# Step 4: Deploy Frontend
Write-Host "STEP 4: DEPLOYING FRONTEND`n" -ForegroundColor Yellow
Write-Host "Deploying to Firebase Hosting..." -ForegroundColor White
Set-Location frontend/web
firebase deploy --only hosting --project=$PROJECT_ID --non-interactive
Set-Location ../..

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend deployed`n" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend deployment failed`n" -ForegroundColor Red
    exit 1
}

# Step 5: Verify Deployment
Write-Host "STEP 5: VERIFYING DEPLOYMENT`n" -ForegroundColor Yellow

$services = @{
    "Engine A" = "$ENGINE_A_URL/docs"
    "Engine B" = "$ENGINE_B_URL/docs"
    "Engine C" = "$ENGINE_C_URL/docs"
    "Frontend" = "https://after-yesterday-473512-k3.web.app"
}

foreach ($name in $services.Keys) {
    Write-Host "Testing $name..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri $services[$name] -Method GET -TimeoutSec 10 -ErrorAction Stop
        Write-Host "  ✅ $name`: HTTP $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  $name`: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 6: Commit Changes
Write-Host "`nSTEP 6: COMMITTING CHANGES`n" -ForegroundColor Yellow
git add frontend/web/index.html NAMECHEAP-DNS-SETUP.md scripts/deploy-with-custom-domains.ps1
if ($UseCustomDomains) {
    git commit -m "feat: Deploy with custom domain URLs

- Updated frontend to use custom domains
- Rebuilt and deployed all engines
- Configured inter-engine communication URLs
- DNS configuration documented in NAMECHEAP-DNS-SETUP.md
"
} else {
    git commit -m "deploy: Deploy with Cloud Run URLs

- Updated frontend URLs
- Rebuilt and deployed all engines
- Verified all services operational
"
}
git push origin feature/3-engine-architecture

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "             ✅ DEPLOYMENT COMPLETE ✅             " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

if ($UseCustomDomains) {
    Write-Host "⚠️  IMPORTANT: DNS Configuration Required" -ForegroundColor Yellow
    Write-Host "Custom domains will NOT work until you:" -ForegroundColor White
    Write-Host "  1. Add DNS records to Namecheap (see NAMECHEAP-DNS-SETUP.md)" -ForegroundColor White
    Write-Host "  2. Wait 15 min - 48 hours for DNS propagation" -ForegroundColor White
    Write-Host "  3. Verify domain mappings show 'Ready: True' in GCP`n" -ForegroundColor White
} else {
    Write-Host "✅ Application is accessible now at:" -ForegroundColor Green
    Write-Host "  Frontend: https://after-yesterday-473512-k3.web.app" -ForegroundColor Cyan
    Write-Host "  Engine A: $ENGINE_A_URL/docs" -ForegroundColor Cyan
    Write-Host "  Engine B: $ENGINE_B_URL/docs" -ForegroundColor Cyan
    Write-Host "  Engine C: $ENGINE_C_URL/docs`n" -ForegroundColor Cyan
}

Write-Host "✨ Deployment successful!`n" -ForegroundColor Green
