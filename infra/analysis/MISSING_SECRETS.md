# Missing Secrets Audit

The following secrets are referenced in infrastructure configuration (`deploy-production.yml`) but are **MISSING** from GCP Secret Manager.

## Critical Missing Secrets (GCP)
These must be created immediately for services to function.

| Secret Name | Required By | Reference in Code | Action Required |
|-------------|-------------|-------------------|-----------------|
| `GEMINI_API_KEY` | `engine-b` | `backend/engine-b` | Create GCP Secret `gemini-api-key` |
| `ENCRYPTION_KEY` | `engine-c` | `backend/engine-c` | Create GCP Secret `encryption-key` |

## Missing GitHub Secrets (CI/CD)
These are referenced in the GitHub Actions workflow but were not found in the repository secrets list.

| Secret Name | Usage | Status |
|-------------|-------|--------|
| `GCP_SERVICE_ACCOUNT` | GCP Auth | ❌ Missing (or Org secret) |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase Deploy | ❌ Missing |
| `DHAN_API_SECRET` | Unknown (Check usage) | ❌ Missing (Only ClientID/Token found) |

Note: `WIF_SERVICE_ACCOUNT` exists but pipeline uses `GCP_WORKLOAD_IDENTITY_PROVIDER`. Ensure these are correctly mapped.
