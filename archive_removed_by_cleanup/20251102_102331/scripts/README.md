# scripts

Utilities to manage GCP resources for InfinityAI.Pro.

## reset_gcp_environment.ps1

Safely reset Cloud Run and Cloud Functions resources in a GCP project and optionally redeploy engines and functions.

- Deletes Cloud Run services for core engines and Firebase Function backends (excludes extension-managed functions by default)
- Deletes Cloud Functions (excludes functions that start with `ext-` by default)
- Optionally purges Artifact Registry repositories and Secret Manager secrets (off by default)
- Optionally redeploys engines A/B/C-execution/D and the frontend, and optionally Firebase Functions
- Saves an inventory snapshot to `scripts/out/`

### Parameters

- `-ProjectId` (default: `infinity-ai-5ec7c`)
- `-Region` (default: `us-central1`)
- `-IncludeExtensions` — also delete Firebase extension functions/services (off by default)
- `-PurgeArtifactRegistry` — delete Artifact Registry repos in the region (off by default)
- `-PurgeSecrets` — delete all Secret Manager secrets (off by default)
- `-NoPrompt` — run non-interactively
- `-DeployEngines` — redeploy engines and frontend after deletion
- `-DeployFunctions` — redeploy Firebase Functions after deletion (requires `firebase-tools` auth)

### Examples

Dry run (shows plan and prompts):

```powershell
pwsh -NoProfile -File scripts/reset_gcp_environment.ps1
```

Delete and redeploy engines (non-interactive):

```powershell
pwsh -NoProfile -File scripts/reset_gcp_environment.ps1 -NoPrompt -DeployEngines
```

Full reset including extension resources and artifact registry, then redeploy engines:

```powershell
pwsh -NoProfile -File scripts/reset_gcp_environment.ps1 -NoPrompt -IncludeExtensions -PurgeArtifactRegistry -DeployEngines
```

Redeploy Firebase Functions as well (requires firebase auth):

```powershell
pwsh -NoProfile -File scripts/reset_gcp_environment.ps1 -NoPrompt -DeployEngines -DeployFunctions
```

Notes:

- The script excludes extension-managed functions (`ext-*`) unless `-IncludeExtensions` is passed.
- Purging secrets is irreversible; avoid `-PurgeSecrets` unless you plan to re-create all required secrets immediately.
- For functions deploys outside CI, ensure you are authenticated with `firebase-tools` and your project is selected or pass `--project`.

## GCP Fetch & Setup Scripts

These scripts help you fetch current GCP state and set up required secrets, APIs, and IAM bindings for InfinityAI.Pro (project `infinity-ai-5ec7c`). They are safe to re-run and aim to be idempotent.

## Prerequisites

- Google Cloud SDK (`gcloud`) logged in with sufficient permissions (Project Owner recommended for first run)
- Firebase CLI (`firebase`) logged in
- GitHub CLI (`gh`) authenticated (`gh auth login`)

## What they do

- Verify billing status and App Engine initialization
- Enable required APIs: Cloud Build, Cloud Run, Cloud Functions (Gen2), Eventarc, Artifact Registry, Secret Manager, Firebase, Firestore
- Create (if missing) and optionally add versions to GSM secrets:
  - gemini-api-key-primary, gemini-api-key-secondary, dhan-api-key, huggingface-token, trading-engine-secret, webhook-verification-token, telegram-bot-token
- Grant IAM roles (best-effort):
  - Deployer SA (from provided JSON): cloudfunctions.developer, iam.serviceAccountUser, artifactregistry.writer, run.admin, eventarc.admin, cloudbuild.builds.editor
  - Runtime SAs (Compute & AppEngine): secretmanager.secretAccessor
- Set Firebase Functions config `secrets.encryption_key`
- Dump current state (secrets, enabled services, IAM policy, Cloud Run services) into `scripts/out/`
- Optionally set GitHub Actions repo secrets via `gh secret set`

## PowerShell (Windows)

```powershell
# From repo root
pwsh ./scripts/gcp_fetch_and_setup.ps1 -ProjectId "infinity-ai-5ec7c" -Region "us-central1" -Repo "raghu-1718/InfinityAI.Pro" -GithubSaJsonPath "C:\\path\\to\\gcp-sa.json"
```

Flags:

- `-NonInteractive` to skip prompts and only use environment variables

Environment variables used for secret values when `-NonInteractive`:

- `GEMINI_API_KEY_PRIMARY`, `GEMINI_API_KEY_SECONDARY`, `DHAN_API_KEY`, `HUGGINGFACE_TOKEN`, `TRADING_ENGINE_SECRET`, `WEBHOOK_VERIFICATION_TOKEN`, `TELEGRAM_BOT_TOKEN`, `ENCRYPTION_KEY`

## Bash (Linux/macOS)

```bash
# From repo root
PROJECT_ID=infinity-ai-5ec7c REGION=us-central1 REPO=raghu-1718/InfinityAI.Pro \
GITHUB_SA_JSON_PATH="$HOME/gcp-sa.json" \
./scripts/gcp_fetch_and_setup.sh
```

Non-interactive (CI) example:

```bash
PROJECT_ID=infinity-ai-5ec7c REGION=us-central1 REPO=raghu-1718/InfinityAI.Pro NON_INTERACTIVE=true \
GEMINI_API_KEY_PRIMARY=... GEMINI_API_KEY_SECONDARY=... DHAN_API_KEY=... ENCRYPTION_KEY=... \
./scripts/gcp_fetch_and_setup.sh
```

## Outputs

- `scripts/out/secrets_list.json` — GSM secrets
- `scripts/out/services_enabled.json` — enabled GCP services
- `scripts/out/project_iam_policy.json` — project IAM policy
- `scripts/out/cloud_run_services.json` — Cloud Run services
- `scripts/out/<service>.json` — individual Cloud Run service descriptions (if present)

## Notes

- If the workflow cannot grant IAM roles (insufficient privileges), grant them once in the console and re-run the script.
- For GitHub repo secrets (`gh secret set`), the CLI must be authenticated and have access to the `raghu-1718/InfinityAI.Pro` repository.
- These scripts don’t store secrets in the repo; they only write state and set secrets in GSM/GitHub.
