param(
    [Parameter(Mandatory=$true)]
    [string]$ApiToken,
    
    [Parameter(Mandatory=$true)]
    [string]$Project
)

$headers = @{
    "Authorization" = "Bearer $ApiToken"
    "Content-Type" = "application/json"
}

$baseUrl = "https://api.northflank.com/v1"

# Service configurations
$services = @(
    @{
        id = "engine-a"
        name = "Engine A - Market Data"
        description = "Real-time market data ingestion and technical analysis"
        buildPath = "/engines/engine-a"
        port = 8000
    },
    @{
        id = "engine-b"
        name = "Engine B - AI ML"
        description = "AI/ML processing with price predictions and sentiment analysis"
        buildPath = "/engines/engine-b"
        port = 8001
    },
    @{
        id = "engine-c-execution"
        name = "Engine C - Execution"
        description = "Secure trade execution with Dhan OAuth and risk management"
        buildPath = "/engines/engine-c-execution"
        port = 8002
    },
    @{
        id = "engine-d"
        name = "Engine D - Orchestrator"
        description = "AI chatbot orchestrator managing multi-engine coordination"
        buildPath = "/engines/engine-d"
        port = 8003
    }
)

Write-Host "`n=== Creating Northflank Services for InfinityAI.Pro ===" -ForegroundColor Cyan
Write-Host "Project: $Project`n" -ForegroundColor Yellow

foreach ($svc in $services) {
    Write-Host "Creating service: $($svc.name) [$($svc.id)]..." -ForegroundColor Green
    
    $payload = @{
        name = $svc.id
        description = $svc.description
        billing = @{
            deploymentPlan = "nf-compute-20"
        }
        deployment = @{
            instances = 1
            storage = @{
                ephemeralStorage = @{
                    storageSize = 1024
                }
            }
            docker = @{
                configType = "dockerfile"
            }
        }
        ports = @(
            @{
                name = "http"
                internalPort = $svc.port
                public = $true
                protocol = "HTTP"
            }
        )
        vcsData = @{
            projectUrl = "https://github.com/raghu-1718/InfinityAI.Pro"
            projectType = "github"
            projectBranch = "recovery/v4.6-stabilization"
            accountLogin = "raghu-1718"
            repoName = "InfinityAI.Pro"
        }
        buildSettings = @{
            dockerfile = @{
                buildEngine = "kaniko"
                dockerFilePath = "$($svc.buildPath)/Dockerfile"
                dockerWorkDir = $svc.buildPath
            }
        }
        runtimeEnvironment = @{}
        buildArguments = @{}
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/projects/$Project/services/combined" `
            -Method Post `
            -Headers $headers `
            -Body $payload `
            -ErrorAction Stop
        
        Write-Host "  ✓ Created: $($svc.id)" -ForegroundColor Green
        Write-Host "    Service ID: $($response.data.id)" -ForegroundColor Gray
        Write-Host "    Status: $($response.data.status)" -ForegroundColor Gray
        
        # Store service ID in GitHub secret
        $secretName = "NF_SERVICE_" + ($svc.id.ToUpper() -replace '-', '_')
        gh secret set $secretName --body $response.data.id
        Write-Host "    GitHub Secret: $secretName = $($response.data.id)" -ForegroundColor Gray
        
    } catch {
        $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "  ✗ Failed to create $($svc.id)" -ForegroundColor Red
        Write-Host "    Error: $($errorDetail.error.message)" -ForegroundColor Red
        
        if ($errorDetail.error.details) {
            Write-Host "    Details:" -ForegroundColor Yellow
            $errorDetail.error.details | ForEach-Object {
                Write-Host "      - $($_.message)" -ForegroundColor Yellow
            }
        }
    }
    
    Start-Sleep -Seconds 2
}

Write-Host "`n=== Service Creation Complete ===" -ForegroundColor Cyan
Write-Host "Verifying services..." -ForegroundColor Yellow

try {
    $servicesResponse = Invoke-RestMethod -Uri "$baseUrl/projects/$Project/services" `
        -Method Get `
        -Headers $headers
    
    Write-Host "`nCreated Services ($($servicesResponse.data.services.Count)):" -ForegroundColor Green
    $servicesResponse.data.services | ForEach-Object {
        Write-Host "  - $($_.name) [$($_.id)]" -ForegroundColor Gray
    }
} catch {
    Write-Host "Could not verify services: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Create API Gateway using setup_northflank_gateway.ps1" -ForegroundColor White
Write-Host "2. Add DNS CNAME records" -ForegroundColor White
Write-Host "3. Push to trigger deployment" -ForegroundColor White
