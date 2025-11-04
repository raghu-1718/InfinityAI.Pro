#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Dhan OAuth Flow Helper and Token Manager
.DESCRIPTION
    Helps complete Dhan OAuth flow to get access token for real-time trading
#>

$ENGINE_C_URL = "https://infinityai-engine-c-execution-573866363639.us-central1.run.app"

Write-Host "`n=== InfinityAI.Pro - Dhan OAuth Flow Helper ===" -ForegroundColor Cyan
Write-Host "Engine C URL: $ENGINE_C_URL`n" -ForegroundColor Gray

# Step 1: Check current OAuth status
Write-Host "[Step 1] Checking current Dhan OAuth status..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "$ENGINE_C_URL/api/dhan/status" -Method Get
    Write-Host "✅ Current Status:" -ForegroundColor Green
    Write-Host "  OAuth Configured: $($status.oauth_configured)" -ForegroundColor White
    Write-Host "  OAuth Active: $($status.oauth_active)" -ForegroundColor White
    Write-Host "  Client ID: $($status.client_id)" -ForegroundColor White
    Write-Host "  Redirect URI: $($status.redirect_uri)" -ForegroundColor White
    Write-Host "  Postback URI: $($status.postback_uri)" -ForegroundColor White
    Write-Host "  Connected Users: $($status.connected_users)" -ForegroundColor White
} catch {
    Write-Host "❌ Error checking status: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Check token status
Write-Host "`n[Step 2] Checking Dhan access token status..." -ForegroundColor Yellow
try {
    $tokenStatus = Invoke-RestMethod -Uri "$ENGINE_C_URL/api/dhan/token/status" -Method Get
    Write-Host "✅ Token Status:" -ForegroundColor Green
    Write-Host "  Has Access Token: $($tokenStatus.has_access_token)" -ForegroundColor White
    
    if ($tokenStatus.has_access_token) {
        Write-Host "  Token Valid: $($tokenStatus.token_valid)" -ForegroundColor White
        Write-Host "  Expires At: $($tokenStatus.expires_at)" -ForegroundColor White
        Write-Host "  Days Until Expiry: $($tokenStatus.days_until_expiry)" -ForegroundColor White
        
        if ($tokenStatus.token_valid) {
            Write-Host "`n🎉 You already have a valid Dhan access token!" -ForegroundColor Green
            Write-Host "You can now test real-time trading features.`n" -ForegroundColor Green
            exit 0
        }
    } else {
        Write-Host "`n⚠️  No access token found. You need to complete OAuth flow." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check token status: $_" -ForegroundColor Yellow
}

# Step 3: Instructions for OAuth flow
Write-Host "`n=== Dhan OAuth Flow Instructions ===" -ForegroundColor Cyan

Write-Host "`nOption 1: Use Dhan Developer Portal" -ForegroundColor Yellow
Write-Host "1. Go to: https://api.dhan.co/developer" -ForegroundColor White
Write-Host "2. Login with your Dhan credentials" -ForegroundColor White
Write-Host "3. Navigate to: API Keys / OAuth Applications" -ForegroundColor White
Write-Host "4. Create new OAuth application or use existing one" -ForegroundColor White
Write-Host "5. Set redirect URI to: https://infinityai.pro/auth/callback" -ForegroundColor White
Write-Host "6. Note your:" -ForegroundColor White
Write-Host "   - Client ID" -ForegroundColor Gray
Write-Host "   - Client Secret" -ForegroundColor Gray
Write-Host "   - API Key" -ForegroundColor Gray

Write-Host "`nOption 2: Generate Authorization URL" -ForegroundColor Yellow
Write-Host "Use this URL to authorize InfinityAI.Pro:" -ForegroundColor White

# Check if we have client ID from secrets
$clientId = $status.client_id
if ($clientId) {
    $authUrl = "https://api.dhan.co/oauth/authorize?client_id=$clientId&redirect_uri=https://infinityai.pro/auth/callback&response_type=code&scope=trade+funds+holdings+positions&state=infinityai_$(Get-Date -Format 'yyyyMMddHHmmss')"
    
    Write-Host "`n📋 Authorization URL:" -ForegroundColor Cyan
    Write-Host $authUrl -ForegroundColor White
    
    Write-Host "`nInstructions:" -ForegroundColor Yellow
    Write-Host "1. Copy the URL above" -ForegroundColor White
    Write-Host "2. Open it in your browser" -ForegroundColor White
    Write-Host "3. Login to Dhan and authorize InfinityAI.Pro" -ForegroundColor White
    Write-Host "4. You'll be redirected with an authorization code" -ForegroundColor White
    Write-Host "5. The code will be automatically exchanged for an access token" -ForegroundColor White
} else {
    Write-Host "❌ Client ID not found in secrets. Please set DHAN_CLIENT_ID in GCP Secret Manager" -ForegroundColor Red
}

Write-Host "`nOption 3: Manual Token Refresh (If you have a refresh token)" -ForegroundColor Yellow
Write-Host "Run this command:" -ForegroundColor White
Write-Host "  curl -X POST $ENGINE_C_URL/api/dhan/token/refresh-from-secret" -ForegroundColor Gray

Write-Host "`n=== Testing Real-Time Features ===" -ForegroundColor Cyan
Write-Host "`nOnce you have a valid token, test these endpoints:" -ForegroundColor Yellow

$testEndpoints = @(
    @{Name="Account Info"; URL="/api/account"},
    @{Name="Holdings"; URL="/api/dhan/holdings/analysis"},
    @{Name="Positions"; URL="/api/positions"},
    @{Name="Portfolio"; URL="/api/portfolio"},
    @{Name="Orders"; URL="/api/orders"}
)

foreach ($endpoint in $testEndpoints) {
    Write-Host "`n$($endpoint.Name):" -ForegroundColor White
    Write-Host "  curl $ENGINE_C_URL$($endpoint.URL)" -ForegroundColor Gray
}

Write-Host "`n=== Market Data Testing (No Token Required) ===" -ForegroundColor Cyan
Write-Host "`nEngine A - Market Data:" -ForegroundColor Yellow
Write-Host "  curl https://infinityai-engine-a-573866363639.us-central1.run.app/api/market-data/NIFTY" -ForegroundColor Gray
Write-Host "  curl https://infinityai-engine-a-573866363639.us-central1.run.app/api/market-data/BANKNIFTY" -ForegroundColor Gray

Write-Host "`nEngine B - AI Signals:" -ForegroundColor Yellow
Write-Host "  curl https://infinityai-engine-b-573866363639.us-central1.run.app/api/ai-signals" -ForegroundColor Gray
Write-Host "  curl https://infinityai-engine-b-573866363639.us-central1.run.app/api/models/status" -ForegroundColor Gray

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
if ($tokenStatus.has_access_token -and $tokenStatus.token_valid) {
    Write-Host "✅ You have a valid Dhan access token - ready for live trading!" -ForegroundColor Green
} else {
    Write-Host "⚠️  No valid token - complete OAuth flow using Option 1 or 2 above" -ForegroundColor Yellow
}

Write-Host "`nDone!" -ForegroundColor Green
