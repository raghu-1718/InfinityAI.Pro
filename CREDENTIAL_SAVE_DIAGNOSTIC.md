# ❌ CREDENTIAL SAVE DIAGNOSTIC

**Status**: Credentials NOT saved to Firestore
**Date**: 2026-01-19 07:06 UTC
**User ID**: `user_1768804393712_idm50j`

---

## What I Checked

✅ Backend logs for POST requests → **NONE FOUND**
✅ API endpoints test → **Still returning 401 "credentials not found"**
✅ Recent activity logs → **Only GET requests, no credential saves**

---

## The Issue

When you clicked "Save Credentials" in the dashboard, the request **did not reach the backend**. This could be because:

1. **Wrong URL configured** - Frontend might be pointing to wrong endpoint
2. **Network error** - Request failed before reaching server
3. **CORS issue** - Browser blocked the request
4. **JavaScript error** - Form submission failed silently

---

## How to Diagnose in Your Browser

### Step 1: Open DevTools Console

1. Press **F12** (Windows) or **Cmd+Option+I** (Mac)
2. Click **Console** tab
3. Look for RED error messages
4. Take a screenshot if you see any

### Step 2: Check Network Tab

1. In DevTools, click **Network** tab
2. Keep it open
3. Go back to Settings → DHAN Account
4. Click "Save Credentials" again
5. **Watch for POST request** in Network tab

**What to look for:**

- Request to: `engine-c-228557716858.us-central1.run.app/api/user/credentials`
- Method: `POST`
- Status: Should be `200` (green)
- Response: Should show `{"status": "success", ...}`

**If you DON'T see the POST request:**

- There's a JavaScript error preventing form submission
- Check Console tab for errors

**If you see the POST request but Status is RED (400/500):**

- Click on the request
- Check "Response" tab
- Copy the error message

### Step 3: Check What Endpoint Is Being Called

In the Network tab, if you see a request when clicking "Save", check:

- **Request URL**: Should be `https://engine-c-228557716858.us-central1.run.app/api/user/credentials`
- **If different**: The frontend has wrong URL configured

---

## Possible Frontend Issues

### Issue 1: Wrong API URL

Frontend might be calling a different endpoint or wrong domain.

**Check**: [frontend/web-app/src/app/(dashboard)/settings/page.tsx](<frontend/web-app/src/app/(dashboard)/settings/page.tsx>) line 117:

```typescript
const response = await fetch(`${ENGINE_C_URL}/api/user/credentials`, {
```

**Expected ENGINE_C_URL**: `https://engine-c-228557716858.us-central1.run.app`

### Issue 2: Network Request Failing

CORS, SSL, or network errors preventing request from completing.

**Symptom**: Console shows errors like:

- "CORS policy blocked"
- "Failed to fetch"
- "Net::ERR_CONNECTION_REFUSED"

### Issue 3: Form Validation Failing

Frontend validation preventing form submission.

**Check**: Are all required fields filled?

- Client ID
- Access Token
- (API Key and API Secret might be optional)

---

## What to Try Next

### Try 1: Manual API Test (Verify Backend Works)

Run this command to test if backend accepts credentials:

```powershell
$body = @{
    user_id = "user_1768804393712_idm50j"
    client_id = "YOUR_CLIENT_ID_HERE"
    access_token = "YOUR_ACCESS_TOKEN_HERE"
    api_key = ""
    api_secret = ""
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://engine-c-228557716858.us-central1.run.app/api/user/credentials" -Method POST -Body $body -ContentType "application/json"
```

**Replace**:

- `YOUR_CLIENT_ID_HERE` with your actual Dhan client ID (e.g., `1101302170`)
- `YOUR_ACCESS_TOKEN_HERE` with your actual access token (starts with `eyJ0...`)

**Expected Response**:

```json
{
  "status": "success",
  "message": "Credentials saved successfully",
  "user_id": "user_1768804393712_idm50j",
  "client_id": "1101302170"
}
```

**If this works**: Backend is fine, issue is in frontend
**If this fails**: Backend has an issue (show me the error)

### Try 2: Check Frontend ENV Variables

Check if `ENGINE_C_URL` is set correctly in frontend:

```powershell
# Check frontend .env file
Get-Content C:\workspace\InfinityAI.Pro\frontend\web-app\.env* 2>$null | Select-String "ENGINE"
```

### Try 3: Check Browser Console

When you click "Save Credentials":

1. Watch Console tab for errors
2. Copy any error messages
3. Share them with me

---

## Quick Test Commands

Run these to verify backend is reachable:

```powershell
# Test health endpoint (should work)
curl -s "https://engine-c-228557716858.us-central1.run.app/health"

# Test credentials endpoint with your user_id (should fail with 401 since no creds saved yet)
curl -s "https://engine-c-228557716858.us-central1.run.app/api/dhan/funds?user_id=user_1768804393712_idm50j"

# Test system status (should work)
curl -s "https://engine-c-228557716858.us-central1.run.app/api/system/status"
```

---

## Next Steps

**Please do this:**

1. Open your dashboard in browser
2. Open DevTools (F12)
3. Go to Settings → DHAN Account
4. Fill in credentials
5. Click "Save Credentials"
6. **Take screenshots of**:
   - Console tab (any errors?)
   - Network tab (any POST request?)
   - Response tab of the POST request (if it exists)
7. Share screenshots or copy/paste error messages

**Then I can:**

- Identify exactly where the request is failing
- Fix the frontend or backend issue
- Get your credentials saved properly

---

## Backend Status

✅ Backend is deployed and working
✅ POST `/api/user/credentials` endpoint exists
✅ Resolver code is ready
❌ No credentials saved yet
❌ POST request never reached backend

The backend is ready - we just need to figure out why the frontend isn't sending the save request successfully.
