# 🚀 InfinityAI.Pro - Live AI Trading Launcher
# PowerShell script to start the advanced AI trading system

Write-Host "🤖 InfinityAI.Pro - Advanced AI Trading System" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✨ Features:" -ForegroundColor Yellow
Write-Host "   • 6% profit → 3% trailing stop" -ForegroundColor Green
Write-Host "   • 12% profit → 6% stop loss protection" -ForegroundColor Green  
Write-Host "   • Automatic signal detection & execution" -ForegroundColor Green
Write-Host "   • Real-time fund management" -ForegroundColor Green
Write-Host "   • Multi-position trailing stops" -ForegroundColor Green
Write-Host ""

# Check current directory
Set-Location -Path "C:\Users\Raghu\InfinityAI.Pro\infinityai-pro"

Write-Host "Current Trading Status:" -ForegroundColor Yellow
Write-Host "======================" -ForegroundColor Yellow

# Run quick analysis first
Write-Host "🔍 Running quick position analysis..." -ForegroundColor Cyan
python continuous_monitor.py

Write-Host ""
Write-Host "Available Trading Modes:" -ForegroundColor Yellow
Write-Host "1. 📊 Analysis Mode (Safe - No trades)" -ForegroundColor White
Write-Host "2. 🔴 LIVE Trading Mode (Real money!)" -ForegroundColor Red
Write-Host "3. 🎯 Single Signal Check" -ForegroundColor White
Write-Host "4. 📈 Dashboard View" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select mode (1-4)"

switch ($choice) {
    "1" {
        Write-Host "📊 Starting Analysis Mode..." -ForegroundColor Green
        Write-Host "✅ Safe mode - No real trades will be executed" -ForegroundColor Green
        python advanced_ai_trader.py
    }
    "2" {
        Write-Host ""
        Write-Host "⚠️  DANGER: LIVE TRADING MODE!" -ForegroundColor Red
        Write-Host "⚠️  This will execute REAL trades with REAL money!" -ForegroundColor Red
        Write-Host "⚠️  Your account balance: Check first!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Features that WILL be active:" -ForegroundColor Yellow
        Write-Host "• Automatic buy/sell orders" -ForegroundColor Red
        Write-Host "• 6% profit → 3% trailing stops" -ForegroundColor Red
        Write-Host "• 12% profit → 6% stop loss" -ForegroundColor Red
        Write-Host "• Live signal execution" -ForegroundColor Red
        Write-Host ""
        
        $confirm1 = Read-Host "Type 'I UNDERSTAND' to continue"
        if ($confirm1 -eq "I UNDERSTAND") {
            $confirm2 = Read-Host "Type 'START LIVE TRADING' to confirm"
            if ($confirm2 -eq "START LIVE TRADING") {
                Write-Host "🔴 STARTING LIVE AI TRADING..." -ForegroundColor Red
                Write-Host "🚀 System will trade automatically every 2 minutes" -ForegroundColor Green
                Write-Host "⏹️  Press Ctrl+C to stop" -ForegroundColor Yellow
                python advanced_ai_trader.py live
            } else {
                Write-Host "❌ Live trading cancelled - Incorrect confirmation" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ Live trading cancelled - Safety check failed" -ForegroundColor Yellow
        }
    }
    "3" {
        Write-Host "🎯 Checking for trading signals..." -ForegroundColor Green
        python advanced_ai_trader.py
    }
    "4" {
        Write-Host "📈 Opening trading dashboard..." -ForegroundColor Green
        python trading_dashboard.py
    }
    default {
        Write-Host "❌ Invalid option. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Session completed" -ForegroundColor Green
Write-Host "📊 Dashboard: https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Pro Tips:" -ForegroundColor Yellow
Write-Host "   • Monitor positions regularly" -ForegroundColor White
Write-Host "   • System automatically trails profits at 6%" -ForegroundColor White
Write-Host "   • Stop losses protect at 12% profit level" -ForegroundColor White
Write-Host "   • Check account balance before live trading" -ForegroundColor White