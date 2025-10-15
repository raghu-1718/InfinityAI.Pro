#!/usr/bin/env pwsh
# InfinityAI.Pro End-to-End Verification Script
# Tests all components and ensures real user data flows correctly

Write-Host "🧩 InfinityAI.Pro End-to-End Verification & Personalization Test" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# Configuration
$DHAN_CLIENT_ID = "1101302170"
$EXPECTED_USER_NAME = "Raghu Chandra Raj"
$ENGINES = @{
    "Engine-A" = "https://engine-a-market-data-573866363639.us-central1.run.app"
    "Engine-B" = "https://engine-b-ai-ml-573866363639.us-central1.run.app" 
    "Engine-C" = "https://engine-c-573866363639-573866363639.us-central1.run.app"
    "Engine-D" = "https://engine-d-chatbot-573866363639.us-central1.run.app"
}
$FRONTEND_URL = "https://frontend-573866363639-573866363639.us-central1.run.app"

# Test results
$results = @()

function Test-Endpoint {
    param($name, $url, $expectedStatus = 200)
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method GET -ErrorAction Stop
        $status = "✅ PASS"
        $details = "HTTP $expectedStatus OK"
        
        # Special checks for specific endpoints
        if ($url -match "/api/portfolio") {
            if ($response.user.name -eq $EXPECTED_USER_NAME) {
                $details += " | User: $($response.user.name) ✅"
            } else {
                $details += " | User: $($response.user.name) ⚠️"
            }
            if ($response.source -eq "live") {
                $details += " | Source: Live ✅"
            } else {
                $details += " | Source: $($response.source) ⚠️"
            }
            if ($response.summary.total_pnl) {
                $details += " | P&L: ₹$($response.summary.total_pnl)"
            }
        }
        
        if ($url -match "/api/ai-signals") {
            $signalCount = $response.ai_signals.Count
            $details += " | Signals: $signalCount"
        }
        
    }
    catch {
        $status = "❌ FAIL"
        $details = $_.Exception.Message
    }
    
    return @{
        Name = $name
        Status = $status  
        Details = $details
    }
}

# Test 1: Dhan API Token Validation
Write-Host "`n🔐 Testing Dhan API Access Token..." -ForegroundColor Yellow
try {
    $token = gcloud secrets versions access latest --secret=dhan-access-token --project=after-yesterday-473512-k3
    $headers = @{ "access-token" = $token }
    
    $positionsResponse = Invoke-RestMethod -Uri "https://api.dhan.co/positions" -Headers $headers -ErrorAction Stop
    $results += @{
        Name = "Dhan API Token"
        Status = "✅ PASS"
        Details = "Valid token | Positions: $($positionsResponse.Count)"
    }
}
catch {
    $results += @{
        Name = "Dhan API Token"
        Status = "❌ FAIL" 
        Details = $_.Exception.Message
    }
}

# Test 2: Backend Engines
Write-Host "`n⚙️ Testing Backend Engines..." -ForegroundColor Yellow
foreach ($engine in $ENGINES.GetEnumerator()) {
    $testUrl = $engine.Value
    
    # Test specific endpoints for each engine
    switch ($engine.Key) {
        "Engine-A" { $testUrl += "/api/market-summary" }
        "Engine-B" { $testUrl += "/api/ai-signals" }
        "Engine-C" { $testUrl += "/api/portfolio" }  
        "Engine-D" { $testUrl += "/health" }
    }
    
    $results += Test-Endpoint -name $engine.Key -url $testUrl
}

# Test 3: Frontend
Write-Host "`n🌐 Testing Frontend..." -ForegroundColor Yellow
$results += Test-Endpoint -name "Frontend" -url $FRONTEND_URL

# Test 4: Portfolio API Integration
Write-Host "`n📊 Testing Portfolio API Integration..." -ForegroundColor Yellow
$portfolioResult = Test-Endpoint -name "Portfolio API" -url "$($ENGINES['Engine-C'])/api/portfolio"
$results += $portfolioResult

# Test 5: AI Signals Integration  
Write-Host "`n🤖 Testing AI Signals Integration..." -ForegroundColor Yellow
$aiResult = Test-Endpoint -name "AI Signals API" -url "$($ENGINES['Engine-B'])/api/ai-signals"
$results += $aiResult

# Display Results
Write-Host "`n📋 VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

$passCount = 0
$failCount = 0

foreach ($result in $results) {
    $color = if ($result.Status -match "✅") { "Green" } else { "Red" }
    Write-Host "$($result.Name.PadRight(20)) $($result.Status) | $($result.Details)" -ForegroundColor $color
    
    if ($result.Status -match "✅") { $passCount++ } else { $failCount++ }
}

Write-Host "`n🎯 FINAL VERIFICATION RESULTS:" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host "✅ Tests Passed: $passCount" -ForegroundColor Green
Write-Host "❌ Tests Failed: $failCount" -ForegroundColor Red

# Check if user personalization is working
$portfolioTest = $results | Where-Object { $_.Name -eq "Portfolio API" }
if ($portfolioTest.Details -match $EXPECTED_USER_NAME) {
    Write-Host "`n🎉 USER PERSONALIZATION: SUCCESS!" -ForegroundColor Green
    Write-Host "   Dashboard should show: 'Welcome, $EXPECTED_USER_NAME'" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ USER PERSONALIZATION: NEEDS ATTENTION" -ForegroundColor Yellow  
    Write-Host "   Dashboard may still show 'Demo User'" -ForegroundColor Yellow
}

# Final Dashboard URL
Write-Host "`n🔗 Access your personalized dashboard at:" -ForegroundColor Cyan
Write-Host "   $FRONTEND_URL" -ForegroundColor White

# DNS Test
Write-Host "`n🌐 Testing DNS Propagation for infinityai.pro..." -ForegroundColor Yellow
try {
    $dnsResult = nslookup infinityai.pro
    if ($dnsResult -match "googlehosted.com") {
        Write-Host "✅ DNS: Points to Google Cloud" -ForegroundColor Green
    } else {
        Write-Host "⚠️ DNS: May still point to old provider" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ DNS: Unable to resolve" -ForegroundColor Red
}

Write-Host "`n✨ Verification Complete!" -ForegroundColor Cyan