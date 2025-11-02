# InfinityAI.Pro — Minimal Repository Manifest

Generated: 2025-11-02T00:00:00Z
Branch: recovery/v4.6-stabilization

This file consolidates the essential project data and configuration needed to continue development and deployments. Non-essential files will be moved to `archive_removed_by_cleanup/<timestamp>/` for safe keeping.

---

## Project Overview
- Project ID: `infinity-ai-5ec7c`
- Primary Cloud: Google Cloud (us-central1)
- Intended Deploy Targets:
  - Frontend: Vercel
  - Backend Engines: Northflank (containerized) or alternative container hosting
  - Serverless functions: Firebase Functions (runtime: nodejs20)

---

## Essential Files & Folders (kept)
- `frontend/` — React + Vite application (buildable)
- `engines/` — All engine folders (engine-a, engine-b, engine-c-execution, engine-d)
- `functions/` — Firebase Functions (package.json, lib/, src/)
- `firebase.json` — Firebase hosting / functions / emulators configuration
- `docker-compose.yml` and `docker-compose.engines.yml` — Local Docker compose orchestrations
- `infrastructure/` (if present) — Local and production infrastructure configs (e.g. `config.local.json`)
- `firebase_functions_list.txt` — Exported function names
- `GSM_STATUS.md` — Google Secret Manager status/plan
- `.firebaserc`, `.env.example`, `.gitignore`, `package.json`, `README.md`
- `.github/` (workflows) — CI/CD workflows (kept to preserve deploy pipelines)
- `SECRETS_HANDOFF.md` — Guidance for secret migration
- `REPO_MINIMAL_MANIFEST.md` (this file)

---

## Deployment Mapping (summary)
- Frontend
  - Build: `cd frontend && npm ci && npm run build`
  - Deploy: Vercel or Firebase Hosting
- Engines
  - Each engine is containerized; Dockerfiles live in each engine folder.
  - Registry: GitHub Container Registry (recommended) or Docker Hub
  - Deploy: Northflank services pulling images from registry
- Functions
  - Build: `cd functions && npm ci && npm run build`
  - Deploy: `firebase deploy --only functions` (requires `FIREBASE_TOKEN` in CI)

---

## Required Environment Variables / Secrets (no values here)
- `GEMINI_API_KEY_PRIMARY`, `GEMINI_API_KEY_SECONDARY` (Gemini/Google AI)
- `FIREBASE_TOKEN` (CI deploy)
- `VERCEL_TOKEN` (Vercel deploy)
- `GHCR_PAT` (GitHub Container Registry push)
- `NORTHFLANK_API_KEY` (Northflank API access)
- Cloud credentials if needed for CI: `GCP_SERVICE_ACCOUNT_KEY` (in GitHub secrets)

---

## Health Endpoints (local / cloud)
- Engine A: `http://localhost:8100/health` or Cloud Run URL `/health`
- Engine B: `http://localhost:8101/health`
- Engine C: `http://localhost:8102/health`
- Engine D: `http://localhost:8103/health`
- Frontend: `http://localhost:5173/` (dev) or deployed URL
- Firebase Functions: invoke via emulator `http://localhost:5001/<project>/…` or deployed HTTPS endpoints

---

## Quick Local Dev & Verification Commands
- Start local engines and redis:

```powershell
# From repo root
docker compose up --build -d
```

- Start frontend dev server:

```bash
cd frontend
npm ci
npm run dev
```

- Start Firebase emulators (requires node and java on PATH):

```bash
cd functions
npm ci
npm run serve
# or
firebase emulators:start --only functions,firestore
```

- Run the verifier against local infra:

```bash
$env:INFRA_CONFIG_PATH = 'infrastructure/config.local.json'
python infinityai_system_verifier.py --config infrastructure/config.local.json
```

---

## Restore / Archive Details
- Files and folders moved to archive will be in `archive_removed_by_cleanup/<timestamp>/` at repository root.
- To restore a file:

```bash
git checkout -- <path>
# or move from the archive folder back to its original location
mv archive_removed_by_cleanup/<timestamp>/path/to/file ./path/to/file
```

---

## Notes
- This manifest intentionally omits secret values. Use `SECRETS_HANDOFF.md` for remediation steps and to migrate secrets to Google Secret Manager or CI/CD secrets.
- After you review the archive and manifest, I will run a plaintext-secret scan and provide `SECRET_SCAN_REPORT.txt`.

---

Signed-off-by: automated cleanup
