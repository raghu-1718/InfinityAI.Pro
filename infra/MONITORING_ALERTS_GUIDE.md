# Cloud Monitoring Alerts - Manual Setup Guide
# Project: galvanic-pulsar-482815-h0
# Use this guide if you prefer manual alert setup via Cloud Console

## Quick Links
- **Cloud Console Alerts:** https://console.cloud.google.com/monitoring/alerting/policies?project=galvanic-pulsar-482815-h0
- **Cloud Monitoring Dashboard:** https://console.cloud.google.com/monitoring/dashboards?project=galvanic-pulsar-482815-h0
- **Cloud Run Services:** https://console.cloud.google.com/run?project=galvanic-pulsar-482815-h0
- **Firestore:** https://console.firebase.google.com/project/galvanic-pulsar-482815-h0/firestore

---

## Alert Policies to Create

### 1. Engine-A Health Check Failure (CRITICAL)
**Alert Name:** [CRITICAL] Engine-A Health Check Failed
**Condition:** Engine-A endpoint returns HTTP 5xx errors
**Duration:** 5 minutes
**Threshold:** Any errors (>0)
**Notification:** Email to raghuyuvi10@gmail.com
**Actions:**
1. Go to Cloud Console Alerts
2. Click "Create Policy"
3. Select "Metric" condition type
4. Resource type: `Cloud Run Revision`
5. Metric: `run.googleapis.com/request_count`
6. Filter: `resource.label.service_name = "engine-a"` AND `metric.response_code_class = "5xx"`
7. Condition: `ABOVE 0 for 5 minutes`
8. Add notification channel (email)
9. Save

**Escalation:** Page on-call engineer immediately

---

### 2. Engine-B Health Check Failure (CRITICAL)
**Alert Name:** [CRITICAL] Engine-B Health Check Failed
**Condition:** Engine-B (ML engine) endpoint returns errors
**Duration:** 5 minutes
**Threshold:** Any errors (>0)
**Notification:** Email + SMS (urgent)
**Actions:**
Same as Engine-A, but:
- Filter: `resource.label.service_name = "engine-b"` AND `metric.response_code_class = "5xx"`

**Escalation:** ML pipeline failure - trading signals not generated

---

### 3. Engine-C Health Check Failure (CRITICAL)
**Alert Name:** [CRITICAL] Engine-C Health Check Failed
**Condition:** Engine-C (trading engine) endpoint returns errors
**Duration:** 5 minutes
**Threshold:** Any errors (>0)
**Notification:** Email + SMS (urgent)
**Actions:**
Same as Engine-A, but:
- Filter: `resource.label.service_name = "engine-c"` AND `metric.response_code_class = "5xx"`

**Escalation:** Trading execution blocked - orders cannot be placed

---

### 4. High Latency Alert (WARNING)
**Alert Name:** [WARNING] Backend Latency > 1000ms
**Condition:** Engine response time exceeds 1 second
**Duration:** 5 minutes
**Threshold:** Latency > 1000ms
**Notification:** Email
**Actions:**
1. Alert type: Metric
2. Resource type: `Cloud Run Revision`
3. Metric: `run.googleapis.com/request_latencies`
4. Condition: `ABOVE 1000 for 5 minutes`
5. Actions: Check Cloud Run auto-scaling, review logs

---

### 5. Cloud Functions Error Rate (WARNING)
**Alert Name:** [WARNING] Cloud Functions Error Rate > 5%
**Condition:** More than 5% of function invocations fail
**Duration:** 10 minutes
**Threshold:** Error rate > 5%
**Notification:** Email
**Actions:**
1. Alert type: Metric
2. Resource type: `Cloud Function`
3. Metric: `cloudfunctions.googleapis.com/function/error_count`
4. Condition: `ABOVE 5% for 10 minutes`
5. Investigate: Check function logs for errors

---

### 6. Firestore Quota Exceeded (CRITICAL)
**Alert Name:** [CRITICAL] Firestore Quota Exceeded
**Condition:** Firestore operations hit quota limit
**Duration:** 1 minute
**Threshold:** Any
**Notification:** Email + SMS
**Actions:**
1. Alert type: Quota
2. Quota metric: `firestore.googleapis.com/quota/read_operations`
3. Condition: `ABOVE 80% for 1 minute`
4. Action: Scale Firestore or implement caching

---

### 7. Min Instances Cost Alert (INFO)
**Alert Name:** [INFO] Cloud Run Min Instances Running
**Condition:** Confirm min instances are provisioned
**Duration:** Continuous
**Threshold:** N/A
**Notification:** None (informational only)
**Purpose:** Document cost baseline ($20-30/month for min instances on 3 engines)

---

## Monitoring Dashboards

### Dashboard 1: System Health Overview
**Panels:**
- Engine-A: Health status + Latency trend
- Engine-B: Health status + ML inference time
- Engine-C: Health status + Dhan connection status
- Cloud Functions: Error rate + Invocation count
- Firestore: Read ops/sec + Write ops/sec

### Dashboard 2: Performance Metrics
**Panels:**
- Backend latency (p50, p95, p99)
- Cloud Run request count by service
- ML inference time histogram
- Dhan API response time
- WebSocket connection count

### Dashboard 3: Error Analysis
**Panels:**
- Error rate by service (5xx errors)
- Error log entries (searchable)
- Quota usage
- Rate limiting events

---

## Alert Severity Levels

### 🔴 CRITICAL (Red Alert)
- Immediate notification (email + SMS)
- Service is down or unavailable
- Trading execution blocked
- Examples: Engine-A/B/C down, Dhan connection lost, Firestore quota exceeded

### 🟡 WARNING (Yellow Alert)
- Email notification
- Performance degradation detected
- May affect user experience
- Examples: High latency (>1000ms), Error rate >5%, Low balance

### 🔵 INFO (Blue Alert)
- Informational only
- System event logged
- No action required
- Examples: Min instances provisioned, Scaling event, Backup completed

---

## Alert Response Playbook

### If Engine-A is Down
1. Check: `gcloud run services describe engine-a --project=galvanic-pulsar-482815-h0`
2. View logs: `gcloud run services logs read engine-a --project=galvanic-pulsar-482815-h0 --limit=50`
3. Check CPU/Memory: Cloud Run revision metrics in Console
4. Redeploy if needed: `gcloud run deploy engine-a ...`
5. Notify users via email/app notification

### If Engine-B is Slow (>1000ms)
1. Check: ML model loading time in logs
2. Check: Yahoo Finance API response time
3. Increase Cloud Run memory if CPU throttled
4. Enable caching for market data (Redis)

### If Engine-C Can't Reach Dhan
1. Check: Dhan API status (external)
2. Check: Credentials validity in Secret Manager
3. Check: Network egress (firewall rules)
4. Fallback: Use cached account data if available

### If Firestore Quota Exceeded
1. Check: Batch write sizes (should be ≤500 per batch)
2. Implement: Client-side caching (reduce reads)
3. Upgrade: Firestore to on-demand pricing (if available)
4. Archive: Old audit logs to BigQuery

---

## Cost Impact Analysis

### Min Instances (3 engines × $12.50/month each)
- **Current:** $37.50/month
- **Benefit:** Eliminates cold starts (400-1000ms latency reduction)
- **ROI:** Acceptable for production trading

### Monitoring & Logging
- **Cloud Monitoring:** Free tier (included)
- **Cloud Logging:** $0.50/GB ingested (low volume)
- **Alert notifications:** Free via email

### Estimated Monthly Cost (with min instances)
```
Cloud Run (3 engines min instances):  $37.50
Cloud Functions (12 functions):       $20-50
Firestore (storage + ops):            $10-30
Firebase Hosting:                     $0 (under 10GB)
Secret Manager:                       $1
Monitoring/Logging:                   $5-10
---
Total:                                $73-128/month
```

---

## Next Steps

1. **Create Notification Channel:**
   ```bash
   gcloud alpha monitoring channels create \
     --display-name="InfinityAI Email Alerts" \
     --type=email \
     --channel-labels=email_address=raghuyuvi10@gmail.com \
     --project=galvanic-pulsar-482815-h0
   ```

2. **List Existing Channels:**
   ```bash
   gcloud alpha monitoring channels list --project=galvanic-pulsar-482815-h0
   ```

3. **Create Policies:** Use Cloud Console at https://console.cloud.google.com/monitoring/alerting/policies?project=galvanic-pulsar-482815-h0

4. **Test Alerts:** Temporarily increase error threshold and verify notification delivery

5. **Document Escalation:** Add alert runbook to team wiki for on-call rotation

---

## Useful Commands

```bash
# List all alert policies
gcloud alpha monitoring policies list --project=galvanic-pulsar-482815-h0

# Describe specific policy
gcloud alpha monitoring policies describe POLICY_ID --project=galvanic-pulsar-482815-h0

# View recent alert incidents
gcloud alpha monitoring incidents list --project=galvanic-pulsar-482815-h0

# Check notification channels
gcloud alpha monitoring channels list --project=galvanic-pulsar-482815-h0

# View Cloud Run service metrics
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="engine-a"' \
  --project=galvanic-pulsar-482815-h0

# Check Firestore metrics
gcloud monitoring time-series list \
  --filter='resource.type="firestore_database"' \
  --project=galvanic-pulsar-482815-h0
```

---

**Last Updated:** 2026-01-09
**Next Review:** After first trading session or when cost optimization is needed
