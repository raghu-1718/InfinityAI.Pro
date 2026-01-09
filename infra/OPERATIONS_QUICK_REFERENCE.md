# InfinityAI.Pro - Operations Quick Reference
# Fast lookup for common tasks and troubleshooting

## 🚀 Quick Commands

### Check System Health
```bash
# All engines status
gcloud run services list --project=galvanic-pulsar-482815-h0

# Test Engine-A
curl https://engine-a-3acobgd3qa-uc.a.run.app/health

# Test Engine-B
curl https://engine-b-3acobgd3qa-uc.a.run.app/health

# Test Engine-C
curl https://engine-c-3acobgd3qa-uc.a.run.app/health
```

### View Recent Errors
```bash
# Last 50 Cloud Function errors
gcloud functions log read --limit 50 --project=galvanic-pulsar-482815-h0

# Engine-A logs (last 20 lines)
gcloud run services logs read engine-a --project=galvanic-pulsar-482815-h0 --limit 20

# Engine-B logs
gcloud run services logs read engine-b --project=galvanic-pulsar-482815-h0 --limit 20

# Engine-C logs
gcloud run services logs read engine-c --project=galvanic-pulsar-482815-h0 --limit 20
```

### Check Firestore
```bash
# List collections
gcloud firestore collections list --project=galvanic-pulsar-482815-h0

# Count documents in trading_sessions
gcloud firestore documents list --project=galvanic-pulsar-482815-h0 --collection-path=trading_sessions --limit=1000 | wc -l

# Search user sessions
gcloud firestore documents list --project=galvanic-pulsar-482815-h0 --collection-path=user_sessions --filter="userId:znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
```

### Redeploy Services
```bash
# Redeploy engine-a
gcloud run deploy engine-a --project=galvanic-pulsar-482815-h0 --min-instances=1

# Redeploy all Cloud Functions
firebase deploy --only functions --project=galvanic-pulsar-482815-h0

# Redeploy frontend
firebase deploy --only hosting --project=galvanic-pulsar-482815-h0
```

---

## 🆘 Troubleshooting

### Problem: "fetchAccountData is not defined"
**Solution:**
1. Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Clear cache: DevTools → Application → Clear Storage
3. Verify: [frontend/web-app/src/hooks/useUserData.ts](../frontend/web-app/src/hooks/useUserData.ts) calls `fetchAccountDataMethod()`

### Problem: Engine returns HTTP 500
**Diagnosis:**
```bash
# Check logs
gcloud run services logs read engine-a --project=galvanic-pulsar-482815-h0 --limit 50

# Check memory/CPU
gcloud run operations list --project=galvanic-pulsar-482815-h0 --filter="engine-a"

# Check quota
gcloud compute project-info describe --project=galvanic-pulsar-482815-h0
```

**Fixes:**
1. Increase memory: `gcloud run deploy engine-a --memory=1Gi`
2. Restart: `gcloud run services update engine-a --min-instances=0` then `--min-instances=1`
3. Check network: `gcloud run services describe engine-a` (verify public invoker enabled)

### Problem: Firestore Quota Exceeded
**Solution:**
1. Check quota: `gcloud compute project-info describe --project=galvanic-pulsar-482815-h0`
2. Reduce operations: Implement client-side caching
3. Upgrade: Switch to on-demand pricing (if available)

### Problem: Dhan API Connection Failed
**Diagnosis:**
```bash
# Check credentials
gcloud secrets versions list dhan-access-token --project=galvanic-pulsar-482815-h0

# Check Dhan API status (external)
curl https://api.dhan.co/health
```

**Fixes:**
1. Refresh access token: Re-authenticate in Settings
2. Check network: Verify egress firewall rules
3. Check Dhan status: https://status.dhan.co

### Problem: Cloud Functions Cold Start Slow
**Solution:**
- Min instances already enabled (should be instant)
- If still slow, increase memory: `firebase functions:config:set run.memory=1GB`
- Pre-warm: Call function periodically to keep warm

---

## 📊 Performance Baseline

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Engine-A health | <500ms | 386ms | ✅ GOOD |
| Engine-B signal | <1000ms | 935ms | ✅ GOOD |
| Engine-C status | <500ms | 873ms | ⚠️ ACCEPTABLE |
| Firestore query | <100ms | <50ms | ✅ EXCELLENT |
| Dhan API call | <500ms | 400-900ms | ⚠️ VARIABLE (external) |
| Cold start (min instances) | ~0ms | ~50ms | ✅ EXCELLENT |

---

## 🔐 Security Reminders

- **Never** commit `.env` files or credentials to git
- **Always** use Secret Manager for sensitive data
- **Verify** IAM policies before deploying
- **Rotate** Dhan access tokens monthly
- **Review** Firestore rules quarterly
- **Monitor** audit logs for suspicious activity

---

## 📞 Emergency Contacts

| Issue | Contact | Response Time |
|-------|---------|----------------|
| System down | raghuyuvi10@gmail.com | Immediate |
| Dhan API down | Dhan Support: support@dhan.co | 2-4 hours |
| GCP service down | GCP Status: https://status.cloud.google.com | Real-time |

---

## 📝 Important Files

| File | Purpose |
|------|---------|
| [VERIFICATION_REPORT_COMPREHENSIVE.md](../VERIFICATION_REPORT_COMPREHENSIVE.md) | Full system audit |
| [MONITORING_ALERTS_GUIDE.md](MONITORING_ALERTS_GUIDE.md) | Alert policy templates |
| [INFRASTRUCTURE_DEPLOYMENT_REPORT.md](INFRASTRUCTURE_DEPLOYMENT_REPORT.md) | Current deployment status |
| [firebase.json](../firebase.json) | Firebase hosting config |
| [firestore.indexes.json](../firestore.indexes.json) | Composite indexes |
| [infra/firebase/firestore.rules](firebase/firestore.rules) | Firestore security rules |

---

## ⚡ Cost Tracking

**Monthly Baseline (Development):**
- Cloud Run (3 engines, min instances): $37.50
- Cloud Functions (12 functions): $20-50
- Firestore: $10-30
- Other: $5-10
- **Total: ~$100/month**

**Monitor Cost:**
```bash
gcloud billing accounts list
gcloud billing budgets list
```

---

## 🔄 Deployment Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Review logs | Daily | On-call engineer |
| Check alerts | Daily | On-call engineer |
| Security audit | Monthly | Platform engineer |
| Cost review | Monthly | Finance |
| Performance review | Quarterly | Architecture |
| Disaster recovery drill | Quarterly | DevOps |

---

## 📌 Quick Links

- **Frontend:** https://galvanic-pulsar-482815-h0.web.app
- **Cloud Console:** https://console.cloud.google.com/run?project=galvanic-pulsar-482815-h0
- **Firestore:** https://console.firebase.google.com/project/galvanic-pulsar-482815-h0/firestore
- **Monitoring:** https://console.cloud.google.com/monitoring/dashboards?project=galvanic-pulsar-482815-h0
- **Alerts:** https://console.cloud.google.com/monitoring/alerting/policies?project=galvanic-pulsar-482815-h0

---

**Last Updated:** 2026-01-09
**Version:** 1.0
**Status:** Production Ready
