#!/usr/bin/env pwsh
# InfinityAI Engine A - Complete Verification Script
# Tests all endpoints, measures performance, and generates comprehensive report

param(
    [string]$ServiceUrl = "https://engine-a-market-data-prod-573866363639.us-central1.run.app"
)

Write-Host "🚀 InfinityAI Engine A - Complete Verification Starting..." -ForegroundColor Green
Write-Host "📊 Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host "⏱️  Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')" -ForegroundColor Cyan
Write-Host "=" * 80

# Initialize results
$results = @{
    timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC'
    service_url = $ServiceUrl
    tests = @()
    summary = @{
        total_tests = 0
        passed = 0
        failed = 0
        avg_response_time = 0
        total_time = 0
    }
}

# Helper function to test endpoint
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$ExpectedStatus = 200
    )
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $success = $false
    $responseData = $null
    $error = $null
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-WebRequest @params
        $stopwatch.Stop()
        
        $responseData = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
        $success = $response.StatusCode -eq $ExpectedStatus
        
        if (-not $success) {
            $error = "Expected status $ExpectedStatus, got $($response.StatusCode)"
        }
    }
    catch {
        $stopwatch.Stop()
        $error = $_.Exception.Message
        if ($_.Exception.Response) {
            try {
                $responseData = $_.Exception.Response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
            } catch {}
        }
    }
    
    $test = @{
        name = $Name
        url = $Url
        method = $Method
        success = $success
        response_time_ms = $stopwatch.ElapsedMilliseconds
        status_code = if ($response) { $response.StatusCode } else { 0 }
        response_data = $responseData
        error = $error
    }
    
    $results.tests += $test
    $results.summary.total_tests++
    
    if ($success) {
        $results.summary.passed++
        Write-Host "✅ $Name" -ForegroundColor Green
        Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms" -ForegroundColor Gray
    } else {
        $results.summary.failed++
        Write-Host "❌ $Name" -ForegroundColor Red
        Write-Host "   Error: $error" -ForegroundColor Red
        Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms" -ForegroundColor Gray
    }
    
    return $test
}

Write-Host "🔍 Testing Core Endpoints..." -ForegroundColor Yellow

# Test 1: Root endpoint
Test-Endpoint -Name "Root Status" -Url "$ServiceUrl/"

# Test 2: Health check
Test-Endpoint -Name "Health Check" -Url "$ServiceUrl/health"

# Test 3: Market signals
Test-Endpoint -Name "Market Signals" -Url "$ServiceUrl/api/signals"

Write-Host "`n🤖 Testing AI Integrations..." -ForegroundColor Yellow

# Test 4: Gemini text generation
$geminiHeaders = @{ 'Content-Type' = 'application/json' }
$geminiBody = '{"text":"Explain AI in 10 words"}'
Test-Endpoint -Name "Gemini Text Generation" -Url "$ServiceUrl/api/gemini/generate" -Method "POST" -Headers $geminiHeaders -Body $geminiBody

# Test 5: Gemini summarization
$summaryBody = '{"text":"The stock market showed strong performance today with NIFTY gaining 2% and banking stocks leading the rally. Technology stocks also performed well with increased investor confidence."}'
Test-Endpoint -Name "Gemini Summarization" -Url "$ServiceUrl/api/gemini/summary" -Method "POST" -Headers $geminiHeaders -Body $summaryBody

# Test 6: HuggingFace sentiment analysis
$sentimentBody = '{"text":"Markets look very bullish today with strong momentum!"}'
Test-Endpoint -Name "HuggingFace Sentiment" -Url "$ServiceUrl/api/huggingface/sentiment" -Method "POST" -Headers $geminiHeaders -Body $sentimentBody

Write-Host "`n💰 Testing Dhan API Integration..." -ForegroundColor Yellow

# Test 7: Dhan positions
Test-Endpoint -Name "Dhan Positions" -Url "$ServiceUrl/api/dhan/positions"

# Test 8: Dhan orders
Test-Endpoint -Name "Dhan Orders" -Url "$ServiceUrl/api/dhan/orders"

# Test 9: Dhan option chain
Test-Endpoint -Name "Dhan Option Chain (NIFTY)" -Url "$ServiceUrl/api/dhan/optionchain/NIFTY"

# Test 10: Dhan callback endpoint
Test-Endpoint -Name "Dhan Callback" -Url "$ServiceUrl/api/dhan/callback?code=test123"

Write-Host "`n📊 Calculating Performance Metrics..." -ForegroundColor Yellow

# Calculate summary statistics
$responseTimes = $results.tests | ForEach-Object { $_.response_time_ms }
$results.summary.avg_response_time = if ($responseTimes.Count -gt 0) { 
    [math]::Round(($responseTimes | Measure-Object -Average).Average, 2) 
} else { 0 }
$results.summary.total_time = ($responseTimes | Measure-Object -Sum).Sum
$results.summary.min_response_time = ($responseTimes | Measure-Object -Minimum).Minimum
$results.summary.max_response_time = ($responseTimes | Measure-Object -Maximum).Maximum

# Performance analysis
$fastTests = ($results.tests | Where-Object { $_.response_time_ms -lt 500 }).Count
$mediumTests = ($results.tests | Where-Object { $_.response_time_ms -ge 500 -and $_.response_time_ms -lt 1000 }).Count
$slowTests = ($results.tests | Where-Object { $_.response_time_ms -ge 1000 }).Count

Write-Host "`n" + "=" * 80
Write-Host "📋 INFINITYAI ENGINE A - VERIFICATION REPORT" -ForegroundColor Green
Write-Host "=" * 80

Write-Host "`n🎯 SUMMARY METRICS:" -ForegroundColor Cyan
Write-Host "   Total Tests: $($results.summary.total_tests)"
Write-Host "   ✅ Passed: $($results.summary.passed)" -ForegroundColor Green
Write-Host "   ❌ Failed: $($results.summary.failed)" -ForegroundColor $(if($results.summary.failed -eq 0){'Green'}else{'Red'})
Write-Host "   📈 Success Rate: $([math]::Round(($results.summary.passed / $results.summary.total_tests) * 100, 2))%"

Write-Host "`n⚡ PERFORMANCE METRICS:" -ForegroundColor Cyan
Write-Host "   Average Response Time: $($results.summary.avg_response_time)ms"
Write-Host "   Minimum Response Time: $($results.summary.min_response_time)ms"
Write-Host "   Maximum Response Time: $($results.summary.max_response_time)ms"
Write-Host "   Total Execution Time: $($results.summary.total_time)ms"

Write-Host "`n🚀 PERFORMANCE DISTRIBUTION:" -ForegroundColor Cyan
Write-Host "   🟢 Fast (< 500ms): $fastTests tests"
Write-Host "   🟡 Medium (500ms-1s): $mediumTests tests"
Write-Host "   🔴 Slow (> 1s): $slowTests tests"

Write-Host "`n🔧 DETAILED TEST RESULTS:" -ForegroundColor Cyan
foreach ($test in $results.tests) {
    $statusIcon = if ($test.success) { "✅" } else { "❌" }
    $statusColor = if ($test.success) { "Green" } else { "Red" }
    
    Write-Host "   $statusIcon $($test.name)" -ForegroundColor $statusColor
    Write-Host "      URL: $($test.url)" -ForegroundColor Gray
    Write-Host "      Method: $($test.method) | Status: $($test.status_code) | Time: $($test.response_time_ms)ms" -ForegroundColor Gray
    
    if ($test.error) {
        Write-Host "      Error: $($test.error)" -ForegroundColor Red
    }
    
    if ($test.response_data -and $test.success) {
        if ($test.response_data.status) {
            Write-Host "      Status: $($test.response_data.status)" -ForegroundColor Gray
        }
        if ($test.response_data.engines) {
            Write-Host "      Engines: $($test.response_data.engines -join ', ')" -ForegroundColor Gray
        }
        if ($test.response_data.version) {
            Write-Host "      Version: $($test.response_data.version)" -ForegroundColor Gray
        }
        if ($test.response_data.count) {
            Write-Host "      Data Count: $($test.response_data.count)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

Write-Host "🏆 ENGINE A CAPABILITY ASSESSMENT:" -ForegroundColor Cyan

# Core functionality assessment
$coreTests = $results.tests | Where-Object { $_.name -match "(Root|Health|Signals)" }
$coreSuccess = ($coreTests | Where-Object { $_.success }).Count
Write-Host "   📊 Core Functionality: $coreSuccess/$($coreTests.Count) - $(if($coreSuccess -eq $coreTests.Count){'✅ OPERATIONAL'}else{'⚠️ DEGRADED'})"

# AI integration assessment
$aiTests = $results.tests | Where-Object { $_.name -match "(Gemini|HuggingFace)" }
$aiSuccess = ($aiTests | Where-Object { $_.success }).Count
Write-Host "   🤖 AI Integration: $aiSuccess/$($aiTests.Count) - $(if($aiSuccess -eq $aiTests.Count){'✅ FULL AI READY'}elseif($aiSuccess -gt 0){'⚠️ PARTIAL AI'}else{'❌ AI OFFLINE'})"

# Dhan integration assessment
$dhanTests = $results.tests | Where-Object { $_.name -match "Dhan" }
$dhanSuccess = ($dhanTests | Where-Object { $_.success }).Count
Write-Host "   💰 Dhan Integration: $dhanSuccess/$($dhanTests.Count) - $(if($dhanSuccess -eq $dhanTests.Count){'✅ MARKET DATA READY'}elseif($dhanSuccess -gt 0){'⚠️ PARTIAL MARKET'}else{'❌ MARKET OFFLINE'})"

Write-Host "`n🎯 OVERALL SYSTEM STATUS:" -ForegroundColor Yellow
$overallHealth = if ($results.summary.passed -eq $results.summary.total_tests) {
    "🟢 FULLY OPERATIONAL"
} elseif ($results.summary.passed -gt ($results.summary.total_tests * 0.7)) {
    "🟡 MOSTLY OPERATIONAL" 
} else {
    "🔴 NEEDS ATTENTION"
}
Write-Host "   $overallHealth" -ForegroundColor $(if($overallHealth.Contains("FULLY")){"Green"}elseif($overallHealth.Contains("MOSTLY")){"Yellow"}else{"Red"})

Write-Host "`n💾 Saving detailed report to engine_a_verification_report.json..." -ForegroundColor Gray
$results | ConvertTo-Json -Depth 10 | Out-File "engine_a_verification_report.json" -Encoding UTF8

Write-Host "`n✅ Verification Complete!" -ForegroundColor Green
Write-Host "📄 Detailed JSON report saved: engine_a_verification_report.json" -ForegroundColor Cyan
Write-Host "🔗 Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host "=" * 80