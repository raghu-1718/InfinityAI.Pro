# InfinityAI.Pro - Secrets Setup Guide

## Overview
This guide documents how to set up and manage secrets for the InfinityAI.Pro platform using GCP Secret Manager.

**Status**: ⚠️ Secrets created but no values set (pending manual configuration)

**Last Updated**: 2025-01-20

---

## Required Secrets

### 1. **gemini-api-key**
- **Used By**: Engine A (Market Data), Engine B (AI/ML)
- **Secret Name**: `GEMINI_API_KEY_PRIMARY`
- **Purpose**: Vertex AI / Gemini API authentication for AI analysis
- **How to Obtain**:
  1. Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
  2. Create API key or use existing service account
  3. Enable Vertex AI API for the project

```powershell
# Set the secret value (replace YOUR_ACTUAL_KEY with real key)
echo "AIzaSyCkg8QKAT3vvbTU9_1qBqB1G7ZL0oQ-Ebs" | gcloud secrets versions add GEMINI_API_KEY_PRIMARY --data-file=- --project=infinity-ai-5ec7c
```

---

### 2. **huggingface-token**
- **Used By**: Engine A (Market Data), Engine B (AI/ML)
- **Environment Variable**: `HUGGINGFACE_API_TOKEN`
- **Purpose**: HuggingFace API authentication for AI models
- **How to Obtain**:
  1. Create account at [huggingface.co](https://huggingface.co)
  2. Go to Settings → Access Tokens
  3. Create a new token with "read" scope

```powershell
# Set the secret value
echo "hf_YOUR_HUGGINGFACE_TOKEN" | gcloud secrets versions add huggingface-token --data-file=- --project=infinity-ai-5ec7c
```

---

### 3. **telegram-bot-token**
- **Used By**: Engine C (Execution), Engine D (Orchestration)
- **Environment Variable**: `TELEGRAM_BOT_TOKEN`
- **Purpose**: Telegram Bot API for notifications and alerts
- **How to Obtain**:
  1. Message [@BotFather](https://t.me/botfather) on Telegram
  2. Send `/newbot` and follow instructions
  3. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

```powershell
# Set the secret value
echo "123456789:YOUR_TELEGRAM_BOT_TOKEN" | gcloud secrets versions add telegram-bot-token --data-file=- --project=infinity-ai-5ec7c
```

---

### 4. **telegram-chat-id**
- **Used By**: Engine C (Execution), Engine D (Orchestration)
- **Environment Variable**: `TELEGRAM_CHAT_ID`
- **Purpose**: Target chat ID for sending notifications
- **How to Obtain**:
  1. Start a chat with your bot on Telegram
  2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
  3. Look for `"chat":{"id":123456789}` in the response

```powershell
# Set the secret value (numeric chat ID)
echo "YOUR_TELEGRAM_CHAT_ID" | gcloud secrets versions add telegram-chat-id --data-file=- --project=infinity-ai-5ec7c
```

---

### 5. **webhook-verification-token**
- **Used By**: Engine C (Execution)
- **Environment Variable**: `WEBHOOK_VERIFICATION_TOKEN`
- **Purpose**: Verify webhook requests from external services
- **How to Generate**: Use a cryptographically secure random string

```powershell
# Generate and set a random token (PowerShell)
$token = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
echo $token | gcloud secrets versions add webhook-verification-token --data-file=- --project=infinity-ai-5ec7c
```

---

### 6. **trading-engine-secret**
- **Used By**: Engine D (Orchestration)
- **Environment Variable**: `JWT_SECRET_KEY`
- **Purpose**: JWT token signing for authentication
- **How to Generate**: Use a cryptographically secure random string

```powershell
# Generate and set a random secret (PowerShell)
$secret = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(64))
echo $secret | gcloud secrets versions add trading-engine-secret --data-file=- --project=infinity-ai-5ec7c
```

---

### 7. **firebase-admin-sdk** (Optional)
- **Used By**: Future authentication features
- **Environment Variable**: `FIREBASE_ADMIN_SDK`
- **Purpose**: Firebase Admin SDK service account JSON
- **How to Obtain**:
  1. Go to [Firebase Console](https://console.firebase.google.com)
  2. Project Settings → Service Accounts
  3. Generate new private key (JSON file)

```powershell
# Set the secret value from JSON file
gcloud secrets versions add firebase-admin-sdk --data-file=path/to/firebase-service-account.json --project=infinity-ai-5ec7c
```

---

### 8. **dhan-access-token** & **dhan-client-id** (Optional - Trading)
- **Used By**: Engine A (Market Data), Engine C (Execution)
- **Environment Variables**: `DHAN_ACCESS_TOKEN`, `DHAN_CLIENT_ID`
- **Purpose**: Dhan trading API authentication
- **How to Obtain**:
  1. Create account at [dhan.co](https://dhan.co)
  2. Go to API access section in dashboard
  3. Generate API credentials

```powershell
# Set Dhan credentials (if needed for live trading)
echo "YOUR_DHAN_ACCESS_TOKEN" | gcloud secrets create dhan-access-token --data-file=- --project=infinity-ai-5ec7c
echo "YOUR_DHAN_CLIENT_ID" | gcloud secrets create dhan-client-id --data-file=- --project=infinity-ai-5ec7c

# Grant access to compute service account
gcloud secrets add-iam-policy-binding dhan-access-token --member="serviceAccount:26140490557-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" --project=infinity-ai-5ec7c
gcloud secrets add-iam-policy-binding dhan-client-id --member="serviceAccount:26140490557-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" --project=infinity-ai-5ec7c
```

---

## Secret Injection Status

| Secret | Version Exists | IAM Access Granted | Injected into Services |
|--------|---------------|-------------------|----------------------|
| gemini-api-key | ❌ No | ✅ Yes | ⚠️ Pending value |
| huggingface-token | ❌ No | ✅ Yes | ⚠️ Pending value |
| telegram-bot-token | ❌ No | ✅ Yes | ⚠️ Pending value |
| telegram-chat-id | ❌ No | ✅ Yes | ⚠️ Pending value |
| webhook-verification-token | ❓ Unknown | ✅ Yes | ⚠️ Verify value |
| trading-engine-secret | ❌ No | ✅ Yes | ⚠️ Pending value |
| firebase-admin-sdk | ❓ Unknown | ❌ No | ❌ Not injected |
| dhan-access-token | ❌ Not created | N/A | ❌ Not injected |
| dhan-client-id | ❌ Not created | N/A | ❌ Not injected |

---

## Automated Secret Injection

Once all secret values are set, run the secret injection script:

```powershell
# Preview changes (dry-run)
.\scripts\secret_injection_and_rotation.ps1

# Execute injection
.\scripts\secret_injection_and_rotation.ps1 -DryRun $false
```

This script will:
1. ✅ Verify all required secrets exist with valid versions
2. ✅ Inject secrets into appropriate Cloud Run services
3. ✅ Set canonical engine URLs for Engine D orchestration
4. ✅ Handle IAM permissions (already configured)

---

## Manual Rollback (if needed)

If secret injection causes issues, revert to previous revisions:

```powershell
# List revisions for a service
gcloud run revisions list --service=infinityai-engine-a --region=us-central1 --project=infinity-ai-5ec7c

# Route 100% traffic back to working revision
gcloud run services update-traffic infinityai-engine-a --to-revisions=infinityai-engine-a-00001-vmn=100 --region=us-central1 --project=infinity-ai-5ec7c
```

---

## Security Best Practices

1. **Never commit secrets to version control**
   - Add `.env*` to `.gitignore`
   - Use Secret Manager exclusively for production

2. **Rotate secrets periodically**
   - API keys: Every 90 days
   - JWT secrets: Every 180 days
   - Trading credentials: On security incidents

3. **Audit secret access**
   ```powershell
   # View who has access to a secret
   gcloud secrets get-iam-policy gemini-api-key --project=infinity-ai-5ec7c
   ```

4. **Monitor secret usage**
   - Cloud Logging captures secret access attempts
   - Set up alerts for failed access attempts

---

## Verification

After setting all secrets and running injection script:

1. Check service health endpoints:
   ```powershell
   .\verify-platform-health.ps1
   ```

2. Verify secrets are accessible:
   ```powershell
   # Check if service can access secret (from logs)
   gcloud logging read "resource.type=cloud_run_revision AND severity>=WARNING" --project=infinity-ai-5ec7c --limit=50
   ```

3. Test API endpoints requiring authentication

---

## Next Steps

- [ ] Set values for all required secrets (gemini-api-key, huggingface-token, etc.)
- [ ] Run secret injection script: `.\scripts\secret_injection_and_rotation.ps1 -DryRun $false`
- [ ] Verify all services are healthy: `.\verify-platform-health.ps1`
- [ ] Remove any local plaintext secret files
- [ ] Document secret locations in password manager
- [ ] Set calendar reminders for secret rotation

---

**For assistance**: Contact DevOps team or refer to [GCP Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
