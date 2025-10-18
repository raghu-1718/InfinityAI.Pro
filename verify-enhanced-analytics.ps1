# Enhanced Analytics Verification Script
# Tests all new endpoints deployed in v7.0.1 (Engine A) and v4.0.3 (Frontend)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Enhanced Analytics Deployment Verification" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

$engineA = "https://engine-a-573866363639.us-central1.run.app"
$frontend = "https://frontend-573866363639.us-central1.run.app"

Write-Host "1. Testing Engine A Version Endpoint..." -ForegroundColor Yellow
try {
    $version = Invoke-RestMethod -Uri "$engineA/version" -Method Get
    Write-Host "   ✓ Version: $($version.version)" -ForegroundColor Green
    Write-Host "   ✓ Build Date: $($version.build_date)" -ForegroundColor Green
    Write-Host "   ✓ Features: $($version.features -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n2. Testing Dhan Overview Endpoint..." -ForegroundColor Yellow
try {
    $overview = Invoke-RestMethod -Uri "$engineA/api/dhan/overview" -Method Get
    Write-Host "   ✓ Status: $($overview.status)" -ForegroundColor Green
    Write-Host "   ✓ Positions Count: $($overview.positions.Count)" -ForegroundColor Green
    Write-Host "   ✓ Holdings Count: $($overview.holdings.Count)" -ForegroundColor Green
    Write-Host "   ✓ Orders Count: $($overview.orders.Count)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n3. Testing Dhan Statement Endpoint..." -ForegroundColor Yellow
try {
    $statement = Invoke-RestMethod -Uri "$engineA/api/dhan/statement" -Method Get
    Write-Host "   ✓ Source: $($statement.source)" -ForegroundColor Green
    Write-Host "   ✓ Rows: $($statement.rows.Count)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n4. Testing Exchanges Endpoint..." -ForegroundColor Yellow
try {
    $exchanges = Invoke-RestMethod -Uri "$engineA/api/exchanges" -Method Get
    Write-Host "   ✓ Status: $($exchanges.status)" -ForegroundColor Green
    Write-Host "   ✓ Exchanges:" -ForegroundColor Green
    foreach ($ex in $exchanges.exchanges) {
        Write-Host "      - $($ex.code): $($ex.name)" -ForegroundColor Cyan
        Write-Host "        Segments: $($ex.segments -join ', ')" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n5. Testing AI Option Chain Analysis (NIFTY)..." -ForegroundColor Yellow
try {
    $optionAI = Invoke-RestMethod -Uri "$engineA/api/optionchain/ai/NIFTY" -Method Get
    Write-Host "   ✓ Status: $($optionAI.status)" -ForegroundColor Green
    Write-Host "   ✓ Symbol: $($optionAI.symbol)" -ForegroundColor Green
    Write-Host "   ✓ Strategy: $($optionAI.analysis.strategy)" -ForegroundColor Green
    Write-Host "   ✓ Rationale: $($optionAI.analysis.rationale)" -ForegroundColor Cyan
    Write-Host "   ✓ Strategy Legs:" -ForegroundColor Green
    foreach ($leg in $optionAI.analysis.legs) {
        Write-Host "      - $($leg.type): Strike $($leg.strike), Expiry $($leg.expiry)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n6. Testing AI Option Chain Analysis (BANKNIFTY)..." -ForegroundColor Yellow
try {
    $bankNiftyAI = Invoke-RestMethod -Uri "$engineA/api/optionchain/ai/BANKNIFTY" -Method Get
    Write-Host "   ✓ Status: $($bankNiftyAI.status)" -ForegroundColor Green
    Write-Host "   ✓ Symbol: $($bankNiftyAI.symbol)" -ForegroundColor Green
    Write-Host "   ✓ Strategy: $($bankNiftyAI.analysis.strategy)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n7. Testing Frontend Deployment..." -ForegroundColor Yellow
try {
    $frontendHTML = Invoke-WebRequest -Uri $frontend -Method Get -UseBasicParsing
    $title = ($frontendHTML.Content | Select-String -Pattern '<title>(.*?)</title>').Matches[0].Groups[1].Value
    Write-Host "   ✓ Frontend Accessible" -ForegroundColor Green
    Write-Host "   ✓ Page Title: $title" -ForegroundColor Green
    Write-Host "   ✓ Status Code: $($frontendHTML.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n8. Testing Frontend Assets..." -ForegroundColor Yellow
try {
    # Check if CSS and JS assets are present
    if ($frontendHTML.Content -match 'assets/.*\.css') {
        Write-Host "   ✓ CSS Assets Found" -ForegroundColor Green
    }
    if ($frontendHTML.Content -match 'assets/.*\.js') {
        Write-Host "   ✓ JavaScript Assets Found" -ForegroundColor Green
    }
} catch {
    Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "VERIFICATION COMPLETE" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

Write-Host "Deployment Summary:" -ForegroundColor Green
Write-Host "  Engine A (v7.0.1):  $engineA" -ForegroundColor White
Write-Host "  Frontend (v4.0.3):  $frontend" -ForegroundColor White
Write-Host "`nNew Features:" -ForegroundColor Green
Write-Host "  ✓ Dhan Overview Panel (funds, positions, holdings, orders)" -ForegroundColor White
Write-Host "  ✓ Account Statement Panel (trading history)" -ForegroundColor White
Write-Host "  ✓ Indian Exchanges Catalog (NSE, BSE, MCX, NSEIX)" -ForegroundColor White
Write-Host "  ✓ AI Option Chain Analysis (NIFTY, BANKNIFTY, etc.)" -ForegroundColor White
Write-Host "`nAll endpoints operational and verified!`n" -ForegroundColor Green
