#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Create all 4 InfinityAI engine services on Northflank
.DESCRIPTION
    Creates Engine A, B, C (execution), and D services in the infinity-ai project
    Links them to the GitHub repository and sets up build configuration
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ApiToken = $env:NORTHFLANK_API_TOKEN,
    
    [Parameter(Mandatory=$false)]
    [string]$Project = "infinity-ai",
    
    [Parameter(Mandatory=$false)]
    [string]$GitHubRepo = "raghu-1718/InfinityAI.Pro",
    
    [Parameter(Mandatory=$false)]
    [string]$Branch = "recovery/v4.6-stabilization"
)

if (-not $ApiToken) {
    Write-Error "NORTHFLANK_API_TOKEN not set. Please set it in environment or pass via -ApiToken parameter."
    exit 1
}

$BaseUrl = "https://api.northflank.com/v1"
$Headers = @{
    'Authorization' = "Bearer $ApiToken"
    'Content-Type' = 'application/json'
}

Write-Host "`n=== Creating Northflank Services for InfinityAI ===" -ForegroundColor Cyan

# Service definitions
$services = @(
    @{
        id = "engine-a"
        name = "Engine A - Market Data"
        description = "Market data ingestion with real-time NSE/BSE feeds"
        buildpack = "dockerfile"
        dockerfilePath = "engines/engine-a/Dockerfile"
        dockerBuildContext = "engines/engine-a"
        port = 8080
    },
    @{
        id = "engine-b"
        name = "Engine B - AI/ML"
        description = "AI/ML processing with TensorFlow predictions"
        buildpack = "dockerfile"
        dockerfilePath = "engines/engine-b/Dockerfile"
        dockerBuildContext = "engines/engine-b"
        port = 8080
    },
    @{
        id = "engine-c-execution"
        name = "Engine C - Execution"
        description = "Trade execution with Dhan OAuth and risk management"
        buildpack = "dockerfile"
        dockerfilePath = "engines/engine-c-execution/Dockerfile"
        dockerBuildContext = "engines/engine-c-execution"
        port = 8080
    },
    @{
        id = "engine-d"
        name = "Engine D - Orchestrator"
        description = "AI chatbot orchestrator with WebSocket coordination"
        buildpack = "dockerfile"
        dockerfilePath = "engines/engine-d/Dockerfile"
        dockerBuildContext = "engines/engine-d"
        port = 8080
    }
)

foreach ($svc in $services) {
    Write-Host "`nCreating service: $($svc.name) (ID: $($svc.id))..." -ForegroundColor Yellow
    
    $body = @{
        name = $svc.name
        description = $svc.description
        projectId = $Project
        spec = @{
            type = "deployment"
            deployment = @{
                instances = 1
                docker = @{
                    configType = "customCommand"
                    customCommand = "python main.py"
                }
                storage = @{
                    ephemeralStorage = @{
                        storageSize = 1024
                    }
                }
            }
            vcsData = @{
                projectUrl = "https://github.com/$GitHubRepo"
                projectType = "github"
                accountLogin = ($GitHubRepo -split '/')[0]
                projectId = [int64]0  # Will be auto-detected
            }
            buildSettings = @{
                dockerfile = @{
                    buildEngine = "kaniko"
                    dockerFilePath = $svc.dockerfilePath
                    dockerWorkDir = $svc.dockerBuildContext
                    useCache = $true
                }
            }
            runtimeEnvironment = @{}
            buildArguments = @{}
            runtimeFiles = @{}
        }
        billing = @{
            deploymentPlan = "nf-compute-20"  # Adjust based on your plan
        }
    } | ConvertTo-Json -Depth 10

    try {
        $response = Invoke-RestMethod -Method POST `
            -Uri "$BaseUrl/projects/$Project/services/combined" `
            -Headers $Headers `
            -Body $body `
            -ErrorAction Stop
        
        Write-Host "  ✓ Created: $($svc.id)" -ForegroundColor Green
        Write-Host "    Service ID: $($response.data.id)" -ForegroundColor Gray
        
    } catch {
        $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($errorDetail.message -match "already exists") {
            Write-Host "  ⚠ Service $($svc.id) already exists, skipping..." -ForegroundColor Yellow
        } else {
            Write-Host "  ✗ Error creating $($svc.id): $($errorDetail.message)" -ForegroundColor Red
            Write-Host "    Full error: $_" -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n=== Retrieving Service IDs for GitHub Secrets ===" -ForegroundColor Cyan

try {
    $allServices = Invoke-RestMethod -Method GET `
        -Uri "$BaseUrl/projects/$Project/services" `
        -Headers $Headers `
        -ErrorAction Stop
    
    Write-Host "`nService IDs to add to GitHub Secrets:" -ForegroundColor White
    Write-Host "======================================" -ForegroundColor White
    
    $serviceMap = @{
        "engine-a" = "NF_SERVICE_ENGINE_A"
        "engine-b" = "NF_SERVICE_ENGINE_B"
        "engine-c-execution" = "NF_SERVICE_ENGINE_C"
        "engine-d" = "NF_SERVICE_ENGINE_D"
    }
    
    foreach ($svc in $allServices.data.services) {
        if ($serviceMap.ContainsKey($svc.id)) {
            $secretName = $serviceMap[$svc.id]
            Write-Host "$secretName=$($svc.id)" -ForegroundColor Cyan
        }
    }
    
    Write-Host "`nTo set these secrets automatically, run:" -ForegroundColor Yellow
    Write-Host "  gh secret set NF_SERVICE_ENGINE_A --body 'engine-a'" -ForegroundColor Gray
    Write-Host "  gh secret set NF_SERVICE_ENGINE_B --body 'engine-b'" -ForegroundColor Gray
    Write-Host "  gh secret set NF_SERVICE_ENGINE_C --body 'engine-c-execution'" -ForegroundColor Gray
    Write-Host "  gh secret set NF_SERVICE_ENGINE_D --body 'engine-d'" -ForegroundColor Gray
    
} catch {
    Write-Host "`n✗ Error retrieving services: $_" -ForegroundColor Red
}

Write-Host "`n=== Service Creation Complete ===" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Set the GitHub secrets above" -ForegroundColor White
Write-Host "2. Run setup_northflank_gateway.ps1 to create API gateway" -ForegroundColor White
Write-Host "3. Push to trigger deployment" -ForegroundColor White
