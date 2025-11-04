# Dhan Live Trading End-to-End Verification Script
# Tests all Dhan integration endpoints with real access token

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dhan Live Trading - End-to-End Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$engineC = "https://infinityai-engine-c-execution-573866363639.us-central1.run.app"
$testResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET"
    )
    
    Write-Host "Testing: $Name..." -NoNewline
    try {
        $response = if ($Method -eq "GET") {
            Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30
        } else {
            Invoke-RestMethod -Uri $Url -Method Post -TimeoutSec 30 -Body "{}" -ContentType "application/json"
        }
        
        Write-Host " ✅ PASS" -ForegroundColor Green
        return @{
            Test = $Name
            Status = "PASS"
            Response = $response
        }
    } catch {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            Test = $Name
            Status = "FAIL"
            Error = $_.Exception.Message
        }
    }
}

Write-Host "Phase 1: Token Verification" -ForegroundColor Yellow
Write-Host ""

# Test 1: Health Check
$result = Test-Endpoint -Name "Engine C Health" -Url "$engineC/health"
$testResults += $result

# Test 2: Token Status
$result = Test-Endpoint -Name "Token Status" -Url "$engineC/api/dhan/token/status"
$testResults += $result

if ($result.Response.has_token) {
    Write-Host ""
    Write-Host "  ✅ Access Token: PRESENT" -ForegroundColor Green
    Write-Host "  Token Expiry: $($result.Response.exp)" -ForegroundColor Cyan
    Write-Host "  Seconds Remaining: $($result.Response.seconds_remaining)" -ForegroundColor Cyan
    Write-Host "  Is Fresh: $($result.Response.is_fresh)" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "  ❌ Access Token: NOT FOUND" -ForegroundColor Red
    Write-Host "  Cannot proceed with live trading tests" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Phase 2: Account & Authentication" -ForegroundColor Yellow
Write-Host ""

# Test 3: Dhan Status
$result = Test-Endpoint -Name "Dhan Integration Status" -Url "$engineC/api/dhan/status"
$testResults += $result

# Test 4: Account Details
$result = Test-Endpoint -Name "Account Details" -Url "$engineC/api/dhan/account"
$testResults += $result

if ($result.Status -eq "PASS") {
    Write-Host ""
    Write-Host "  ✅ Account Connected" -ForegroundColor Green
    if ($result.Response.clientId) {
        Write-Host "  Client ID: $($result.Response.clientId)" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "Phase 3: Holdings & Positions" -ForegroundColor Yellow
Write-Host ""

# Test 5: Holdings
$result = Test-Endpoint -Name "Holdings" -Url "$engineC/api/dhan/holdings"
$testResults += $result

if ($result.Status -eq "PASS" -and $result.Response.data) {
    Write-Host "  Holdings Count: $($result.Response.data.Count)" -ForegroundColor Cyan
}

# Test 6: Holdings Analysis
$result = Test-Endpoint -Name "Holdings Analysis" -Url "$engineC/api/dhan/holdings/analysis"
$testResults += $result

# Test 7: Positions
$result = Test-Endpoint -Name "Positions" -Url "$engineC/api/positions"
$testResults += $result

if ($result.Status -eq "PASS" -and $result.Response.positions) {
    Write-Host "  Open Positions: $($result.Response.positions.Count)" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Phase 4: Fund Management" -ForegroundColor Yellow
Write-Host ""

# Test 8: Fund Limits
$result = Test-Endpoint -Name "Fund Limits" -Url "$engineC/api/dhan/funds"
$testResults += $result

if ($result.Status -eq "PASS") {
    if ($result.Response.availableBalance) {
        Write-Host "  Available Balance: ₹$($result.Response.availableBalance)" -ForegroundColor Cyan
    }
    if ($result.Response.sodLimit) {
        Write-Host "  SOD Limit: ₹$($result.Response.sodLimit)" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "Phase 5: Order Management" -ForegroundColor Yellow
Write-Host ""

# Test 9: Orders Status
$result = Test-Endpoint -Name "Orders Status" -Url "$engineC/api/orders/status"
$testResults += $result

# Test 10: Order History
$result = Test-Endpoint -Name "Order History" -Url "$engineC/api/dhan/orders"
$testResults += $result

if ($result.Status -eq "PASS" -and $result.Response.data) {
    Write-Host "  Total Orders: $($result.Response.data.Count)" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Phase 6: Portfolio Analysis" -ForegroundColor Yellow
Write-Host ""

# Test 11: Portfolio Summary
$result = Test-Endpoint -Name "Portfolio Summary" -Url "$engineC/api/portfolio"
$testResults += $result

if ($result.Status -eq "PASS") {
    if ($result.Response.total_value) {
        Write-Host "  Portfolio Value: ₹$($result.Response.total_value)" -ForegroundColor Cyan
    }
    if ($result.Response.total_pnl) {
        $pnlColor = if ($result.Response.total_pnl -gt 0) { "Green" } else { "Red" }
        Write-Host "  Total P&L: ₹$($result.Response.total_pnl)" -ForegroundColor $pnlColor
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$passed = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
$total = $testResults.Count

Write-Host "Total Tests: $total" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if($failed -gt 0){"Red"}else{"Green"})
Write-Host ""

$passRate = [math]::Round(($passed / $total) * 100, 1)
Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if($passRate -eq 100){"Green"}elseif($passRate -gt 70){"Yellow"}else{"Red"})

Write-Host ""

if ($failed -eq 0) {
    Write-Host "🎉 All tests passed! Dhan live trading is fully operational." -ForegroundColor Green
} else {
    Write-Host "⚠️  Some tests failed. Review the results above." -ForegroundColor Yellow
}

Write-Host ""

# Save results to JSON
$testResults | ConvertTo-Json -Depth 10 | Out-File "dhan-live-trading-test-results.json"
Write-Host "Results saved to: dhan-live-trading-test-results.json" -ForegroundColor Cyan

Write-Host ""
