# Namecheap DNS Configuration for InfinityAI.Pro

**Date**: November 3, 2025  
**Domain**: infinityai.pro  
**GCP Project**: after-yesterday-473512-k3  
**Project Number**: 573866363639

---

## Current DNS Records (Already Configured)

### 1. Main Domain (infinityai.pro)
**Purpose**: Frontend website (mapped to Cloud Run service `frontend-new-prod`)

```
Type: A
Host: @
Value: 216.239.32.21
TTL: Automatic

Type: A
Host: @
Value: 216.239.34.21
TTL: Automatic

Type: A
Host: @
Value: 216.239.36.21
TTL: Automatic

Type: A
Host: @
Value: 216.239.38.21
TTL: Automatic

Type: AAAA
Host: @
Value: 2001:4860:4802:32::15
TTL: Automatic

Type: AAAA
Host: @
Value: 2001:4860:4802:34::15
TTL: Automatic

Type: AAAA
Host: @
Value: 2001:4860:4802:36::15
TTL: Automatic

Type: AAAA
Host: @
Value: 2001:4860:4802:38::15
TTL: Automatic
```

---

## New DNS Records to Add (Backend Engines)

### 2. Engine A - Market Data (engine-a.infinityai.pro)
**Purpose**: Real-time market data ingestion and technical analysis  
**Cloud Run Service**: `engine-a`  
**URL**: https://engine-a-573866363639.us-central1.run.app

**Action Required**: Run the following command to create domain mapping and get DNS records:
```bash
gcloud beta run domain-mappings create --service engine-a --domain engine-a.infinityai.pro --region us-central1 --project after-yesterday-473512-k3
gcloud beta run domain-mappings describe --domain engine-a.infinityai.pro --region us-central1 --project after-yesterday-473512-k3 --format="yaml(status.resourceRecords)"
```

**Expected DNS Records**:
```
Type: A or CNAME
Host: engine-a
Value: (will be provided by gcloud command above)
TTL: Automatic
```

---

### 3. Engine B - AI/ML Processing (engine-b.infinityai.pro)
**Purpose**: AI/ML processing with price predictions and sentiment analysis  
**Cloud Run Service**: `engine-b-ai-ml-prod`  
**URL**: https://engine-b-ai-ml-prod-573866363639.us-central1.run.app

**Action Required**: Run the following command to create domain mapping and get DNS records:
```bash
gcloud beta run domain-mappings create --service engine-b-ai-ml-prod --domain engine-b.infinityai.pro --region us-central1 --project after-yesterday-473512-k3
gcloud beta run domain-mappings describe --domain engine-b.infinityai.pro --region us-central1 --project after-yesterday-473512-k3 --format="yaml(status.resourceRecords)"
```

**Expected DNS Records**:
```
Type: A or CNAME
Host: engine-b
Value: (will be provided by gcloud command above)
TTL: Automatic
```

---

### 4. Engine C - Trade Execution (engine-c.infinityai.pro)
**Purpose**: Secure trade execution with Dhan OAuth and risk management  
**Cloud Run Service**: `engine-c-execution-prod`  
**URL**: https://engine-c-execution-prod-573866363639.us-central1.run.app

**Action Required**: Run the following command to create domain mapping and get DNS records:
```bash
gcloud beta run domain-mappings create --service engine-c-execution-prod --domain engine-c.infinityai.pro --region us-central1 --project after-yesterday-473512-k3
gcloud beta run domain-mappings describe --domain engine-c.infinityai.pro --region us-central1 --project after-yesterday-473512-k3 --format="yaml(status.resourceRecords)"
```

**Expected DNS Records**:
```
Type: A or CNAME
Host: engine-c
Value: (will be provided by gcloud command above)
TTL: Automatic
```

---

### 5. Engine D - Orchestrator (engine-d.infinityai.pro)
**Purpose**: AI chatbot orchestrator managing multi-engine coordination  
**Cloud Run Service**: `engine-d-orchestration-prod`  
**URL**: https://engine-d-orchestration-prod-573866363639.us-central1.run.app

**Action Required**: Run the following command to create domain mapping and get DNS records:
```bash
gcloud beta run domain-mappings create --service engine-d-orchestration-prod --domain engine-d.infinityai.pro --region us-central1 --project after-yesterday-473512-k3
gcloud beta run domain-mappings describe --domain engine-d.infinityai.pro --region us-central1 --project after-yesterday-473512-k3 --format="yaml(status.resourceRecords)"
```

**Expected DNS Records**:
```
Type: A or CNAME
Host: engine-d
Value: (will be provided by gcloud command above)
TTL: Automatic
```

---

## Vercel Deployments (To Be Configured)

### 6. Frontend (Vercel)
**Project ID**: prj_IgZM5pKlOJPk2AMLPvEi0P84EWqz  
**Deployment URL**: Will be provided after successful deployment  
**Custom Domain**: infinityai.pro (already using Cloud Run mapping)

**Alternative**: If you want to use Vercel for frontend instead of Cloud Run:
1. Go to Vercel Dashboard → Project Settings → Domains
2. Add domain: infinityai.pro
3. Copy the CNAME or A records provided by Vercel
4. Replace the existing @ host records in Namecheap

---

### 7. API Webhooks (Vercel)
**Project ID**: prj_MiGVALqsWy03Yt0VzIqLNXIaSADO  
**Deployment URL**: Will be provided after successful deployment  
**Suggested Custom Domain**: api.infinityai.pro or webhooks.infinityai.pro

**Action Required**:
1. Go to Vercel Dashboard → api-webhooks project → Settings → Domains
2. Add domain: api.infinityai.pro
3. Copy the provided DNS records
4. Add to Namecheap:
```
Type: CNAME
Host: api
Value: (provided by Vercel, typically cname.vercel-dns.com)
TTL: Automatic
```

---

## Firebase Functions

**Project**: after-yesterday-473512-k3  
**Functions URL**: https://us-central1-after-yesterday-473512-k3.cloudfunctions.net/

Firebase Functions are accessed via Cloud Functions URLs and typically don't require custom domain mappings unless you set up Firebase Hosting.

---

## Summary of Actions

### Immediate Actions (Run These Commands):
```bash
# Set project context
gcloud config set project after-yesterday-473512-k3

# Create domain mappings for all 4 engines
gcloud beta run domain-mappings create --service engine-a --domain engine-a.infinityai.pro --region us-central1
gcloud beta run domain-mappings create --service engine-b-ai-ml-prod --domain engine-b.infinityai.pro --region us-central1
gcloud beta run domain-mappings create --service engine-c-execution-prod --domain engine-c.infinityai.pro --region us-central1
gcloud beta run domain-mappings create --service engine-d-orchestration-prod --domain engine-d.infinityai.pro --region us-central1

# Get DNS records for all mappings
gcloud beta run domain-mappings describe --domain engine-a.infinityai.pro --region us-central1 --format="yaml(status.resourceRecords)"
gcloud beta run domain-mappings describe --domain engine-b.infinityai.pro --region us-central1 --format="yaml(status.resourceRecords)"
gcloud beta run domain-mappings describe --domain engine-c.infinityai.pro --region us-central1 --format="yaml(status.resourceRecords)"
gcloud beta run domain-mappings describe --domain engine-d.infinityai.pro --region us-central1 --format="yaml(status.resourceRecords)"
```

### In Namecheap Dashboard:
1. Login to Namecheap
2. Go to Domain List → infinityai.pro → Manage → Advanced DNS
3. Add the DNS records as shown above for each engine subdomain
4. Wait 5-30 minutes for DNS propagation
5. Verify with: `nslookup engine-a.infinityai.pro`

---

## Verification Steps

After adding DNS records, verify each endpoint:

```bash
# Check DNS propagation
nslookup engine-a.infinityai.pro
nslookup engine-b.infinityai.pro
nslookup engine-c.infinityai.pro
nslookup engine-d.infinityai.pro

# Test HTTPS endpoints
curl -Ik https://infinityai.pro/health
curl -Ik https://engine-a.infinityai.pro/health
curl -Ik https://engine-b.infinityai.pro/health
curl -Ik https://engine-c.infinityai.pro/health
curl -Ik https://engine-d.infinityai.pro/health
```

---

## Architecture Summary

```
infinityai.pro (Cloud Run: frontend-new-prod)
├── engine-a.infinityai.pro (Cloud Run: engine-a)
├── engine-b.infinityai.pro (Cloud Run: engine-b-ai-ml-prod)
├── engine-c.infinityai.pro (Cloud Run: engine-c-execution-prod)
├── engine-d.infinityai.pro (Cloud Run: engine-d-orchestration-prod)
├── api.infinityai.pro (Vercel: api-webhooks) [To be configured]
└── Firebase Functions (via Cloud Functions URLs)
```

**Single GCP Project**: after-yesterday-473512-k3  
**Single Billing Account**: 017B9F-F463F6-7BA3A7 (Firebase Payment - OPEN)  
**All services authenticated and authorized with proper IAM roles**

---

## Next Steps After DNS Configuration

1. ✅ Monitor GitHub Actions deployment: https://github.com/raghu-1718/InfinityAI.Pro/actions
2. ⏳ Wait for all 4 engines to deploy successfully on Cloud Run
3. ⏳ Create domain mappings using commands above
4. ⏳ Add DNS records in Namecheap
5. ⏳ Configure Vercel custom domains for frontend and api-webhooks (optional)
6. ⏳ Test all endpoints for health and functionality
7. ⏳ Delete unused project `infinitygt-b2287` after confirming everything works
8. ⏳ Close unused billing accounts after project deletion

---

**Last Updated**: November 3, 2025  
**Status**: Deployment in progress, DNS configuration pending
