# 🔧 Quick Reference Card - InfinityAI.Pro Production

## Service URLs

```
Engine A:    https://engine-a-3acobgd3qa-uc.a.run.app
Engine B:    https://engine-b-3acobgd3qa-uc.a.run.app
Engine C:    https://engine-c-3acobgd3qa-uc.a.run.app
Frontend:    https://galvanic-pulsar-482815-h0.web.app
```

## Common Commands

### Check Service Status
```bash
gcloud run services list --project=galvanic-pulsar-482815-h0
gcloud run services describe engine-a --region=us-central1 --project=galvanic-pulsar-482815-h0
```

### View Recent Logs
```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --project=galvanic-pulsar-482815-h0 --limit=50

# Errors only
gcloud logging read "severity=ERROR" \
  --project=galvanic-pulsar-482815-h0 --limit=50
```

### Monitor Specific Service
```bash
gcloud run services logs read engine-c \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --limit=100
```

### Check Environment Variables
```bash
gcloud run services describe engine-a \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --format="value(spec.template.spec.containers[0].env)"
```

### Restart Service (uses existing image)
```bash
gcloud run deploy engine-a \
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-a:latest \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

### Rollback to Previous Revision
```bash
gcloud run services update-traffic engine-a \
  --to-revisions=engine-a-00043-prev=100 \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

## Security Verification

### Test CORS (Localhost should be BLOCKED)
```bash
curl -i -H "Origin: http://localhost:3000" \
  https://engine-a-3acobgd3qa-uc.a.run.app/health
# Expected: No access-control-allow-origin header
```

### Test CORS (Production should be ALLOWED)
```bash
curl -i -H "Origin: https://infinityai.pro" \
  https://engine-a-3acobgd3qa-uc.a.run.app/health
# Expected: access-control-allow-origin: https://infinityai.pro
```

### Check KMS Key
```bash
gcloud kms keys describe dhan-credentials \
  --location=us-central1 \
  --keyring=infinityai-credentials \
  --project=galvanic-pulsar-482815-h0
```

### Check KMS IAM Permissions
```bash
gcloud kms keys get-iam-policy dhan-credentials \
  --location=us-central1 \
  --keyring=infinityai-credentials \
  --project=galvanic-pulsar-482815-h0
```

## Firestore Operations

### Check Credentials Collection
```bash
# View encrypted credentials (via CLI)
gcloud firestore documents list --collection-path=dhan_credentials \
  --project=galvanic-pulsar-482815-h0

# View user credentials
gcloud firestore documents list --collection-path=user_broker_credentials \
  --project=galvanic-pulsar-482815-h0
```

## Environment Variables

**Production Values** (all 3 engines):
```bash
ENVIRONMENT=production
GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0
LOG_LEVEL=INFO
DEBUG=false
ENABLE_LOCALHOST_CORS=false
```

## Build Commands

### Build Individual Engine
```bash
gcloud builds submit --config=backend/engine-a/cloudbuild.yaml \
  --project=galvanic-pulsar-482815-h0 --region=us-central1
```

### Build Frontend
```bash
cd frontend/web-app
npm run build
firebase deploy --only hosting --project=galvanic-pulsar-482815-h0
```

## Monitoring Dashboards

**Cloud Console URLs**:
- Cloud Run: https://console.cloud.google.com/run?project=galvanic-pulsar-482815-h0
- Logging: https://console.cloud.google.com/logs?project=galvanic-pulsar-482815-h0
- Cloud Build: https://console.cloud.google.com/cloud-build?project=galvanic-pulsar-482815-h0
- KMS: https://console.cloud.google.com/security/kms?project=galvanic-pulsar-482815-h0

## Emergency Procedures

### If Service Down
```bash
# Check status
gcloud run services describe engine-a --region=us-central1

# Redeploy from latest image
gcloud run deploy engine-a \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0 \
  --allow-unauthenticated

# Check logs
gcloud run services logs read engine-a --region=us-central1 --limit=100
```

### If CORS Errors
```bash
# Check current config
gcloud run services describe engine-a \
  --format="value(spec.template.spec.containers[0].env[?name==ENVIRONMENT])"

# Temporarily allow localhost (development mode)
gcloud run services update engine-a \
  --set-env-vars="ENVIRONMENT=development" \
  --region=us-central1
```

### If Credentials Won't Decrypt
```bash
# Check Engine C logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-c" \
  --filter="severity>=ERROR" --limit=50

# Verify ENCRYPTION_KEY exists
gcloud secrets versions list ENCRYPTION_KEY --project=galvanic-pulsar-482815-h0

# Test decryption locally
python tools/test_decryption.py
```

## Key Files & Locations

| File | Purpose |
|------|---------|
| `backend/shared/cors_config.py` | CORS configuration |
| `backend/engine-a/cloudbuild.yaml` | Engine A build config |
| `backend/engine-b/cloudbuild.yaml` | Engine B build config |
| `backend/engine-c/src/user_credentials.py` | Credential encryption/decryption |
| `frontend/web-app/next.config.ts` | Frontend Firebase config |
| `frontend/functions/lib/storeCredentials.js` | Cloud Functions encryption |

## Documentation

| Document | Purpose |
|----------|---------|
| `PRODUCTION_DEPLOYMENT_COMPLETE.md` | Full deployment report |
| `KMS_AND_ENCRYPTION_STATUS.md` | Security architecture |
| `COMPREHENSIVE_ANALYSIS_AND_FIXES.md` | System analysis |
| `KMS_CREDENTIAL_ENCRYPTION_SETUP.md` | KMS implementation guide |

## Git Workflow

```bash
# View deployment commits
git log --oneline --grep="Deploy\|Security" -n 10

# View recent changes
git log --stat -n 5

# Check branch status
git status
git branch -a
```

## Useful Links

- **GCP Console**: https://console.cloud.google.com
- **Firebase Console**: https://console.firebase.google.com/project/galvanic-pulsar-482815-h0
- **GitHub Repo**: https://github.com/raghu-1718/InfinityAI.Pro
- **Cloud Build Status**: https://console.cloud.google.com/cloud-build?project=galvanic-pulsar-482815-h0
- **Cloud Logging**: https://console.cloud.google.com/logs?project=galvanic-pulsar-482815-h0

## Contact & Support

**Issues/Escalation**:
- GitHub Issues: https://github.com/raghu-1718/InfinityAI.Pro/issues
- GCP Support: https://console.cloud.google.com/support
- Email: ops@infinityai.pro

**On-Call Runbook**: See PRODUCTION_DEPLOYMENT_COMPLETE.md → Emergency Procedures

---

**Last Updated**: January 19, 2026  
**Status**: 🟢 Production Ready  
**Next Review**: After 24-hour monitoring period
