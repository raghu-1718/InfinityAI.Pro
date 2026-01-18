# 🔐 DHAN CREDENTIALS - QUICK REFERENCE

**Last Updated**: January 11, 2026
**Project**: galvanic-pulsar-482815-h0

---

## 📋 QUICK START: Verify Your Credentials in 5 Minutes

### 1️⃣ Check Firestore (30 seconds)
```bash
# Show all user credential documents
gcloud firestore documents list --collection-path=user_credentials \
  --project=galvanic-pulsar-482815-h0

# Check YOUR specific document
gcloud firestore documents get user_credentials/YOUR_USER_ID \
  --project=galvanic-pulsar-482815-h0
```

### 2️⃣ Check Secret Manager (30 seconds)
```bash
# List all user credential secrets
gcloud secrets list --filter="name:user-creds-*" \
  --project=galvanic-pulsar-482815-h0

# Check YOUR specific secret
gcloud secrets describe user-creds-YOUR_ESCAPED_ID \
  --project=galvanic-pulsar-482815-h0
```

### 3️⃣ Test Cloud Function (1 minute)
```bash
# Call getUserCredentials function
gcloud functions call getUserCredentials \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --data='{"user_id":"YOUR_USER_ID"}'
```

### 4️⃣ Test Dhan API (1 minute)
```bash
curl -X POST https://engine-c-738553258162.us-central1.run.app/api/dhan/verify \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "client_id": "YOUR_CLIENT_ID",
    "access_token": "YOUR_ACCESS_TOKEN"
  }'
```

### 5️⃣ Run Full Diagnostic (2 minutes)
```bash
cd c:\workspace\InfinityAI.Pro
python tools/verify_credentials.py YOUR_USER_ID YOUR_CLIENT_ID YOUR_ACCESS_TOKEN
```

---

## 🎯 VERIFICATION ENDPOINTS

### Firestore REST API
```
GET https://firestore.googleapis.com/v1/projects/galvanic-pulsar-482815-h0/databases/default/documents/user_credentials/{userId}
```

### Cloud Functions
```
POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/getUserCredentials
Body: { "user_id": "YOUR_USER_ID" }
```

### Engine-C Backend
```
POST /api/dhan/verify
POST /api/dhan/credentials
GET  /api/dhan/credentials/{user_id}
DELETE /api/dhan/credentials/{user_id}
GET  /api/v1/user/{user_id}/account
GET  /api/dhan/overview
```

---

## 📊 CREDENTIAL STORAGE PATHS

| Layer | Location | Access Pattern | Backup | Encryption |
|-------|----------|-----------------|--------|-----------|
| **Firestore** | `user_credentials/{user_id}` | Direct Firestore | Primary | At-rest |
| **Secret Manager** | `user-creds-{user_id}` | Versioned secrets | Secondary | At-rest + versioning |
| **Cloud Function** | Memory (temporary) | Called per request | None | Cached in memory |

---

## ✅ WHAT TO EXPECT

### Successful Firestore Document
```json
{
  "user_id": "rBwWLLL6XiS6KBeXkiacx6c848q1",
  "dhan_client_id": "1234567890",
  "dhan_access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "updated_at": "2026-01-11T15:30:45.000Z"
}
```

### Successful Cloud Function Response
```json
{
  "success": true,
  "dhan_client_id": "1234567890",
  "dhan_access_token": "eyJ0eXAi...",
  "updated_at": "2026-01-11T15:30:45.000Z"
}
```

### Successful Dhan API Response
```json
{
  "success": true,
  "verified": true,
  "message": "Connection verified successfully"
}
```

---

## ❌ COMMON ERRORS & FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `404 Not Found` (Firestore) | Document not created | Re-submit credentials from Dashboard |
| `401 Unauthorized` (Dhan API) | Invalid/expired token | Regenerate token in Dhan settings |
| `503 Service Unavailable` | Dhan API down | Wait 5 minutes, retry |
| `PERMISSION_DENIED` | Missing IAM roles | Check Cloud IAM settings |
| `Secret not found` (Secret Manager) | Secret never created | Verify submitDhanCredentialsV2 deployed |

---

## 🔒 SECURITY CHECKLIST

- [ ] Credentials NOT stored in browser LocalStorage
- [ ] Credentials NOT in browser session cookies
- [ ] Credentials NOT printed in browser console logs
- [ ] Credentials NOT exposed in Cloud Function logs
- [ ] Credentials ONLY accessed over HTTPS
- [ ] Credentials ONLY accessed by authenticated users
- [ ] Credentials AUTOMATICALLY encrypted in both vaults
- [ ] Old credentials DELETED when new ones added
- [ ] Credentials VERSIONED in Secret Manager
- [ ] Access AUDIT-LOGGED by GCP

---

## 📞 TROUBLESHOOTING

### "Credentials saved but not verified"
**Meaning**: Stored in Firestore/Secret Manager BUT Dhan API rejected them
**Action**: Check Dhan console if token is enabled & not expired

### "No credentials found"
**Meaning**: Document/secret doesn't exist anywhere
**Action**: Re-submit credentials from Settings → Dhan Account

### "Verification failed: Invalid response"
**Meaning**: Dhan API accepted credentials but returned unexpected format
**Action**: Check Dhan API status, contact support

### "Permission denied accessing Secret Manager"
**Meaning**: Service account lacks IAM permissions
**Action**: Check Cloud IAM settings, verify service account has Secret Manager Reader role

---

## 🚀 NEXT STEPS

After verification:

1. ✅ Credentials verified → Proceed to trading
2. ⚠️ Some checks failed → See troubleshooting above
3. ❌ Critical failures → Run diagnostic script & share output

---

## 📚 FULL DOCUMENTATION

For detailed guides, see:
- **DHAN_CREDENTIAL_VERIFICATION_GUIDE.md** - Comprehensive guide with screenshots
- **DHAN_CREDENTIAL_VERIFICATION_CHECKLIST.md** - Complete checklist (print & mark)
- **tools/verify_credentials.py** - Automated diagnostic tool

---

## 💡 KEY FACTS

✅ **Credentials are stored in TWO places:**
- Firestore (primary vault)
- Google Secret Manager (backup vault)

✅ **Credentials are automatically:**
- Encrypted at rest
- Versioned
- Audit-logged
- Masked in responses

✅ **Credentials are accessed via:**
- Cloud Functions (frontend)
- Engine-C backend (trading)
- Dhan API (broker)

❌ **Credentials are NEVER:**
- Stored in browser
- Printed in logs
- Shared with unauthorized services
- Sent over HTTP (only HTTPS)

---

## 🎯 CONFIDENCE SIGNALS

### ✅ If You See These, You're Good:
- Firestore document with recent timestamp
- Secret Manager secret with latest version
- Cloud Function returns credentials successfully
- Dhan API verification succeeds
- Dashboard shows "CONNECTED ✓ Verified"

### ⚠️ If You See These, Something's Wrong:
- Credentials saved but Dhan returns 401
- Firestore document exists but very old timestamp
- Secret Manager secret exists but old version
- Cloud Function times out or throws error
- Dashboard shows "DISCONNECTED" even after save

---

## 📊 STATUS SUMMARY

```
YOUR CREDENTIAL VERIFICATION STATUS
═══════════════════════════════════

┌─────────────────────────────────────┐
│ Firestore:   [████████████] 100%    │
│ Secret Mgr:  [████████████] 100%    │
│ Dhan API:    [████████████] 100%    │
│ Dashboard:   [████████████] 100%    │
└─────────────────────────────────────┘

Overall: ✅ FULLY VERIFIED
Status:  Ready for Live Trading
```

---

**Questions?** See full guides or contact support with diagnostic output from `verify_credentials.py`
