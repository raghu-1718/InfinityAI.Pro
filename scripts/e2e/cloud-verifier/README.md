# Cloud Verifier — End-to-End Manual Runner

Purpose: Collection of scripts to verify live cloud systems (GCP Cloud Run, Firebase, Secret Manager, Firestore) in a real authenticated user context. These are _manual_, non-destructive checks you run in the target environment (Mode A from the verification plan).

Security note: These scripts require real credentials (Firebase test user, optional broker credentials). DO NOT commit secrets into the repo. Pass secrets via environment variables or run locally.

Prerequisites
- gcloud CLI authenticated and set to the target project (gcloud auth login; gcloud config set project <PROJECT_ID>)
- gh CLI authenticated (for GitHub inventory steps) — optional
- firebase CLI (optional for some steps) — optional
- curl, jq, node (>=18) and npm on the host

Directory: scripts/e2e/cloud-verifier

Usage (recommended):

1) Prepare environment variables (export in your shell or use a .env file):

- GCP_PROJECT (optional if gcloud project configured)
- FIREBASE_API_KEY (only required for Firebase user auth REST flows)
- FIREBASE_TEST_EMAIL
- FIREBASE_TEST_PASSWORD
- BROKER_TEST_TOKEN (optional; for broker connect / trading dry-run)
- RUN_SAMPLE_POSTS=true (set to enable POST contract tests)

2) Run the inventory and probes (non-destructive):

bash run_all.sh

This will produce output files under scripts/e2e/cloud-verifier/output/ with timestamped JSON/logs. Check these outputs and the final report.

Script summary
- run_inventory.sh — collects GCP, Cloud Run, Secrets, Firestore, GitHub metadata (safe; does not read secret values)
- probe_engines.sh — hits /health, /openapi.json and optional POST contract checks (requires RUN_SAMPLE_POSTS=true and you should review payloads before running)
- firebase_e2e.js — signs in a test Firebase user (email/password) and performs Firestore read/write under user context; requires FIREBASE_API_KEY and user creds
- run_all.sh — runs all of the above, aggregates results into the output folder

How to share results
- The scripts write JSON + log files to scripts/e2e/cloud-verifier/output/. Share only the sanitized JSON (remove any accidental secret exposures) if you want me to analyze the output.

If you'd like, I can also create a variant that runs headless Playwright to exercise the dashboard flow (login, navigate, trigger AI signal requests) — say the word and I’ll add it.

---

Runbook hints and safety
- Review the POST sample payloads before enabling them (they can trigger side-effects if the engine accepts them as real requests)
- Use a broker sandbox account when testing trading dry-runs
- If you want me to analyze output files, upload them via the secure channel or paste them into the chat after sanitizing
