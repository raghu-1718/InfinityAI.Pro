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

Write-Host "InfinityAI.Pro - 3-Engine Architecture Deployment" -ForegroundColor Cyan
Write-Host "================================================================================"

$PROJECT_ID = gcloud config get-value project
if (-not $PROJECT_ID) {
    $PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
}
if (-not $PROJECT_ID) {
    Write-Error "Project ID not set. Run 'gcloud config set project <PROJECT_ID>' or set GOOGLE_CLOUD_PROJECT env var."
    exit 1
}
$REGION = "us-central1"
$ENGINES = @("engine-a", "engine-b", "engine-c")

if ($ProductionMode) {
    Write-Host "PRODUCTION MODE: Requires min-instances=1 for all engines" -ForegroundColor Yellow
    Write-Host "   This requires 10+ CPUs total." -ForegroundColor Yellow
    Write-Host "   Ensure you have increased your quota." -ForegroundColor Yellow
}

# Configuration based on mode
$config = if ($ProductionMode) {
    @{
        "engine-a" = @{
            memory       = "512Mi"
            cpu          = 1
            minInstances = 1
            maxInstances = 10
            timeout      = 300
        }
        "engine-b" = @{
            memory       = "1Gi"
            cpu          = 2
            minInstances = 1
            maxInstances = 5
            timeout      = 300
        }
        "engine-c" = @{
            memory       = "512Mi"  # Increased for WebSocket support
            cpu          = 1
            minInstances = 1  # Always-on for WebSocket connections
            maxInstances = 10
            timeout      = 300
        }
    }
}
else {
    Write-Host "ON-DEMAND MODE: min-instances=0 to stay within quota" -ForegroundColor Yellow
    Write-Host "   Note: This may cause 3-5 second cold start delays" -ForegroundColor Yellow
    @{
        "engine-a" = @{
            memory       = "512Mi"
            cpu          = 1
            minInstances = 0
            maxInstances = 10
            timeout      = 300
        }
        "engine-b" = @{
            memory       = "1Gi"
            cpu          = 2
            minInstances = 0
            maxInstances = 5
            timeout      = 300
        }
        "engine-c" = @{
            memory       = "512Mi"
            cpu          = 1
            minInstances = 0
            maxInstances = 10
            timeout      = 300
        }
    }
}

# Deploy engines
Write-Host "`nDeploying Engines..." -ForegroundColor Cyan
foreach ($engine in $ENGINES) {
    Write-Host "`nDeploying $engine..." -ForegroundColor Yellow

    $engineConfig = $config[$engine]
    $enginePath = "backend/$engine"

    if (-not (Test-Path $enginePath)) {
        Write-Host "Engine directory not found: $enginePath" -ForegroundColor Red
        continue
    }

    Push-Location $enginePath

    # Build container (skip if flag set)
    if (-not $SkipBuild) {
        Write-Host "  Building container..." -ForegroundColor Gray
        # Using cmd /c to ensure proper execution of gcloud command if powershell has issues
        cmd /c "gcloud builds submit --quiet --tag gcr.io/$PROJECT_ID/infinityai-$engine --project=$PROJECT_ID"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Build failed for $engine" -ForegroundColor Red
            Pop-Location
            continue
        }
        Write-Host "  Build complete" -ForegroundColor Green
    }

    # Deploy to Cloud Run
    Write-Host "  Deploying to Cloud Run..." -ForegroundColor Gray
    
    # Construct args manually to avoid array issues
    $envVars = "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    if ($engine -eq "engine-c") {
        $envVars += ",ENABLE_WEBSOCKET=true,ENABLE_CHATBOT=true,ENABLE_HEALTH_ORCHESTRATOR=true"
    }

    $minInst = $engineConfig.minInstances
    $maxInst = $engineConfig.maxInstances
    $mem = $engineConfig.memory
    $timeout = $engineConfig.timeout
    $cpu = $engineConfig.cpu

    cmd /c "gcloud run deploy $engine --quiet --image gcr.io/$PROJECT_ID/infinityai-$engine --region $REGION --project $PROJECT_ID --platform managed --allow-unauthenticated --memory $mem --cpu $cpu --min-instances $minInst --max-instances $maxInst --timeout ${timeout}s --set-env-vars $envVars"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $engine deployed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "  Deployment failed for $engine" -ForegroundColor Red
    }

    Pop-Location
}

# Deploy Frontend
Write-Host "`nDeploying Frontend..." -ForegroundColor Cyan
Push-Location "frontend/web-app"

if (-not $SkipBuild) {
    Write-Host "  Building frontend..." -ForegroundColor Gray
    cmd /c "npm run build"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Frontend build failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

Write-Host "  Deploying to Firebase Hosting..." -ForegroundColor Gray
cmd /c "firebase deploy --only hosting --project $PROJECT_ID --token \"$env:FIREBASE_TOKEN\""

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Frontend deployed successfully" -ForegroundColor Green
}
else {
    Write-Host "  Frontend deployment failed" -ForegroundColor Red
}

Pop-Location

# Summary
Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host ""
