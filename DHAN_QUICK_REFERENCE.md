# 🚀 Dhan OAuth - Quick Reference Card

## ✅ Configuration Status: READY

All API credentials are configured. **You only need to request a new access token.**

---

## 🔑 Your Dhan Credentials (Configured in Secret Manager)

| Credential | Value | Status |
|------------|-------|--------|
| **Client ID** | `1101302170` | ✅ Working |
| **API Key** | `3f2311ba...` | ✅ Working |
| **API Secret** | `e127a8ec-b89e-4074-885e-e94a07f92189` | ✅ Working |
| **Access Token** | Empty (needs OAuth flow) | ⚠️ Action Required |

---

## 🔗 URLs to Configure in Dhan Developer Portal

Visit: **https://developer.dhan.co** → Your OAuth App → Settings

### Redirect URL (OAuth Callback)
```
https://infinityai.pro/auth/dhan/callback
```

### Postback URL (Webhook)
```
https://infinityai.pro/api/webhooks/dhan
```

### OAuth Scopes
- ✅ `trade` - Place and modify orders
- ✅ `funds` - View fund limits
- ✅ `holdings` - View holdings
- ✅ `positions` - View open positions

---

## 🎯 How to Get Access Token (3 Simple Steps)

### Step 1: Get Authorization URL

Run this command:
```powershell
$response = curl -s "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/auth/dhan/initiate" | ConvertFrom-Json
Write-Host $response.authorization_url
```

**Expected Output**:
```
https://api.dhan.co/oauth/authorize?client_id=1101302170&redirect_uri=https://infinityai.pro/auth/dhan/callback&response_type=code&scope=trade+funds+holdings+positions&state=infinityai_...
```

### Step 2: Complete Authorization

1. **Copy the URL** from Step 1
2. **Open it in your browser**
3. **Login** with your Dhan trading account
4. **Click "Authorize"** to grant InfinityAI.Pro access

### Step 3: Verify Token

After authorization, Dhan redirects back and Engine C automatically exchanges the code for a token.

Verify it worked:
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/token/status"
```

**Expected Response**:
```json
{
  "has_token": true,
  "token_type": "Bearer",
  "status": "active"
}
```

---

## ✅ Once Token is Acquired, Test These Endpoints

### Get Account Details
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/account"
```

### Get Holdings
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/dhan/holdings"
```

### Get Current Positions
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/positions"
```

### Get Portfolio Analysis
```bash
curl "https://infinityai-engine-c-execution-573866363639.us-central1.run.app/api/portfolio"
```

---

## 🛠️ Troubleshooting

### Issue: "Client ID mismatch"
**Solution**: Verify Client ID in Dhan portal matches `1101302170`

### Issue: "Redirect URI mismatch"
**Solution**: Ensure Dhan portal has exact URL: `https://infinityai.pro/auth/dhan/callback`

### Issue: "Token not found after OAuth"
**Solution**: Check Engine C logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=infinityai-engine-c-execution" --limit=20 --format=json --project=after-yesterday-473512-k3 | jq '.[] | select(.textPayload | contains("dhan")) | .textPayload'
```

### Issue: SSL certificate not ready
**Solution**: OAuth flow requires HTTPS. Wait for SSL provisioning (15-60 min) or use direct Cloud Run URLs for now.

---

## 📋 Verification Checklist

Before requesting access token, ensure:

- [ ] Logged into Dhan Developer Portal
- [ ] OAuth app exists with Client ID `1101302170`
- [ ] Redirect URI set to `https://infinityai.pro/auth/dhan/callback`
- [ ] Postback URI set to `https://infinityai.pro/api/webhooks/dhan`
- [ ] Scopes include: trade, funds, holdings, positions
- [ ] API Key and Secret match values in Secret Manager

---

## 🎉 Summary

**Current Status**: ✅ **All credentials configured and working**

**What's Working**:
- ✅ Client ID: `1101302170`
- ✅ API Key: Configured
- ✅ API Secret: Configured
- ✅ Redirect URL: Set
- ✅ Postback URL: Set
- ✅ OAuth endpoints: Operational

**What You Need to Do**:
1. Verify URLs in Dhan Developer Portal
2. Run OAuth flow to get access token (3 simple steps above)
3. Start live trading!

---

**Need Help?** Run: `pwsh scripts/verify_dhan_config.ps1`

**Full Documentation**: See `DHAN_OAUTH_CONFIGURATION.md`
