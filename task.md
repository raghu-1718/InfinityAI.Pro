# Operational Alignment & Hardening

- [ ] **1. Normalize API Routing**
  - [x] Scan frontend for legacy `*.run.app` URLs.
  - [x] Scan frontend for legacy paths (`/apisystemstate`, `/health`).
  - [x] Replace with canonical relative paths (`/api/system/state`, etc.).
  - [x] Validate `firebase.json` rewrites match E2E report.
  - [x] Redeploy frontend and verify Network tab.

- [ ] **2. Reconfirm Engine Health**
  - [x] Engine A: `GET /api/system/state` (JSON 200).
  - [x] Engine B: `POST /api/v1/signals/batch` (JSON 2xx).
  - [x] Engine C: `POST /api/auth/coupon/verify` & `/api/dhan/*` (JSON 2xx).
  - [x] Ensure no HTML error pages.

- [x] **3. Cleanup CORS**
  - [x] Verify CORS headers on Cloud Run services (Engine A, B, C).
  - [x] Ensure `OPTIONS` requests return 204/200 with headers.
  - [x] Verify no CORS errors in Browser Console.

- [x] **4. Enforce JSON-only Responses**
  - [x] Identify Funds/Credentials endpoints.
  - [x] Backend: Ensure JSON errors (no HTML).
  - [x] Frontend: Harden `fetch` handling (check Content-Type).
  - [x] Regression test Funds/Credentials UI.

- [x] **5. Fix Secret Manager IAM**
  - [x] Identify Engine C Service Account.
  - [x] Grant `roles/secretmanager.secretAccessor` & `secretVersionAdder`.
  - [x] Verify Dhan credentials save/read flow.

- [ ] **6. Final Verification**
  - [ ] "Hard Refresh" check.
  - [ ] System Banner "NORMAL".
  - [ ] Monitoring & Alerts setup.

- [ ] **7. Domain Mapping (Cloud Run)**
  - [/] Verify `infinityai.pro` ownership in Cloud Run (Pending Propagation).
  - [/] Map `engine-a.infinityai.pro` -> Engine A (Pending Propagation).
  - [/] Map `engine-b.infinityai.pro` -> Engine B (Pending Propagation).
  - [/] Map `engine-c.infinityai.pro` -> Engine C (Pending Propagation).
  - [/] Map `engine-c.infinityai.pro` -> Engine C (Pending Propagation).
  - [x] Provide DNS records to user.

- [x] **8. Real-time End-to-End Verification**
  - [x] **Frontend & Routing**: Verify `https://infinityai.pro` rewrites to Engines A/B/C.
  - [x] **Firestore Integration**: Verify read/write access from both Frontend and Backend.
  - [x] **AI/ML (Engine B)**: Validate signal generation and model response.
  - [x] **Dhan Integration (Engine C)**: Verify broker connectivity and execution logic.
  - [x] **Data Flow**: Trace request/response cycle across all components.
  - [x] **Final Report**: Generate `verification_report.md`.
