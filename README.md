# InfinityAI.Pro

Production-ready AI trading platform for Indian markets (NSE/BSE/MCX), built as four independently deployable microservices on Google Cloud Run with a React + Vite frontend on Firebase Hosting.

Live site: https://infinityai.pro

---

## Architecture

- Engine A — Market data ingestion + technicals (FastAPI)
- Engine B — AI/ML signals and predictions (FastAPI, TensorFlow/Vertex integration)
- Engine C — Trade execution with Dhan OAuth + risk management (FastAPI)
- Engine D — Orchestrator + AI assistant + WebSocket aggregator (FastAPI)
- Frontend — React + Vite + TypeScript dashboard (Firebase Hosting)

GCP Project: after-yesterday-473512-k3 (region: us-central1)

### Cloud Run services (deployed)

- Engine A: https://infinityai-engine-a-bprmddefsa-uc.a.run.app
- Engine B: https://infinityai-engine-b-bprmddefsa-uc.a.run.app
- Engine C: https://infinityai-engine-c-execution-bprmddefsa-uc.a.run.app
- Engine D: https://infinityai-engine-d-bprmddefsa-uc.a.run.app

Custom domains (configured):
- Frontend: https://infinityai.pro
- Engine subdomains: engine-a.infinityai.pro, engine-b.infinityai.pro, engine-c.infinityai.pro, engine-d.infinityai.pro

---

## Health and key endpoints

- Engine A
  - GET /health
  - GET /api/market-data/{SYMBOL} (e.g., NIFTY, RELIANCE)
- Engine B
  - GET /health
  - GET /api/ai-signals
- Engine C
  - GET /health
  - GET /api/orders/status (auth required)
  - GET /api/dhan/demat/export (auth required)
- Engine D
  - GET /health
  - WS /ws/dashboard

Security headers are enforced by a shared middleware (no sniff, frame deny, HSTS). SSL is active on the production domain.

---

## Security and secrets

- No hardcoded secrets. All credentials are stored in Google Cloud Secret Manager and loaded at runtime using `get_secret()`.
- Dhan OAuth secrets and access tokens are managed via Secret Manager; Engine C reads them on demand.
- JWTs are issued by Engine D for authenticated frontend calls.
- CORS is configured for the frontend origin.

---

## Verification status (Nov 6, 2025)

- 150/150 tasks verified (see reports below)
- Automated test suite: 19/19 PASS (100%)
- Engines A–D: Healthy (A 344ms, B 341ms avg latency)
- Frontend: Live with SSL at https://infinityai.pro
- Dhan: Live integration confirmed (balance/positions/orders verified)

Reports and scripts:
- COMPLETE_150_VERIFICATION_REPORT.md (full details)
- FINAL_150_SUMMARY.md (quick stats)
- PLATFORM_STATUS.md (task matrix)
- VERIFICATION_SUMMARY.md (exec summary)
- verification-results-20251106-195434.json (automation output)
- scripts/complete-150-verification.ps1 (re-runs non-auth checks)

Run the automated verification (Windows PowerShell):

```powershell
pwsh -File .\scripts\complete-150-verification.ps1
```

---

## Local development

Prereqs: Python 3.10+, Node 18+, Google Cloud SDK, Firebase CLI.

Install backend deps (repeat per engine):

```powershell
pip install -r engines/engine-a/requirements.txt
```

Run engines locally (examples):

```powershell
cd engines/engine-a; python main.py
cd engines/engine-b; python main.py
cd engines/engine-c-execution; python main.py
cd engines/engine-d; python main.py
```

Install and run frontend:

```powershell
npm install --prefix frontend
npm run dev --prefix frontend
```

---

## Deployment and operations

Cloud Run (us-central1) with Cloud Build; Firebase Hosting for frontend.

Quick verification commands (already executed during platform audit):

```powershell
# GCP
gcloud run services list --region=us-central1
gcloud dns managed-zones list
gcloud dns record-sets list --zone=infinityai-pro-zone
gcloud secrets list
gcloud builds list --limit=10
gcloud iam service-accounts list

# Firebase
firebase projects:list
firebase functions:list --project=after-yesterday-473512-k3
firebase firestore:indexes --project=after-yesterday-473512-k3
```

---

## Risk and trading controls

Engine C enforces conservative risk parameters and authorization checks before trade execution. Callback URLs and webhooks are restricted to the production domain and validated with shared secrets.

---

## Folder structure (top-level)

- engines/ — Engine A/B/C/D microservices
- frontend/ — React + Vite frontend
- functions/ — Firebase Functions (callable)
- scripts/ — Automation (verification, deployment, diagnostics)
- config/ — Environment/config references (no secrets)
- docs/ — Architecture and project documentation
- reports/*.md — Generated audit and verification reports

---

## License

Copyright © InfinityAI. All rights reserved.
