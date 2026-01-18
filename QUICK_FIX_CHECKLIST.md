# 🚀 IMMEDIATE ACTION REQUIRED - 3 Steps to Fix

## Step 1: Stop Dev Server & Clear Cache (2 min)

**In Terminal:**
```
Ctrl+C
```

**In Browser:**
1. Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
2. Select "All time" from time range
3. Check: Cookies, Cache, Cached images/files
4. Click "Clear data"
5. Close browser tab

## Step 2: Restart Dev Server (1 min)

**In Terminal:**
```bash
npm run dev
```

Wait for:
```
✓ Ready in XX.Xs
```

## Step 3: Test Login (2 min)

1. Open `http://localhost:3000`
2. Click **"Sign in with Google"**
3. Should see Google sign-in popup (NO referer error)
4. Complete sign-in
5. Enter **2FA code** if prompted

---

## Expected Results

### ✅ After Step 2 - Dev Server Restarted
- Next.js starts without errors
- Console shows "Ready in XXs"

### ✅ After Step 3 - Login Succeeds
- Google sign-in popup appears
- NO error: `auth/requests-from-referer-http://localhost:3000-are-blocked`
- Dashboard loads
- Shows "3 Engines Online"
- Shows "Dhan Account Not Connected" (normal - needs token)

### ❌ If Still Failing

**Firebase Referer Error**:
- Check `.env.local` has `galvanic-pulsar-482815-h0` (not `gen-lang-client`)
- Full cache clear (including Application cache in DevTools)
- Try incognito window

**Session State Error**:
- This is OK - waiting for Firestore index to build (~5 min)
- Run: `gcloud firestore indexes composite list --project=galvanic-pulsar-482815-h0`
- Should show all indexes with `STATE: READY`

**getFunds HTTP 500**:
- Normal before connecting Dhan account
- Go to Settings → Dhan Connection
- Paste valid access token
- Should then work

---

## What Was Fixed

| Issue | Problem | Fix | Status |
|-------|---------|-----|--------|
| **Firebase Auth** | Wrong project ID in .env | Updated to galvanic-pulsar-482815-h0 | ✅ Ready |
| **Session State** | Missing read permissions | Added Firebase rules fallback | ✅ Ready |
| **Firestore Index** | Missing uid/timestamp index | Added composite index | ⏳ Building |

---

## Verify Everything Works

After login succeeds:

1. **Check Dashboard**
   - [ ] Shows "All Engines Online"
   - [ ] Shows "3" engines running
   - [ ] See A, B, C status indicators

2. **Check Settings**
   - [ ] Click Settings tab
   - [ ] See "Dhan Connection"
   - [ ] Status should say "Not Connected" (until token added)

3. **Monitor Real-Time Updates**
   - [ ] Open Dev Tools (F12)
   - [ ] Go to Network tab
   - [ ] Refresh page
   - [ ] Should see WebSocket connection to Firebase (not Firestore permission errors)

---

## Timeline

```
NOW     → Step 1 (Clear cache) ........... 2 min
2 min   → Step 2 (Restart) .............. 1 min
3 min   → Step 3 (Test login) ........... 2 min
5 min   → Systems operational ........... ✅ DONE
5 min   → Firestore index builds ........ 5 min (parallel)
10 min  → All features ready ............ ✅ DONE
```

---

## If Stuck

### Console Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `auth/requests-from-referer-http://localhost:3000-are-blocked` | Wrong Firebase project | Check `.env.local` has correct API key |
| `Missing or insufficient permissions` | Firestore rules not propagated | Wait 5 min + refresh page |
| `HTTP 500 from getFunds` | No Dhan credentials | Normal - go to Settings to add token |
| `COOP policy would block window.close` | Browser security headers | OK - warning only, doesn't block login |

---

**Market opens: Monday 9:15 AM IST (Jan 13)**
**Recovery ETA: 10 minutes from now**
