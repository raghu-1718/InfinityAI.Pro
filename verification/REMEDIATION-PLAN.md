# InfinityAI.Pro - Remediation Plan

## Priority Matrix

| Priority | Count | Severity | Action Required |
|----------|-------|----------|-----------------|
| P1 - Critical | 0 | Blocking | Immediate |
| P2 - High | 2 | Performance Impact | Within 24 hours |
| P3 - Medium | 2 | Optimization | Within 1 week |
| P4 - Low | 0 | Cosmetic | As time permits |

---

## P2 - High Priority (Within 24 hours)

### PERF-001: Cloud Run Cold Start Latency

**Issue**: All engines show latency >300ms threshold (avg ~780ms) due to cold starts

**Impact**: Poor user experience during initial requests, potential timeout issues

**Root Cause**: `min-instances=0` configuration on all Cloud Run services

**Remediation Steps**:

```powershell
# Set min-instances for each engine
gcloud run services update engine-a --min-instances=1 --region=us-central1
gcloud run services update engine-b --min-instances=1 --region=us-central1
gcloud run services update engine-c --min-instances=1 --region=us-central1
```

**Cost Impact**: ~$25-50/month per service for always-on instance

**Verification**:
```powershell
# Test latency after update
1..5 | ForEach-Object {
  $start = Get-Date
  Invoke-RestMethod "https://engine-b-429140669077.us-central1.run.app/health"
  ((Get-Date) - $start).TotalMilliseconds
}
# Expected: <200ms after warm-up
```

---

### BACKUP-001: Firestore Point-in-Time Recovery Disabled

**Issue**: No point-in-time recovery enabled for Firestore database

**Impact**: Data loss risk if accidental deletion or corruption occurs

**Root Cause**: Feature not enabled during database creation

**Remediation Steps**:

```powershell
# Enable PITR for Firestore
gcloud firestore databases update --database="(default)" \
  --project=gen-lang-client-0779271931 \
  --enable-pitr
```

**Cost Impact**: Additional storage costs for recovery points

**Verification**:
```powershell
gcloud firestore databases describe --database="(default)" \
  --project=gen-lang-client-0779271931 \
  --format="value(pointInTimeRecoveryEnablement)"
# Expected: POINT_IN_TIME_RECOVERY_ENABLED
```

---

## P3 - Medium Priority (Within 1 week)

### DNS-001: API Gateway Domain Not Configured

**Issue**: `api.infinityai.pro` domain returns "No such host"

**Impact**: API gateway functionality not accessible via custom domain

**Root Cause**: CNAME record not configured in DNS

**Remediation Steps**:

1. Go to Namecheap DNS settings for infinityai.pro
2. Add CNAME record:
   - Host: `api`
   - Value: `ghs.googlehosted.com.`
   - TTL: 300

3. Verify Cloud Run domain mapping:
```powershell
gcloud run domain-mappings list --region=us-central1
```

4. If not mapped, create mapping:
```powershell
gcloud run domain-mappings create --service=engine-a \
  --domain=api.infinityai.pro --region=us-central1
```

**Verification**:
```powershell
nslookup api.infinityai.pro
# Expected: Should resolve to Google IPs
```

---

### CODE-001: Demo Mode Fallback Code

**Issue**: 12 files contain "demo" pattern, 4 contain "placeholder"

**Impact**: Potential for demo data to be served if live feeds fail

**Root Cause**: Fallback mechanisms for when market data unavailable

**Files to Review**:
```
backend/engine-core/src/signal_api.py:348 - demo_mode flag
backend/engine-core/src/signal_api.py:353 - demo response note
```

**Remediation Steps**:

1. Audit all demo mode code paths
2. Ensure demo mode is explicitly disabled in production:

```python
# In config or environment
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# In code
if DEMO_MODE:
    logger.warning("Demo mode active - should not be in production")
```

3. Add production-only validation:
```python
if os.getenv("ENVIRONMENT") == "production" and DEMO_MODE:
    raise RuntimeError("Demo mode not allowed in production")
```

**Verification**:
```powershell
# Search for demo mode in production responses
$resp = Invoke-RestMethod "https://engine-b.../api/v1/signal" -Method POST -Body '{"symbol":"RELIANCE"}' -ContentType "application/json"
$resp | ConvertTo-Json | Select-String "demo"
# Expected: No matches
```

---

## Verification Checklist

After implementing remediations, run these verification tests:

### Performance Verification
```powershell
# Test cold start elimination
for ($i=0; $i -lt 10; $i++) {
    $start = Get-Date
    Invoke-RestMethod "https://engine-b-429140669077.us-central1.run.app/health" -TimeoutSec 10
    $latency = ((Get-Date) - $start).TotalMilliseconds
    Write-Host "Request $i`: $([math]::Round($latency))ms"
}
```

### Backup Verification
```powershell
gcloud firestore databases describe --database="(default)" \
  --format="yaml(pointInTimeRecoveryEnablement,earliestVersionTime)"
```

### DNS Verification
```powershell
Resolve-DnsName api.infinityai.pro
curl -I https://api.infinityai.pro/health
```

### Demo Mode Verification
```powershell
# Ensure no demo responses in production
Get-ChildItem -Path "backend" -Recurse -Include "*.py" |
  Select-String -Pattern 'demo_mode.*=.*True' |
  ForEach-Object { Write-Host "[FAIL] $_" -ForegroundColor Red }
```

---

## Monitoring Alerts to Add

### 1. Cold Start Alert
```yaml
# Alert if p95 latency exceeds 500ms
condition:
  filter: resource.type="cloud_run_revision"
  threshold: 500ms
  duration: 5m
```

### 2. Demo Mode Alert
```yaml
# Alert if demo mode activated
condition:
  filter: textPayload=~"demo_mode"
  threshold: 1
```

### 3. Token Expiry Alert
```yaml
# Alert 7 days before Dhan token expires
condition:
  filter: textPayload=~"DH-901"
  threshold: 1
```

---

## Timeline

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Set min-instances=1 | DevOps | Dec 2, 2025 | ⏳ Pending |
| Enable Firestore PITR | DevOps | Dec 2, 2025 | ⏳ Pending |
| Configure api.infinityai.pro DNS | DevOps | Dec 5, 2025 | ⏳ Pending |
| Audit demo mode code | Dev | Dec 7, 2025 | ⏳ Pending |

---

*Generated: December 2, 2025*
*Next Review: December 9, 2025*
