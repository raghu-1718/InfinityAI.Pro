# 🚨 URGENT: Firebase Auth Configuration Fix

## Problem
```
Firebase: Error (auth/requests-from-referer-http://localhost:3000-are-blocked.)
```

## Root Cause
`.env.local` was pointing to **wrong Firebase project**:
- ❌ Was: `gen-lang-client-0779271931` (wrong)
- ✅ Now: `galvanic-pulsar-482815-h0` (correct)

## Changes Made
Updated `.env.local` with correct credentials:
- API Key: `AIzaSyD_y3lIPm7bTEXy3Uy4deGTnZPpjr2A8B8`
- Auth Domain: `galvanic-pulsar-482815-h0.firebaseapp.com`
- Project ID: `galvanic-pulsar-482815-h0`

## Step 1: Clear Browser Cache & Restart Dev Server

```bash
# Kill running dev server (Ctrl+C)
# Then:
npm run dev
```

Browser: **Ctrl+Shift+Delete** → Clear all cookies/cache → Refresh localhost:3000

## Step 2: If Still Blocked - Add localhost:3000 to Firebase

Go to [Firebase Console](https://console.firebase.google.com/):

1. Select **galvanic-pulsar-482815-h0** project
2. Go to **Authentication** → **Settings** → **Authorized Domains**
3. Click **Add Domain**
4. Enter: `localhost:3000`
5. Click **Add**

## Step 3: Verify Login Works

After config change:
- Refresh browser
- Try signing in with Google
- Should see two-step verification

## Expected Result

✅ Firebase login should work
✅ Session state permissions restored (from earlier fix)
✅ getFunds endpoint should work (once Dhan credentials saved)

---

**Timeline**: Changes take effect immediately after Save in Firebase Console
