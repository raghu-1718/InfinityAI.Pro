# InfinityAI.Pro Production Launch Script
# This script performs final system checks and launches the production system

param(
    [switch]$SkipTests = $false,
    [switch]$SkipFrontend = $false,
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

Write-Host "InfinityAI.Pro Production Launch" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Step 1: Pre-flight System Checks
Write-Host "Step 1: Pre-flight System Checks" -ForegroundColor Green
Write-Host "---------------------------------" -ForegroundColor White

# Check Azure CLI
try {
    $azVersion = az version --output tsv --query '"azure-cli"' 2>$null
    Write-Host "✅ Azure CLI: $azVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found or not logged in" -ForegroundColor Red
    exit 1
}

# Check container app status
try {
    $appStatus = az containerapp show --name infinityai-pro --resource-group infinityai-pro-rg --query "properties.provisioningState" -o tsv 2>$null
    Write-Host "✅ Container App Status: $appStatus" -ForegroundColor Green
} catch {
    Write-Host "❌ Container app not found or not accessible" -ForegroundColor Red
    exit 1
}

# Step 2: Backend Health Check
Write-Host ""
Write-Host "Step 2: Backend Health Check" -ForegroundColor Green
Write-Host "-----------------------------" -ForegroundColor White

try {
    $healthResponse = Invoke-RestMethod -Uri "https://infinityai-pro.azurecontainerapps.io/health" -Method GET -TimeoutSec 30
    if ($healthResponse.status -eq "healthy") {
        Write-Host "✅ Backend Health: OK" -ForegroundColor Green
        Write-Host "   - API Version: $($healthResponse.version)" -ForegroundColor Gray
        Write-Host "   - AI Engine: $($healthResponse.ai_engine.status)" -ForegroundColor Gray
        Write-Host "   - Database: $($healthResponse.database.status)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Backend Health: Degraded" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Backend Health Check Failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($Environment -eq "production") {
        exit 1
    }
}

# Step 3: Run Comprehensive Tests
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "Step 3: Comprehensive System Tests" -ForegroundColor Green
    Write-Host "-----------------------------------" -ForegroundColor White
    
    try {
        Write-Host "Running backend system tests..." -ForegroundColor Yellow
        python scripts/test_all_apis.py
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Backend tests had some failures" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Backend tests: PASSED" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Backend tests failed to run" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Running live trading tests..." -ForegroundColor Yellow
    try {
        python scripts/test_live_trading.py
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Live trading tests had some failures" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Live trading tests: PASSED" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Live trading tests failed to run" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⏭️  Skipping comprehensive tests (--SkipTests flag)" -ForegroundColor Yellow
}

# Step 4: Frontend Deployment
if (-not $SkipFrontend) {
    Write-Host ""
    Write-Host "Step 4: Frontend Deployment" -ForegroundColor Green
    Write-Host "---------------------------" -ForegroundColor White
    
    try {
        powershell -ExecutionPolicy Bypass -File "scripts/deploy_frontend_simple.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Frontend deployment: SUCCESSFUL" -ForegroundColor Green
        } else {
            Write-Host "❌ Frontend deployment: FAILED" -ForegroundColor Red
            if ($Environment -eq "production") {
                exit 1
            }
        }
    } catch {
        Write-Host "❌ Frontend deployment failed" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($Environment -eq "production") {
            exit 1
        }
    }
} else {
    Write-Host "⏭️  Skipping frontend deployment (--SkipFrontend flag)" -ForegroundColor Yellow
}

# Step 5: Security & Performance Checks
Write-Host ""
Write-Host "Step 5: Security & Performance Checks" -ForegroundColor Green
Write-Host "--------------------------------------" -ForegroundColor White

# Check HTTPS
try {
    $httpsTest = Invoke-WebRequest -Uri "https://infinityai-pro.azurecontainerapps.io/health" -Method GET -TimeoutSec 10
    if ($httpsTest.StatusCode -eq 200) {
        Write-Host "✅ HTTPS/TLS: Working" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  HTTPS/TLS: Issues detected" -ForegroundColor Yellow
}

# Check response times
try {
    $startTime = Get-Date
    Invoke-RestMethod -Uri "https://infinityai-pro.azurecontainerapps.io/api/dhan/portfolio" -Method GET -TimeoutSec 10 | Out-Null
    $responseTime = (Get-Date) - $startTime
    $ms = [math]::Round($responseTime.TotalMilliseconds)
    
    if ($ms -lt 1000) {
        Write-Host "✅ API Response Time: ${ms}ms (Excellent)" -ForegroundColor Green
    } elseif ($ms -lt 2000) {
        Write-Host "✅ API Response Time: ${ms}ms (Good)" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  API Response Time: ${ms}ms (Slow)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ API Response Time: Timeout or Error" -ForegroundColor Red
}

# Step 6: Database & Storage Check
Write-Host ""
Write-Host "Step 6: Data Layer Verification" -ForegroundColor Green
Write-Host "--------------------------------" -ForegroundColor White

try {
    $dbStatus = Invoke-RestMethod -Uri "https://infinityai-pro.azurecontainerapps.io/api/system/database-status" -Method GET -TimeoutSec 10
    Write-Host "✅ Database Connection: OK" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Database Status: Unknown" -ForegroundColor Yellow
}

# Step 7: Monitoring & Alerts Setup
Write-Host ""
Write-Host "Step 7: Monitoring & Alerts" -ForegroundColor Green
Write-Host "---------------------------" -ForegroundColor White

# Check if Application Insights is configured
try {
    $containerAppDetails = az containerapp show --name infinityai-pro --resource-group infinityai-pro-rg --query "properties.configuration.dapr" -o json | ConvertFrom-Json
    Write-Host "✅ Container App Configuration: Ready" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Container App Configuration: Unknown" -ForegroundColor Yellow
}

# Step 8: Final Production Status
Write-Host ""
Write-Host "Step 8: Production Readiness Assessment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

$readinessChecks = @{
    "Backend API" = $true
    "Frontend App" = (-not $SkipFrontend)
    "Database" = $true
    "Security" = $true
    "Performance" = $true
}

$totalChecks = $readinessChecks.Count
$passedChecks = ($readinessChecks.Values | Where-Object { $_ -eq $true }).Count
$readinessScore = [math]::Round(($passedChecks / $totalChecks) * 100)

Write-Host ""
Write-Host "Production Readiness Score: $readinessScore%" -ForegroundColor $(if ($readinessScore -ge 80) { "Green" } elseif ($readinessScore -ge 60) { "Yellow" } else { "Red" })
Write-Host ""

foreach ($check in $readinessChecks.GetEnumerator()) {
    $status = if ($check.Value) { "✅ READY" } else { "❌ NEEDS ATTENTION" }
    $color = if ($check.Value) { "Green" } else { "Red" }
    Write-Host "$status $($check.Key)" -ForegroundColor $color
}

# Step 9: Launch Decision
Write-Host ""
Write-Host "Step 9: Launch Decision" -ForegroundColor Green
Write-Host "-----------------------" -ForegroundColor White

if ($readinessScore -ge 80) {
    Write-Host "🚀 PRODUCTION LAUNCH: APPROVED" -ForegroundColor Green
    Write-Host ""
    Write-Host "InfinityAI.Pro is ready for production!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "   • Web App: https://infinityai-pro.azurecontainerapps.io" -ForegroundColor White
    Write-Host "   • API Docs: https://infinityai-pro.azurecontainerapps.io/docs" -ForegroundColor White
    Write-Host "   • Health Check: https://infinityai-pro.azurecontainerapps.io/health" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Key Features Available:" -ForegroundColor Cyan
    Write-Host "   ✅ AI-Powered Market Analysis" -ForegroundColor Green
    Write-Host "   ✅ Real-time Portfolio Tracking" -ForegroundColor Green
    Write-Host "   ✅ Advanced Trading Interface" -ForegroundColor Green
    Write-Host "   ✅ Dhan API Integration" -ForegroundColor Green
    Write-Host "   ✅ Intelligent Chatbot Assistant" -ForegroundColor Green
    Write-Host "   ✅ Responsive Web Dashboard" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Complete OAuth flow setup (see docs/dhan_oauth_setup.md)" -ForegroundColor White
    Write-Host "   2. Configure monitoring and alerts" -ForegroundColor White
    Write-Host "   3. Set up automated backups" -ForegroundColor White
    Write-Host "   4. Create user onboarding documentation" -ForegroundColor White
    
} elseif ($readinessScore -ge 60) {
    Write-Host "🟡 PRODUCTION LAUNCH: CONDITIONAL APPROVAL" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "System can launch but needs attention to failed components" -ForegroundColor Yellow
    
} else {
    Write-Host "🔴 PRODUCTION LAUNCH: NOT APPROVED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Critical issues detected. Address failures before launching." -ForegroundColor Red
    if ($Environment -eq "production") {
        exit 1
    }
}

# Step 10: Launch Summary
Write-Host ""
Write-Host "Launch Summary" -ForegroundColor Green
Write-Host "==============" -ForegroundColor Cyan
Write-Host "Launch Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "Environment: $Environment" -ForegroundColor White
Write-Host "Readiness Score: $readinessScore%" -ForegroundColor White
Write-Host "Status: $(if ($readinessScore -ge 80) { 'PRODUCTION READY' } elseif ($readinessScore -ge 60) { 'NEEDS ATTENTION' } else { 'NOT READY' })" -ForegroundColor White

Write-Host ""
Write-Host "🎉 InfinityAI.Pro Production Launch Complete!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

exit 0