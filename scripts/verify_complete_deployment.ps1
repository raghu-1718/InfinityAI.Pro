# InfinityAI.Pro - Complete Deployment Verification Script
# Tests all 4 engines, Firebase services, and generates performance report
# Date: November 3, 2025

$ErrorActionPreference = "Stop"

$PROJECT_ID = "after-yesterday-473512-k3"
$REGION = "us-central1"

# Service URLs (update after deployment)
$SERVICES = @{
    "Engine-A" = "https://infinityai-engine-a-573866363639.us-central1.run.app"
    "Engine-B" = "https://infinityai-engine-b-573866363639.us-central1.run.app"
    "Engine-C" = "https://infinityai-engine-c-execution-573866363639.us-central1.run.app"
    "Engine-D" = "https://infinityai-engine-d-573866363639.us-central1.run.app"
    "Frontend" = "https://infinityai.pro"
}

$results = @()

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "InfinityAI.Pro - Complete Deployment Verification" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Cloud Run Services List
Write-Host "[Test 1] Listing Cloud Run Services..." -ForegroundColor Yellow
$cloudRunServices = gcloud run services list --region $REGION --project $PROJECT_ID --format=json | ConvertFrom-Json
Write-Host "Found $($cloudRunServices.Count) services" -ForegroundColor Green
Write-Host ""

# Test 2: Engine Health Endpoints
Write-Host "[Test 2] Testing Engine Health Endpoints..." -ForegroundColor Yellow
foreach ($service in $SERVICES.Keys) {
    if ($service -ne "Frontend") {
        $url = "$($SERVICES[$service])/health"
        Write-Host "  Testing $service..." -NoNewline
        
        try {
            $response = Invoke-RestMethod -Uri $url -TimeoutSec 10
            $status = if ($response.status -eq "healthy") { "✓ HEALTHY" } else { "✗ UNHEALTHY" }
            Write-Host " $status" -ForegroundColor $(if ($response.status -eq "healthy") { "Green" } else { "Red" })
            
            $results += [PSCustomObject]@{
                Service = $service
                Test = "Health Check"
                Status = $response.status
                ResponseTime = "N/A"
                Result = if ($response.status -eq "healthy") { "PASS" } else { "FAIL" }
            }
        } catch {
            Write-Host " ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
            $results += [PSCustomObject]@{
                Service = $service
                Test = "Health Check"
                Status = "ERROR"
                ResponseTime = "N/A"
                Result = "FAIL"
            }
        }
    }
}
Write-Host ""

# Test 3: Engine A - Market Data API
Write-Host "[Test 3] Testing Engine A - Market Data API..." -ForegroundColor Yellow
try {
    $url = "$($SERVICES['Engine-A'])/api/market-data/NIFTY"
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $marketData = Invoke-RestMethod -Uri $url -TimeoutSec 15
    $stopwatch.Stop()
    
    $responseTime = $stopwatch.ElapsedMilliseconds
    Write-Host "  ✓ Market data fetched in ${responseTime}ms" -ForegroundColor Green
    Write-Host "  Symbol: $($marketData.symbol)" -ForegroundColor Gray
    Write-Host "  Price: $($marketData.price)" -ForegroundColor Gray
    
    $results += [PSCustomObject]@{
        Service = "Engine-A"
        Test = "Market Data API"
        Status = "SUCCESS"
        ResponseTime = "${responseTime}ms"
        Result = if ($responseTime -lt 500) { "PASS" } else { "WARN" }
    }
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $results += [PSCustomObject]@{
        Service = "Engine-A"
        Test = "Market Data API"
        Status = "ERROR"
        ResponseTime = "N/A"
        Result = "FAIL"
    }
}
Write-Host ""

# Test 4: Engine B - AI Predictions API
Write-Host "[Test 4] Testing Engine B - AI Predictions API..." -ForegroundColor Yellow
try {
    $url = "$($SERVICES['Engine-B'])/api/ai-signals"
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $aiSignals = Invoke-RestMethod -Uri $url -TimeoutSec 15
    $stopwatch.Stop()
    
    $responseTime = $stopwatch.ElapsedMilliseconds
    Write-Host "  ✓ AI signals generated in ${responseTime}ms" -ForegroundColor Green
    Write-Host "  Signals count: $($aiSignals.signals.Count)" -ForegroundColor Gray
    
    $results += [PSCustomObject]@{
        Service = "Engine-B"
        Test = "AI Predictions API"
        Status = "SUCCESS"
        ResponseTime = "${responseTime}ms"
        Result = if ($responseTime -lt 1000) { "PASS" } else { "WARN" }
    }
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $results += [PSCustomObject]@{
        Service = "Engine-B"
        Test = "AI Predictions API"
        Status = "ERROR"
        ResponseTime = "N/A"
        Result = "FAIL"
    }
}
Write-Host ""

# Test 5: Engine C - Order Status API
Write-Host "[Test 5] Testing Engine C - Order Status API..." -ForegroundColor Yellow
try {
    $url = "$($SERVICES['Engine-C'])/api/orders/status"
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $orderStatus = Invoke-RestMethod -Uri $url -TimeoutSec 10
    $stopwatch.Stop()
    
    $responseTime = $stopwatch.ElapsedMilliseconds
    Write-Host "  ✓ Order status retrieved in ${responseTime}ms" -ForegroundColor Green
    
    $results += [PSCustomObject]@{
        Service = "Engine-C"
        Test = "Order Status API"
        Status = "SUCCESS"
        ResponseTime = "${responseTime}ms"
        Result = if ($responseTime -lt 200) { "PASS" } else { "WARN" }
    }
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $results += [PSCustomObject]@{
        Service = "Engine-C"
        Test = "Order Status API"
        Status = "ERROR"
        ResponseTime = "N/A"
        Result = "FAIL"
    }
}
Write-Host ""

# Test 6: Engine D - Orchestration Health
Write-Host "[Test 6] Testing Engine D - Orchestration..." -ForegroundColor Yellow
try {
    $url = "$($SERVICES['Engine-D'])/health"
    $response = Invoke-RestMethod -Uri $url -TimeoutSec 10
    Write-Host "  ✓ Orchestration healthy" -ForegroundColor Green
    
    $results += [PSCustomObject]@{
        Service = "Engine-D"
        Test = "Orchestration Health"
        Status = "SUCCESS"
        ResponseTime = "N/A"
        Result = "PASS"
    }
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $results += [PSCustomObject]@{
        Service = "Engine-D"
        Test = "Orchestration Health"
        Status = "ERROR"
        ResponseTime = "N/A"
        Result = "FAIL"
    }
}
Write-Host ""

# Test 7: Firebase Functions
Write-Host "[Test 7] Listing Firebase Functions..." -ForegroundColor Yellow
try {
    $functions = firebase functions:list --project $PROJECT_ID 2>&1
    $functionCount = ($functions | Select-String -Pattern "https://" -AllMatches).Matches.Count
    Write-Host "  ✓ Found $functionCount deployed functions" -ForegroundColor Green
    
    $results += [PSCustomObject]@{
        Service = "Firebase"
        Test = "Functions Deployment"
        Status = "SUCCESS"
        ResponseTime = "N/A"
        Result = if ($functionCount -ge 13) { "PASS" } else { "WARN" }
    }
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $results += [PSCustomObject]@{
        Service = "Firebase"
        Test = "Functions Deployment"
        Status = "ERROR"
        ResponseTime = "N/A"
        Result = "FAIL"
    }
}
Write-Host ""

# Test 8: Check Scale-to-Zero Configuration
Write-Host "[Test 8] Verifying Scale-to-Zero Configuration..." -ForegroundColor Yellow
$scaleToZeroEngines = @("infinityai-engine-a", "infinityai-engine-b", "infinityai-engine-c-execution", "infinityai-engine-d")
foreach ($engine in $scaleToZeroEngines) {
    try {
        $service = gcloud run services describe $engine --region $REGION --project $PROJECT_ID --format=json | ConvertFrom-Json
        $minInstances = $service.spec.template.metadata.annotations.'autoscaling.knative.dev/minScale'
        $cpu = $service.spec.template.spec.containers[0].resources.limits.cpu
        $memory = $service.spec.template.spec.containers[0].resources.limits.memory
        
        Write-Host "  $engine : CPU=$cpu, Memory=$memory, Min=$minInstances" -ForegroundColor $(if ($minInstances -eq "0") { "Green" } else { "Yellow" })
        
        $results += [PSCustomObject]@{
            Service = $engine
            Test = "Scale-to-Zero Config"
            Status = "Min=$minInstances, CPU=$cpu, Mem=$memory"
            ResponseTime = "N/A"
            Result = if ($minInstances -eq "0") { "PASS" } else { "WARN" }
        }
    } catch {
        Write-Host "  ✗ FAILED: $engine" -ForegroundColor Red
    }
}
Write-Host ""

# Test 9: Performance Summary
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
$results | Format-Table -AutoSize

$passCount = ($results | Where-Object { $_.Result -eq "PASS" }).Count
$warnCount = ($results | Where-Object { $_.Result -eq "WARN" }).Count
$failCount = ($results | Where-Object { $_.Result -eq "FAIL" }).Count

Write-Host ""
Write-Host "PASS: $passCount" -ForegroundColor Green -NoNewline
Write-Host " | " -NoNewline
Write-Host "WARN: $warnCount" -ForegroundColor Yellow -NoNewline
Write-Host " | " -NoNewline
Write-Host "FAIL: $failCount" -ForegroundColor Red

# Export results to JSON
$reportPath = "DEPLOYMENT_VERIFICATION_REPORT.json"
$report = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Project = $PROJECT_ID
    Region = $REGION
    Results = $results
    Summary = @{
        Pass = $passCount
        Warn = $warnCount
        Fail = $failCount
        Total = $results.Count
    }
}
$report | ConvertTo-Json -Depth 10 | Out-File $reportPath
Write-Host ""
Write-Host "Report saved to: $reportPath" -ForegroundColor Cyan
