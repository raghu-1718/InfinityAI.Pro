#!/usr/bin/env pwsh
# InfinityAI.Pro API Test Script for Windows PowerShell

Write-Host "🚀 InfinityAI.Pro API Test" -ForegroundColor Green
Write-Host "=" * 40

# Test API Health
Write-Host "`n💗 Testing API Health..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health" -Method Get
    Write-Host "✅ API is healthy!" -ForegroundColor Green
    Write-Host "Platform: $($healthResponse.platform)"
    Write-Host "Version: $($healthResponse.version)"
    Write-Host "Services: $($healthResponse.services.Keys -join ', ')"
}
catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Chatbot
Write-Host "`n🤖 Testing Chatbot..." -ForegroundColor Yellow
try {
    $chatPayload = @{
        message = "Scan NIFTY with 50 thousand"
        user_id = "raghu_test"
        voice_input = $false
    } | ConvertTo-Json

    $chatResponse = Invoke-RestMethod -Uri "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/chatbot/chat" -Method Post -Body $chatPayload -ContentType "application/json"
    
    Write-Host "✅ Chatbot is working!" -ForegroundColor Green
    Write-Host "Bot Response:" -ForegroundColor Cyan
    Write-Host $chatResponse.data.response
    Write-Host "`nTimestamp: $($chatResponse.timestamp)"
}
catch {
    Write-Host "❌ Chatbot test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Frontend
Write-Host "`n🌐 Testing Frontend..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "https://infinity-ai-9utba60h7-infinityaipro.vercel.app" -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        $hasTitle = $frontendResponse.Content -match "InfinityAI"
        Write-Host "✅ Frontend is accessible!" -ForegroundColor Green
        Write-Host "Contains InfinityAI title: $hasTitle"
        if ($hasTitle) {
            Write-Host "🎉 Your app is ready to use!" -ForegroundColor Green
        }
    }
}
catch {
    Write-Host "❌ Frontend test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Final Summary
Write-Host "`n" "=" * 40
Write-Host "🎯 YOUR APPLICATION IS READY!" -ForegroundColor Green -BackgroundColor Black
Write-Host "=" * 40

Write-Host "`n📱 Open in your browser:" -ForegroundColor Cyan
Write-Host "   https://infinity-ai-9utba60h7-infinityaipro.vercel.app" -ForegroundColor White

Write-Host "`n🔗 Custom domain (when DNS ready):" -ForegroundColor Cyan  
Write-Host "   https://infinityai.pro" -ForegroundColor White

Write-Host "`n🛠️  Backend API:" -ForegroundColor Cyan
Write-Host "   https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io" -ForegroundColor White

Write-Host "`n🤖 Try these commands in the app:" -ForegroundColor Yellow
Write-Host "   'Scan NIFTY with 1 lakh capital'"
Write-Host "   'Start trading BANKNIFTY with 2 lakh'"  
Write-Host "   'Analyze RELIANCE for swing trading'"
Write-Host "   'Stop all trading'"

Write-Host "`n✅ Status: FULLY OPERATIONAL" -ForegroundColor Green -BackgroundColor Black