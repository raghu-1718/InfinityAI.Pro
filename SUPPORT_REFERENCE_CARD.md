# 🆘 SUPPORT REFERENCE: Credential 404 Error Troubleshooting

**Date**: January 12, 2026
**Issue**: 404 errors on Dashboard/Trading after updating Dhan credentials
**Status**: Known issue with fix in progress

---

## 🚨 Quick Diagnosis

### User Reports:
- "Account data won't load"
- "Getting 404 error on dashboard"
- "Trading page shows error"
- "Fund balance showing ₹0.00"

### What's Happening:
Transient issue where account data can't load immediately after credential update. **It always resolves itself**.

### Root Cause:
Backend retry logic missing. System needs 2-3 seconds to fully process credentials.

---

## ✅ Immediate Fix (Tell User This)

### Step 1: Go to Settings
```
Click: Settings gear icon (top right)
       ↓
Go to: "Dhan Account" tab
```

### Step 2: Click Verify Connection
```
Look for: "Verify Connection" button
Click it: This retries credential verification
Wait: ~2-3 seconds for status to update
```

### Step 3: Refresh Dashboard
```
Close: Settings panel
Refresh: Browser (Ctrl+R or Cmd+R)
Observe: Account Overview should now load correctly
```

### Expected Result:
✅ Dashboard shows account balance
✅ Trading page loads without errors
✅ Status shows "CONNECTED ✓ VERIFIED"

---

## 🔧 If That Doesn't Work

### Step 1: Check Browser Console
```
Open: Developer Tools (F12)
Go to: Console tab
Look for: Any red error messages
Screenshot: Any errors you see
```

### Step 2: Try Incognito Mode
```
Open: Incognito/Private window
Go to: Dashboard
Try: Load account data again
If works: Cache issue (clear browser cache)
If fails: Genuine error (escalate)
```

### Step 3: Check Credentials Status
```
Go to: Settings → Dhan Account
Check: Does it show "CONNECTED ✓ VERIFIED"?
YES: Dashboard should work (refresh page)
NO: Credentials may need re-entry
```

---

## 📊 Diagnosis Table

| Symptom | Cause | Fix |
|---------|-------|-----|
| 404 right after updating credentials | Timing issue | Click "Verify Connection" |
| 404 persists after verify button | Real error or cache | Clear browser cache |
| Shows "DISCONNECTED" | Credentials invalid/expired | Re-enter credentials |
| Shows ₹0.00 balance | Data fetch failed | Refresh page (5 sec interval) |
| Works in incognito, not normal | Browser cache corrupted | Clear cache & cookies |

---

## 🎯 Expected Recovery Timeline

| Time | Status | Action |
|------|--------|--------|
| T+0s | ❌ Error shown | User experiences issue |
| T+3s | 🔄 "Verify Connection" clicked | Manual retry initiated |
| T+5s | ✅ Verification succeeds | Credentials confirmed |
| T+10s | ✅ Dashboard refreshes | Data loads normally |

**Total**: ~10 seconds from error to full recovery

---

## 📞 Escalation Criteria

### ESCALATE to Engineering if:
- User reports 404 persists after clicking "Verify Connection" twice
- Status shows "DISCONNECTED" (credentials might be invalid)
- Error message contains: "500 Internal Server Error"
- Dashboard works but balance shows $0.00 for >5 minutes
- Same error appears on ALL InfinityAI pages

### DO NOT ESCALATE if:
- Single 404 after credential update (normal, fixes itself)
- "Verify Connection" resolves the issue
- Refreshing page makes it work
- Works fine after 1-2 minutes
- Only affects Dashboard, not Trading or Settings

### PREPARE FOR ESCALATION:
1. Get exact error message from browser console (F12)
2. Take screenshot of error state
3. Screenshot of Settings → Dhan Account page
4. Note exact time error occurred
5. Confirm user has tried "Verify Connection" button
6. Confirm user has refreshed browser

---

## 💬 Sample Support Responses

### Response 1: Standard 404 (Most Common)
```
Hi [User],

Thanks for reporting! We're aware of this issue. It's a temporary
timing issue that happens sometimes when updating credentials.

Here's how to fix it:

1. Go to Settings (gear icon)
2. Click the "Dhan Account" tab
3. Click the "Verify Connection" button
4. Refresh your browser

Your account should load normally now.

We're rolling out a permanent fix this week that will eliminate
this issue entirely. Your credentials are secure and safe!

Let me know if you need anything else.
```

### Response 2: Persistent Issue
```
Hi [User],

I see you're still experiencing the 404 error even after clicking
"Verify Connection". Let me help troubleshoot:

Can you please:
1. Open Developer Tools (F12)
2. Go to the Console tab
3. Try to load the Dashboard again
4. Take a screenshot of any red error messages
5. Send me that screenshot

Also, can you confirm:
- Does Settings → Dhan Account show "CONNECTED ✓ VERIFIED"?
- Can you try in a private/incognito browser window?

Once I have this info, I can help get you sorted out.
```

### Response 3: Preventative (During Deployment)
```
Hi [InfinityAI Users],

We're rolling out a fix today for an issue some users experienced
with 404 errors after updating Dhan credentials.

What was the issue?
- Sometimes account data wouldn't load immediately after updating
  credentials
- Clicking "Verify Connection" would fix it
- Now it will work automatically

What changes?
- Faster account data loading (2 seconds instead of 15)
- No more need to click "Verify Connection"
- Better error messages if anything goes wrong

What's the same?
- Same security and encryption
- Same trading functionality
- Nothing to do on your end

Expected deployment: [TIME]

Thanks for using InfinityAI!
```

---

## 📋 Common Questions from Users

### Q: Is my account hacked?
**A**: No. Your credentials are encrypted and secure. This is just a timing issue in data loading, not a security problem.

### Q: Will I lose money from this?
**A**: No. You can't trade if account data doesn't load, so no trades are executed. Your balance is safe.

### Q: Will this happen again?
**A**: We're rolling out a fix this week. After that, it shouldn't happen anymore.

### Q: Why does my balance show ₹0.00?
**A**: The account data fetch failed, so it shows a default value. Clicking "Verify Connection" fixes it.

### Q: Can I trade while this is happening?
**A**: We recommend waiting for the data to load first. Click "Verify Connection" and the data will appear.

---

## 🔍 Monitoring Checklist

### Daily (While Issue Exists)
- [ ] Check support ticket volume for "404" errors
- [ ] Note any patterns (time of day, user count, etc.)
- [ ] Confirm "Verify Connection" resolves all cases
- [ ] No reports of data loss or security issues

### Post-Deployment
- [ ] Confirm error rate drops to near zero
- [ ] Monitor error logs for any regression
- [ ] Verify no new issues introduced
- [ ] Customer satisfaction scores improve

---

## 📞 Contact Info

**If escalating to Engineering**:
- Slack: #engine-c-issues
- Email: support+engineering@infinityai.pro
- Include:
  - User email/Client ID
  - Exact timestamp of issue
  - Error message from console
  - Screenshot of error state

**Engineering Response SLA**:
- Critical (data loss): 15 minutes
- High (persistent errors): 1 hour
- Medium (transient issues): 4 hours

---

## 🚀 Deployment Status

| Component | Status | ETA |
|-----------|--------|-----|
| Backend retry fix | ✅ Ready | TODAY |
| Frontend error handling | ✅ Ready | TODAY |
| Logging enhancement | ✅ Ready | TODAY |
| Deployment | ⏳ Pending approval | <4 hours |
| Monitoring setup | ✅ Ready | TODAY |

**After deployment**, this troubleshooting guide becomes less relevant as the fix prevents the issue.

---

## 📚 Additional Resources

- **Full Analysis**: See `INCIDENT_ANALYSIS_CREDENTIAL_SYNC_TIMING.md` in project root
- **User Explanation**: See `USER_FACING_INCIDENT_SUMMARY.md`
- **Deployment Plan**: See `REMEDIATION_ACTION_PLAN.md`
- **Executive Summary**: See `EXECUTIVE_BRIEF_CREDENTIAL_INCIDENT.md`

---

## ⚡ TL;DR for Support Team

**What**: 404 errors on Dashboard/Trading after credential update
**Why**: Timing issue, not permanent
**Fix**: Click "Verify Connection" button in Settings → Dhan Account
**Time**: 10 seconds to recover
**Permanent Fix**: Deploying today with automatic retry
**Safety**: All credentials secure, no data loss risk

**Support script**: "Click Verify Connection in Settings, then refresh your browser. We're rolling out a permanent fix today that will prevent this issue."

---

**Last Updated**: January 12, 2026
**Version**: 1.0
**Status**: Active until fix deployed, then archive
