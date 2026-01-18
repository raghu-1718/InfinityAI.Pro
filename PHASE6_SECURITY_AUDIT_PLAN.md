# 🔐 Phase 6: Security Audit Plan

**Date**: January 19, 2026
**Duration**: 2 hours
**Objective**: Perform a comprehensive, read-only security audit across Cloud Run, Firebase Hosting, Firestore rules, IAM, Secret Manager/KMS, and logging.
**Sign-Off Authority**: Security Lead

---

## 📋 Scope & Checks

- **Cloud Run (Engine A/B/C)**
  - Ingress and auth settings (public vs restricted)
  - Instance limits, concurrency, startup probes
  - Secrets injection (Secret Manager), KMS usage
  - Resource limits and CPU throttling
- **Firebase Hosting & CORS**
  - Hosting rewrites to Cloud Run; domain restrictions
  - CORS configs in functions/services
- **Firestore Rules**
  - Access isolation by user
  - Open read surfaces (coupons, sessions) evaluated for data sensitivity
- **IAM & Service Accounts**
  - Least-privilege review of project-level roles
  - Service accounts for Cloud Run/Functions/Deploy
- **Secret Manager & KMS**
  - Secret inventory; replication policy
  - KMS keyring/key existence and rotation policy
- **Logging & PII**
  - ERROR logs for secret/PII leakage
  - Startup/runtime failures and mitigation

---

## 🛠️ Commands (READ-ONLY)

Already executed (evidence captured):

- Cloud Run describe: engine-a/b/c (ingress=all; secrets from Secret Manager)
- IAM roles summary: `gcloud projects get-iam-policy ...`
- Service accounts list: engine-a/b/c, deployer SAs
- Secret Manager list: dhan-_ , encryption-key, gemini-api-key, user-creds-_
- Logs sample: Cloud Run errors (engine-c startup import issues; verifycoupon CORS error)
- KMS list: **NOT_FOUND** for keyring `infinityai-credentials` (global)

To execute if needed for deeper evidence (still READ-ONLY):

```bash
# Per-service ingress/auth (concise view)
gcloud run services describe engine-a --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --format='value(metadata.annotations["run.googleapis.com/ingress"],status.url)'

# IAM bindings detail (narrowed)
gcloud projects get-iam-policy galvanic-pulsar-482815-h0 \
  --flatten='bindings[].members' \
  --filter='bindings.role:owner OR bindings.role:editor' \
  --format='table(bindings.role,bindings.members)'

# Secret metadata
gcloud secrets describe dhan-client-id --project=galvanic-pulsar-482815-h0 \
  --format='value(replication.policy)'

# KMS keyrings/keys check (global/us)
gcloud kms keyrings list --location=global --project=galvanic-pulsar-482815-h0
```

---

## ✅ Acceptance / Sign-Off Criteria

- Cloud Run ingress posture documented; action items for public endpoints (ingress=all) defined.
- Secret storage verified: all sensitive values via Secret Manager; no plaintext envs.
- KMS posture clarified: keyring/key exists with rotation **or** action item to create/enable.
- IAM review completed; high-privileged roles scoped/justified; action items for over-broad roles.
- Firestore rules reviewed; open reads (coupons/coupon_sessions) confirmed intentional; no open writes.
- CORS/Hosting rewrites assessed; confirm production domains only and HTTPS enforced.
- Logs reviewed; no PII/secret leakage; note any startup errors needing remediation.
- Deliverables produced (plan + results) with Security Lead approval.

---

## 🧭 Timeline (2 hours)

1. Evidence capture (20m) — completed commands above.
2. Findings synthesis (40m) — document ingress, secrets, IAM, rules, logs.
3. Recommendations & action items (30m) — hardening steps.
4. Results doc + sign-off (30m).

---

## 📦 Outputs

- PHASE6_SECURITY_AUDIT_RESULTS.md (findings, risks, actions, sign-off)

---

_Status: Ready to execute (read-only)._
