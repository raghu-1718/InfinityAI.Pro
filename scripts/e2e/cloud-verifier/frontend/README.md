# Frontend E2E Verifier (Playwright)

Purpose: Run a safe, read-only end-to-end verification of the InfinityAI.Pro frontend to ensure:
- Firebase authentication works for a test user
- Dashboard loads and triggers backend API calls
- Backend calls reach cloud run engines indirectly
- UI reflects backend responses with no fatal errors

Safety guarantees (MANDATORY)
- No trades will be placed. No writes to trading APIs.
- No secret values are read or printed.
- Firestore writes are NOT performed (only very small, optional read-only checks via Firebase SDK if explicitly enabled).
- All tests are headless and can be run locally in your secure environment.

Prerequisites
- Node.js (>=18) and npm
- gcloud, firebase CLI (optional) installed for other verifier scripts
- Playwright installed (the run script will install it if missing)

Required environment variables
- BASE_URL - base URL of the deployed frontend (e.g., https://www.infinityai.pro)
- FIREBASE_TEST_EMAIL - test user email (non-privileged)
- FIREBASE_TEST_PASSWORD - test user password

Files
- playwright.config.ts — Playwright configuration (chromium, headless, 60s timeout)
- frontend_e2e.spec.ts — The spec implementing the verification flow (safe and read-only)
- run_frontend_e2e.sh — Wrapper script to validate env, install deps, run tests, and emit results
- package.json — (devDependency: @playwright/test)

Outputs
- Generated under `scripts/e2e/cloud-verifier/output/frontend/`
  - `frontend_e2e_report_<timestamp>.json` (detailed JSON)
  - `summary_<timestamp>.md` (human summary)
  - `screenshots/` (on failures)

How to run
1. Export required env vars:
   export BASE_URL="https://<your-site>"
   export FIREBASE_TEST_EMAIL="test@example.com"
   export FIREBASE_TEST_PASSWORD="hunter2"
2. Execute:
   bash run_frontend_e2e.sh

Notes & Validation
- The test fails loudly: any failed step makes the test exit non-zero and detailed failure reasons are written to the JSON and summary.
- The test does NOT call engine services directly; it observes frontend network requests and reports whether engine hostnames appeared in network traffic (indirect confirmation).
- Review `scripts/e2e/cloud-verifier/output/frontend/` for artifacts and sanitized results.

Security
- Do NOT commit test user credentials to source control or paste them in chat.
- Use ephemeral test accounts with minimal permissions.

If you want, I can add a Playwright Playwright/Trace-enabled debugging mode to help investigate failures (off by default).