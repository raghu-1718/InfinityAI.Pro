# InfinityAI.Pro - Remediation Plan

**Generated:** December 2, 2025
**Mode:** DRY-RUN
**Priority Scale:** P1 (Critical) → P4 (Low)

---

## 🔴 P1 - Critical (None Identified)

No critical issues found. All production services are healthy and responding.

---

## 🟠 P2 - High Priority

### 1. Add Security Headers to FastAPI Applications

**Status:** ⚠️ Missing
**Impact:** Security vulnerability - potential clickjacking, XSS, MIME sniffing attacks
**Effort:** Low (1-2 hours)

**Implementation:**

Add security middleware to each engine's `main.py`:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

**Files to Update:**
- `backend/engine-a/src/main.py`
- `backend/engine-b/src/main.py`
- `backend/engine-c/src/main.py`

**Verification:**
```bash
curl -I https://engine-a-573866363639.us-central1.run.app/health | grep -E "Strict|X-Frame|X-Content|Content-Security"
```

---

## 🟡 P3 - Medium Priority

### 2. Clean Up Old Container Images

**Status:** ⚠️ 55+ images to delete
**Impact:** Storage costs, registry clutter
**Effort:** Low (automated with --approve)

**Commands (DRY-RUN first, then with --approve):**

```powershell
# List deletion candidates
gcloud container images list-tags us-central1-docker.pkg.dev/after-yesterday-473512-k3/infinityai/engine-a `
  --filter="timestamp.datetime < '2025-12-01'" --format="table(digest,tags,timestamp)"

# Delete old engine-a images (keep 3 most recent)
gcloud container images delete us-central1-docker.pkg.dev/after-yesterday-473512-k3/infinityai/engine-a@sha256:DIGEST --quiet

# Delete ALL legacy engine-core images
gcloud container images list-tags us-central1-docker.pkg.dev/after-yesterday-473512-k3/infinityai/engine-core --format="value(digest)" | ForEach-Object {
    gcloud container images delete "us-central1-docker.pkg.dev/after-yesterday-473512-k3/infinityai/engine-core@sha256:$_" --quiet
}
```

**Retention Policy:**
- Keep images tagged `latest`
- Keep images deployed to active Cloud Run revisions
- Keep 3 most recent images per service
- Delete images older than 30 days

---

### 3. Remove Demo Mode from Live Signal Endpoint

**Status:** ⚠️ Demo fallback exists
**Impact:** Low - not the primary signal endpoint
**Effort:** Medium (requires testing)

**Location:** `backend/engine-a/src/signal_api.py` (lines 320-355)

**Recommendation:**
Replace demo data with call to Engine B's `/api/v1/signal` endpoint:

```python
@app.get("/api/live-signal/{symbol}")
async def get_live_signal(symbol: str, strategy: str = Query("momentum")):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://engine-b-573866363639.us-central1.run.app/api/v1/signal",
                json={"symbol": symbol, "timeframe": "1h"}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Signal fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Signal generation failed")
```

---

### 4. Clean Up Cloud Run Revisions

**Status:** ⚠️ 66 old revisions
**Impact:** UI clutter, no cost impact
**Effort:** Low (optional)

**Note:** Cloud Run automatically manages revision garbage collection. Manual cleanup is optional.

```powershell
# List old revisions (informational)
gcloud run revisions list --service=engine-a --region=us-central1 --filter="status.conditions.status!=True"

# Delete specific old revision (if needed)
gcloud run revisions delete engine-a-00001-xxx --region=us-central1 --quiet
```

---

## 🟢 P4 - Low Priority

### 5. Document Empty GCS Buckets

**Status:** ℹ️ 2 empty buckets
**Impact:** None (no storage cost for empty buckets)

**Buckets:**
- `after-yesterday-473512-k3-ml-models` - Intended for ML model storage
- `after-yesterday-473512-k3-trading-history` - Intended for trade logs

**Action:** Add documentation explaining intended use or remove if not needed.

---

### 6. Clean Up Local Docker Images

**Status:** ℹ️ 30+ local images
**Impact:** Local disk space only

```powershell
# Remove old gcr.io images (no longer used)
docker images "gcr.io/after-yesterday-473512-k3/*" --format "{{.Repository}}:{{.Tag}}" | ForEach-Object { docker rmi $_ }

# Prune images older than 7 days
docker image prune -a --filter "until=168h" --force
```

---

### 7. Add Version Tags to Git

**Status:** ℹ️ No tags present
**Impact:** Release tracking

```bash
git tag -a v3.7.0 -m "Version 3.7.0 - Google integrations complete"
git push origin v3.7.0
```

---

## 📊 Summary by Priority

| Priority | Issues | Status |
|----------|--------|--------|
| P1 Critical | 0 | ✅ None |
| P2 High | 1 | ⚠️ Security headers |
| P3 Medium | 3 | ⚠️ Cleanup tasks |
| P4 Low | 3 | ℹ️ Nice to have |

---

## 🔧 Quick Win Commands

```powershell
# 1. Verify current state
curl -s https://engine-a-573866363639.us-central1.run.app/health
curl -s https://engine-b-573866363639.us-central1.run.app/health
curl -s https://engine-c-573866363639.us-central1.run.app/health

# 2. Check registry image count
gcloud container images list-tags us-central1-docker.pkg.dev/after-yesterday-473512-k3/infinityai/engine-a --format="value(digest)" | Measure-Object

# 3. View active revisions
gcloud run services describe engine-a --region=us-central1 --format="value(status.latestReadyRevisionName)"
gcloud run services describe engine-b --region=us-central1 --format="value(status.latestReadyRevisionName)"
gcloud run services describe engine-c --region=us-central1 --format="value(status.latestReadyRevisionName)"
```

---

## ✅ Rollback Plan

If any cleanup causes issues:

1. **Registry Images:** Manifests saved in `artifacts/registry_manifests/`
2. **Cloud Run:** Previous revisions still available, switch traffic:
   ```
   gcloud run services update-traffic engine-a --to-revisions=engine-a-00020-bvj=100 --region=us-central1
   ```
3. **Git:** Revert to previous commit:
   ```
   git revert 62d37929
   ```

---

*This remediation plan was generated in DRY-RUN mode.*
*Run with `--approve` to execute cleanup operations.*
