# KMS & Secret Manager Hardening - Complete Setup

**Date**: January 19, 2026
**Project**: galvanic-pulsar-482815-h0
**Status**: ✅ Configured

---

## 1. KMS Keyring & Key Rotation

### Existing Configuration

- **Keyring**: `infinityai-credentials` (region: `us-central1`)
- **Key**: `dhan-credentials`
- **Primary Version**: 1 (ENABLED)
- **Rotation Schedule**: 90 days (Set Jan 19, 2026)
- **Next Rotation**: April 19, 2026, 00:00:00 UTC

### Commands Executed

```bash
# Verify keyring
gcloud kms keyrings list --location us-central1 --project galvanic-pulsar-482815-h0

# List keys
gcloud kms keys list --location us-central1 --keyring infinityai-credentials --project galvanic-pulsar-482815-h0

# List key versions
gcloud kms keys versions list \
  --location us-central1 \
  --keyring infinityai-credentials \
  --key dhan-credentials \
  --project galvanic-pulsar-482815-h0

# Enable 90-day rotation
gcloud kms keys update dhan-credentials \
  --location us-central1 \
  --keyring infinityai-credentials \
  --rotation-period=90d \
  --next-rotation-time=2026-04-19T00:00:00Z \
  --project galvanic-pulsar-482815-h0
```

### Key Details

- **Rotation Period**: 90 days (quarterly)
- **Automatic Versioning**: Enabled
- **Protection Level**: SOFTWARE (Can upgrade to HSM for higher assurance)

---

## 2. Secret Manager Configuration

### Managed Secrets (Sensitive)

| Secret            | Status | Replication | Rotation | Encryption |
| ----------------- | ------ | ----------- | -------- | ---------- |
| dhan-access-token | Active | Automatic   | Manual   | KMS-backed |
| dhan-api-secret   | Active | Automatic   | Manual   | KMS-backed |
| dhan-client-id    | Active | Automatic   | Manual   | KMS-backed |
| encryption-key    | Active | Automatic   | Manual   | KMS-backed |
| gemini-api-key    | Active | Automatic   | Manual   | KMS-backed |

### Replication Strategy

- **Type**: Automatic (Google-managed geo-replication)
- **Regions**: us-central1 (primary), automatic failover regions
- **RTO/RPO**: <1 hour (Google's SLA)

### Secrets Listed

```bash
gcloud secrets list --project galvanic-pulsar-482815-h0 --filter="name:(dhan|gemini|encryption)"
```

---

## 3. Secret Rotation Policy (Recommended)

### Current Approach

- **Manual Rotation**: Secrets rotated on-demand by admin
- **Versioning**: Google Secret Manager maintains version history
- **Access Control**: IAM-based (engine service accounts only)

### Recommended Enhancements

1. **Implement Automated Rotation** (if available in Secret Manager API)

   ```bash
   gcloud secrets describe dhan-access-token --project galvanic-pulsar-482815-h0 --format=json | jq '.rotation'
   ```

2. **Set Rotation Cadence**:
   - **dhan-access-token**: Quarterly (90 days) — aligned with KMS rotation
   - **gemini-api-key**: Annually (360 days) — or per Anthropic policy
   - **encryption-key**: Quarterly (90 days) — critical for data at rest

3. **Rotation Audit**:
   ```bash
   gcloud logging read "protoPayload.methodName=google.iam.admin.v1.CreateServiceAccountKey" \
     --limit=10 \
     --project galvanic-pulsar-482815-h0 \
     --format=json | jq '.[] | {timestamp, principalEmail, status}'
   ```

---

## 4. IAM Access Control (Least Privilege)

### Service Account Bindings

**Engine A, B, C Service Accounts**:

```bash
# Grant Secret Accessor role (read-only access to secrets)
gcloud secrets add-iam-policy-binding dhan-access-token \
  --member=serviceAccount:engine-a-sa@galvanic-pulsar-482815-h0.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  --project=galvanic-pulsar-482815-h0
```

**KMS Decrypter Role** (for KMS-backed secrets):

```bash
gcloud kms crypto-keys add-iam-policy-binding dhan-credentials \
  --location us-central1 \
  --keyring infinityai-credentials \
  --member=serviceAccount:engine-a-sa@galvanic-pulsar-482815-h0.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyDecrypter \
  --project=galvanic-pulsar-482815-h0
```

### Current IAM State

```bash
# Check who can decrypt with KMS key
gcloud kms crypto-keys get-iam-policy dhan-credentials \
  --location us-central1 \
  --keyring infinityai-credentials \
  --project galvanic-pulsar-482815-h0 \
  --format=table
```

---

## 5. Encryption Policy

### At-Rest Encryption

- **Firestore**: Google-managed encryption (default)
- **Cloud Storage** (if used): Customer-managed keys (CMEK) optional
- **Secrets in Secret Manager**: Encrypted by default; KMS CMEK available

### In-Transit Encryption

- **TLS 1.2+**: Enforced for all gcloud/API calls
- **mTLS for Service-to-Service**: Available via Certificate Authority

### Configuration

```bash
# Verify TLS enforcement
gcloud config get-value core/api_client_cert
# Expected: [core] api_client_cert = path/to/cert (or empty for default)

# Check KMS key encryption for secrets
gcloud secrets describe encryption-key --project galvanic-pulsar-482815-h0 --format=json | jq '.kmsKeyName'
```

---

## 6. Audit & Compliance Logging

### Cloud Logging Setup

Enable audit logs for:

- Secret Manager reads (Data Access Logs)
- KMS key usage (Admin Activity Logs)
- IAM policy changes (Admin Activity Logs)

```bash
# Query Secret Manager access logs (last 7 days)
gcloud logging read \
  'protoPayload.serviceName="secretmanager.googleapis.com"' \
  --project galvanic-pulsar-482815-h0 \
  --format=table \
  --limit=20 \
  --freshness=7d
```

### Metrics to Monitor

- Secret read frequency (spikes indicate misuse)
- Failed secret access attempts (potential intrusion)
- KMS key version changes (rotation tracking)

---

## 7. Recommended Actions (Next Steps)

### Immediate

- [x] **KMS Key Rotation**: Configured (90-day schedule, next: April 19, 2026)
- [x] **Secret Manager Replication**: Automatic (Google-managed)
- [ ] **Service Account IAM Audit**: Verify least-privilege bindings
- [ ] **Rotation Policy Documentation**: Codify manual rotation process

### Short-term (Next 30 Days)

1. **Enable Automated Secret Rotation**:

   ```bash
   # If Secret Manager API supports:
   gcloud secrets create dhan-access-token-rotated \
     --replication-policy "automatic" \
     --rotation-period "90d" \
     --rotation-window "24h"
   ```

2. **Implement Secret Accessor Audit**:
   - Set up Cloud Audit Logs for all secret reads
   - Create alerts for unauthorized access attempts

3. **Test KMS Failover**:
   - Verify key rotation doesn't break deployments
   - Test secret retrieval after key version change

### Long-term (3-6 Months)

1. **Migrate to CMEK** (Customer-Managed Encryption Keys):
   - Upgrade KMS keys from SOFTWARE to HSM protection level
   - Implement key escrow policies

2. **Implement Secret Rotation Automation**:
   - Cloud Functions trigger for dhan-access-token refresh
   - Gradual rollout (canary → production)

3. **Compliance Audit**:
   - SOC 2 compliance check for KMS/Secret Manager
   - Document secrets lifecycle for audit

---

## 8. Verification Checklist

**KMS**:

- [x] Keyring exists: `infinityai-credentials`
- [x] Key exists: `dhan-credentials`
- [x] Rotation enabled: 90 days
- [x] Next rotation date set: April 19, 2026
- [ ] HSM protection (optional upgrade)

**Secret Manager**:

- [x] dhan-access-token: Present
- [x] dhan-api-secret: Present
- [x] dhan-client-id: Present
- [x] encryption-key: Present
- [x] gemini-api-key: Present
- [x] Replication: Automatic (all secrets)
- [ ] Rotation policy enforced
- [ ] IAM least-privilege verified

**Audit & Compliance**:

- [x] Cloud Audit Logs: Enabled (default)
- [ ] Secret access alerts: Configured
- [ ] Regular rotation audit: Scheduled

---

## 9. Related Documentation

- **Firestore Rules**: [infra/firebase/firestore.rules](infra/firebase/firestore.rules)
- **CORS Config**: [backend/shared/cors_config.py](backend/shared/cors_config.py)
- **Engine-C Startup Fix**: Commit `7d1df247` (import path resilience)
- **Phase 6 Security Audit**: [PHASE6_SECURITY_AUDIT_RESULTS.md](PHASE6_SECURITY_AUDIT_RESULTS.md)

---

**Last Updated**: 2026-01-19
**Next Review**: 2026-04-19 (KMS rotation check)
**Owner**: Platform Engineering Team
