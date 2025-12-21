# Safe Apply Plan (READ-ONLY)

**DO NOT EXECUTE AUTOMATICALLY.** This is a plan to fix the identified issues.

## 1. Create Missing GCP Secrets
The following secrets are required for Cloud Run services `engine-b` and `engine-c` to start.

```bash
# Engine B Dependency
printf "YOUR_GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=- --project=gen-lang-client-0779271931

# Engine C Dependency
printf "YOUR_ENCRYPTION_KEY" | gcloud secrets create encryption-key --data-file=- --project=gen-lang-client-0779271931
```

## 2. Fix Firebase Configuration
Update `firebase.json` to point to the correct functions source directory used by CI/CD.

**Current:**
```json
"functions": [ { "source": "functions" } ]
```

**Proposed Change:**
```json
"functions": [ { "source": "frontend/web/functions" } ]
```

## 3. Restore Missing GitHub Secrets
The CI/CD pipeline requires these secrets to deploy.

```bash
# Firebase Deployment Service Account
gh secret set FIREBASE_SERVICE_ACCOUNT < firebase-sa-key.json

# Dhan API Secret (missing from GitHub, present in GCP)
gh secret set DHAN_API_SECRET
```

## 4. Verify Cloud Run bindings
After creating GCP secrets, redeploy services to ensure they pick up the latest secret versions (Cloud Run mounts "latest").

```bash
gcloud run services update engine-b --region=us-central1
gcloud run services update engine-c --region=us-central1
```
