# InfinityAI.Pro Render Deployment Verification Script
# Run this after your services are deployed

Write-Host "🚀 Verifying InfinityAI.Pro Deployment on Render..." -ForegroundColor Green

# Frontend URL (replace with your actual Render URL)
$FRONTEND_URL = "https://infinityai-frontend.onrender.com"
$BACKEND_URL = "https://infinityai-backend.onrender.com"

Write-Host "`n📱 Frontend Checks:" -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri $FRONTEND_URL -Method GET -TimeoutSec 10
    Write-Host "✅ Frontend accessible: $($frontendResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🔧 Backend API Checks:" -ForegroundColor Yellow

# Health check
try {
    $healthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/health" -Method GET -TimeoutSec 10
    Write-Host "✅ Health endpoint: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Root endpoint
try {
    $rootResponse = Invoke-RestMethod -Uri "$BACKEND_URL/" -Method GET -TimeoutSec 10
    Write-Host "✅ Root endpoint: $($rootResponse.message)" -ForegroundColor Green
} catch {
    Write-Host "❌ Root endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# AI health check
try {
    $aiHealthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/ai/health" -Method GET -TimeoutSec 10
    Write-Host "✅ AI endpoint accessible" -ForegroundColor Green
} catch {
    Write-Host "⚠️ AI endpoint: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Trading health check
try {
    $tradingHealthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/trading/health" -Method GET -TimeoutSec 10
    Write-Host "✅ Trading endpoint accessible" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Trading endpoint: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n🎉 Deployment verification complete!" -ForegroundColor Green
Write-Host "Visit your app at: $FRONTEND_URL" -ForegroundColor Cyan

# Instructions for user
Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update the URLs in this script with your actual Render URLs"
Write-Host "2. Set up your environment variables in Render dashboard"
Write-Host "3. Monitor logs in Render dashboard for any issues"
Write-Host "4. Test your trading functionality with paper trading first"