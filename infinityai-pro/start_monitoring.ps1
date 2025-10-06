# 🚀 InfinityAI.Pro - Monitoring System Launcher
# PowerShell script to start the monitoring system

Write-Host "🌟 InfinityAI.Pro - Automatic Trading Monitor" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python." -ForegroundColor Red
    exit 1
}

# Change to the project directory
Set-Location -Path "C:\Users\Raghu\InfinityAI.Pro\infinityai-pro"

Write-Host ""
Write-Host "Available monitoring options:" -ForegroundColor Yellow
Write-Host "1. Single Analysis (Run once)" -ForegroundColor White
Write-Host "2. Continuous Monitoring (Every 5 minutes)" -ForegroundColor White
Write-Host "3. Auto Trading System (AI-powered)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select option (1-3)"

switch ($choice) {
    "1" {
        Write-Host "🔍 Running single analysis..." -ForegroundColor Green
        python continuous_monitor.py
    }
    "2" {
        Write-Host "🔄 Starting continuous monitoring..." -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
        python continuous_monitor.py continuous
    }
    "3" {
        Write-Host "🤖 Starting AI auto-trading system..." -ForegroundColor Green
        Write-Host "⚠️  WARNING: This will execute real trades!" -ForegroundColor Red
        $confirm = Read-Host "Type 'YES' to confirm auto-trading"
        if ($confirm -eq "YES") {
            python auto_trading_system.py
        } else {
            Write-Host "❌ Auto-trading cancelled" -ForegroundColor Yellow
        }
    }
    default {
        Write-Host "❌ Invalid option. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Monitoring session completed" -ForegroundColor Green
Write-Host "📊 Check your positions at: https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io" -ForegroundColor Cyan