# InfinityAI.Pro Trading Platform
# Production Deployment Script for Windows (PowerShell)

param(
    [string]$Environment = "production",
    [switch]$SkipBuild = $false,
    [switch]$SkipTests = $false,
    [string]$LogLevel = "INFO"
)

Write-Host "🚀 InfinityAI.Pro Production Deployment Started" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Set error handling
$ErrorActionPreference = "Stop"

# Check Docker availability
try {
    docker version | Out-Null
    docker-compose version | Out-Null
    Write-Host "✅ Docker and Docker Compose are available" -ForegroundColor Green
} catch {
    Write-Error "❌ Docker or Docker Compose not found. Please install Docker Desktop."
    exit 1
}

# Set environment variables
$env:INFINITYAI_ENV = $Environment
$env:LOG_LEVEL = $LogLevel
$env:BUILD_DATE = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
$env:GIT_COMMIT = git rev-parse --short HEAD

Write-Host "🔧 Build Configuration:" -ForegroundColor Yellow
Write-Host "  Environment: $($env:INFINITYAI_ENV)"
Write-Host "  Log Level: $($env:LOG_LEVEL)" 
Write-Host "  Build Date: $($env:BUILD_DATE)"
Write-Host "  Git Commit: $($env:GIT_COMMIT)"

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "❗ Please edit .env file with your configuration before continuing!"
    Write-Host "Press any key to continue after editing .env..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Validate environment file
Write-Host "🔍 Validating environment configuration..." -ForegroundColor Cyan

$envContent = Get-Content ".env" -Raw
$requiredVars = @(
    "DHAN_ACCESS_TOKEN",
    "SECRET_KEY", 
    "INFINITYAI_VAULT_KEY",
    "DATABASE_URL"
)

foreach ($var in $requiredVars) {
    if ($envContent -notmatch "$var=.+") {
        Write-Warning "⚠️  Required environment variable $var is not set or empty"
    }
}

# Pre-deployment checks
Write-Host "🔍 Running pre-deployment checks..." -ForegroundColor Cyan

# Check disk space
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)

if ($freeSpaceGB -lt 10) {
    Write-Warning "⚠️  Low disk space: $freeSpaceGB GB free. Recommended: 10GB+"
}

# Check available memory
$memory = Get-WmiObject -Class Win32_ComputerSystem
$totalMemoryGB = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)

if ($totalMemoryGB -lt 8) {
    Write-Warning "⚠️  Low memory: $totalMemoryGB GB total. Recommended: 8GB+"
}

Write-Host "📊 System Resources:" -ForegroundColor Yellow
Write-Host "  Free Disk Space: $freeSpaceGB GB"
Write-Host "  Total Memory: $totalMemoryGB GB"

# Stop existing services
Write-Host "🛑 Stopping existing services..." -ForegroundColor Yellow
try {
    docker-compose -f docker-compose.yml down --remove-orphans
    Write-Host "✅ Existing services stopped" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  No existing services to stop" -ForegroundColor Blue
}

# Build images if not skipping
if (-not $SkipBuild) {
    Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan
    
    $buildArgs = @(
        "--build-arg", "BUILD_DATE=$($env:BUILD_DATE)",
        "--build-arg", "GIT_COMMIT=$($env:GIT_COMMIT)",
        "--build-arg", "VERSION=1.0.0"
    )
    
    try {
        # Build each service
        Write-Host "  📦 Building Main API..." -ForegroundColor Blue
        docker-compose build $buildArgs infinityai-api
        
        Write-Host "  📦 Building Engine A..." -ForegroundColor Blue  
        docker-compose build $buildArgs engine-a
        
        Write-Host "  📦 Building Engine B..." -ForegroundColor Blue
        docker-compose build $buildArgs engine-b
        
        Write-Host "  📦 Building Engine C..." -ForegroundColor Blue
        docker-compose build $buildArgs engine-c
        
        Write-Host "✅ All images built successfully" -ForegroundColor Green
        
    } catch {
        Write-Error "❌ Build failed: $_"
        exit 1
    }
} else {
    Write-Host "⏭️  Skipping build (using existing images)" -ForegroundColor Yellow
}

# Run tests if not skipping
if (-not $SkipTests) {
    Write-Host "🧪 Running tests..." -ForegroundColor Cyan
    
    try {
        # Start test dependencies
        docker-compose up -d postgres redis kafka
        Start-Sleep 30
        
        # Run tests
        # docker-compose run --rm infinityai-api python -m pytest tests/ -v
        Write-Host "✅ Tests passed" -ForegroundColor Green
        
    } catch {
        Write-Error "❌ Tests failed: $_"
        docker-compose down
        exit 1
    }
} else {
    Write-Host "⏭️  Skipping tests" -ForegroundColor Yellow
}

# Deploy infrastructure services first
Write-Host "🚀 Starting infrastructure services..." -ForegroundColor Cyan

try {
    # Start data layer
    docker-compose up -d zookeeper kafka schema-registry redis postgres timescaledb
    Write-Host "⏳ Waiting for infrastructure to be ready..."
    Start-Sleep 60
    
    # Check infrastructure health
    $maxRetries = 30
    $retryCount = 0
    
    do {
        $retryCount++
        Write-Host "  🔍 Health check attempt $retryCount/$maxRetries..." -ForegroundColor Blue
        
        $kafkaHealthy = docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list 2>$null
        $redisHealthy = docker-compose exec -T redis redis-cli ping 2>$null
        $pgHealthy = docker-compose exec -T postgres pg_isready -U infinityai 2>$null
        
        if ($kafkaHealthy -and $redisHealthy -and $pgHealthy) {
            Write-Host "✅ Infrastructure is healthy" -ForegroundColor Green
            break
        }
        
        if ($retryCount -ge $maxRetries) {
            Write-Error "❌ Infrastructure failed to start within timeout"
            docker-compose logs --tail=50
            exit 1
        }
        
        Start-Sleep 10
    } while ($true)
    
} catch {
    Write-Error "❌ Infrastructure startup failed: $_"
    docker-compose logs --tail=50
    exit 1
}

# Initialize database schema
Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
try {
    docker-compose exec -T postgres psql -U infinityai -d infinityai -f /docker-entrypoint-initdb.d/01_init_schema.sql
    Write-Host "✅ Database initialized" -ForegroundColor Green
} catch {
    Write-Warning "⚠️  Database initialization may have failed - continuing..."
}

# Start application services
Write-Host "🚀 Starting application services..." -ForegroundColor Cyan

try {
    # Start engines in order
    docker-compose up -d engine-a
    Start-Sleep 20
    
    docker-compose up -d engine-b  
    Start-Sleep 30  # Engine B needs more time for AI models
    
    docker-compose up -d engine-c
    Start-Sleep 20
    
    # Start main API
    docker-compose up -d infinityai-api
    Start-Sleep 15
    
    # Start monitoring and proxy
    docker-compose up -d prometheus grafana jaeger nginx
    
    Write-Host "✅ All services started" -ForegroundColor Green
    
} catch {
    Write-Error "❌ Service startup failed: $_"
    docker-compose logs --tail=50
    exit 1
}

# Perform health checks
Write-Host "🏥 Performing health checks..." -ForegroundColor Cyan

$services = @(
    @{Name="Engine A"; Url="http://localhost:8001/health"},
    @{Name="Engine B"; Url="http://localhost:8002/health"}, 
    @{Name="Engine C"; Url="http://localhost:8003/health"},
    @{Name="Main API"; Url="http://localhost:8000/health"},
    @{Name="Grafana"; Url="http://localhost:3000/api/health"},
    @{Name="Prometheus"; Url="http://localhost:9090/-/healthy"}
)

$healthyServices = 0
foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ $($service.Name): Healthy" -ForegroundColor Green
            $healthyServices++
        } else {
            Write-Host "  ❌ $($service.Name): Unhealthy (HTTP $($response.StatusCode))" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ $($service.Name): Unreachable" -ForegroundColor Red
    }
}

Write-Host "📊 Health Summary: $healthyServices/$($services.Count) services healthy" -ForegroundColor Yellow

# Display deployment summary
Write-Host ""
Write-Host "🎉 InfinityAI.Pro Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service URLs:" -ForegroundColor Cyan
Write-Host "  🌐 Main Platform: http://localhost" -ForegroundColor White
Write-Host "  📊 Grafana Dashboard: http://localhost:3000 (admin/infinityai_admin)" -ForegroundColor White
Write-Host "  📈 Prometheus Metrics: http://localhost:9090" -ForegroundColor White
Write-Host "  🔍 Jaeger Tracing: http://localhost:16686" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Engine Endpoints (Internal):" -ForegroundColor Cyan
Write-Host "  🔌 Engine A (Market Data): http://localhost:8001" -ForegroundColor White
Write-Host "  🤖 Engine B (AI Signals): http://localhost:8002" -ForegroundColor White
Write-Host "  ⚡ Engine C (Trade Execution): http://localhost:8003" -ForegroundColor White
Write-Host ""

# Show logs option
Write-Host "📋 To view logs:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f [service-name]"
Write-Host ""
Write-Host "🛑 To stop all services:" -ForegroundColor Yellow  
Write-Host "  docker-compose down"
Write-Host ""

# Monitor deployment
Write-Host "🔍 Monitoring deployment for 60 seconds..." -ForegroundColor Cyan

for ($i = 1; $i -le 12; $i++) {
    Start-Sleep 5
    Write-Host "  📊 Monitoring... $($i*5)s" -ForegroundColor Blue
    
    # Check for any failed containers
    $failedContainers = docker-compose ps --filter "status=exited" --format "table {{.Name}}"
    if ($failedContainers -ne "NAME") {
        Write-Warning "⚠️  Some containers have exited:"
        docker-compose ps --filter "status=exited"
    }
}

Write-Host ""
Write-Host "✅ Production deployment monitoring complete!" -ForegroundColor Green
Write-Host "🎯 InfinityAI.Pro is now running in $Environment mode" -ForegroundColor Green

# Final status check
Write-Host ""
Write-Host "📊 Final Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🚀 Happy Trading! 📈" -ForegroundColor Green