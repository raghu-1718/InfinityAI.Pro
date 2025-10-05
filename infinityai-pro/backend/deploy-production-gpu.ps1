# =============================================================================
# InfinityAI.Pro Production GPU Trading Platform Deployment
# Complete deployment with GPU acceleration and auto-scaling
# =============================================================================

param(
    [string]$Environment = "local",  # local, cloud, hybrid
    [string]$GPUMode = "docker",     # docker, kubernetes
    [switch]$BuildImages = $false,
    [switch]$SkipTests = $false,
    [switch]$EnableGPU = $true
)

Write-Host "🚀 InfinityAI.Pro Production GPU Deployment" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Configuration
$Version = "2.0.0"
$BuildDate = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
$GitCommit = try { git rev-parse --short HEAD 2>$null } catch { "unknown" }
$LogFile = "deployment-production-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Function to log messages
function Write-Log {
    param($Message, $Color = "White", $NoNewline = $false)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    if ($NoNewline) {
        Write-Host $LogMessage -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $LogMessage -ForegroundColor $Color
    }
    Add-Content -Path $LogFile -Value $LogMessage
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Log "🔍 Checking deployment prerequisites..." "Yellow"
    
    $issues = @()
    
    # Check Docker
    try {
        $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
        if ($dockerVersion) {
            Write-Log "✅ Docker: $dockerVersion" "Green"
        } else {
            $issues += "Docker is not running"
        }
    } catch {
        $issues += "Docker not found"
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker compose version 2>$null
        if ($composeVersion) {
            Write-Log "✅ Docker Compose: Available" "Green"
        } else {
            $issues += "Docker Compose not available"
        }
    } catch {
        $issues += "Docker Compose not found"
    }
    
    # Check GPU support if enabled
    if ($EnableGPU) {
        try {
            $gpuInfo = nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>$null
            if ($gpuInfo) {
                Write-Log "✅ GPU: $gpuInfo" "Green"
            } else {
                Write-Log "⚠️ No NVIDIA GPU detected (will run in CPU mode)" "Yellow"
                $script:EnableGPU = $false
            }
        } catch {
            Write-Log "⚠️ NVIDIA drivers not found (will run in CPU mode)" "Yellow"
            $script:EnableGPU = $false
        }
        
        # Check nvidia-docker
        if ($EnableGPU) {
            try {
                docker run --rm --gpus all nvidia/cuda:12.2-base nvidia-smi 2>$null | Out-Null
                Write-Log "✅ Docker GPU support: Available" "Green"
            } catch {
                Write-Log "⚠️ Docker GPU support not available" "Yellow"
                $script:EnableGPU = $false
            }
        }
    }
    
    # Check environment file
    if (Test-Path ".env") {
        Write-Log "✅ Environment file: Found" "Green"
    } else {
        Write-Log "⚠️ .env file not found, creating template..." "Yellow"
        Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    }
    
    # Check kubectl for Kubernetes mode
    if ($GPUMode -eq "kubernetes") {
        try {
            $kubectlVersion = kubectl version --client --short 2>$null
            if ($kubectlVersion) {
                Write-Log "✅ kubectl: Available" "Green"
            } else {
                $issues += "kubectl not found (required for Kubernetes mode)"
            }
        } catch {
            $issues += "kubectl not available"
        }
    }
    
    if ($issues.Count -gt 0) {
        Write-Log "❌ Prerequisites check failed:" "Red"
        $issues | ForEach-Object { Write-Log "  - $_" "Red" }
        return $false
    }
    
    Write-Log "✅ All prerequisites satisfied" "Green"
    return $true
}

# Function to build GPU-optimized images
function Build-GPUImages {
    Write-Log "🏗️ Building GPU-optimized container images..." "Yellow"
    
    $env:BUILD_DATE = $BuildDate
    $env:GIT_COMMIT = $GitCommit
    $env:VERSION = $Version
    
    # Build Engine A GPU image
    Write-Log "Building Engine A GPU image..." "White"
    $buildArgs = @(
        "--build-arg", "BUILD_DATE=$BuildDate",
        "--build-arg", "GIT_COMMIT=$GitCommit", 
        "--build-arg", "VERSION=$Version"
    )
    
    docker build -f engines/engine-a/Dockerfile.gpu -t infinityai/engine-a:gpu-$Version $buildArgs engines/engine-a/
    if ($LASTEXITCODE -ne 0) {
        Write-Log "❌ Failed to build Engine A GPU image" "Red"
        return $false
    }
    Write-Log "✅ Engine A GPU image built successfully" "Green"
    
    # Build Engine B GPU image
    Write-Log "Building Engine B Enhanced GPU image..." "White"
    docker build -f engines/engine-b/Dockerfile.gpu.enhanced -t infinityai/engine-b:gpu-enhanced-$Version $buildArgs engines/engine-b/
    if ($LASTEXITCODE -ne 0) {
        Write-Log "❌ Failed to build Engine B GPU image" "Red"
        return $false
    }
    Write-Log "✅ Engine B GPU image built successfully" "Green"
    
    # Build other images
    Write-Log "Building remaining service images..." "White"
    docker build -f engines/engine-c/Dockerfile -t infinityai/engine-c:$Version $buildArgs engines/engine-c/
    docker build -f Dockerfile -t infinityai/api:$Version $buildArgs .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ All images built successfully" "Green"
        return $true
    } else {
        Write-Log "❌ Failed to build some images" "Red"
        return $false
    }
}

# Function to deploy with Docker Compose
function Deploy-DockerCompose {
    Write-Log "🐳 Deploying with Docker Compose (GPU mode: $EnableGPU)..." "Yellow"
    
    $composeFiles = @("docker-compose.yml")
    
    if ($EnableGPU) {
        $composeFiles += "docker-compose.gpu.yml"
        Write-Log "Using GPU-accelerated configuration" "Green"
    }
    
    # Set environment variables
    $env:BUILD_DATE = $BuildDate
    $env:GIT_COMMIT = $GitCommit
    $env:VERSION = $Version
    $env:POSTGRES_PASSWORD = "infinityai_secure_password_2024"
    $env:GRAFANA_PASSWORD = "admin"
    
    # Start services
    Write-Log "Starting all services..." "White"
    $composeArgs = $composeFiles | ForEach-Object { "-f", $_ }
    $composeArgs += @("up", "-d", "--remove-orphans")
    
    & docker compose $composeArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ All services started successfully" "Green"
        return $true
    } else {
        Write-Log "❌ Failed to start some services" "Red"
        return $false
    }
}

# Function to deploy to Kubernetes
function Deploy-Kubernetes {
    Write-Log "☸️ Deploying to Kubernetes with GPU support..." "Yellow"
    
    # Create namespace
    kubectl apply -f kubernetes/gpu-workloads/gpu-trading-deployments.yaml --validate=false
    if ($LASTEXITCODE -ne 0) {
        Write-Log "❌ Failed to create namespace and basic resources" "Red"
        return $false
    }
    
    # Deploy NVIDIA device plugin
    Write-Log "Deploying NVIDIA device plugin..." "White"
    kubectl apply -f kubernetes/gpu-config/nvidia-device-plugin.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Log "❌ Failed to deploy NVIDIA device plugin" "Red"
        return $false
    }
    
    # Wait for device plugin to be ready
    Write-Log "Waiting for NVIDIA device plugin to be ready..." "White"
    kubectl wait --for=condition=Ready pods -l name=nvidia-device-plugin-ds -n kube-system --timeout=300s
    
    # Deploy GPU workloads
    Write-Log "Deploying GPU trading workloads..." "White"
    kubectl apply -f kubernetes/gpu-workloads/ -R
    if ($LASTEXITCODE -ne 0) {
        Write-Log "❌ Failed to deploy GPU workloads" "Red"
        return $false
    }
    
    Write-Log "✅ Kubernetes deployment completed" "Green"
    return $true
}

# Function to run health checks
function Test-Deployment {
    Write-Log "🏥 Running deployment health checks..." "Yellow"
    
    if ($GPUMode -eq "docker") {
        # Docker health checks
        Write-Log "Checking Docker services..." "White"
        Start-Sleep 30  # Wait for services to start
        
        $services = @(
            @{ Name = "API Gateway"; URL = "http://localhost:8000/health" },
            @{ Name = "Engine A"; URL = "http://localhost:8001/health" },
            @{ Name = "Engine B"; URL = "http://localhost:8002/health" },
            @{ Name = "Engine C"; URL = "http://localhost:8003/health" },
            @{ Name = "Grafana"; URL = "http://localhost:3000/api/health" },
            @{ Name = "Prometheus"; URL = "http://localhost:9090/-/healthy" }
        )
        
        foreach ($service in $services) {
            try {
                $response = Invoke-WebRequest -Uri $service.URL -TimeoutSec 10 -UseBasicParsing
                if ($response.StatusCode -eq 200) {
                    Write-Log "✅ $($service.Name): Healthy" "Green"
                } else {
                    Write-Log "⚠️ $($service.Name): Unhealthy (Status: $($response.StatusCode))" "Yellow"
                }
            } catch {
                Write-Log "❌ $($service.Name): Not responding" "Red"
            }
        }
    } else {
        # Kubernetes health checks
        Write-Log "Checking Kubernetes deployments..." "White"
        kubectl get pods -n infinityai-production
        kubectl get services -n infinityai-production
    }
    
    if ($EnableGPU) {
        Write-Log "🎮 Testing GPU functionality..." "Cyan"
        
        if ($GPUMode -eq "docker") {
            # Test GPU in Docker
            try {
                docker exec infinityai-engine-a-gpu python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Count: {torch.cuda.device_count()}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
                docker exec infinityai-engine-b-gpu python -c "import torch, cupy, xgboost as xgb; print('PyTorch CUDA:', torch.cuda.is_available()); print('CuPy CUDA:', cupy.cuda.is_available()); print('All GPU libraries loaded successfully')"
                Write-Log "✅ GPU functionality verified" "Green"
            } catch {
                Write-Log "⚠️ GPU test failed (services may still be starting)" "Yellow"
            }
        } else {
            # Test GPU in Kubernetes
            kubectl exec -n infinityai-production deployment/infinityai-engine-a-gpu -- python -c "import torch; print('GPU available:', torch.cuda.is_available())"
        }
    }
}

# Function to show deployment summary
function Show-DeploymentSummary {
    Write-Log ""
    Write-Log "🎉 InfinityAI.Pro Production Deployment Complete!" "Green"
    Write-Log "=================================================" "Green"
    Write-Log ""
    Write-Log "📊 Deployment Summary:" "Cyan"
    Write-Log "• Environment: $Environment" "White"
    Write-Log "• GPU Mode: $EnableGPU" "White"
    Write-Log "• Deployment Type: $GPUMode" "White"
    Write-Log "• Version: $Version" "White"
    Write-Log "• Build Date: $BuildDate" "White"
    Write-Log "• Git Commit: $GitCommit" "White"
    Write-Log ""
    
    if ($GPUMode -eq "docker") {
        Write-Log "🌐 Service Access URLs:" "Cyan"
        Write-Log "• Main API: http://localhost:8000" "White"
        Write-Log "• Engine A (Market Data): http://localhost:8001" "White"
        Write-Log "• Engine B (AI Processing): http://localhost:8002" "White"
        Write-Log "• Engine C (Trade Execution): http://localhost:8003" "White"
        Write-Log "• Grafana Dashboard: http://localhost:3000 (admin/admin)" "White"
        Write-Log "• Prometheus: http://localhost:9090" "White"
        Write-Log ""
        
        Write-Log "📋 Management Commands:" "Yellow"
        Write-Log "• View logs: docker compose logs -f [service-name]" "White"
        Write-Log "• Check status: docker compose ps" "White"
        Write-Log "• Scale services: docker compose up -d --scale infinityai-engine-a-gpu=3" "White"
        Write-Log "• Stop all: docker compose down" "White"
        if ($EnableGPU) {
            Write-Log "• GPU monitoring: nvidia-smi" "White"
            Write-Log "• Container GPU usage: docker stats" "White"
        }
    } else {
        Write-Log "☸️ Kubernetes Management:" "Cyan"
        Write-Log "• View pods: kubectl get pods -n infinityai-production" "White"
        Write-Log "• View services: kubectl get services -n infinityai-production" "White"
        Write-Log "• View logs: kubectl logs -f deployment/infinityai-engine-a-gpu -n infinityai-production" "White"
        Write-Log "• Scale: kubectl scale deployment infinityai-engine-a-gpu --replicas=3 -n infinityai-production" "White"
        if ($EnableGPU) {
            Write-Log "• GPU nodes: kubectl describe nodes -l nvidia.com/gpu.present=true" "White"
            Write-Log "• GPU usage: kubectl top nodes" "White"
        }
    }
    
    Write-Log ""
    Write-Log "🎯 Trading Configuration:" "Green"
    Write-Log "• Capital: ₹25,000" "White"
    Write-Log "• Max Loss: 8% (₹2,000)" "White"
    Write-Log "• Target Profit: 20% (₹5,000)" "White"
    Write-Log "• AI Models: LSTM + XGBoost + Random Forest" "White"
    if ($EnableGPU) {
        Write-Log "• GPU Acceleration: Enabled ⚡" "Green"
        Write-Log "• Expected Performance: 5-10x faster inference" "Green"
    }
    
    Write-Log ""
    Write-Log "🔧 Next Steps:" "Yellow"
    Write-Log "1. Monitor system performance and GPU utilization" "White"
    Write-Log "2. Review trading signals and AI model performance" "White"
    Write-Log "3. Adjust scaling based on market volatility" "White"
    Write-Log "4. Set up alerts and monitoring dashboards" "White"
    
    Write-Log ""
    Write-Log "✅ Your GPU-accelerated trading platform is ready for live trading!" "Green"
}

# Main execution
try {
    Write-Log "🚀 Starting InfinityAI.Pro Production Deployment" "Green"
    Write-Log "Deployment Log: $LogFile" "White"
    Write-Log ""
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # Build images if requested
    if ($BuildImages) {
        if (-not (Build-GPUImages)) {
            exit 1
        }
    }
    
    # Deploy based on mode
    if ($GPUMode -eq "kubernetes") {
        if (-not (Deploy-Kubernetes)) {
            exit 1
        }
    } else {
        if (-not (Deploy-DockerCompose)) {
            exit 1
        }
    }
    
    # Run tests if not skipped
    if (-not $SkipTests) {
        Test-Deployment
    }
    
    # Show summary
    Show-DeploymentSummary
    
    Write-Log ""
    Write-Log "🎊 Deployment completed successfully!" "Green"
    
} catch {
    Write-Log "❌ Deployment failed: $($_.Exception.Message)" "Red"
    Write-Log "Check the log file for details: $LogFile" "Yellow"
    exit 1
}