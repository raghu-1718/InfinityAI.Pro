# InfinityAI v4.6 — Google Secret Manager Status

Initial manifest for tracking required secrets and their usage across services. Update the Latest Version and Enabled columns after running the verification commands below.

| Secret Name | Purpose | Latest Version | Enabled | Bound Services |
|---|---|---:|:--:|---|
| gemini-api-key-primary | Gemini model key | TBD | TBD | engine-b |
| gemini-api-key-secondary | Fallback Gemini key | TBD | TBD | engine-b |
| dhan-api-key | Trading API key | TBD | TBD | engine-c, engine-d |
| firebase-admin-sdk | Firestore Admin credentials | TBD | TBD | engines a/b/c/d, functions |
| huggingface-token | AI model key | TBD | TBD | engine-b |
| trading-engine-secret | Encryption/verification token | TBD | TBD | engine-d |
| webhook-verification-token | Webhook auth | TBD | TBD | engine-d |
| telegram-bot-token | Alerting | TBD | TBD | engine-d (if used) |

## How to verify

```bash
gcloud secrets list --project infinity-ai-5ec7c
gcloud secrets versions list gemini-api-key-primary --project infinity-ai-5ec7c
gcloud secrets versions list gemini-api-key-secondary --project infinity-ai-5ec7c
gcloud secrets versions list dhan-api-key --project infinity-ai-5ec7c
```

Ensure each runtime service account has access:

- roles/secretmanager.secretAccessor for Cloud Run service accounts (engines and frontend)
- roles/secretmanager.secretAccessor for Firebase Functions service account (if applicable)

### Rotation and hygiene

- Rotate keys older than 90 days.
- Remove DISABLED or DESTROYED versions if no longer needed.
- Record rotation date and approver in this manifest.
