# =====================================================================
# InfinityAI.Pro - Complete Deployment Guide (Dhan-Only Architecture)
# =====================================================================
# Date: November 28, 2025
# Version: 3.0 (Angel/TOTP Eliminated)
# =====================================================================

## 🎯 Architecture Overview

### 3-Engine Architecture (Dhan-Only)

```
┌─────────────────────────────────────────────────────────────────┐
│                     INFINITYAI.PRO                              │
│                  (Custom Domain via Cloud Run)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  ENGINE A: Orchestration & Dhan OAuth (engine-analytics)        │
│  - Dhan OAuth callback handler                                  │
│  - Trade orchestration endpoint (/api/v1/trade/start)           │
│  - Port: 8080                                                   │
│  - URL: https://infinityai.pro                                  │
└─────────────────────────────────────────────────────────────────┘
            ↓ (calls)                    ↓ (calls)
┌─────────────────────────┐    ┌──────────────────────────────────┐
│  ENGINE B: AI/ML Signals │    │  ENGINE C: Dhan Execution        │
│  (engine-core)           │    │  (engine-execution)              │
│  - Signal generation     │    │  - Order placement               │
│  - /api/v1/signal        │    │  - /api/dhan/place-order         │
│  - Port: 8080            │    │  - Port: 8080                    │
└─────────────────────────┘    └──────────────────────────────────┘
```

---

## 📋 Prerequisites

1. **GCP Project**: `gen-lang-client-0779271931`
2. **Dhan Account**: Active DhanHQ trading account
3. **Dhan OAuth App**: Register at [Dhan Developer Portal](https://api.dhan.co)
4. **Domain**: `infinityai.pro` (DNS configured via Namecheap → Google domains)
5. **Tools**: `gcloud`, `docker`, `git`

---

## 🔐 Step 1: Clean Up Legacy Resources

### 1.1 Run Cleanup Script

```bash
# Make script executable
chmod +x scripts/cleanup-legacy-gcp-resources.sh

# Execute cleanup
./scripts/cleanup-legacy-gcp-resources.sh
```

**This will delete**:
- Legacy Cloud Run services (engine-d, duplicates)
- Angel/TOTP secrets from Secret Manager
- Unused Gemini API secrets (optional)

### 1.2 Verify Cleanup

```bash
# Check no legacy services remain
gcloud run services list --region=us-central1 --project=gen-lang-client-0779271931

# Check no Angel secrets remain
gcloud secrets list --project=gen-lang-client-0779271931 --filter="name:angel-*"
```

---

## 🔑 Step 2: Configure Dhan OAuth Secrets

### 2.1 Obtain Dhan Credentials

1. Go to [Dhan Developer Console](https://api.dhan.co)
2. Create a new OAuth app
3. Note down:
   - **Client ID**
   - **API Secret** (Client Secret)
   - **Redirect URI**: `https://infinityai.pro/api/auth/dhan/callback`

### 2.2 Store Secrets in Google Secret Manager

**Option A: Use Script (Recommended)**

```bash
chmod +x scripts/setup-dhan-secrets.sh
./scripts/setup-dhan-secrets.sh
```

**Option B: Manual Setup**

```bash
PROJECT_ID="gen-lang-client-0779271931"

# Create secrets
echo -n "YOUR_DHAN_CLIENT_ID" | gcloud secrets create dhan-client-id \
  --replication-policy="automatic" --data-file=- --project=$PROJECT_ID

echo -n "YOUR_DHAN_API_SECRET" | gcloud secrets create dhan-api-secret \
  --replication-policy="automatic" --data-file=- --project=$PROJECT_ID

echo -n "YOUR_DHAN_ACCESS_TOKEN" | gcloud secrets create dhan-access-token \
  --replication-policy="automatic" --data-file=- --project=$PROJECT_ID

echo -n "https://infinityai.pro/api/auth/dhan/callback" | gcloud secrets create dhan-redirect-uri \
  --replication-policy="automatic" --data-file=- --project=$PROJECT_ID
```

### 2.3 Grant Service Account Access

```bash
SERVICE_ACCOUNT="gen-lang-client-0779271931@appspot.gserviceaccount.com"

for secret in dhan-client-id dhan-api-secret dhan-access-token dhan-redirect-uri; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID
done
```

---

## 🚀 Step 3: Deploy Engines to Cloud Run

### 3.1 Set Environment Variables

```bash
export PROJECT_ID="gen-lang-client-0779271931"
export REGION="us-central1"
export REPO="gcr.io/${PROJECT_ID}"
```

### 3.2 Build and Deploy Engine A (Orchestration)

```bash
cd backend/engine-analytics

# Build Docker image
docker build -t ${REPO}/engine-analytics:latest .

# Push to GCR
docker push ${REPO}/engine-analytics:latest

# Deploy to Cloud Run
gcloud run deploy engine-analytics \
  --image=${REPO}/engine-analytics:latest \
  --platform=managed \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},ENGINE_B_URL=https://engine-core-<hash>.run.app,ENGINE_C_URL=https://engine-execution-<hash>.run.app" \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_API_SECRET=dhan-api-secret:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest,DHAN_REDIRECT_URI=dhan-redirect-uri:latest"
```

### 3.3 Build and Deploy Engine B (AI/ML)

```bash
cd ../engine-core

# Build Docker image
docker build -t ${REPO}/engine-core:latest .

# Push to GCR
docker push ${REPO}/engine-core:latest

# Deploy to Cloud Run
gcloud run deploy engine-core \
  --image=${REPO}/engine-core:latest \
  --platform=managed \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"
```

### 3.4 Build and Deploy Engine C (Execution)

```bash
cd ../engine-execution

# Build Docker image
docker build -t ${REPO}/engine-execution:latest .

# Push to GCR
docker push ${REPO}/engine-execution:latest

# Deploy to Cloud Run
gcloud run deploy engine-execution \
  --image=${REPO}/engine-execution:latest \
  --platform=managed \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"
```

### 3.5 Get Service URLs

```bash
# Get Engine B URL
ENGINE_B_URL=$(gcloud run services describe engine-core --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')

# Get Engine C URL
ENGINE_C_URL=$(gcloud run services describe engine-execution --region=${REGION} --project=${PROJECT_ID} --format='value(status.url)')

echo "Engine B URL: $ENGINE_B_URL"
echo "Engine C URL: $ENGINE_C_URL"
```

### 3.6 Update Engine A with Service URLs

```bash
gcloud run services update engine-analytics \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --set-env-vars="ENGINE_B_URL=${ENGINE_B_URL},ENGINE_C_URL=${ENGINE_C_URL}"
```

---

## 🌐 Step 4: Configure Custom Domain

### 4.1 Map Domain to Engine A

```bash
# Map infinityai.pro to engine-analytics
gcloud run domain-mappings create \
  --service=engine-analytics \
  --domain=infinityai.pro \
  --region=${REGION} \
  --project=${PROJECT_ID}
```

### 4.2 Get DNS Configuration

```bash
gcloud run domain-mappings describe infinityai.pro \
  --region=${REGION} \
  --project=${PROJECT_ID}
```

### 4.3 Update DNS Records (Namecheap)

Add these records in Namecheap DNS settings:

| Type  | Host | Value (from GCP)                  | TTL  |
|-------|------|-----------------------------------|------|
| A     | @    | `<IP from GCP>`                   | 300  |
| AAAA  | @    | `<IPv6 from GCP>`                 | 300  |
| CNAME | www  | `ghs.googlehosted.com.`           | 300  |

### 4.4 Verify Domain Mapping

```bash
# Check SSL certificate provisioning (may take 15-60 minutes)
gcloud run domain-mappings describe infinityai.pro \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(status.resourceRecords)'
```

---

## ✅ Step 5: Verify Deployment

### 5.1 Health Checks

```bash
# Engine A
curl https://infinityai.pro/healthz

# Engine B
curl $ENGINE_B_URL/healthz

# Engine C
curl $ENGINE_C_URL/healthz
```

Expected response:
```json
{"status": "healthy", "service": "engine-X", ...}
```

### 5.2 Test Dhan OAuth Flow

1. Open browser: `https://infinityai.pro/api/auth/dhan/login`
2. Redirected to Dhan login page
3. Authorize the app
4. Redirected back to `/api/auth/dhan/callback?code=...`
5. Verify token exchange response

### 5.3 Test Signal Generation

```bash
curl -X POST $ENGINE_B_URL/api/v1/signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE"}'
```

Expected response:
```json
{
  "symbol": "RELIANCE",
  "signal": "BUY",
  "confidence": 78.5,
  "predicted_price": 2456.32,
  "timestamp": "2025-11-28T10:30:00.000Z",
  "model_version": "ai-ml-3.0-dhan"
}
```

### 5.4 Test End-to-End Trade Flow

```bash
curl -X POST https://infinityai.pro/api/v1/trade/start \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "qty": 1,
    "strategy": "momentum"
  }'
```

Expected response:
```json
{
  "status": "execution_scheduled",
  "signal": { ... },
  "execution_payload": { ... },
  "timestamp": "..."
}
```

---

## 🔒 Step 6: Security Hardening

### 6.1 Enable Cloud Run IAM Authentication (Optional)

For Engine B and C (internal services):

```bash
# Remove public access
gcloud run services update engine-core --no-allow-unauthenticated --region=${REGION}
gcloud run services update engine-execution --no-allow-unauthenticated --region=${REGION}

# Grant Engine A permission to invoke
gcloud run services add-iam-policy-binding engine-core \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region=${REGION}

gcloud run services add-iam-policy-binding engine-execution \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region=${REGION}
```

### 6.2 Update Engine A Code for IAM Auth

Add to `backend/engine-analytics/src/main.py`:

```python
from google.auth.transport.requests import Request
from google.oauth2 import id_token

def get_id_token():
    """Get ID token for Cloud Run service-to-service auth"""
    auth_req = Request()
    return id_token.fetch_id_token(auth_req, ENGINE_B_URL)

# In orchestrate_trade function:
headers = {"Authorization": f"Bearer {get_id_token()}"}
signal_response = await client.post(f"{ENGINE_B_URL}/api/v1/signal", json=..., headers=headers)
```

---

## 📊 Step 7: Monitoring Setup

### 7.1 Enable Cloud Logging

```bash
# View logs for Engine A
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-analytics" --limit=50 --project=${PROJECT_ID}
```

### 7.2 Set Up Uptime Monitoring

```bash
# Create uptime check for Engine A
gcloud monitoring uptime create https://infinityai.pro/healthz \
  --display-name="InfinityAI.Pro Health" \
  --check-interval=60s
```

### 7.3 Configure Alerts

Use `monitoring/alert-*.json` configurations from the repository.

---

## 🎉 Deployment Complete!

### Production URLs:
- **Engine A (Orchestration)**: `https://infinityai.pro`
- **Engine B (AI/ML)**: `https://engine-core-<hash>.run.app`
- **Engine C (Execution)**: `https://engine-execution-<hash>.run.app`

### API Endpoints:
- Dhan OAuth Login: `https://infinityai.pro/api/auth/dhan/login`
- Start Trade: `https://infinityai.pro/api/v1/trade/start`
- Generate Signal: `<ENGINE_B_URL>/api/v1/signal`
- Place Order: `<ENGINE_C_URL>/api/dhan/place-order`

---

## 🔄 Next Steps

1. **Frontend Deployment**: Follow `FRONTEND-CLEANUP-PLAN.md`
2. **Test OAuth Flow**: Authenticate with Dhan
3. **Paper Trading**: Test with small quantities
4. **Monitor Logs**: Watch Cloud Run logs for errors
5. **Scale Testing**: Increase traffic gradually

---

## 📞 Support & Troubleshooting

### Common Issues:

**Issue**: "Dhan credentials not configured"
- **Fix**: Verify secrets are created and IAM permissions granted

**Issue**: "Engine B/C timeout"
- **Fix**: Check Cloud Run logs, increase memory/CPU

**Issue**: "Domain not resolving"
- **Fix**: Wait for DNS propagation (15-60 mins), verify DNS records

---

**Status**: Production Ready ✅
**Architecture**: 3-Engine Dhan-Only
**Last Updated**: November 28, 2025
