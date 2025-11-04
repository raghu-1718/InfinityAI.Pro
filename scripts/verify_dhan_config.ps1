# Dhan OAuth Configuration Verification Script
# Verifies all Dhan credentials and URLs are properly configured

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Dhan OAuth Configuration Verification" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check secrets in Secret Manager
Write-Host "1️⃣  Checking Google Secret Manager..." -ForegroundColor Yellow
Write-Host ""

$secrets = @{
    'dhan-client-id' = 'Client ID'
    'dhan-api-key' = 'API Key'
    'dhan-api-secret' = 'API Secret'
    'dhan-access-token' = 'Access Token'
    'dhan-webhook-secret' = 'Webhook Secret'
}

$allConfigured = $true
foreach ($secret in $secrets.Keys) {
    try {
        $value = gcloud secrets versions access latest --secret=$secret --project=after-yesterday-473512-k3 2>$null
        if ($value) {
            if ($secret -eq 'dhan-access-token' -and ($value -eq 'placeholder' -or $value -eq 'demo-token')) {
                Write-Host "  ⚠️  $($secrets[$secret]) ($secret): OAuth flow needed" -ForegroundColor Yellow
            } else {
                # Show partial value for verification
                $displayValue = if ($value.Length -gt 16) { 
                    "$($value.Substring(0, 8))..." 
                } else { 
                    $value 
                }
                Write-Host "  ✅ $($secrets[$secret]) ($secret): $displayValue" -ForegroundColor Green
            }
        } else {
            Write-Host "  ❌ $($secrets[$secret]) ($secret): Not set" -ForegroundColor Red
            $allConfigured = $false
        }
    } catch {
        Write-Host "  ❌ $($secrets[$secret]) ($secret): Error accessing secret" -ForegroundColor Red
        $allConfigured = $false
    }
}

Write-Host ""
Write-Host "2️⃣  Checking Engine C OAuth Status..." -ForegroundColor Yellow
Write-Host ""

try {
    $status = curl -s "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/status" | ConvertFrom-Json
    
    Write-Host "  OAuth Active: " -NoNewline
    Write-Host $status.oauth_active -ForegroundColor $(if($status.oauth_active){'Green'}else{'Red'})
    
    Write-Host "  OAuth Configured: " -NoNewline
    Write-Host $status.oauth_configured -ForegroundColor $(if($status.oauth_configured){'Green'}else{'Red'})
    
    Write-Host "  Client ID: " -NoNewline
    Write-Host $status.client_id -ForegroundColor Cyan
    
    Write-Host "  Integration Status: " -NoNewline
    Write-Host $status.integration_status -ForegroundColor Green
    
    Write-Host ""
    Write-Host "  Redirect URI: " -NoNewline
    Write-Host $status.redirect_uri -ForegroundColor Cyan
    
    Write-Host "  Postback URI: " -NoNewline
    Write-Host $status.postback_uri -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "  Scopes: " -NoNewline
    Write-Host ($status.scopes -join ', ') -ForegroundColor Cyan
    
} catch {
    Write-Host "  ❌ Failed to connect to Engine C" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "3️⃣  Checking Token Status..." -ForegroundColor Yellow
Write-Host ""

try {
    $tokenStatus = curl -s "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/token/status" | ConvertFrom-Json
    
    Write-Host "  Has Token: " -NoNewline
    if ($tokenStatus.has_token) {
        Write-Host "✅ Yes" -ForegroundColor Green
        Write-Host "  Token Type: " -NoNewline
        Write-Host $tokenStatus.token_type -ForegroundColor Cyan
    } else {
        Write-Host "❌ No - OAuth flow required" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ⚠️  Could not check token status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "URLs for Dhan Developer Portal" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Copy these URLs to your Dhan OAuth app configuration:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Redirect URI (OAuth Callback):" -ForegroundColor White
Write-Host "  https://infinityai.pro/auth/dhan/callback" -ForegroundColor Green
Write-Host ""
Write-Host "Postback URI (Webhook):" -ForegroundColor White
Write-Host "  https://infinityai.pro/api/webhooks/dhan" -ForegroundColor Green
Write-Host ""

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

if (-not $tokenStatus.has_token) {
    Write-Host "To get an access token, run:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host '  $response = curl -s "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/auth/dhan/initiate" | ConvertFrom-Json' -ForegroundColor Cyan
    Write-Host '  Write-Host $response.authorization_url' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Then open the URL in your browser and complete the OAuth flow." -ForegroundColor White
} else {
    Write-Host "✅ Access token is configured!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test live trading endpoints:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  # Get account details" -ForegroundColor Gray
    Write-Host '  curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/account"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Get holdings" -ForegroundColor Gray
    Write-Host '  curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/holdings"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Get positions" -ForegroundColor Gray
    Write-Host '  curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/positions"' -ForegroundColor Cyan
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Configuration Summary" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

if ($allConfigured -and $status.oauth_configured) {
    Write-Host "✅ All credentials configured in Secret Manager" -ForegroundColor Green
    Write-Host "✅ OAuth endpoints configured in Engine C" -ForegroundColor Green
    Write-Host "✅ Redirect and Postback URIs set" -ForegroundColor Green
    Write-Host ""
    if ($tokenStatus.has_token) {
        Write-Host "🎉 Status: READY FOR LIVE TRADING" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Status: READY - Complete OAuth flow to get access token" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Some configuration issues detected" -ForegroundColor Yellow
    Write-Host "Review the output above and fix any ❌ items" -ForegroundColor Yellow
}

Write-Host ""
