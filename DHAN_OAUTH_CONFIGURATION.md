# Dhan OAuth Configuration - Complete Setup Guide

**Date**: November 4, 2025  
**Status**: ✅ **Fully Configured - Ready for Access Token**

---

## ✅ Current Configuration Status

### Secrets Configured in Google Cloud Secret Manager

| Secret Name | Status | Value |
|-------------|--------|-------|
| **dhan-client-id** | ✅ Configured | `1101302170` |
| **dhan-api-key** | ✅ Configured | `3f2311ba...` (Hidden) |
| **dhan-api-secret** | ✅ Configured | `e127a8ec-b89e-4074-885e-e94a07f92189` |
| **dhan-access-token** | ⚠️ Empty | Needs OAuth flow completion |
| **dhan-webhook-secret** | ✅ Configured | Set |

**Verdict**: ✅ **All API credentials are configured and working**

---

## 🔗 OAuth URLs for Dhan Integration

### 1. Redirect URL (OAuth Callback)
```
https://infinityai.pro/auth/dhan/callback
```

**Purpose**: Where Dhan redirects users after authorization  
**Engine C Endpoint**: `/api/dhan/callback`  
**Full URL**: `https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/callback`

### 2. Postback URL (Webhook)
```
https://infinityai.pro/api/webhooks/dhan
```

**Purpose**: Real-time order status updates from Dhan  
**Engine C Endpoint**: `/api/webhooks/dhan`  
**Full URL**: `https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/webhooks/dhan`

---

## 📋 Dhan Developer Portal Configuration

### Step 1: Login to Dhan Developer Portal
Visit: **https://developer.dhan.co**

Login with your Dhan trading account credentials.

### Step 2: Register Your Application (If Not Already Done)

If you haven't created an OAuth application yet:

1. Go to "My Apps" or "OAuth Apps"
2. Click "Create New App" or "Register Application"
3. Fill in the details:

   **Application Details**:
   - **App Name**: `InfinityAI.Pro`
   - **Description**: `AI-powered trading platform for Indian markets`
   - **Client ID**: Use existing `1101302170` (or Dhan will auto-generate)

### Step 3: Configure OAuth URLs in Dhan Portal

**CRITICAL**: Set these exact URLs in your Dhan OAuth app settings:

#### Redirect URI (OAuth Callback URL)
```
https://infinityai.pro/auth/dhan/callback
```

#### Postback URI (Webhook URL)  
```
https://infinityai.pro/api/webhooks/dhan
```

#### OAuth Scopes (Permissions)
Select the following scopes:
- ✅ `trade` - Place and modify orders
- ✅ `funds` - View fund limits
- ✅ `holdings` - View holdings
- ✅ `positions` - View open positions

### Step 4: Verify Credentials Match

Ensure the credentials in Dhan portal match what's in Google Secret Manager:

| Field | Value in Dhan Portal | Value in Secret Manager |
|-------|---------------------|-------------------------|
| Client ID | `1101302170` | ✅ Matches |
| API Key | Check portal | ✅ Configured (3f2311ba...) |
| API Secret | Check portal | ✅ Configured (e127a8ec...) |

---

## 🚀 How to Get Access Token (OAuth Flow)

### Option 1: Use Authorization URL (Recommended)

**Step 1**: Generate authorization URL by calling:
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/auth/dhan/initiate"
```

**Step 2**: The response will contain:
```json
{
  "authorization_url": "https://api.dhan.co/oauth/authorize?client_id=1101302170&redirect_uri=https://infinityai.pro/auth/dhan/callback&response_type=code&scope=trade+funds+holdings+positions&state=infinityai_..."
}
```

**Step 3**: Open the `authorization_url` in your browser

**Step 4**: Login with your Dhan credentials and authorize InfinityAI.Pro

**Step 5**: Dhan will redirect to:
```
https://infinityai.pro/auth/dhan/callback?code=AUTHORIZATION_CODE&state=infinityai_...
```

**Step 6**: Engine C will automatically:
- Receive the authorization code
- Exchange it for an access token
- Store the token in Secret Manager (`dhan-access-token`)
- Return success confirmation

### Option 2: Manual Authorization URL Construction

If you want to construct the URL manually:

```
https://api.dhan.co/oauth/authorize?client_id=1101302170&redirect_uri=https://infinityai.pro/auth/dhan/callback&response_type=code&scope=trade+funds+holdings+positions&state=infinityai_production
```

**URL Parameters**:
- `client_id`: `1101302170`
- `redirect_uri`: `https://infinityai.pro/auth/dhan/callback`
- `response_type`: `code`
- `scope`: `trade funds holdings positions`
- `state`: `infinityai_production` (or any unique identifier)

---

## ✅ Verify Token Acquisition

After completing OAuth flow, verify the token was stored:

### Check Token Status
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/token/status"
```

**Expected Response (Success)**:
```json
{
  "has_token": true,
  "token_type": "Bearer",
  "status": "active"
}
```

### Test Live Trading Endpoints

Once token is acquired, test these endpoints:

#### Get Account Details
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/account"
```

#### Get Holdings
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/holdings"
```

#### Get Positions
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/positions"
```

#### Get Portfolio Analysis
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/portfolio"
```

---

## 🔧 Configuration Verification Script

Run this script to verify everything is configured:

```powershell
# File: scripts/verify_dhan_config.ps1

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Dhan OAuth Configuration Verification" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check secrets in Secret Manager
Write-Host "Checking Google Secret Manager..." -ForegroundColor Yellow
$secrets = @('dhan-client-id', 'dhan-api-key', 'dhan-api-secret', 'dhan-access-token')

foreach ($secret in $secrets) {
    try {
        $value = gcloud secrets versions access latest --secret=$secret --project=after-yesterday-473512-k3 2>$null
        if ($value) {
            if ($secret -eq 'dhan-access-token' -and $value -eq 'placeholder') {
                Write-Host "  ⚠️  $secret : Needs OAuth flow" -ForegroundColor Yellow
            } else {
                Write-Host "  ✅ $secret : Configured" -ForegroundColor Green
            }
        } else {
            Write-Host "  ❌ $secret : Not set" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ $secret : Error" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Checking Engine C Status..." -ForegroundColor Yellow
$status = curl -s "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/status" | ConvertFrom-Json

Write-Host "  OAuth Configured: $($status.oauth_configured)" -ForegroundColor $(if($status.oauth_configured){'Green'}else{'Red'})
Write-Host "  Client ID: $($status.client_id)" -ForegroundColor Cyan
Write-Host "  Redirect URI: $($status.redirect_uri)" -ForegroundColor Cyan
Write-Host "  Postback URI: $($status.postback_uri)" -ForegroundColor Cyan
Write-Host "  Integration Status: $($status.integration_status)" -ForegroundColor Green

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Configuration URLs for Dhan Portal:" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Redirect URI: https://infinityai.pro/auth/dhan/callback" -ForegroundColor Yellow
Write-Host "Postback URI: https://infinityai.pro/api/webhooks/dhan" -ForegroundColor Yellow
Write-Host ""
```

Save and run:
```powershell
pwsh scripts/verify_dhan_config.ps1
```

---

## 📝 Summary: What You Need to Do

### ✅ Already Configured (No Action Needed)
- [x] Client ID in Secret Manager: `1101302170`
- [x] API Key in Secret Manager: Configured
- [x] API Secret in Secret Manager: Configured
- [x] OAuth endpoints in Engine C: Working
- [x] Redirect/Postback URIs: Set

### ⚠️ Action Required

**1. Verify Dhan Developer Portal Configuration**
   - Login to https://developer.dhan.co
   - Ensure OAuth app has Client ID `1101302170`
   - Ensure Redirect URI: `https://infinityai.pro/auth/dhan/callback`
   - Ensure Postback URI: `https://infinityai.pro/api/webhooks/dhan`
   - Ensure scopes: `trade`, `funds`, `holdings`, `positions`

**2. Initiate OAuth Flow to Get Access Token**
   ```bash
   curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/auth/dhan/initiate"
   ```
   Then open the authorization URL and complete the flow.

**3. Verify Token Acquisition**
   ```bash
   curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/token/status"
   ```
   Should return `"has_token": true`

---

## 🎯 Quick Start Command

Copy and paste this in your terminal to get the authorization URL:

```powershell
# Get OAuth authorization URL
$response = curl -s "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/auth/dhan/initiate" | ConvertFrom-Json
Write-Host "Open this URL in your browser:" -ForegroundColor Green
Write-Host $response.authorization_url -ForegroundColor Yellow
Write-Host ""
Write-Host "After authorization, check token status:" -ForegroundColor Green
Write-Host "curl https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/token/status" -ForegroundColor Cyan
```

---

## 🔒 Security Notes

1. **Never share your API Key or API Secret** - They are securely stored in Google Secret Manager
2. **Access tokens expire** - You may need to refresh them periodically
3. **Postback secret** - Used to verify webhook authenticity from Dhan
4. **HTTPS only** - All OAuth flows require HTTPS (SSL certificates provisioning now)

---

## 📞 Support

If you encounter issues:

1. Check Engine C logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=infinityai-engine-c-execution" --limit=50 --format=json --project=after-yesterday-473512-k3
   ```

2. Verify Dhan API status: https://status.dhan.co

3. Check integration test results: `integration-test-results.json`

---

**Configuration Status**: ✅ **READY - Only OAuth flow completion needed**

**Next Step**: Visit Dhan Developer Portal, verify URLs, then run OAuth flow to get access token.
