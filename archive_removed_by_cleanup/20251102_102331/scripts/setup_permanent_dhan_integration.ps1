# Complete Dhan API Integration Setup for InfinityAI.Pro
# This script sets up permanent Dhan API integration with automated token refresh

Write-Host "🚀 Setting up permanent Dhan API integration for InfinityAI.Pro" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# Check if Python is available
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    exit 1
}

# Check if required files exist
$requiredFiles = @("dhan_auto_refresh.py", "nifty_options_analysis.py", "setup_dhan_token_scheduler.ps1")
foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        Write-Host "❌ $file not found. Please run the setup scripts first." -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required files found" -ForegroundColor Green

# Test the auto-refresh service
Write-Host "🔄 Testing automated token refresh service..." -ForegroundColor Yellow
try {
    $output = python dhan_auto_refresh.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Auto-refresh service test passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Auto-refresh service test failed" -ForegroundColor Red
        Write-Host "Output: $output" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Auto-refresh service test failed with exception: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test the main analysis script (run quietly)
Write-Host "📊 Testing NIFTY options analysis with Dhan API..." -ForegroundColor Yellow
try {
    $output = python nifty_options_analysis.py 2>&1
    if ($output -match "Analysis completed successfully") {
        Write-Host "✅ NIFTY analysis script test passed" -ForegroundColor Green
    } else {
        Write-Host "❌ NIFTY analysis script test failed" -ForegroundColor Red
        Write-Host "Output: $output" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ NIFTY analysis script test failed with exception: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Set up Windows Task Scheduler
Write-Host "📅 Setting up Windows Task Scheduler for daily token refresh..." -ForegroundColor Yellow
try {
    $output = powershell -ExecutionPolicy Bypass -File setup_dhan_token_scheduler.ps1 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Windows Task Scheduler setup completed" -ForegroundColor Green
    } else {
        Write-Host "❌ Windows Task Scheduler setup failed" -ForegroundColor Red
        Write-Host "Output: $output" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Windows Task Scheduler setup failed with exception: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "" -ForegroundColor White
Write-Host "🎉 Dhan API permanent integration setup completed successfully!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "📋 What was set up:" -ForegroundColor White
Write-Host "   ✅ Automated token refresh service (dhan_auto_refresh.py)" -ForegroundColor Green
Write-Host "   ✅ Updated NIFTY analysis with auto token validation" -ForegroundColor Green
Write-Host "   ✅ Windows Task Scheduler for daily token refresh at 9:00 AM" -ForegroundColor Green
Write-Host "   ✅ Fallback to NSE data when Dhan API is unavailable" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "🔄 How it works:" -ForegroundColor White
Write-Host "   • Tokens are validated before each API call" -ForegroundColor Cyan
Write-Host "   • Expired tokens are automatically refreshed using API key/secret" -ForegroundColor Cyan
Write-Host "   • Daily scheduled refresh ensures tokens never expire" -ForegroundColor Cyan
Write-Host "   • NSE fallback provides reliable data when needed" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "📊 To use:" -ForegroundColor White
Write-Host "   • Run 'python nifty_options_analysis.py' anytime for fresh analysis" -ForegroundColor Yellow
Write-Host "   • Tokens refresh automatically - no manual intervention needed" -ForegroundColor Yellow
Write-Host "   • Check Task Scheduler for refresh status and logs" -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "⚠️ Important Notes:" -ForegroundColor White
Write-Host "   • Keep your API key and secret secure" -ForegroundColor Red
Write-Host "   • Monitor the logs for any authentication issues" -ForegroundColor Red
Write-Host "   • The system will automatically handle token expiration" -ForegroundColor Red
Write-Host "" -ForegroundColor White
Write-Host "🎯 You're all set for permanent Dhan API integration!" -ForegroundColor Green