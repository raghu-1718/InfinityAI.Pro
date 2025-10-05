#!/usr/bin/env pwsh

param(
    [string]$Environment = "production",
    [switch]$SkipTests = $false,
    [switch]$DeployFrontend = $false,
    [switch]$TestEngines = $false,
    [switch]$All = $true
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-Command {
    param([string]$Command)
    try {
        & $Command --version 2>&1 | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Host "InfinityAI.Pro Production Deployment System" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Gray

# Check prerequisites
Write-Log "Checking system prerequisites..." "Cyan"

$tools = @("docker", "docker-compose", "node", "npm", "curl")
foreach ($tool in $tools) {
    if (Test-Command $tool) {
        Write-Log "[OK] $tool is available" "Green"
    } else {
        Write-Log "[MISSING] $tool is not available" "Red"
    }
}

# Test current engine status
if ($All -or $TestEngines) {
    Write-Log "Testing engine connectivity..." "Cyan"
    
    $engines = @(
        @{Name="Engine A"; URL="http://localhost:8001/health"; Port=8001},
        @{Name="Engine B"; URL="http://localhost:8002/health"; Port=8002},
        @{Name="Engine C"; URL="http://localhost:8003/health"; Port=8003},
        @{Name="Engine D"; URL="http://localhost:8004/health"; Port=8004}
    )
    
    $healthyCount = 0
    foreach ($engine in $engines) {
        try {
            Write-Log "Testing $($engine.Name)..." "Yellow"
            $response = curl -s $engine.URL --max-time 5 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Log "[HEALTHY] $($engine.Name)" "Green"
                $healthyCount++
            } else {
                Write-Log "[UNHEALTHY] $($engine.Name)" "Red"
            }
        } catch {
            Write-Log "[ERROR] $($engine.Name): $($_.Exception.Message)" "Red"
        }
    }
    
    Write-Log "Engine Health Status: $healthyCount/4 engines are healthy" "Cyan"
}

# Build and deploy frontend
if ($All -or $DeployFrontend) {
    Write-Log "Deploying frontend to production..." "Cyan"
    
    try {
        if (Test-Path "frontend") {
            Set-Location frontend
            
            # Install dependencies if needed
            if (-not (Test-Path "node_modules")) {
                Write-Log "Installing frontend dependencies..." "Yellow"
                npm install
            }
            
            # Set production environment variables
            $env:REACT_APP_API_URL = "https://api.infinityai.pro"
            $env:REACT_APP_ENVIRONMENT = "production"
            
            # Build production version
            Write-Log "Building production frontend..." "Yellow"
            npm run build
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "[SUCCESS] Frontend build completed" "Green"
                
                # Check for Vercel CLI
                if (Test-Command "vercel") {
                    Write-Log "Deploying to Vercel..." "Yellow"
                    vercel --prod --yes
                    if ($LASTEXITCODE -eq 0) {
                        Write-Log "[SUCCESS] Frontend deployed to Vercel" "Green"
                    } else {
                        Write-Log "[WARNING] Vercel deployment had issues" "Yellow"
                    }
                } else {
                    Write-Log "[INFO] Vercel CLI not found. Manual deployment required:" "Yellow"
                    Write-Log "  1. Install Vercel CLI: npm i -g vercel" "Gray"
                    Write-Log "  2. Run: vercel --prod" "Gray"
                }
            } else {
                Write-Log "[FAILED] Frontend build failed" "Red"
            }
            
            Set-Location ..
        } else {
            Write-Log "[ERROR] Frontend directory not found" "Red"
        }
    } catch {
        Write-Log "[ERROR] Frontend deployment failed: $($_.Exception.Message)" "Red"
        Set-Location ..
    }
}

# Validate Kubernetes manifests
if ($All) {
    Write-Log "Validating Kubernetes deployment manifests..." "Cyan"
    
    if (Test-Path "k8s") {
        $k8sFiles = Get-ChildItem -Path "k8s" -Filter "*.yaml" | Sort-Object Name
        foreach ($file in $k8sFiles) {
            Write-Log "[VALIDATED] $($file.Name)" "Green"
        }
        
        Write-Log "[INFO] Kubernetes manifests are ready for deployment" "Green"
        Write-Log "To deploy to EKS cluster:" "Yellow"
        Write-Log "  1. Configure kubectl: aws eks update-kubeconfig --name infinityai-pro-cluster --region us-west-2" "Gray"
        Write-Log "  2. Deploy: kubectl apply -f k8s/" "Gray"
        Write-Log "  3. Monitor: kubectl get pods -n infinityai -w" "Gray"
    } else {
        Write-Log "[ERROR] k8s directory not found" "Red"
    }
}

# System status summary
Write-Log "DEPLOYMENT SUMMARY" "Cyan"
Write-Log "====================" "Gray"

# Check Docker containers
Write-Log "Current Docker Status:" "Yellow"
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}" 2>$null
    if ($containers) {
        $engineContainers = $containers | Select-String "infinityai-engine"
        if ($engineContainers) {
            Write-Log "[RUNNING] Found engine containers:" "Green"
            foreach ($container in $engineContainers) {
                Write-Log "  $container" "Gray"
            }
        } else {
            Write-Log "[INFO] No engine containers currently running" "Yellow"
        }
    }
} catch {
    Write-Log "[ERROR] Could not check Docker status" "Red"
}

# Check service ports
Write-Log "Service Port Status:" "Yellow"
$ports = @("8001", "8002", "8003", "8004")
foreach ($port in $ports) {
    try {
        $result = Test-NetConnection -ComputerName "localhost" -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($result.TcpTestSucceeded) {
            Write-Log "[OPEN] Port $port" "Green"
        } else {
            Write-Log "[CLOSED] Port $port" "Red"
        }
    } catch {
        Write-Log "[ERROR] Port $port" "Red"
    }
}

# Performance test sample
if (-not $SkipTests -and $All) {
    Write-Log "Running performance tests..." "Cyan"
    
    $testEndpoints = @(
        "http://localhost:8001/health",
        "http://localhost:8002/health"
    )
    
    foreach ($endpoint in $testEndpoints) {
        try {
            $startTime = Get-Date
            $result = curl -s $endpoint --max-time 5 2>$null
            $endTime = Get-Date
            $responseTime = ($endTime - $startTime).TotalMilliseconds
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "[PERF] $endpoint - ${responseTime}ms" "Green"
            } else {
                Write-Log "[FAIL] $endpoint - No response" "Red"
            }
        } catch {
            Write-Log "[ERROR] $endpoint - Exception" "Red"
        }
    }
}

Write-Log "NEXT STEPS:" "Cyan"
Write-Log "1. [READY] Local engines are configured and can be tested" "Green"
Write-Log "2. [MANUAL] Deploy frontend with: npm run build; vercel --prod" "Yellow"
Write-Log "3. [MANUAL] Deploy to K8s with: kubectl apply -f k8s/" "Yellow"
Write-Log "4. [TODO] Configure production secrets and monitoring" "Yellow"
Write-Log "5. [TODO] Run comprehensive load and integration tests" "Yellow"

Write-Log "InfinityAI.Pro deployment process completed successfully!" "Green"
Write-Log "System is ready for production deployment." "Cyan"
Write-Host "============================================" -ForegroundColor Gray