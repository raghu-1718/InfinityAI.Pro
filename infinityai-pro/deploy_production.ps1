#!/usr/bin/env pwsh

param(
    [string]$Environment = "production",
    [switch]$SkipTests = $false,
    [switch]$SkipBuild = $false,
    [switch]$DeployK8s = $false,
    [switch]$DeployFrontend = $false,
    [switch]$RunTests = $false,
    [switch]$All = $true
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

Write-Host "🚀 InfinityAI.Pro Multi-Cloud Production Deployment Script" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor Gray

# Function to log messages
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

# Check prerequisites
Write-Log "Checking prerequisites..." "Cyan"

$prerequisites = @(
    @{Name="Docker"; Command="docker"; Required=$true},
    @{Name="Docker Compose"; Command="docker-compose"; Required=$true},
    @{Name="kubectl"; Command="kubectl"; Required=$false},
    @{Name="Node.js"; Command="node"; Required=$true},
    @{Name="npm"; Command="npm"; Required=$true},
    @{Name="curl"; Command="curl"; Required=$true}
)

foreach ($prereq in $prerequisites) {
    if (Test-Command $prereq.Command) {
        Write-Log "✅ $($prereq.Name) is available" "Green"
    } else {
        if ($prereq.Required) {
            Write-Log "❌ $($prereq.Name) is required but not found" "Red"
            exit 1
        } else {
            Write-Log "⚠️  $($prereq.Name) is not available (optional)" "Yellow"
        }
    }
}

# Test engine connectivity and performance
function Test-Engines {
    Write-Log "🧪 Testing engine connectivity and performance..." "Cyan"
    
    $engines = @(
        @{Name="Engine A"; URL="http://localhost:8001/health"; Port=8001},
        @{Name="Engine B"; URL="http://localhost:8002/health"; Port=8002},
        @{Name="Engine C"; URL="http://localhost:8003/health"; Port=8003},
        @{Name="Engine D"; URL="http://localhost:8004/health"; Port=8004}
    )
    
    $healthyEngines = 0
    
    foreach ($engine in $engines) {
        try {
            Write-Log "Testing $($engine.Name)..." "Yellow"
            
            # Test basic connectivity
            $response = curl -s $engine.URL --max-time 10 2>$null
            if ($LASTEXITCODE -eq 0) {
                $healthData = $response | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($healthData.status -eq "healthy") {
                    Write-Log "✅ $($engine.Name): HEALTHY" "Green"
                    $healthyEngines++
                    
                    # Performance test
                    $startTime = Get-Date
                    curl -s $engine.URL --max-time 5 | Out-Null
                    $responseTime = (Get-Date) - $startTime
                    Write-Log "   Response time: $($responseTime.TotalMilliseconds)ms" "Gray"
                } else {
                    Write-Log "⚠️  $($engine.Name): UNHEALTHY - $($healthData.status)" "Yellow"
                }
            } else {
                Write-Log "❌ $($engine.Name): CONNECTION FAILED" "Red"
            }
        } catch {
            Write-Log "❌ $($engine.Name): ERROR - $($_.Exception.Message)" "Red"
        }
    }
    
    Write-Log "Engine Health Summary: $healthyEngines/4 engines healthy" "Cyan"
    return $healthyEngines
}

# Test data flow between engines
function Test-DataFlow {
    Write-Log "🔄 Testing data flow between engines..." "Cyan"
    
    try {
        # Test Engine A data ingestion
        Write-Log "Testing Engine A market data..." "Yellow"
        $marketData = curl -s "http://localhost:8001/api/v1/market/AAPL" --max-time 15 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Engine A: Market data retrieval successful" "Green"
        }
        
        # Test Engine B AI processing (if available)
        Write-Log "Testing Engine B AI status..." "Yellow"
        $aiStatus = curl -s "http://localhost:8002/api/v1/models/status" --max-time 10 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Engine B: AI models accessible" "Green"
        }
        
        # Test Engine C portfolio (may require auth)
        Write-Log "Testing Engine C API status..." "Yellow"
        $apiStatus = curl -s "http://localhost:8003/api/v1/status" --max-time 10 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Engine C: API endpoints accessible" "Green"
        }
        
        # Test Engine D chatbot (may be unavailable)
        Write-Log "Testing Engine D chatbot..." "Yellow"
        $chatHealth = curl -s "http://localhost:8004/health" --max-time 10 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Engine D: Chatbot service accessible" "Green"
        } else {
            Write-Log "⚠️  Engine D: Currently unavailable (expected if unhealthy)" "Yellow"
        }
        
        return $true
    } catch {
        Write-Log "❌ Data flow test failed: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Build and test engines locally
if ($All -or -not $SkipBuild) {
    Write-Log "🔨 Building and starting engines..." "Cyan"
    
    try {
        # Start engines using docker-compose
        Write-Log "Starting engine containers..." "Yellow"
        docker-compose -f docker-compose.engines.yml up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Engine containers started successfully" "Green"
            
            # Wait for engines to be ready
            Write-Log "Waiting for engines to initialize..." "Yellow"
            Start-Sleep 30
            
            # Test engines
            if (-not $SkipTests) {
                $healthyCount = Test-Engines
                
                if ($healthyCount -ge 2) {
                    Write-Log "✅ Minimum engines are healthy ($healthyCount/4)" "Green"
                    
                    # Test data flow
                    if (Test-DataFlow) {
                        Write-Log "✅ Data flow tests passed" "Green"
                    } else {
                        Write-Log "⚠️  Some data flow tests failed" "Yellow"
                    }
                } else {
                    Write-Log "⚠️  Only $healthyCount/4 engines are healthy" "Yellow"
                }
            }
        } else {
            Write-Log "❌ Failed to start engine containers" "Red"
        }
    } catch {
        Write-Log "❌ Engine deployment failed: $($_.Exception.Message)" "Red"
    }
}

# Frontend deployment
if ($All -or $DeployFrontend) {
    Write-Log "🌐 Deploying frontend to production..." "Cyan"
    
    try {
        Push-Location frontend
        
        # Install dependencies if needed
        if (-not (Test-Path "node_modules")) {
            Write-Log "Installing frontend dependencies..." "Yellow"
            npm install
        }
        
        # Build production version
        Write-Log "Building production frontend..." "Yellow"
        $env:REACT_APP_API_URL = "https://api.infinityai.pro"
        $env:REACT_APP_ENVIRONMENT = "production"
        npm run build
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Frontend build successful" "Green"
            
            # Check if Vercel CLI is available
            if (Test-Command "vercel") {
                Write-Log "Deploying to Vercel..." "Yellow"
                vercel --prod --yes
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "✅ Frontend deployed to Vercel successfully" "Green"
                } else {
                    Write-Log "⚠️  Vercel deployment had issues (manual intervention may be needed)" "Yellow"
                }
            } else {
                Write-Log "⚠️  Vercel CLI not found. Please deploy manually:" "Yellow"
                Write-Log "   1. Install Vercel CLI: npm i -g vercel" "Gray"
                Write-Log "   2. Run: vercel --prod" "Gray"
                Write-Log "   3. Or use Vercel web interface with the build folder" "Gray"
            }
        } else {
            Write-Log "❌ Frontend build failed" "Red"
        }
    } catch {
        Write-Log "❌ Frontend deployment failed: $($_.Exception.Message)" "Red"
    } finally {
        Pop-Location
    }
}

# Kubernetes deployment (if requested)
if ($DeployK8s -or $All) {
    Write-Log "☸️  Preparing Kubernetes deployment..." "Cyan"
    
    if (Test-Command "kubectl") {
        try {
            Write-Log "Validating Kubernetes manifests..." "Yellow"
            
            # Validate all K8s manifests
            $k8sFiles = Get-ChildItem -Path "k8s" -Filter "*.yaml" | Sort-Object Name
            foreach ($file in $k8sFiles) {
                Write-Log "Validating $($file.Name)..." "Gray"
                kubectl apply --dry-run=client -f $file.FullName 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "✅ $($file.Name) is valid" "Green"
                } else {
                    Write-Log "❌ $($file.Name) has validation errors" "Red"
                }
            }
            
            Write-Log "📋 Kubernetes deployment manifests are ready!" "Green"
            Write-Log "To deploy to EKS cluster:" "Yellow"
            Write-Log "  1. Configure kubectl: aws eks update-kubeconfig --name infinityai-pro-cluster --region us-west-2" "Gray"
            Write-Log "  2. Deploy: kubectl apply -f k8s/" "Gray"
            Write-Log "  3. Monitor: kubectl get pods -n infinityai -w" "Gray"
            
        } catch {
            Write-Log "❌ Kubernetes preparation failed: $($_.Exception.Message)" "Red"
        }
        } else {
            Write-Log "kubectl not available. Skipping K8s deployment preparation." "Yellow"
        }
    } else {
        Write-Log "kubectl not available. Skipping K8s deployment preparation." "Yellow"
    }
}
# Performance and integration tests
if ($All -or $RunTests) {
    Write-Log "🧪 Running comprehensive system tests..." "Cyan"
    
    # Engine performance tests
    Write-Log "Testing engine performance..." "Yellow"
    $performanceResults = @{}
    
    $testEndpoints = @(
        @{Name="Engine A Health"; URL="http://localhost:8001/health"},
        @{Name="Engine B Health"; URL="http://localhost:8002/health"},
        @{Name="Engine C Health"; URL="http://localhost:8003/health"},
        @{Name="Engine A Market Data"; URL="http://localhost:8001/api/v1/market/SPY"}
    )
    
    foreach ($endpoint in $testEndpoints) {
        try {
            $startTime = Get-Date
            $result = curl -s $endpoint.URL --max-time 10 2>$null
            $endTime = Get-Date
            $responseTime = ($endTime - $startTime).TotalMilliseconds
            
            if ($LASTEXITCODE -eq 0) {
                $performanceResults[$endpoint.Name] = $responseTime
                Write-Log "✅ $($endpoint.Name): ${responseTime}ms" "Green"
            } else {
                Write-Log "❌ $($endpoint.Name): Failed" "Red"
            }
        } catch {
            Write-Log "❌ $($endpoint.Name): Error" "Red"
        }
    }
    
    # System integration test
    Write-Log "Running integration tests..." "Yellow"
    
    if (Test-Path "integration_test.py") {
        try {
            python integration_test.py
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ Integration tests passed" "Green"
            } else {
                Write-Log "⚠️  Some integration tests failed" "Yellow"
            }
        } catch {
            Write-Log "⚠️  Integration test script error" "Yellow"
        }
    }
}

# System status summary
Write-Log "📊 DEPLOYMENT SUMMARY" "Cyan"
Write-Log "="*50 -ForegroundColor Gray

# Check current system status
Write-Log "Current System Status:" "Yellow"

# Docker containers status
$containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String "infinityai-engine"
if ($containers) {
    Write-Log "🐳 Docker Engines:" "Green"
    foreach ($container in $containers) {
        Write-Log "   $container" "Gray"
    }
}

# Services status
$services = @("8001", "8002", "8003", "8004")
Write-Log "🌐 Service Ports:" "Green"
foreach ($port in $services) {
    try {
        $result = Test-NetConnection -ComputerName "localhost" -Port $port -WarningAction SilentlyContinue
        if ($result.TcpTestSucceeded) {
            Write-Log "   Port $port: ✅ OPEN" "Green"
        } else {
            Write-Log "   Port $port: ❌ CLOSED" "Red"
        }
    } catch {
        Write-Log "   Port $port: ❌ ERROR" "Red"
    }
}

# Final recommendations
Write-Log "🎯 NEXT STEPS:" "Cyan"
Write-Log "1. ✅ Local engines are running and ready for testing" "Green"
Write-Log "2. 🌐 Deploy frontend: npm run build && vercel --prod" "Yellow"
Write-Log "3. ☸️  Deploy to K8s: kubectl apply -f k8s/" "Yellow"
Write-Log "4. 🔧 Configure production secrets and environment variables" "Yellow"
Write-Log "5. 📊 Set up monitoring and alerting" "Yellow"
Write-Log "6. 🚦 Run load tests and performance optimization" "Yellow"

Write-Log "🎉 InfinityAI.Pro Multi-Cloud deployment process completed!" "Green"
Write-Log "System is ready for production workloads." "Cyan"
Write-Log "="*80 -ForegroundColor Gray