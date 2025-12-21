# GitHub Secrets Audit

## Existing Secrets
*   `DHAN_CLIENT_ID`
*   `DHAN_ACCESS_TOKEN`
*   `WIF_SERVICE_ACCOUNT`

## Missing or Mismatched Secrets
The following secrets are used in `deploy-production.yml` but were not found in the repository secrets list (they might be Organization secrets, or genuinely missing).

| Secret Name | Usage | Status | Action |
|-------------|-------|--------|--------|
| `GCP_SERVICE_ACCOUNT` | Used for `google-github-actions/auth` | ❌ **Missing** | Verify if Organization secret, else add. |
| `FIREBASE_SERVICE_ACCOUNT` | Used for `FirebaseExtended/action-hosting-deploy` | ❌ **Missing** | **CRITICAL**: Deployment will fail. Add secret. |
| `DHAN_API_SECRET` | Used in Cloud Run deploy flags | ❌ **Missing** | Add request to GitHub secrets. |
| `GITHUB_TOKEN` | Used for Firebase Action | ✅ Built-in | No action needed. |

## Workload Identity Federation
*   `WIF_SERVICE_ACCOUNT` exists but the pipeline uses `GCP_WORKLOAD_IDENTITY_PROVIDER`.
*   **Action**: Confirm if `WIF_SERVICE_ACCOUNT` contains the Provider string. If so, update workflow to use `${{ secrets.WIF_SERVICE_ACCOUNT }}` instead of `GCP_WORKLOAD_IDENTITY_PROVIDER` (or rename the secret).
