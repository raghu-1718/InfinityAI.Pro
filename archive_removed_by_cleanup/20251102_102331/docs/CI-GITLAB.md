InfinityAI.Pro — GitLab CI/CD with Google Cloud & Firebase (Firestudio)

Overview
- Goal: Deploy Engines A–D (Cloud Run), Frontend (Cloud Run), and optionally Firebase Hosting/Functions via GitLab CI using Google Cloud Workload Identity Federation (WIF). Run live verification and secrets checks in CI.

What you’ll set up
- GitLab → GCP WIF trust (OIDC) without long‑lived keys
- GitLab CI variables for provider, service account, and project/region
- A pipeline (.gitlab-ci.yml) that:
  - Submits Cloud Build (cloudbuild.yaml) to build/deploy all services
  - Verifies platform health (infinityai_system_verifier.py)
  - Validates Gemini API keys via Secret Manager
  - Optionally deploys Firebase (Hosting/Functions)
  - Checks GCP API enablement and Firestore access via ADC
  - Produces a CI pipeline summary artifact

1) Create Workload Identity Federation for GitLab
1. In Google Cloud Console → IAM & Admin → Workforce identity federation (or Workload Identity Federation), create a pool e.g. gitlab-pool.
2. Add a provider “OpenID Connect” with Issuer: https://gitlab.com (GitLab CI OIDC).
3. Attribute mapping (examples):
   - assertion.sub → attribute.sub
   - assertion.project_id → attribute.project_id (optional)
   - assertion.ref → attribute.ref (optional)
   - assertion.ref_type → attribute.ref_type (optional)
4. Note the provider resource name, e.g.:
   projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab-pool/providers/gitlab

2) Bind GCP Service Account to GitLab identities
- Choose or create a deploy SA, e.g. github-actions-fix@infinity-ai-5ec7c.iam.gserviceaccount.com
- Grant required roles to this SA (principle of least privilege):
  - roles/run.admin (Cloud Run admin)
  - roles/cloudbuild.builds.editor (Cloud Build submit)
  - roles/secretmanager.secretAccessor (for verifier/secrets check)
  - roles/storage.admin (if images/artifacts in Artifact Registry)
  - roles/iam.serviceAccountUser (impersonation as needed)
- Allow principalSet for your WIF pool provider to impersonate the SA:
  - Members (example): principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab-pool/attribute.sub:project_path:OWNER/REPO
  - Role: roles/iam.workloadIdentityUser

3) Configure GitLab CI/CD Variables
In GitLab → Settings → CI/CD → Variables:
- WORKLOAD_IDENTITY_PROVIDER = projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab-pool/providers/gitlab (masked, protected)
- SERVICE_ACCOUNT_EMAIL = github-actions-fix@infinity-ai-5ec7c.iam.gserviceaccount.com (masked, protected)
- GCP_PROJECT_ID = infinity-ai-5ec7c
- GCP_REGION = us-central1
- Optional fallback: GCP_SA_KEY (JSON for SA key; use only if WIF not ready)
- Optional: FIREBASE_TOKEN (only if you want Firebase deploy from GitLab)

Note: .gitlab-ci.yml also supports PROJECT_NUMBER, WIF_POOL_ID, WIF_PROVIDER_ID and composes WORKLOAD_IDENTITY_PROVIDER internally if you prefer that style.

4) Understand the pipeline
- .gitlab-ci.yml (added at repo root) defines stages:
  - build_and_deploy: runs gcloud builds submit using cloudbuild.yaml
  - verify_platform: runs infinityai_system_verifier.py and uploads report artifacts
  - check_gemini_secrets: ensures Secret Manager has Gemini keys (artifacts: gemini_*_versions.json)
  - check_gcp_services: ensures required GCP APIs are enabled (Run, Secret Manager, Cloud Build, Firestore, Firebase, Artifact Registry)
  - check_firestore_access: uses ADC via WIF to perform a Firestore write/read smoke test
  - firebase_deploy (optional, manual): deploys Firebase Hosting/Functions if FIREBASE_TOKEN is set
  - summarize_pipeline: collects artifact names into CI_PIPELINE_SUMMARY.md

5) Running it
- Push to main. Pipeline triggers build_and_deploy then verify and secrets check.
- To deploy Firebase from GitLab, set FIREBASE_TOKEN and trigger the optional job manually.

6) Notes & Tips
- Prefer WIF over SA keys (no long‑lived secrets in GitLab).
- Cloud Build uses cloudbuild.yaml to build and deploy Engines/Frontend consistently with current GCP setup.
- Verifier connects to production endpoints listed in infrastructure/config.json. Update if domains change.
- Gemini issues: secrets job confirms keys exist; Engine B still depends on egress and API responsiveness.

Troubleshooting
- OIDC auth fails: verify provider audience/issuer, and SA binding roles. Inspect gcloud auth login --cred-file output in logs.
- Cloud Build fails: check cloudbuild.yaml substitutions, Artifact Registry permissions, and quotas.
- Verifier fails on Engine B Gemini: check Secret Manager keys and allow egress to generativelanguage.googleapis.com.
- Firebase deploy in CI: prefer FIREBASE_TOKEN; WIF support in Firebase CLI is evolving—use token-based auth to avoid friction.

GitHub read-only mirror
- In GitLab → Settings → Repository → Mirroring repositories:
  - Add a pull mirror from GitHub (HTTPS read-only URL) pointing to your GitHub repo.
  - Set schedule as desired; this keeps GitLab in sync while making GitHub your read-only mirror for visibility.
  - Ensure protected branches and CI rules still trigger as intended on updates.

Appendix: Minimal roles matrix
- Cloud Build submit: roles/cloudbuild.builds.editor
- Cloud Run deploy: roles/run.admin, roles/iam.serviceAccountUser for runtime SAs
- Artifact Registry: roles/artifactregistry.admin (or reader/uploader narrower)
- Secret Manager: roles/secretmanager.secretAccessor

Pipeline outputs and artifacts
- infinityai_verification_report_*.json (from verify job)
- gemini_primary_versions.json and gemini_secondary_versions.json (from secrets check)
- CI_PIPELINE_SUMMARY.md (summary of outputs)
# GitLab CI/CD with Google Cloud & Firebase/Firestore

This guide shows how to connect GitLab to Google Cloud (Cloud Run, Cloud Build, Secret Manager) without service account keys using Workload Identity Federation (WIF), and how to optionally deploy Firebase Hosting/Functions.

## 1) Pick a strategy
- Keep GitHub Actions for what’s already working (Firebase), and add GitLab for Cloud Run + verification; or
- Move everything to GitLab incrementally.

This repo ships a ready `.gitlab-ci.yml` that:
- Authenticates to GCP using GitLab OIDC + WIF (no keys)
- Triggers Cloud Build via `cloudbuild.yaml` for builds/deploys
- Runs the in-repo end-to-end verifier (`infinityai_system_verifier.py`)

## 2) Create Workload Identity Federation for GitLab
Replace names as needed.

```bash
PROJECT_ID=infinity-ai-5ec7c
PROJECT_NUMBER=26140490557
POOL_ID=gitlab-pool
PROVIDER_ID=gitlab-oidc
SA_EMAIL=github-actions-fix@${PROJECT_ID}.iam.gserviceaccount.com
REGION=us-central1

# Create the pool
gcloud iam workload-identity-pools create ${POOL_ID} \
  --project=${PROJECT_ID} \
  --location=global \
  --display-name="GitLab OIDC Pool"

# Create provider for GitLab.com
ISSUER="https://gitlab.com"
gcloud iam workload-identity-pools providers create-oidc ${PROVIDER_ID} \
  --project=${PROJECT_ID} \
  --location=global \
  --workload-identity-pool=${POOL_ID} \
  --display-name="GitLab OIDC" \
  --issuer-uri=${ISSUER} \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.project_path,attribute.ref=assertion.ref" \
  --attribute-condition="attribute.repository=='raghu-1718/InfinityAI.Pro'"

# Allow the GitLab repo to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding ${SA_EMAIL} \
  --project=${PROJECT_ID} \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/raghu-1718/InfinityAI.Pro" \
  --condition=None

# Assign required roles to the SA (least privilege)
for ROLE in roles/run.admin roles/run.developer roles/artifactregistry.writer roles/cloudbuild.builds.editor roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None
done
```

Notes:
- If you want per-branch scoping, narrow `--attribute-condition` to `attribute.ref=='refs/heads/main'`.
- Prefer minimal roles; expand only if a pipeline step complains.

## 3) Configure GitLab CI/CD variables
In your GitLab project:
- Project > Settings > CI/CD > Variables
- Add the following variables (masked/protected as needed):
  - `PROJECT_ID = infinity-ai-5ec7c`
  - `PROJECT_NUMBER = 26140490557`
  - `REGION = us-central1`
  - `WIF_POOL_ID = gitlab-pool`
  - `WIF_PROVIDER_ID = gitlab-oidc`
  - `SERVICE_ACCOUNT_EMAIL = github-actions-fix@infinity-ai-5ec7c.iam.gserviceaccount.com`

No service account keys are required. The pipeline uses `CI_JOB_JWT_V2` to obtain short-lived credentials.

## 4) Pipeline overview
See `.gitlab-ci.yml`:
- `build_and_deploy`: uses `gcloud builds submit --config cloudbuild.yaml` to build and deploy all engines & frontend as defined by your Cloud Build config.
- `verify_production`: runs `infinityai_system_verifier.py` to check all services, Firebase functions accessibility, and overall status.

Artifacts: JSON verification report is saved per run.

## 5) Optional: Firebase (Hosting/Functions)
The file includes a commented job `firebase_deploy` that demonstrates deploying via `firebase-tools` using WIF/ADC. Enable once validated in your environment.
- Ensure your SA has appropriate Firebase roles (e.g., `roles/firebase.admin` and `roles/storage.admin` if needed).
- If CLI requires `FIREBASE_TOKEN`, you can generate a short-lived token at runtime using SA impersonation and `gcloud auth print-access-token` with `--impersonate-service-account` and set `FIREBASE_TOKEN` accordingly; otherwise rely on ADC if supported by your firebase-tools version.

## 6) Gemini API keys & secrets
- Keys are stored in Secret Manager (primary/secondary):
  - `projects/${PROJECT_ID}/secrets/gemini-api-key-primary`
  - `projects/${PROJECT_ID}/secrets/gemini-api-key-secondary`
- Engine B lazily fetches the key via Secret Manager in production.
- Ensure the SA has `roles/secretmanager.secretAccessor`.

Quick validation (optional):
```bash
gcloud secrets versions list gemini-api-key-primary --project=${PROJECT_ID}
gcloud secrets versions access latest --secret=gemini-api-key-primary --project=${PROJECT_ID} | wc -c
```

## 7) Firestore / "Firestudio"
- If by "Firestudio" you mean the Firestore admin tools (console) or 3rd-party GUIs, nothing special is required for CI/CD.
- For programmatic access, CI jobs that call Firestore or Firebase Admin SDK will use the same WIF credentials via ADC.

## 8) Going Live
1. Create WIF pool/provider + IAM bindings
2. Add GitLab variables
3. Push to `main` to trigger `build_and_deploy` then `verify_production`
4. Review artifacts: `infinityai_verification_report_*.json`

## 9) Troubleshooting
- OIDC errors: Check provider `issuer-uri`, attribute mapping/condition, and SA bindings.
- Permission denied: Add missing role to the SA, prefer least privilege.
- Firebase deploy auth: verify `firebase-tools` version supports ADC; if not, consider generating a token from SA impersonation at runtime.
- Cloud Run timeouts: adjust min instances, timeouts, or use health-mode endpoints; our verifier is already tuned.
