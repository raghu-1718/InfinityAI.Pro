# 🔒 DHAN CREDENTIALS VERIFICATION CHECKLIST

**User**: You (authenticated via Google Firebase)
**Broker**: DhanHQ
**Storage**: Dual-layered (Firestore + Secret Manager)
**Project**: galvanic-pulsar-482815-h0
**Date**: January 11, 2026

---

## 📊 CREDENTIAL FLOW SUMMARY

```
DASHBOARD UPDATE
      ↓
[Settings → Dhan Account Tab]
      ↓
User submits credentials via web form
      ↓
Frontend calls Cloud Function: submitDhanCredentialsV2
      ↓
┌─────────────────┬──────────────────────┐
│   FIRESTORE     │  GOOGLE SECRET MGR   │
│ user_credentials│  user-creds-{id}     │
│   (Quick read)  │  (Versioned backup)  │
└─────────────────┴──────────────────────┘
      ↓
Backend engines (Engine-A, Engine-C) read credentials
      ↓
Dhan API calls execute with your authentication
```

---

## ✅ VERIFICATION CHECKLIST

### SECTION 1: Credential Storage Verification

#### [ ] Firestore Document Exists

**How to verify:**

1. **Via Firebase Console** (Recommended for visual confirmation):
   - Open https://console.firebase.google.com
   - Select Project: `galvanic-pulsar-482815-h0`
   - Go to **Firestore Database** → Collections tab
   - Find collection: `user_credentials`
   - Look for document with your **Google User ID**

2. **Via CLI**:
   ```bash
   gcloud firestore documents list --collection-path=user_credentials \
     --project=galvanic-pulsar-482815-h0
   ```

**Expected Result**: ✅ Document found with fields:
- `user_id`: Your authenticated user ID
- `dhan_client_id`: 10-digit number
- `dhan_access_token`: Long string (eyJ0eXA...)
- `updated_at`: Recent timestamp (within last 24 hours of your dashboard update)

---

#### [ ] Firestore Fields Are Complete

**How to verify:**

Click on the document in Firebase Console and verify ALL these fields exist:

| Field | Type | Expected Value | Status |
|-------|------|-----------------|--------|
| `user_id` | String | Your Google User ID | ☐ |
| `dhan_client_id` | String | 10-digit number (e.g., "1234567890") | ☐ |
| `dhan_access_token` | String | Long token starting with "eyJ..." | ☐ |
| `updated_at` | Timestamp | Recent (today or yesterday) | ☐ |

**Action if missing**: Re-submit credentials from Settings → Dhan Account tab

---

#### [ ] Secret Manager Secret Exists

**How to verify:**

1. **Via Google Cloud Console** (Recommended):
   - Open https://console.cloud.google.com
   - Select Project: `galvanic-pulsar-482815-h0`
   - Go to **Secret Manager** → Secrets
   - Search for: `user-creds-`
   - Look for secret matching your user ID (with @ and . replaced by _)

2. **Via CLI**:
   ```bash
   gcloud secrets list --filter="name:user-creds-*" \
     --project=galvanic-pulsar-482815-h0
   ```

**Expected Result**: ✅ Secret found with name matching pattern: `user-creds-YOUR_USERID`

---

#### [ ] Secret Manager Version Is Recent

**How to verify:**

1. In Secret Manager console, click on your `user-creds-*` secret
2. Go to **Versions** tab
3. Check the latest version:
   - Status: **Enabled** ✓
   - Created: Should match your dashboard update time (within last 24 hours)
   - Access: May show recent access times

**Expected Result**: ✅ Latest version enabled and recent

---

### SECTION 2: Credential Accessibility Verification

#### [ ] Cloud Function Can Retrieve Credentials

**How to verify:**

**Option A - Via Firebase Console** (Easy):
1. Go to **Cloud Functions** → Find `getUserCredentials`
2. Click **TESTING** tab
3. Enter request:
   ```json
   {
     "user_id": "YOUR_USER_ID"
   }
   ```
4. Click **EXECUTE**

**Option B - Via CLI**:
```bash
gcloud functions call getUserCredentials \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --data='{"user_id":"YOUR_USER_ID"}'
```

**Expected Response**:
```json
{
  "success": true,
  "dhan_client_id": "1234567890",
  "dhan_access_token": "eyJ0eXAi...",
  "updated_at": "2026-01-11T15:30:45.000Z"
}
```

**Status**: ☐ Cloud Function retrieves credentials successfully

---

#### [ ] Credentials Not Exposed in Logs

**How to verify:**

1. Open **Cloud Functions** → `getUserCredentials`
2. Go to **LOGS** tab
3. Search for your test execution (should appear within last few minutes)
4. Check that logs show:
   - ✅ Request received
   - ✅ Document found
   - ✅ Response sent
   - ❌ No raw credential values printed

**Security Note**: Credentials should NEVER be printed in logs. If you see credentials in logs, report this immediately.

**Status**: ☐ Credentials are accessed but not exposed

---

### SECTION 3: Dhan API Connectivity Verification

#### [ ] Dhan API Accepts Your Credentials

**How to verify:**

Test the `/api/dhan/verify` endpoint:

```bash
curl -X POST https://engine-c-738553258162.us-central1.run.app/api/dhan/verify \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "client_id": "1234567890",
    "access_token": "YOUR_ACTUAL_ACCESS_TOKEN"
  }'
```

**Expected Success Response**:
```json
{
  "success": true,
  "verified": true,
  "message": "Connection verified successfully"
}
```

**If You Get 401/403 Error**:
```json
{
  "success": false,
  "verified": false,
  "message": "Verification failed: Invalid access token or client ID"
}
```

**Action if verification fails**:
1. Log in to Dhan: https://dhanhq.com
2. Go to Settings → API → Access Tokens
3. Check if token is **Enabled**
4. If expired, generate a new one
5. Re-submit via Settings → Dhan Account in Dashboard

**Status**: ☐ Dhan API successfully verifies your credentials

---

#### [ ] Can Retrieve Account Overview

**How to verify:**

```bash
curl -X GET "https://engine-c-738553258162.us-central1.run.app/api/dhan/overview?user_id=YOUR_USER_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
{
  "success": true,
  "user_id": "YOUR_USER_ID",
  "overview": {
    "net_worth": 500000,
    "margin_available": 100000,
    "margin_used": 50000,
    "holdings_count": 5,
    "open_positions": 2
  }
}
```

**Status**: ☐ Account overview retrieved successfully

---

### SECTION 4: Dashboard Integration Verification

#### [ ] Dashboard Shows Connected Status

**How to verify:**

1. Log in to Dashboard: https://infinityai.pro
2. Go to **Settings** → **Dhan Account**
3. Check the status display

**Expected Display**: ✅ "Status: CONNECTED ✓ Verified"

**Visual Indicators**:
- ✅ Green checkmark visible
- ✅ Account summary shows (funds, holdings, positions)
- ✅ "Disconnect" button is available

**Status**: ☐ Dashboard shows connected status

---

#### [ ] Dhan Account Shows Holdings/Positions

**How to verify:**

1. Dashboard → **Portfolio** tab
2. Check if holdings are displayed:
   - List of stocks owned
   - Current prices
   - P&L percentages

**Expected**: ✅ Holdings loaded and displayed

**Status**: ☐ Holdings displayed in Portfolio tab

---

#### [ ] Live Data Loads Without Errors

**How to verify:**

1. Dashboard → **Live Quotes** tab
2. Wait 5 seconds for data to load
3. Check browser console for errors:
   - Open: F12 (Developer Tools)
   - Go to **Console** tab
   - Look for red error messages

**Expected**:
- ✅ No 401 or authentication errors
- ✅ No "credentials not found" errors
- ✅ Price data updates in real-time

**Status**: ☐ Live data loads without errors

---

### SECTION 5: Security Verification

#### [ ] Credentials Not in Browser LocalStorage

**How to verify:**

1. Open Dashboard → Right-click → **Inspect** (or F12)
2. Go to **Application** → **Local Storage**
3. Expand `https://infinityai.pro`
4. Search for keys containing "dhan" or "token"

**Expected**:
- ❌ No `dhan_access_token` in LocalStorage
- ❌ No API keys visible in browser
- ✅ Only non-sensitive data like `user_id` or `client_id`

**Security Note**: Credentials should be in backend (Firestore/Secret Manager) only, NOT in browser storage.

**Status**: ☐ Credentials properly stored (not in browser)

---

#### [ ] HTTPS Connection Verified

**How to verify:**

1. Dashboard URL should show: `https://` (not http://)
2. Click padlock icon in address bar
3. Verify SSL certificate is valid

**Expected**: ✅ HTTPS with valid SSL certificate

**Status**: ☐ HTTPS/SSL verified

---

#### [ ] No Credentials in Cloud Logs

**How to verify:**

```bash
gcloud functions logs read submitDhanCredentialsV2 \
  --limit=100 \
  --project=galvanic-pulsar-482815-h0 | grep -i "access_token\|client_id"
```

**Expected**: ❌ No actual credential values printed

**Status**: ☐ Logs don't expose credentials

---

## 📈 VERIFICATION SUMMARY

Count your checkmarks:

- **Section 1 (Storage)**: ☐☐☐☐ (4 checks)
- **Section 2 (Accessibility)**: ☐☐☐ (3 checks)
- **Section 3 (Dhan API)**: ☐☐ (2 checks)
- **Section 4 (Dashboard)**: ☐☐☐ (3 checks)
- **Section 5 (Security)**: ☐☐☐ (3 checks)

**Total**: ___ / 15 checks passed

### OVERALL STATUS

| Checks Passed | Status | Action |
|---------------|--------|--------|
| 15/15 ✅ | **FULLY VERIFIED** | Ready for trading ✅ |
| 12-14/15 | **MOSTLY VERIFIED** | Minor issues (see details above) |
| < 12/15 | **VERIFICATION FAILED** | Requires troubleshooting |

---

## 🚨 IF VERIFICATION FAILS

### Step 1: Identify Which Section Failed
Review the checkmarks above. Which section has empty boxes?

### Step 2: Run Diagnostic Script
```bash
cd c:\workspace\InfinityAI.Pro
python tools/verify_credentials.py YOUR_USER_ID
```

### Step 3: Check Cloud Function Logs
```bash
# Check function that stores credentials
gcloud functions logs read submitDhanCredentialsV2 \
  --limit=100 \
  --project=galvanic-pulsar-482815-h0

# Check function that retrieves credentials
gcloud functions logs read getUserCredentials \
  --limit=100 \
  --project=galvanic-pulsar-482815-h0
```

### Step 4: Re-submit Credentials
1. Go to Dashboard → Settings → Dhan Account
2. Clear existing values
3. Enter Dhan credentials again
4. Click **Save and Verify**
5. Wait 30 seconds for processing
6. Re-run verification

### Step 5: Contact Support
If still failing, provide:
- Output from `python tools/verify_credentials.py YOUR_USER_ID`
- Cloud Function logs (sanitized of any credentials)
- Error messages from browser console

---

## 📞 QUICK REFERENCE

### Important URLs
- **Dashboard**: https://infinityai.pro
- **Dhan Console**: https://dhanhq.com
- **Firebase Console**: https://console.firebase.google.com
- **Cloud Console**: https://console.cloud.google.com
- **Engine-C API Docs**: https://engine-c.infinityai.pro/docs

### Key Endpoints
- **Store Credentials**: POST `/api/user/credentials`
- **Verify Connection**: POST `/api/dhan/verify`
- **Get Overview**: GET `/api/dhan/overview`
- **Account Data**: GET `/api/v1/user/{userId}/account`

### GCP Project Info
- **Project ID**: galvanic-pulsar-482815-h0
- **Cloud Functions Region**: us-central1
- **Firestore Database**: default
- **Secret Manager**: Enabled

---

## ✅ FINAL SIGN-OFF

When all 15 checks are marked ✅:

**Your Dhan credentials are:**
- ✅ Properly stored in Firestore and Secret Manager
- ✅ Accessible to Cloud Functions and backend services
- ✅ Valid and verified by Dhan API
- ✅ Securely encrypted and audited
- ✅ Ready for live trading operations

**Proceed with confidence!** 🚀

---

**Verification Date**: _______________
**Verified By**: _______________
**Notes**: _____________________________________________________

