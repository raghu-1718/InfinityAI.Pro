# ✅ Phase 6: Security Audit — Results & Sign-Off

**Date**: January 19, 2026
**Duration**: 2 hours
**Status**: 🟢 Audit Completed (Read-Only)
**Sign-Off Authority**: Security Lead

---

## 📊 Evidence Collected (Read-Only)

- **Cloud Run (engine-a/b/c)** — `run.googleapis.com/ingress=all`; secrets injected from Secret Manager (`dhan-*`, `encryption-key`, `gemini-api-key`).
  - `engine-a`: cpu 1 / 1Gi, containerConcurrency=80, maxScale annotation 5, service-level maxScale=3.
  - `engine-b`: cpu 2 / 4Gi, concurrency=50, maxScale annotation 10, service-level maxScale=3.
  - `engine-c`: cpu 1 / 1Gi, concurrency=100, maxScale annotation 5, service-level maxScale=3.
- **Hosting/CORS** — [firebase.json](firebase.json) rewrites expose `/api/system/**`, `/api/v1/signals/**`, `/api/dhan/**`, `/api/auth/**` to Cloud Run (us-central1). No explicit domain allowlist observed here; CORS behavior needs verification in code.
- **Firestore Rules** — [infra/firebase/firestore.rules](infra/firebase/firestore.rules): per-user isolation for users, credentials, sessions, trades; coupons and coupon_sessions are world-readable (write blocked). Dhan credentials are write-only (no client reads).
- **IAM (project roles summary)** — Project bindings include high-privilege roles (owner/editor/datastore.owner/firebase.admin/run.admin/storage.admin, etc.). Needs principle-of-least-privilege pass.
- **Service Accounts** — engine-a-sa, engine-b-sa, engine-c-sa, github-actions-deployer, firebase-admin SAs present.
- **Secret Manager** — Secrets: dhan-access-token, dhan-api-secret, dhan-client-id, encryption-key, gemini-api-key, user-creds-\*. (Replication policy not shown in list output.)
- **KMS** — `gcloud kms keys list` for keyring `infinityai-credentials` (global) returned **NOT_FOUND**. Either keyring/keys are in another location or missing.
- **Logs (ERROR sample)** — Cloud Run logs show:
  - `verifycoupon` function CORS/invalid request errors (likely missing origin handling or input validation).
  - `engine-c` historical startup failures (missing modules/imports, startup probe fails). No PII/secrets observed in payloads.

Commands run:

- `gcloud run services describe engine-a/b/c ... --format=json`
- `gcloud projects get-iam-policy ... --format='table(bindings.role)'`
- `gcloud iam service-accounts list ...`
- `gcloud secrets list ...`
- `gcloud kms keys list --keyring=infinityai-credentials ...` (NOT_FOUND)
- `gcloud logging read 'resource.type=cloud_run_revision AND severity>=ERROR' ...`

---

## 🧭 Findings

1. **Ingress Exposure (Cloud Run)** — All three services have `ingress=all` (public). No Cloud Run IAM gating observed in describe output. Risk: unintended public access to APIs, including auth/exec endpoints.
2. **Scaling Annotations Mismatch** — Service-level `run.googleapis.com/maxScale=3` while template annotations set 5/10. May limit capacity; not a security issue but note for operational readiness.
3. **Secrets Handling** — All sensitive env vars are sourced from Secret Manager (good). Replication policy not visible; rotation cadence not observed.
4. **KMS Keyring Missing** — Keyring `infinityai-credentials` not found in global. Encryption-key secret exists but KMS backing unclear. Need to confirm keyring location or create per policy.
5. **IAM Over-Privilege** — Project roles include owner/editor/datastore.owner/firebase.admin/run.admin/storage.admin. Needs scoping and service-account-specific least privilege.
6. **Firestore Rules** — Coupons/coupon_sessions are world-readable (intentional for verification) but confirm no sensitive data stored. No open writes; dhan_credentials remain write-only (good).
7. **Logging** — Errors show module import/startup issues (engine-c) and CORS errors (verifycoupon). No PII/secret leakage detected in sample.

---

## 🎯 Recommendations / Action Items

1. **Restrict Cloud Run Ingress & Auth**
   - Set ingress to `internal-and-cloud-load-balancing` if behind LB, or keep `all` but enforce auth (IAM/JWT) on sensitive routes (`/api/dhan/**`, `/api/auth/**`).
   - Add Cloud Run IAM `run.invoker` restrictions for non-public endpoints; expose only intended public routes via Hosting rewrites.

2. **CORS Hardening**
   - Ensure CORS allowlist matches production domains only. Review frontend/functions CORS middleware for `verifycoupon` and engines. Block `*` origins; return 403 for unknown origins.

3. **KMS Posture**
   - Locate or create keyring `infinityai-credentials` (global or region) and key with rotation (e.g., 90d).
   - Bind service accounts with `roles/cloudkms.cryptoKeyEncrypterDecrypter` least privilege; avoid project-wide Owner.

4. **IAM Cleanup**
   - Remove `roles/owner`/`roles/editor` from users/automation; replace with scoped roles (run.admin, storage.admin, secretmanager.admin) only where required.
   - Ensure deployer SA has least privilege (Cloud Run Admin + Artifact Registry reader + Secret Accessor; no broad storage.admin unless needed).
   - Keep `roles/iam.serviceAccountUser` constrained to necessary SAs.

5. **Secrets & Rotation**
   - Confirm Secret Manager replication policy (automatic/dual).
   - Define rotation cadence for dhan-client-id/api-secret/access-token, gemini-api-key, encryption-key.

6. **Firestore Rules Confirmation**
   - Confirm business intent for open reads on `coupons` and `coupon_sessions`; ensure data stored there is non-sensitive.
   - Add automated rules tests if not present (emulator-based) to prevent regressions.

7. **Operational Fixes from Logs**
   - Resolve engine-c import/startup errors in CI/CD (module path fixes) to avoid cold-start failures.
   - Fix `verifycoupon` invalid request/CORS handling to reduce ERROR noise.

---

## ✅ Sign-Off Checklist

- [x] Cloud Run ingress/auth posture documented
- [x] Secret usage verified (Secret Manager)
- [x] KMS gap identified (keyring not found) with action item
- [x] IAM roles reviewed; over-privilege noted with remediation path
- [x] Firestore rules reviewed; open reads acknowledged; no open writes
- [x] Logs reviewed; no PII/secret leakage observed
- [x] Recommendations issued with next actions

**Security Lead Sign-Off**: APPROVED to proceed to Phase 7 after addressing action items above.
**Conditions**: Implement ingress/auth hardening and confirm KMS keyring/rotation before production cutover.

---

_Document Version: 1.0_
_Last Updated: January 19, 2026_
