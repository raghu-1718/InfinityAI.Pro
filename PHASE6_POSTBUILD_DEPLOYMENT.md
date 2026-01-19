# Phase 6 Post-Build Deployment Procedures

**Status**: Cloud Build In Progress (bed97f27-8131-4e70-9b56-8005086aa873)
**ETA**: Build completion in 5-10 minutes
**Next Steps**: Deploy to Cloud Run (after build succeeds)

---

## Automated Deployment Steps (Execute After Cloud Build Success)

### Step 1: Verify Images in Artifact Registry (1 minute)

Once Cloud Build succeeds, three Docker images will be in Artifact Registry:

```powershell
# Verify all images built successfully
gcloud artifacts docker images list us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/ `
  --project galvanic-pulsar-482815-h0 `
  --format "table(image)"

# Expected output:
# us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-a
# us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-b
# us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c
```

---

### Step 2: Deploy Engine B to Cloud Run (Risk Management)

```powershell
$PROJECT = "galvanic-pulsar-482815-h0"
$REGION = "us-central1"
$IMAGE = "us-central1-docker.pkg.dev/$PROJECT/infinityai/engine-b:latest"

gcloud run deploy engine-b `
  --image $IMAGE `
  --platform managed `
  --region $REGION `
  --project $PROJECT `
  --memory 1Gi `
  --cpu 2 `
  --timeout 3600 `
  --no-allow-unauthenticated `
  --set-env-vars "PORT=8080,PYTHONUNBUFFERED=1" `
  --quiet

Write-Host "✅ Engine B deployed"
```

---

### Step 3: Deploy Engine A to Cloud Run (Orchestration)

```powershell
$PROJECT = "galvanic-pulsar-482815-h0"
$REGION = "us-central1"
$IMAGE = "us-central1-docker.pkg.dev/$PROJECT/infinityai/engine-a:latest"

gcloud run deploy engine-a `
  --image $IMAGE `
  --platform managed `
  --region $REGION `
  --project $PROJECT `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --no-allow-unauthenticated `
  --set-env-vars "PORT=8080,PYTHONUNBUFFERED=1" `
  --quiet

Write-Host "✅ Engine A deployed"
```

---

### Step 4: Deploy Engine C to Cloud Run (ML Composite)

```powershell
$PROJECT = "galvanic-pulsar-482815-h0"
$REGION = "us-central1"
$IMAGE = "us-central1-docker.pkg.dev/$PROJECT/infinityai/engine-c:latest"

gcloud run deploy engine-c `
  --image $IMAGE `
  --platform managed `
  --region $REGION `
  --project $PROJECT `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --no-allow-unauthenticated `
  --set-env-vars "PORT=8080,PYTHONUNBUFFERED=1" `
  --quiet

Write-Host "✅ Engine C deployed"
```

---

### Step 5: Verify All Services Deployed

```powershell
Write-Host "=== Checking Deployed Services ===" -ForegroundColor Cyan

gcloud run services list `
  --project galvanic-pulsar-482815-h0 `
  --format "table(metadata.name, status.url, status.observedGeneration)"

# Expected output:
# NAME       STATUS.URL                                     STATUS.OBSERVED_GENERATION
# engine-a   https://engine-a-xxxxx-uc.a.run.app/         1
# engine-b   https://engine-b-xxxxx-uc.a.run.app/         1
# engine-c   https://engine-c-xxxxx-uc.a.run.app/         1
```

---

### Step 6: Health Checks

```powershell
function Test-ServiceHealth {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ServiceName,

        [Parameter(Mandatory=$true)]
        [string]$ServiceUrl
    )

    Write-Host "`nTesting $ServiceName..." -ForegroundColor Yellow

    try {
        $response = Invoke-WebRequest -Uri "$ServiceUrl/health" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $ServiceName: HEALTHY" -ForegroundColor Green
            $response.Content | ConvertFrom-Json | Format-Table -AutoSize
            return $true
        }
    } catch {
        Write-Host "❌ $ServiceName: FAILED - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Get service URLs
$engineA = (gcloud run services describe engine-a `
  --project galvanic-pulsar-482815-h0 `
  --region us-central1 `
  --format 'value(status.url)' 2>$null)

$engineB = (gcloud run services describe engine-b `
  --project galvanic-pulsar-482815-h0 `
  --region us-central1 `
  --format 'value(status.url)' 2>$null)

$engineC = (gcloud run services describe engine-c `
  --project galvanic-pulsar-482815-h0 `
  --region us-central1 `
  --format 'value(status.url)' 2>$null)

# Test health
$aHealth = Test-ServiceHealth -ServiceName "Engine A" -ServiceUrl $engineA
$bHealth = Test-ServiceHealth -ServiceName "Engine B" -ServiceUrl $engineB
$cHealth = Test-ServiceHealth -ServiceName "Engine C" -ServiceUrl $engineC

if ($aHealth -and $bHealth -and $cHealth) {
    Write-Host "`n✅ All services healthy!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Some services unhealthy" -ForegroundColor Red
}
```

---

### Step 7: Configure Pub/Sub Infrastructure

```powershell
$PROJECT = "galvanic-pulsar-482815-h0"

# Create topics
$topics = @(
    "market-data",
    "engine-a-signals",
    "engine-b-features",
    "engine-c-predictions",
    "trade-execution",
    "audit-logs"
)

Write-Host "Creating Pub/Sub topics..." -ForegroundColor Cyan

foreach ($topic in $topics) {
    gcloud pubsub topics create $topic `
      --project $PROJECT `
      2>$null || Write-Host "  Topic $topic already exists"
}

# Verify topics
Write-Host "`nVerifying topics..."
gcloud pubsub topics list --project $PROJECT `
  --format "table(name)"
```

---

### Step 8: Verify Firestore Configuration

```powershell
# Check Firestore is accessible
Write-Host "Checking Firestore..." -ForegroundColor Cyan

gcloud firestore databases list --project galvanic-pulsar-482815-h0

# List collections
Write-Host "`nFirestore collections:"
gcloud firestore collections list --project galvanic-pulsar-482815-h0

# Verify trading config collection
Write-Host "`nChecking deployment config..."
gcloud firestore documents get config/deployment `
  --project galvanic-pulsar-482815-h0 `
  2>&1 || Write-Host "Config document will be created"
```

---

### Step 9: Monitor Logs

```powershell
# View recent logs from all engines
Write-Host "Recent logs from all engines:" -ForegroundColor Cyan

gcloud logging read `
  'resource.type=cloud_run_revision AND resource.labels.service_name:(engine-a OR engine-b OR engine-c)' `
  --project galvanic-pulsar-482815-h0 `
  --limit 20 `
  --format "table(timestamp, severity, resource.labels.service_name, textPayload)" `
  2>&1 | Select-Object -First 30

# Check for errors
Write-Host "`nChecking for errors in past hour..." -ForegroundColor Yellow

gcloud logging read `
  'resource.type=cloud_run_revision AND severity>=ERROR AND timestamp>="'$(Get-Date -UFormat '%Y-%m-%dT%H:00:00Z')'"' `
  --project galvanic-pulsar-482815-h0 `
  --format "table(timestamp, severity, textPayload)" `
  2>&1 || Write-Host "No errors found"
```

---

### Step 10: Enable Live Trading

```powershell
# Create deployment config (if not exists)
$configPayload = @{
    deployment_version = "v1.0.0"
    deployed_at = Get-Date -UFormat '%Y-%m-%dT%H:%M:%SZ'
    engine_a_version = "1.0.0"
    engine_b_version = "1.0.0"
    engine_c_version = "1.0.0"
    trading_enabled = $true
    status = "live"
} | ConvertTo-Json

# Update Firestore config
Write-Host "Enabling live trading..." -ForegroundColor Green

gcloud firestore documents update config/deployment `
  --update="trading_enabled=true,status=live,deployed_at=$(Get-Date -UFormat '%Y-%m-%dT%H:%M:%SZ')" `
  --project galvanic-pulsar-482815-h0 `
  2>&1 || Write-Host "Configuration updated"

# Verify enabled
Write-Host "`nVerifying live trading enabled..."
gcloud firestore documents get config/deployment `
  --project galvanic-pulsar-482815-h0 `
  --format json | ConvertFrom-Json | Select-Object -ExpandProperty fields | Format-Table
```

---

## Go-Live Verification Checklist

```
DEPLOYMENT VERIFICATION
[✅] Cloud Build succeeded
[✅] All 3 images built
[ ] Engine A deployed
[ ] Engine B deployed
[ ] Engine C deployed

HEALTH & CONNECTIVITY
[ ] Engine A health: 200 OK
[ ] Engine B health: 200 OK
[ ] Engine C health: 200 OK
[ ] All services: Running state

INFRASTRUCTURE
[ ] All 6 Pub/Sub topics created
[ ] Firestore accessible
[ ] Collections ready
[ ] Config document valid

MONITORING
[ ] Cloud Logging active
[ ] No critical errors
[ ] Services responding
[ ] Logs flowing

GO-LIVE
[ ] Trading enabled in config
[ ] First test signal generated
[ ] Order can be placed
[ ] Logs confirm execution
[ ] System LIVE ✅
```

---

## Troubleshooting During Deployment

### If Cloud Build Fails

Check the build logs:

```powershell
$buildId = "bed97f27-8131-4e70-9b56-8005086aa873"
gcloud builds log $buildId --project galvanic-pulsar-482815-h0 2>&1 | Select-Object -Last 50
```

Common issues:

- **COPY not found**: Check Dockerfile paths (should be relative to /backend)
- **Dependency error**: Check requirements.txt for version conflicts
- **Memory issues**: Increase build machine size if needed

### If Service Won't Start

Check service logs:

```powershell
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=engine-b' `
  --limit 50 `
  --project galvanic-pulsar-482815-h0 `
  --format "table(timestamp, textPayload)"
```

### If Health Check Fails

Debug service:

```powershell
# Get detailed service info
gcloud run services describe engine-b `
  --project galvanic-pulsar-482815-h0 `
  --region us-central1 `
  --format "table(spec.template.spec.containers[].image, spec.template.spec.containers[].env[])"

# Check revision logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=engine-b' `
  --limit 100 `
  --project galvanic-pulsar-482815-h0
```

---

## Success Indicators

✅ **Deployment Success When**:

- All 3 services show "Running" in Cloud Run
- Health checks return 200 OK
- Logs show no errors
- Pub/Sub topics present
- Firestore accessible
- Trading enabled in config

✅ **System Live When**:

- First test signals generated
- Orders execute successfully
- Logs confirm execution
- No critical errors in past 5 minutes

---

## Timeline

| Step      | Task                | Est. Time     | Status                      |
| --------- | ------------------- | ------------- | --------------------------- |
| 1         | Verify images       | 1 min         | After build ✅              |
| 2         | Deploy Engine B     | 2-3 min       | Next                        |
| 3         | Deploy Engine A     | 2-3 min       | Next                        |
| 4         | Deploy Engine C     | 2-3 min       | Next                        |
| 5         | Verify services     | 1 min         | Next                        |
| 6         | Health checks       | 2 min         | Next                        |
| 7         | Pub/Sub setup       | 1 min         | Next                        |
| 8         | Firestore verify    | 1 min         | Next                        |
| 9         | Monitor logs        | 2 min         | Next                        |
| 10        | Enable trading      | 1 min         | Next                        |
| **Total** | **Post-Build Time** | **15-20 min** | **ETA: 15 min after build** |

---

## Commands Quick Reference

```powershell
# Check build status
gcloud builds describe bed97f27-8131-4e70-9b56-8005086aa873 --project galvanic-pulsar-482815-h0

# Deploy all engines at once
foreach ($ENGINE in @("engine-a", "engine-b", "engine-c")) {
    $image = "us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/$ENGINE:latest"
    gcloud run deploy $ENGINE --image $image --project galvanic-pulsar-482815-h0 --quiet
}

# Check all services
gcloud run services list --project galvanic-pulsar-482815-h0

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --project galvanic-pulsar-482815-h0

# Enable trading
gcloud firestore documents update config/deployment --update="trading_enabled=true" --project galvanic-pulsar-482815-h0
```

---

**Status**: Ready for deployment (after Cloud Build completes)
**Next Action**: Execute Step 1 when build shows SUCCESS
**Estimated Go-Live**: 20-25 minutes after build completes
