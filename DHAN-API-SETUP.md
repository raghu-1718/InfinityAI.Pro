# Dhan API Configuration Guide

**Date:** November 28, 2025  
**Project:** InfinityAI.Pro Trading Platform

---

## 🔑 Dhan API Credentials Setup

### Step 1: Register Your Application with Dhan

Visit **Dhan API Portal**: https://myaccount.dhan.co

1. Login to your Dhan account
2. Navigate to **Settings** → **API**
3. Click **Create New API App**
4. Fill in the details:

---

## 📋 Required Configuration URLs

### Postback URL (for Order Updates/Webhooks)
```
https://engine-c.infinityai.pro/api/dhan/postback
```
**Purpose:** Receives real-time order execution updates from Dhan

### Redirect URL (for OAuth Authentication)
```
https://infinityai.pro/auth/dhan/callback
```
**OR (if using Firebase directly)**
```
https://after-yesterday-473512-k3.web.app/auth/dhan/callback
```
**Purpose:** OAuth callback after successful authentication

---

## 🔐 API Credentials You'll Receive

After registering, Dhan will provide:

| Credential | Environment Variable | Storage Location | Update Frequency |
|------------|---------------------|------------------|------------------|
| **Client ID** | `DHAN_CLIENT_ID` | Secret Manager | Once (permanent) |
| **API Key** | N/A | Secret: `dhan-api-key` | Once (permanent) |
| **API Secret** | N/A | Secret: `dhan-api-secret` | Once (permanent) |
| **Access Token** | `DHAN_ACCESS_TOKEN` | Frontend Update | Daily |

---

## ⚙️ Configure Credentials in Secret Manager

### One-Time Setup (Run Once)

```powershell
# Navigate to project directory
cd C:\workspace\InfinityAI.Pro

# Set Client ID
gcloud secrets create DHAN_CLIENT_ID `
  --replication-policy=automatic `
  --project=after-yesterday-473512-k3

echo "YOUR_CLIENT_ID_HERE" | gcloud secrets versions add DHAN_CLIENT_ID `
  --data-file=- `
  --project=after-yesterday-473512-k3

# Update API Key (already exists)
echo "YOUR_API_KEY_HERE" | gcloud secrets versions add dhan-api-key `
  --data-file=- `
  --project=after-yesterday-473512-k3

# Update API Secret (already exists)
echo "YOUR_API_SECRET_HERE" | gcloud secrets versions add dhan-api-secret `
  --data-file=- `
  --project=after-yesterday-473512-k3
```

---

## 🔄 Daily Access Token Update

### Method 1: Via Frontend Dashboard (Recommended)

1. Open: https://infinityai.pro/settings
2. Navigate to **API Configuration** section
3. Paste your new Dhan Access Token
4. Click **Update Token**
5. System automatically updates Secret Manager

### Method 2: Via Command Line

```powershell
# Update access token manually
echo "YOUR_NEW_ACCESS_TOKEN" | gcloud secrets versions add DHAN_ACCESS_TOKEN `
  --data-file=- `
  --project=after-yesterday-473512-k3
```

---

## 📊 Market Analysis - November 28, 2025

### Market Timing (IST)
- **Pre-Market:** 9:00 AM - 9:15 AM
- **Regular Session:** 9:15 AM - 3:30 PM
- **Post-Market:** 3:40 PM - 4:00 PM

### Current Status
**Check Live Status:** [NSE India](https://www.nseindia.com) | [BSE India](https://www.bseindia.com)

### To Get Real-Time Market Data:

1. **Configure Dhan API** (follow steps above)
2. **Update Access Token** daily
3. **Test Engine B:**
   ```bash
   curl -X POST https://engine-b.infinityai.pro/orchestrate \
     -H "Content-Type: application/json" \
     -d '{"symbol": "NIFTY", "qty": 1, "strategy": "intraday"}'
   ```

---

## 🧪 Test Your Configuration

### 1. Test Engine C (Execution)
```powershell
Invoke-RestMethod -Uri "https://engine-c.infinityai.pro/" -Method Get
```
**Expected:** Should show trade execution capabilities

### 2. Test Engine B (Orchestration)
```powershell
Invoke-RestMethod -Uri "https://engine-b.infinityai.pro/" -Method Get
```
**Expected:** Should show orchestration capabilities

### 3. Test Live Data Subscription
```powershell
$body = @{
    symbol = "RELIANCE"
    exchange = "NSE"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://engine-b.infinityai.pro/dhan/subscribe-live-data" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

---

## 🚨 Important Notes

1. **Access Token Expiry:** Dhan access tokens typically expire daily
2. **Update Schedule:** Update token before 9:00 AM IST daily
3. **Security:** Never commit access tokens to Git
4. **Monitoring:** Check Engine logs if orders fail

---

## 📱 Frontend Token Update Interface

The frontend dashboard (`https://infinityai.pro/settings`) includes:

- ✅ Secure token input field
- ✅ One-click update to Secret Manager
- ✅ Token validation
- ✅ Last update timestamp
- ✅ Connection status indicator

---

## 🔗 Useful Links

- **Dhan API Documentation:** https://dhanhq.co/docs
- **Dhan Account:** https://myaccount.dhan.co
- **Engine A Docs:** https://engine-a.infinityai.pro/docs
- **Engine B Docs:** https://engine-b.infinityai.pro/docs
- **Engine C Docs:** https://engine-c.infinityai.pro/docs

---

## ✅ Verification Checklist

- [ ] Registered app at Dhan API portal
- [ ] Configured Postback URL
- [ ] Configured Redirect URL
- [ ] Received Client ID, API Key, API Secret
- [ ] Stored credentials in Secret Manager
- [ ] Updated DHAN_CLIENT_ID environment variable
- [ ] Tested token update via frontend
- [ ] Verified live data subscription works
- [ ] Confirmed order placement functionality

---

**Status:** Ready for Dhan API integration  
**Next Step:** Register your app at https://myaccount.dhan.co
