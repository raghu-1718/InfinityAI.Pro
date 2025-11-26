#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy 3-Engine Architecture with CPU quota management
.DESCRIPTION
    Handles deployment of InfinityAI.Pro with 3 engines (Analytics, Core, Execution)
    after Engine D migration. Manages CPU quota constraints intelligently.
.NOTES
    Author: InfinityAI.Pro Team
    Date: January 2025
    Prerequisites: gcloud CLI, Firebase CLI, appropriate IAM permissions
#>

param(
    [switch]$SkipBuild,
    [switch]$OnDemandMode,  # Deploy with min-instances=0 to stay within 6 CPU quota
    [switch]$ProductionMode  # Deploy with min-instances=1 (requires CPU quota increase)
)

Write-Host "🚀 InfinityAI.Pro - 3-Engine Architecture Deployment" -ForegroundColor Cyan
Write-Host "=" * 80

$PROJECT_ID = "infinity-ai-5ec7c"
$REGION = "us-central1"
$ENGINES = @("engine-a", "engine-b", "engine-c-execution")

# Check current CPU quota
Write-Host "`n🔍 Checking CPU quota..." -ForegroundColor Yellow
$quotaCheck = gcloud compute project-info describe --project=$PROJECT_ID --format="value(quotas.filter(metric:CPUS).filter(region:$REGION))" 2>&1

if ($ProductionMode) {
    Write-Host "⚠️  PRODUCTION MODE: Requires min-instances=1 for all engines" -ForegroundColor Yellow
    Write-Host "   This requires 10+ CPUs total. Current quota: 6 CPUs" -ForegroundColor Yellow
    Write-Host "   " -ForegroundColor Yellow
    Write-Host "   To increase quota:" -ForegroundColor White
    Write-Host "   1. Go to: https://console.cloud.google.com/iam-admin/quotas?project=$PROJECT_ID" -ForegroundColor Cyan
    Write-Host "   2. Search for: 'CPUs us-central1'" -ForegroundColor Cyan
    Write-Host "   3. Request increase to: 10 CPUs" -ForegroundColor Cyan
    Write-Host "   4. Justification: 'Production deployment with WebSocket support'" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Have you increased the CPU quota to 10+? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "❌ Deployment cancelled. Run with -OnDemandMode flag to deploy within current quota." -ForegroundColor Red
        exit 1
    }
}

# Configuration based on mode
$config = if ($ProductionMode) {
    @{
        "engine-a" = @{
            memory = "512Mi"
            cpu = 1
            minInstances = 1
            maxInstances = 10
            timeout = 300
        }
        "engine-b" = @{
            memory = "1Gi"
            cpu = 2
            minInstances = 1
            maxInstances = 5
            timeout = 300
        }
        "engine-c-execution" = @{
            memory = "512Mi"  # Increased for WebSocket support
            cpu = 1
            minInstances = 1  # Always-on for WebSocket connections
            maxInstances = 10
            timeout = 300
        }
    }
} else {
    Write-Host "📊 ON-DEMAND MODE: min-instances=0 to stay within 6 CPU quota" -ForegroundColor Yellow
    Write-Host "   Note: This may cause 3-5 second cold start delays" -ForegroundColor Yellow
    @{
        "engine-a" = @{
            memory = "512Mi"
            cpu = 1
            minInstances = 0  # On-demand to save CPUs
            maxInstances = 10
            timeout = 300
        }
        "engine-b" = @{
            memory = "1Gi"
            cpu = 2
            minInstances = 0  # On-demand to save CPUs
            maxInstances = 5
            timeout = 300
        }
        "engine-c-execution" = @{
            memory = "512Mi"
            cpu = 1
            minInstances = 0  # On-demand (WebSocket may disconnect)
            maxInstances = 10
            timeout = 300
        }
    }
}

# Deploy engines
Write-Host "`n🔧 Deploying Engines..." -ForegroundColor Cyan
foreach ($engine in $ENGINES) {
    Write-Host "`n📦 Deploying $engine..." -ForegroundColor Yellow
    
    $engineConfig = $config[$engine]
    $enginePath = "backend/$engine"
    
    if (-not (Test-Path $enginePath)) {
        Write-Host "❌ Engine directory not found: $enginePath" -ForegroundColor Red
        continue
    }
    
    Set-Location $enginePath
    
    # Build container (skip if flag set)
    if (-not $SkipBuild) {
        Write-Host "  🏗️  Building container..." -ForegroundColor Gray
        $buildResult = gcloud builds submit --tag "gcr.io/$PROJECT_ID/infinityai-$engine" --project=$PROJECT_ID 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ❌ Build failed for $engine" -ForegroundColor Red
            Write-Host $buildResult
            Set-Location $PSScriptRoot
            continue
        }
        Write-Host "  ✅ Build complete" -ForegroundColor Green
    }
    
    # Deploy to Cloud Run
    Write-Host "  🚀 Deploying to Cloud Run..." -ForegroundColor Gray
    $deployArgs = @(
        "run", "deploy", "infinityai-$engine",
        "--image", "gcr.io/$PROJECT_ID/infinityai-$engine",
        "--region", $REGION,
        "--project", $PROJECT_ID,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--memory", $engineConfig.memory,
        "--cpu", $engineConfig.cpu.ToString(),
        "--min-instances", $engineConfig.minInstances.ToString(),
        "--max-instances", $engineConfig.maxInstances.ToString(),
        "--timeout", "$($engineConfig.timeout)s",
        "--set-env-vars", "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    )
    
    # Add Engine C specific configurations
    if ($engine -eq "engine-c-execution") {
        $deployArgs += "--set-env-vars"
        $deployArgs += "ENABLE_WEBSOCKET=true,ENABLE_CHATBOT=true,ENABLE_HEALTH_ORCHESTRATOR=true"
    }
    
    $deployResult = & gcloud @deployArgs 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $engine deployed successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Deployment failed for $engine" -ForegroundColor Red
        Write-Host $deployResult
    }
    
    Set-Location $PSScriptRoot
}

# Deploy Frontend
Write-Host "`n🌐 Deploying Frontend..." -ForegroundColor Cyan
Set-Location "frontend/web"

if (-not $SkipBuild) {
    Write-Host "  📦 Building frontend..." -ForegroundColor Gray
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Frontend build failed" -ForegroundColor Red
        Set-Location $PSScriptRoot
        exit 1
    }
}

Write-Host "  🚀 Deploying to Firebase Hosting..." -ForegroundColor Gray
firebase deploy --only hosting --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Frontend deployed successfully" -ForegroundColor Green
} else {
    Write-Host "  ❌ Frontend deployment failed" -ForegroundColor Red
}

Set-Location $PSScriptRoot

# Health check
Write-Host "`n🏥 Running Health Checks..." -ForegroundColor Cyan
Start-Sleep -Seconds 10  # Wait for services to stabilize

$healthChecks = @{
    "Engine A (Analytics)" = "https://infinityai-engine-a-573866363639.us-central1.run.app/health"
    "Engine B (Core)" = "https://infinityai-engine-b-573866363639.us-central1.run.app/health"
    "Engine C (Execution)" = "https://infinityai-engine-c-execution-26140490557.us-central1.run.app/health"
    "Frontend" = "https://infinityai.pro"
}

foreach ($service in $healthChecks.Keys) {
    $url = $healthChecks[$service]
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ $service: OK" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  $service: HTTP $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ $service: Failed - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host ""

if ($OnDemandMode) {
    Write-Host "⚠️  ON-DEMAND MODE ACTIVE" -ForegroundColor Yellow
    Write-Host "   - Engines will scale to zero when idle" -ForegroundColor White
    Write-Host "   - Cold start latency: 3-5 seconds" -ForegroundColor White
    Write-Host "   - WebSocket may disconnect during idle periods" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 To enable production mode (min-instances=1):" -ForegroundColor Cyan
    Write-Host "   1. Request CPU quota increase to 10+ CPUs" -ForegroundColor White
    Write-Host "   2. Re-run: .\scripts\deploy-3-engine-architecture.ps1 -ProductionMode" -ForegroundColor White
}

Write-Host "`n📊 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Test WebSocket: Open https://infinityai.pro and check DevTools → Network → WS" -ForegroundColor White
Write-Host "  2. Verify all engines: .\scripts\verify-backend.ps1" -ForegroundColor White
Write-Host "  3. Monitor logs: gcloud logs tail --project=$PROJECT_ID" -ForegroundColor White
Write-Host "  4. Review migration: See MIGRATION_ENGINE_D_TO_C.md" -ForegroundColor White

Write-Host "`n🔗 Service URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: https://infinityai.pro" -ForegroundColor White
Write-Host "  Engine A: https://infinityai-engine-a-573866363639.us-central1.run.app" -ForegroundColor White
Write-Host "  Engine B: https://infinityai-engine-b-573866363639.us-central1.run.app" -ForegroundColor White
Write-Host "  Engine C: https://infinityai-engine-c-execution-26140490557.us-central1.run.app" -ForegroundColor White
Write-Host "  WebSocket: wss://infinityai-engine-c-execution-26140490557.us-central1.run.app/ws/dashboard" -ForegroundColor White
