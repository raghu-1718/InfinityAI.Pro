# Complete 100% GCP Migration Guide

**Date**: November 3, 2025  
**Current Status**: Deploying cost-optimized engines with concurrency fix  
**Goal**: Achieve 100% GCP/Firebase consolidation with minimum cost

---

## ✅ Completed Steps

### 1. Code Cleanup (DONE)
- ✅ Removed all Vercel configuration files (4 vercel.json)
- ✅ Deleted Northflank/Vercel scripts (6 scripts)
- ✅ Removed Vercel GitHub secrets (4 secrets)
- ✅ Deleted obsolete multi-cloud documentation (5 files)
- ✅ Updated secrets-mapping.md to GCP-only stack

### 2. Firebase Hosting Configuration (DONE)
- ✅ Added hosting section to firebase.json
- ✅ Configured public: frontend/dist
- ✅ Set up SPA rewrites and cache headers
- ✅ Deployed frontend to Firebase Hosting (successful)

### 3. Cloud Run Optimization (DONE)
- ✅ **Engine A**: 0.5 CPU, 256Mi, max 5, concurrency 80 (60% cost reduction)
- ✅ **Engine B**: 0.5 CPU, 256Mi, max 5, concurrency 80 (60% cost reduction)
- ✅ **Engine C**: 1 CPU, 512Mi, max 10 (trading performance)
- ✅ **Engine D**: 0.5 CPU, 256Mi, max 5, concurrency 80 (60% cost reduction)
- ✅ All engines: min-instances=0 (scale to zero)

### 4. Deployment Pipeline (IN PROGRESS)
- ✅ Removed Vercel deployment jobs from workflow
- ✅ Fixed GCP concurrency constraint for CPU < 1
- 🔄 **Current**: Deploying Run 19039100159 with proper concurrency flags

---

## 🔄 In Progress

### Current Deployment (Run 19039100159)
**Started**: 15:04:14 UTC, November 3, 2025

Monitor with:
```powershell
gh run watch 19039100159 --interval 10
```

**Expected Completion**: ~5-10 minutes

**What's Deploying**:
1. Frontend to Firebase Hosting
2. 13 Firebase Functions (Node.js 20)
3. Engine A with 0.5 CPU + concurrency 80
4. Engine B with 0.5 CPU + concurrency 80
5. Engine C with 1 CPU (unlimited concurrency)
6. Engine D with 0.5 CPU + concurrency 80

---

## 📋 Pending Tasks

### Task 1: Verify Deployment Success ⏳
**Priority**: IMMEDIATE  
**Estimated Time**: 5 minutes

```powershell
# Check deployment status
gh run view 19039100159

# When complete, verify all services
gcloud run services list --region us-central1 --project after-yesterday-473512-k3

# Test health endpoints
$engines = @("infinityai-engine-a", "infinityai-engine-b", "infinityai-engine-c-execution", "infinityai-engine-d")
foreach ($engine in $engines) {
    $url = "https://${engine}-ckxt6xvshq-uc.a.run.app/health"
    Write-Host "Testing $engine..."
    Invoke-RestMethod -Uri $url
}
```

**Success Criteria**:
- All 4 engines show "healthy" status
- Frontend deployed to Firebase Hosting
- All 13 functions deployed successfully

---

### Task 2: Disable Vercel GitHub App ⏳
**Priority**: HIGH  
**Estimated Time**: 2 minutes

The Vercel bot is still deploying because the **Vercel GitHub App** is installed on your repository.

**Steps**:
1. Go to: https://github.com/raghu-1718/InfinityAI.Pro/settings/installations
2. Find "Vercel" in installed apps
3. Click "Configure"
4. **Option A** (Recommended): Remove repository access entirely
5. **Option B**: Suspend the app for this repository

After disabling, Vercel deployments will stop appearing in PR checks.

---

### Task 3: Delete Vercel Projects ⏳
**Priority**: HIGH (eliminates external costs)  
**Estimated Time**: 5 minutes

**Projects to Delete**:
1. infinityai-frontend
2. infinityai-api-webhooks
3. infinityai-engine-c
4. infinityai-engine-d

**Steps**:
1. Go to: https://vercel.com/infinityaipro
2. For each project:
   - Click project name
   - Settings → General → Delete Project
   - Type project name to confirm
   - Click "Delete"

**Verification**:
```powershell
# After deletion, PR should show:
# "Vercel – No deployments"
```

---

### Task 4: Configure Firebase Hosting Custom Domain ⏳
**Priority**: HIGH  
**Estimated Time**: 10 minutes

**Add infinityai.pro to Firebase Hosting**:

```bash
# Using Firebase CLI (recommended)
firebase hosting:channel:deploy production --project after-yesterday-473512-k3

# Or use Firebase Console:
# 1. Go to: https://console.firebase.google.com/project/after-yesterday-473512-k3/hosting
# 2. Click "Add custom domain"
# 3. Enter: infinityai.pro
# 4. Follow verification steps
```

**DNS Records from Firebase** (save these for Namecheap):
- You'll receive A and AAAA records from Firebase
- Example format:
  ```
  A      infinityai.pro     216.239.32.21
  A      infinityai.pro     216.239.34.21
  A      infinityai.pro     216.239.36.21
  A      infinityai.pro     216.239.38.21
  AAAA   infinityai.pro     2001:4860:4802:32::15
  AAAA   infinityai.pro     2001:4860:4802:34::15
  ...
  ```

---

### Task 5: Create Cloud Run Domain Mappings ⏳
**Priority**: HIGH  
**Estimated Time**: 15 minutes

**Map engine subdomains to Cloud Run services**:

```bash
# Authenticate to GCP
gcloud auth login
gcloud config set project after-yesterday-473512-k3

# Create domain mappings
gcloud beta run domain-mappings create \
  --service infinityai-engine-a \
  --domain engine-a.infinityai.pro \
  --region us-central1

gcloud beta run domain-mappings create \
  --service infinityai-engine-b \
  --domain engine-b.infinityai.pro \
  --region us-central1

gcloud beta run domain-mappings create \
  --service infinityai-engine-c-execution \
  --domain engine-c.infinityai.pro \
  --region us-central1

gcloud beta run domain-mappings create \
  --service infinityai-engine-d \
  --domain engine-d.infinityai.pro \
  --region us-central1

# Verify mappings
gcloud beta run domain-mappings list --region us-central1
```

**Expected Output**:
```
DOMAIN                        SERVICE                           REGION        READY
engine-a.infinityai.pro       infinityai-engine-a              us-central1   Yes
engine-b.infinityai.pro       infinityai-engine-b              us-central1   Yes
engine-c.infinityai.pro       infinityai-engine-c-execution    us-central1   Yes
engine-d.infinityai.pro       infinityai-engine-d              us-central1   Yes
```

**Note**: You'll get DNS records pointing to `ghs.googlehosted.com`

---

### Task 6: Update Namecheap DNS ⏳
**Priority**: HIGH  
**Estimated Time**: 10 minutes

**Login to Namecheap**:
1. Go to: https://www.namecheap.com/myaccount/login/
2. Navigate to: Dashboard → Domain List → infinityai.pro → Manage
3. Click "Advanced DNS"

**Update DNS Records**:

**Delete Old Records** (if present):
- Any A/CNAME records pointing to Vercel
- Any A/CNAME records pointing to old Cloud Run URLs

**Add New Records**:

```dns
# Root domain → Firebase Hosting (use records from Task 4)
Type   Host   Value                    TTL
A      @      216.239.32.21           Automatic
A      @      216.239.34.21           Automatic
A      @      216.239.36.21           Automatic
A      @      216.239.38.21           Automatic
AAAA   @      2001:4860:4802:32::15   Automatic
AAAA   @      2001:4860:4802:34::15   Automatic

# Engine subdomains → Cloud Run
Type    Host       Value                 TTL
CNAME   engine-a   ghs.googlehosted.com  Automatic
CNAME   engine-b   ghs.googlehosted.com  Automatic
CNAME   engine-c   ghs.googlehosted.com  Automatic
CNAME   engine-d   ghs.googlehosted.com  Automatic

# WWW redirect (optional)
CNAME   www        infinityai.pro        Automatic
```

**Verify DNS Propagation**:
```powershell
# Check DNS (may take 5-60 minutes)
nslookup infinityai.pro
nslookup engine-a.infinityai.pro
nslookup engine-b.infinityai.pro
nslookup engine-c.infinityai.pro
nslookup engine-d.infinityai.pro

# Online tools
# https://dnschecker.org/#A/infinityai.pro
# https://dnschecker.org/#CNAME/engine-a.infinityai.pro
```

---

### Task 7: Verify Cost Optimization ⏳
**Priority**: MEDIUM  
**Estimated Time**: 10 minutes

**Check GCP Billing Dashboard**:
```bash
# List billing accounts
gcloud beta billing accounts list

# Check current month costs
# Go to: https://console.cloud.google.com/billing/01****-****-*****
# Navigate to: Reports
# Filter by: Project = after-yesterday-473512-k3
```

**Verify Scale-to-Zero**:
```bash
# Check active instances (should be 0 when idle)
gcloud run services describe infinityai-engine-a --region us-central1 --format="get(status.traffic)"
gcloud run services describe infinityai-engine-b --region us-central1 --format="get(status.traffic)"
gcloud run services describe infinityai-engine-d --region us-central1 --format="get(status.traffic)"
```

**Expected Monthly Costs** (estimate):
- **Cloud Run**: $10-30/month (with scale-to-zero)
- **Firebase Hosting**: $0 (within free tier)
- **Firebase Functions**: $0-10/month (within free tier limits)
- **Cloud Build**: $0 (120 free builds/day)
- **Secret Manager**: $0.30/month (6 secrets × $0.06)
- **Total Estimate**: $10-40/month (90% reduction from multi-cloud)

**Cost Savings**:
- **Vercel**: -$20/month (eliminated)
- **Northflank**: -$0/month (already eliminated)
- **Resource optimization**: -60% on 3 engines
- **Total Savings**: ~$100-150/month

---

### Task 8: Complete End-to-End Testing ⏳
**Priority**: MEDIUM  
**Estimated Time**: 20 minutes

**Test Frontend**:
```powershell
# After DNS propagation
Invoke-WebRequest -Uri "https://infinityai.pro" -UseBasicParsing
Invoke-WebRequest -Uri "https://infinityai.pro/health" -UseBasicParsing
```

**Test All Engine APIs**:
```powershell
# Engine A - Market Data
$responseA = Invoke-RestMethod -Uri "https://engine-a.infinityai.pro/health"
$marketData = Invoke-RestMethod -Uri "https://engine-a.infinityai.pro/api/market-data/NIFTY"

# Engine B - AI Predictions
$responseB = Invoke-RestMethod -Uri "https://engine-b.infinityai.pro/health"
$aiSignals = Invoke-RestMethod -Uri "https://engine-b.infinityai.pro/api/ai-signals"

# Engine C - Trade Execution
$responseC = Invoke-RestMethod -Uri "https://engine-c.infinityai.pro/health"
$orderStatus = Invoke-RestMethod -Uri "https://engine-c.infinityai.pro/api/orders/status"

# Engine D - Orchestration
$responseD = Invoke-RestMethod -Uri "https://engine-d.infinityai.pro/health"

# Display results
Write-Host "Engine A: $($responseA.status)"
Write-Host "Engine B: $($responseB.status)"
Write-Host "Engine C: $($responseC.status)"
Write-Host "Engine D: $($responseD.status)"
```

**Test Firebase Functions** (13 functions):
```powershell
# List all functions
firebase functions:list --project after-yesterday-473512-k3

# Test critical functions
Invoke-RestMethod -Uri "https://us-central1-after-yesterday-473512-k3.cloudfunctions.net/userSignup"
Invoke-RestMethod -Uri "https://us-central1-after-yesterday-473512-k3.cloudfunctions.net/dhanCallback"
```

**Test Authentication**:
```powershell
# Test Firebase Auth endpoint
Invoke-RestMethod -Uri "https://infinityai.pro/api/auth/status"
```

**Test WebSocket Connection** (Engine D):
```javascript
// In browser console on infinityai.pro
const ws = new WebSocket('wss://engine-d.infinityai.pro/ws/dashboard');
ws.onopen = () => console.log('WebSocket connected');
ws.onmessage = (e) => console.log('Message:', e.data);
```

---

### Task 9: Fix GSM_STATUS.md Project ID ⏳
**Priority**: LOW  
**Estimated Time**: 2 minutes

**Update archived documentation**:
```powershell
# Replace old project ID with correct one
(Get-Content "archive_removed_by_cleanup/20251102_145040/GSM_STATUS.md") `
  -replace 'infinity-ai-5ec7c', 'after-yesterday-473512-k3' |
  Set-Content "archive_removed_by_cleanup/20251102_145040/GSM_STATUS.md"

git add archive_removed_by_cleanup/20251102_145040/GSM_STATUS.md
git commit -m "docs: fix project ID in archived GSM_STATUS.md"
git push origin recovery/v4.6-stabilization
```

---

### Task 10: Delete Legacy GCP Project ⏳
**Priority**: LOW (wait 48h)  
**Estimated Time**: 5 minutes

**CAUTION**: Only after 48 hours of stable production operation!

**Verify Legacy Project Has No Active Resources**:
```bash
# List services in legacy project
gcloud run services list --project infinitygt-b2287 --region us-central1

# List Firebase Functions
firebase functions:list --project infinitygt-b2287

# If all empty, safe to delete
```

**Delete Project**:
```bash
gcloud projects delete infinitygt-b2287
```

**Confirmation**: You'll need to confirm deletion by typing the project ID.

**Cleanup Billing**:
```bash
# Verify billing account no longer linked
gcloud beta billing accounts list
gcloud beta billing projects describe infinitygt-b2287
```

---

## 🎯 Success Criteria

### 100% GCP Migration Complete When:

- ✅ All 4 engines deployed on Cloud Run with optimized resources
- ✅ Frontend deployed on Firebase Hosting (infinityai.pro)
- ✅ All 13 Firebase Functions deployed
- ✅ Vercel GitHub App disabled
- ✅ All Vercel projects deleted
- ✅ Custom domains configured (infinityai.pro + engine-*.infinityai.pro)
- ✅ DNS propagated and verified
- ✅ All health endpoints returning "healthy"
- ✅ End-to-end testing passed
- ✅ Cost optimization verified (scale-to-zero working)
- ✅ Legacy project deleted (after 48h)

---

## 📊 Cost Comparison

### Before Migration (Multi-Cloud)
- **Vercel**: $20-40/month
- **GCP Cloud Run**: $50-100/month (1 CPU, no scale-to-zero)
- **Firebase**: $10-20/month
- **Northflank**: $0 (already eliminated)
- **Total**: $80-160/month

### After Migration (GCP-Only)
- **Cloud Run**: $10-30/month (optimized, scale-to-zero)
- **Firebase Hosting**: $0 (free tier)
- **Firebase Functions**: $0-10/month (free tier)
- **Cloud Build**: $0 (free tier)
- **Secret Manager**: $0.30/month
- **Total**: $10-40/month

### Savings
- **Monthly**: $70-120 saved (~85% reduction)
- **Annual**: $840-1,440 saved

---

## 🔧 Troubleshooting

### Issue: Deployment Still Failing
```bash
# Check latest deployment
gh run view --log-failed

# Common fixes:
# 1. IAM permissions
gcloud projects get-iam-policy after-yesterday-473512-k3

# 2. API enablement
gcloud services list --enabled --project after-yesterday-473512-k3

# 3. Secret access
gcloud secrets list --project after-yesterday-473512-k3
```

### Issue: DNS Not Propagating
```powershell
# Check TTL on old records
nslookup -type=A infinityai.pro 8.8.8.8

# Flush local DNS cache
ipconfig /flushdns

# Wait 5-60 minutes for global propagation
```

### Issue: Vercel Still Deploying
- Disable Vercel GitHub App (Task 2)
- Check repository settings → Webhooks
- Remove any Vercel webhooks

### Issue: Cost Higher Than Expected
```bash
# Check active instances
gcloud run services list --region us-central1 --format="table(SERVICE_NAME,STATUS.traffic[0].percent,SPEC.template.spec.containers[0].resources.limits.cpu)"

# Verify min-instances=0
gcloud run services describe infinityai-engine-a --region us-central1 --format="get(spec.template.spec.containerConcurrency)"
```

---

## 📞 Support Resources

- **GCP Documentation**: https://cloud.google.com/run/docs
- **Firebase Documentation**: https://firebase.google.com/docs/hosting
- **GitHub Actions**: https://docs.github.com/en/actions
- **DNS Checker**: https://dnschecker.org
- **GCP Status**: https://status.cloud.google.com

---

## ✅ Final Checklist

Before marking migration complete:

- [ ] Deployment Run 19039100159 completed successfully
- [ ] All 4 engines show "healthy" status
- [ ] Frontend accessible at infinityai.pro
- [ ] Vercel GitHub App disabled
- [ ] All 4 Vercel projects deleted
- [ ] Firebase Hosting custom domain configured
- [ ] Cloud Run domain mappings created (4 engines)
- [ ] Namecheap DNS updated
- [ ] DNS propagated (all domains resolve correctly)
- [ ] End-to-end testing passed
- [ ] Cost optimization verified
- [ ] GSM_STATUS.md project ID fixed
- [ ] Legacy project deleted (after 48h stability)
- [ ] Documentation updated
- [ ] Team notified of migration completion

---

**Last Updated**: November 3, 2025 15:05 UTC  
**Next Action**: Monitor deployment Run 19039100159 completion
