# 🚀 QUICK ACTION GUIDE - GET YOUR SYSTEM RUNNING

**Status**: Backend is FIXED and deployed ✅  
**Your Action**: Save credentials to Firestore  
**Time to Complete**: 5 minutes  
**Expected Outcome**: All API endpoints working, portfolio data showing

---

## The Situation

Your backend has been fixed and deployed, but your **credentials are not saved in Firestore**. Once you save them, everything will work.

Think of it like this:
- ✅ Backend has the **recipe** (code to get data)
- ✅ DhanHQ has the **ingredients** (your account data)
- ❌ System is missing the **seasoning** (your credentials)

---

## 🎯 5-Minute Fix

### Step 1: Open Settings (1 minute)
1. Go to: **https://galvanic-pulsar-482815-h0.web.app**
2. Log in (if needed)
3. Click **Settings** (usually top-right menu or left sidebar)
4. Find the **"DHAN Account"** or **"Credentials"** tab

### Step 2: Enter Your Dhan Credentials (2 minutes)
You'll see a form asking for:
- **Client ID** 
- **API Key**
- **API Secret**  
- **Access Token**

**Where to get these:**
1. Log in to: https://dhanhq.com
2. Go to: **Settings** → **API** → **Access Tokens**
3. Copy your **Client ID** (10-digit number like `1101302170`)
4. Copy your **Active Token** (long JWT string starting with `eyJ0...`)

**IMPORTANT**: When pasting:
- ✅ Paste directly without extra spaces
- ✅ Don't add newlines before/after
- ❌ Don't manually edit the token

### Step 3: Save & Verify (2 minutes)
1. Paste your credentials into the form
2. Click **"Save Credentials"** button
3. **Wait for success message** - should show:
   - ✅ "Credentials saved and verified!"
   - or ✅ "Credentials saved successfully"
4. If you see error, check that your token hasn't expired (regenerate from Dhan if needed)

### Step 4: Verify in Browser (Optional but Recommended)
1. Open Browser DevTools: Press **F12**
2. Go to **Network** tab
3. Click **"Save Credentials"** again
4. Look for request: `POST` → `engine-c.run.app/api/user/credentials`
5. Click it and check **Response** tab
   - Should show: `{"status": "success", "user_id": "user_...", ...}`

### Step 5: Test It Works!
1. Go back to **Dashboard** (or refresh page)
2. Look for **Portfolio** or **Positions** section
3. Should see:
   - ✅ Your actual portfolio value (not ₹0)
   - ✅ Your positions list
   - ✅ Engines showing as "RUNNING" (not "Offline")
   - ✅ "DhanHQ Connection: Connected" (not Disconnected)

---

## 🔍 If Something Goes Wrong

### Problem: "Failed to save credentials"
**Solution**: 
- Check your token hasn't expired (get new one from Dhan)
- Try copying again without extra spaces
- Refresh page and try again

### Problem: "Credentials saved but verification failed"
**Solution**:
- Go back to Dhan and check if token is **Enabled** (not disabled/expired)
- Generate a new access token in Dhan
- Come back and save again

### Problem: Data still not showing after save
**Solution**:
- Hard refresh browser: **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac)
- Wait 30 seconds (system needs to process)
- If still not working, check DevTools Console for errors

### Problem: Console shows "Dhan Client ID stored: ..."
**Solution**:
- This is expected from system diagnostic logging
- Should also show you actual user_id being used
- If data still doesn't display, refresh page

---

## ✅ How to Know It's Working

After saving credentials, you should see:

| Indicator | Before | After |
|-----------|--------|-------|
| Portfolio Value | ₹0 | ₹X,XXX |
| Positions | "No active positions" | List of your positions |
| Engines | "Offline" (red) | "Running" (green) |
| DhanHQ Status | "Disconnected" | "Connected" |
| API Requests | HTTP 500 errors | HTTP 200 success |

---

## 📝 Troubleshooting Checklist

Before contacting support, please check:

- [ ] I'm using my actual Dhan token (not placeholder)
- [ ] I haven't added extra spaces or newlines to credentials
- [ ] My token is still active (not expired) in Dhan settings
- [ ] I clicked "Save Credentials" and waited for success message
- [ ] I hard refreshed my browser (Ctrl+Shift+R)
- [ ] I waited 30+ seconds for system to process
- [ ] DevTools Network tab shows POST request to `/api/user/credentials` with `"status": "success"` response

---

## 🎓 What Just Got Fixed (Technical Details - FYI)

The backend code had a bug where the credential resolver was returning the wrong user's credentials. This has been fixed and deployed. The system now correctly:

- ✅ Resolves generated user IDs to the right Firestore document
- ✅ Strips whitespace from tokens (preventing JWT header errors)
- ✅ Uses encrypted storage for all sensitive data
- ✅ Validates credentials with DhanHQ before saving

Full technical details: See `CREDENTIAL_RESOLVER_ROOT_CAUSE_ANALYSIS.md`

---

## Need Help?

If credentials aren't saving after trying these steps:

1. Screenshot the error message
2. Check if error appears in DevTools Console (F12)
3. Note your user ID (shown in settings or at top of page)
4. Contact support with this information

Your user ID appears to be: `user_1768804393712_idm50j` (this is auto-generated and not the same as email)

---

**You've got this! 💪 Your system is ready to go - just save your credentials and you're done.**

