#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Rebuild and redeploy all InfinityAI.Pro services to GCP Cloud Run
    
.DESCRIPTION
    This script rebuilds Docker images, pushes them to Artifact Registry,
    and redeploys all services (Engines A/B/C/D/Ultra and Frontend) to Cloud Run
    
.EXAMPLE
    .\redeploy-gcp-all-services.ps1
    .\redeploy-gcp-all-services.ps1 -SkipBuild
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "after-yesterday-473512-k3",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [string]$ArtifactRepo = "infinityai-repo",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "engines", "frontend", "engine-a", "engine-b", "engine-c", "engine-d", "engine-ultra")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Header { param($msg) Write-Host "`n$('=' * 100)`n$msg`n$('=' * 100)" -ForegroundColor Magenta }

Write-Header "🚀 InfinityAI.Pro - Complete GCP Cloud Run Redeploy"
Write-Info "Project: $ProjectId"
Write-Info "Region: $Region"
Write-Info "Artifact Registry: $ArtifactRepo"
Write-Info "Target: $Target"

# Full registry path
$RegistryHost = "us-central1-docker.pkg.dev"
$RegistryPath = "$RegistryHost/$ProjectId/$ArtifactRepo"
$timestamp = Get-Date -Format "yyyyMMddHHmmss"

# Verify GCP authentication
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

# Configure Docker for Artifact Registry
Write-Info "Configuring Docker for Artifact Registry..."
gcloud auth configure-docker $RegistryHost --quiet
Write-Success "Docker configured for Artifact Registry"

# Engine deployment configuration
$engines = @(
    @{
        Name = "engine-a"
        DisplayName = "Engine A (Market Data)"
        Path = "backend/engines/engine-a-market-data"
        ServiceName = "engine-a-market-data-prod"
        ImageName = "engine-a-market-data-prod"
        Port = 8000
        Memory = "1Gi"
        CPU = "1"
        MinInstances = 1
        MaxInstances = 10
        EnvVars = @()
    },
    @{
        Name = "engine-b"
        DisplayName = "Engine B (AI/ML)"
        Path = "backend/engines/engine-b-ai-ml"
        ServiceName = "engine-b-ai-ml-prod"
        ImageName = "engine-b-ai-ml-prod"
        Port = 8001
        Memory = "2Gi"
        CPU = "2"
        MinInstances = 1
        MaxInstances = 10
        EnvVars = @()
    },
    @{
        Name = "engine-c"
        DisplayName = "Engine C (Trade Execution)"
        Path = "backend/engines/engine-c-execution"
        ServiceName = "engine-c-prod"
        ImageName = "engine-c-prod"
        Port = 8002
        Memory = "1Gi"
        CPU = "1"
        MinInstances = 1
        MaxInstances = 10
        EnvVars = @(
            "GCP_PROJECT_ID=$ProjectId",
            "FRONTEND_URL=https://infinityai.pro"
        )
    },
    @{
        Name = "engine-d"
        DisplayName = "Engine D (AI Chatbot)"
        Path = "backend/engines/engine-d-chatbot"
        ServiceName = "engine-d-chatbot-prod"
        ImageName = "engine-d-chatbot-prod"
        Port = 8003
        Memory = "1Gi"
        CPU = "1"
        MinInstances = 1
        MaxInstances = 10
        EnvVars = @(
            "ENGINE_A_URL=https://engine-a-market-data-prod-573866363639.us-central1.run.app",
            "ENGINE_B_URL=https://engine-b-ai-ml-prod-573866363639.us-central1.run.app",
            "ENGINE_C_URL=https://engine-c-prod-573866363639.us-central1.run.app"
        )
    },
    @{
        Name = "engine-ultra"
        DisplayName = "Engine Ultra (Ultra Aggressive)"
        Path = "backend/engines/engine-ultra-aggressive"
        ServiceName = "engine-ultra-aggressive-prod"
        ImageName = "engine-ultra-aggressive-prod"
        Port = 8000
        Memory = "1Gi"
        CPU = "1"
        MinInstances = 1
        MaxInstances = 5
        EnvVars = @()
    }
)

function Deploy-Engine {
    param($Engine)
    
    Write-Header "🔧 Deploying $($Engine.DisplayName)"
    
    # Check if path exists
    if (-not (Test-Path $Engine.Path)) {
        Write-Error "Path not found: $($Engine.Path)"
        return $false
    }
    
    $originalPath = Get-Location
    Set-Location $Engine.Path
    
    try {
        # Build and push image
        if (-not $SkipBuild) {
            $imageName = "$RegistryPath/$($Engine.ImageName):$timestamp"
            $imageNameLatest = "$RegistryPath/$($Engine.ImageName):latest"
            
            Write-Info "Building Docker image: $imageName"
            docker build -t $imageName -t $imageNameLatest . 2>&1 | Out-String | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Docker build failed for $($Engine.DisplayName)"
                return $false
            }
            Write-Success "Image built: $imageName"
            
            Write-Info "Pushing image to Artifact Registry..."
            docker push $imageName 2>&1 | Out-String | Write-Host
            docker push $imageNameLatest 2>&1 | Out-String | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Docker push failed for $($Engine.DisplayName)"
                return $false
            }
            Write-Success "Image pushed: $imageName"
        } else {
            $imageName = "$RegistryPath/$($Engine.ImageName):latest"
            Write-Info "Using existing image: $imageName"
        }
        
        # Deploy to Cloud Run
        Write-Info "Deploying to Cloud Run service: $($Engine.ServiceName)"
        
        $deployArgs = @(
            "run", "deploy", $Engine.ServiceName,
            "--image=$imageName",
            "--platform=managed",
            "--region=$Region",
            "--allow-unauthenticated",
            "--port=$($Engine.Port)",
            "--memory=$($Engine.Memory)",
            "--cpu=$($Engine.CPU)",
            "--min-instances=$($Engine.MinInstances)",
            "--max-instances=$($Engine.MaxInstances)",
            "--timeout=300s",
            "--project=$ProjectId"
        )
        
        # Add environment variables if any
        if ($Engine.EnvVars.Count -gt 0) {
            $envVarString = $Engine.EnvVars -join ","
            $deployArgs += "--set-env-vars=$envVarString"
        }
        
        # Execute deployment
        & gcloud $deployArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Cloud Run deployment failed for $($Engine.DisplayName)"
            return $false
        }
        
        # Get service URL
        $serviceUrl = gcloud run services describe $Engine.ServiceName --region=$Region --format="value(status.url)" --project=$ProjectId 2>$null
        Write-Success "$($Engine.DisplayName) deployed: $serviceUrl"
        
        return $true
    }
    catch {
        Write-Error "Deployment error for $($Engine.DisplayName): $_"
        return $false
    }
    finally {
        Set-Location $originalPath
    }
}

function Deploy-Frontend {
    Write-Header "🌐 Deploying Frontend"
    
    $frontendPath = "frontend/web"
    if (-not (Test-Path $frontendPath)) {
        Write-Error "Frontend path not found: $frontendPath"
        return $false
    }
    
    $originalPath = Get-Location
    Set-Location $frontendPath
    
    try {
        # Build frontend if not skipping
        if (-not $SkipBuild) {
            Write-Info "Installing npm dependencies..."
            npm install --legacy-peer-deps 2>&1 | Out-String | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "npm install failed"
                return $false
            }
            Write-Success "Dependencies installed"
            
            Write-Info "Building production bundle..."
            $env:REACT_APP_ENGINE_A_URL = "https://infinityai.pro/api/engine-a"
            $env:REACT_APP_ENGINE_B_URL = "https://infinityai.pro/api/engine-b"
            $env:REACT_APP_ENGINE_C_URL = "https://infinityai.pro/api/engine-c"
            $env:REACT_APP_ENGINE_D_URL = "https://infinityai.pro/api/engine-d"
            $env:REACT_APP_ENGINE_ULTRA_URL = "https://infinityai.pro/api/engine-ultra"
            
            npm run build 2>&1 | Out-String | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "npm build failed"
                return $false
            }
            Write-Success "Production build completed"
            
            # Build Docker image
            $imageName = "$RegistryPath/infinityai-frontend:$timestamp"
            $imageNameLatest = "$RegistryPath/infinityai-frontend:latest"
            
            Write-Info "Building Docker image: $imageName"
            docker build -t $imageName -t $imageNameLatest . 2>&1 | Out-String | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Docker build failed for frontend"
                return $false
            }
            Write-Success "Image built: $imageName"
            
            Write-Info "Pushing image to Artifact Registry..."
            docker push $imageName 2>&1 | Out-String | Write-Host
            docker push $imageNameLatest 2>&1 | Out-String | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Docker push failed for frontend"
                return $false
            }
            Write-Success "Image pushed: $imageName"
        } else {
            $imageName = "$RegistryPath/infinityai-frontend:latest"
            Write-Info "Using existing image: $imageName"
        }
        
        # Deploy to Cloud Run
        Write-Info "Deploying to Cloud Run service: infinityai-frontend"
        
        gcloud run deploy infinityai-frontend `
            --image=$imageName `
            --platform=managed `
            --region=$Region `
            --allow-unauthenticated `
            --port=8080 `
            --memory=1Gi `
            --cpu=1 `
            --min-instances=1 `
            --max-instances=10 `
            --timeout=300s `
            --project=$ProjectId
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Cloud Run deployment failed for frontend"
            return $false
        }
        
        # Get service URL
        $serviceUrl = gcloud run services describe infinityai-frontend --region=$Region --format="value(status.url)" --project=$ProjectId 2>$null
        Write-Success "Frontend deployed: $serviceUrl"
        
        return $true
    }
    catch {
        Write-Error "Frontend deployment error: $_"
        return $false
    }
    finally {
        Set-Location $originalPath
    }
}

# Main deployment logic
$deploymentResults = @{}

if ($Target -eq "all" -or $Target -eq "engines") {
    Write-Header "📦 Deploying All Engines"
    foreach ($engine in $engines) {
        $result = Deploy-Engine -Engine $engine
        $deploymentResults[$engine.Name] = $result
    }
}
elseif ($Target -eq "frontend") {
    $result = Deploy-Frontend
    $deploymentResults["frontend"] = $result
}
elseif ($Target -match "^engine-") {
    # Deploy specific engine
    $engineToDeploy = $engines | Where-Object { $_.Name -eq $Target }
    if ($engineToDeploy) {
        $result = Deploy-Engine -Engine $engineToDeploy
        $deploymentResults[$Target] = $result
    } else {
        Write-Error "Engine not found: $Target"
        exit 1
    }
}
else {
    # Deploy everything
    Write-Header "📦 Deploying All Engines"
    foreach ($engine in $engines) {
        $result = Deploy-Engine -Engine $engine
        $deploymentResults[$engine.Name] = $result
    }
    
    Write-Header "🌐 Deploying Frontend"
    $result = Deploy-Frontend
    $deploymentResults["frontend"] = $result
}

# Summary
Write-Header "📊 Deployment Summary"
Write-Host ""
$successCount = 0
$failCount = 0

foreach ($service in $deploymentResults.GetEnumerator()) {
    if ($service.Value) {
        Write-Success "$($service.Key): Deployed successfully"
        $successCount++
    } else {
        Write-Error "$($service.Key): Deployment failed"
        $failCount++
    }
}

Write-Host ""
Write-Info "Total: $($deploymentResults.Count) | Success: $successCount | Failed: $failCount"

if ($failCount -eq 0) {
    Write-Success "🎉 All services deployed successfully!"
    Write-Host ""
    Write-Info "Access your platform at: https://infinityai.pro"
    Write-Host ""
} else {
    Write-Warning "⚠️  Some deployments failed. Review the logs above."
    exit 1
}
