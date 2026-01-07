# Firebase Authorized Domains Fix

## Problem

Firebase Authentication is blocking requests from `galvanic-pulsar-482815-h0.web.app` with error:

```
Firebase: Error (auth/requests-from-referer-https://galvanic-pulsar-482815-h0.web.app-are-blocked.)
```

## Root Cause

The domain `galvanic-pulsar-482815-h0.web.app` is not in the Firebase Authentication authorized domains list.

## Solution

### Option 1: Firebase Console (Manual - RECOMMENDED)

1. Go to [Firebase Console](https://console.firebase.google.com/project/galvanic-pulsar-482815-h0/authentication/providers)
2. Click **Settings** (gear icon) in Authentication
3. Scroll to **Authorized domains**
4. Click **Add domain**
5. Add the following domains:
   - `galvanic-pulsar-482815-h0.web.app`
   - `galvanic-pulsar-482815-h0.firebaseapp.com`
   - `localhost` (for local development)

### Option 2: gcloud Command Line

```powershell
# Update Identity Platform config
gcloud identity platform project-configs update `
  --add-authorized-domains="galvanic-pulsar-482815-h0.web.app,galvanic-pulsar-482815-h0.firebaseapp.com" `
  --project=galvanic-pulsar-482815-h0
```

### Option 3: REST API

```powershell
$PROJECT_ID = "galvanic-pulsar-482815-h0"
$ACCESS_TOKEN = (gcloud auth print-access-token)

$body = @{
  authorizedDomains = @(
    "galvanic-pulsar-482815-h0.web.app",
    "galvanic-pulsar-482815-h0.firebaseapp.com",
    "localhost"
  )
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://identitytoolkit.googleapis.com/admin/v2/projects/$PROJECT_ID/config?updateMask=authorizedDomains" `
  -Method PATCH `
  -Headers @{ Authorization = "Bearer $ACCESS_TOKEN"; "Content-Type" = "application/json" } `
  -Body $body
```

## Verification

After adding domains, test authentication:

1. Open: https://galvanic-pulsar-482815-h0.web.app/login
2. Click "Sign in with Google"
3. Should authenticate without error

## Expected Domains List

- `galvanic-pulsar-482815-h0.web.app` ✅
- `galvanic-pulsar-482815-h0.firebaseapp.com` ✅
- `localhost` ✅ (development only)

## Status

🔴 **ACTION REQUIRED:** Add authorized domains via Firebase Console (fastest method)
