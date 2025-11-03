# GitHub Secrets Mapping & Status

## GCP/Firebase Infrastructure Secrets

| Required by Workflow | GitHub Secret Name | Status | Source |
|---------------------|-------------------|--------|--------|
| Firebase Token | `FIREBASE_TOKEN` | ✅ SET | CI/CD token |
| Firebase Project ID | `FIREBASE_PROJECT_ID` | ✅ SET | after-yesterday-473512-k3 |
| GCP Service Account | `GCP_SERVICE_ACCOUNT_KEY` | ✅ SET | GCP Console IAM |
| GCP Project ID | `GCP_PROJECT_ID` | ✅ SET | after-yesterday-473512-k3 |
| GCP Region | `GCP_REGION` | ✅ SET | us-central1 |

## Engine-Specific Firebase Service Accounts

| Engine | GitHub Secret Name | Status | Purpose |
|--------|-------------------|--------|---------|
| Engine A | `FIREBASE_SERVICE_ACCOUNT_KEY_ENGINE_A` | ✅ SET | Market Data Processing |
| Engine B | `FIREBASE_SERVICE_ACCOUNT_KEY_ENGINE_B` | ✅ SET | AI/ML Processing |
| Engine C | `FIREBASE_SERVICE_ACCOUNT_KEY_ENGINE_C` | ✅ SET | Trade Execution |
| Engine D | `FIREBASE_SERVICE_ACCOUNT_KEY_ENGINE_D` | ✅ SET | Orchestration |

## API Keys

| API Provider | GitHub Secret Name | Status | Purpose |
|--------------|-------------------|--------|---------|
| Gemini Primary | `GEMINI_API_KEY_PRIMARY` | ✅ SET | AI Analysis |
| Gemini Secondary | `GEMINI_API_KEY_SECONDARY` | ✅ SET | Failover |
| OpenAI | `OPENAI_API_KEY` | ✅ SET | AI Processing |
| Dhan Client | `DHAN_CLIENT_ID` | ✅ SET | Trading Broker Integration |

## Platform Architecture

**Complete GCP/Firebase Stack:**
- ✅ Frontend: Firebase Hosting (infinityai.pro)
- ✅ API Webhooks: Firebase Cloud Functions
- ✅ Engine A: Cloud Run (infinityai-engine-a)
- ✅ Engine B: Cloud Run (infinityai-engine-b)
- ✅ Engine C: Cloud Run (infinityai-engine-c-execution)
- ✅ Engine D: Cloud Run (infinityai-engine-d)
- ✅ Backend Functions: Firebase Cloud Functions (13 functions)

**Cost Optimization:**
- Engines A/B/D: 0.5 CPU, 256Mi memory, max 5 instances
- Engine C: 1 CPU, 512Mi memory, max 10 instances (trading execution)
- All engines: min-instances=0 (scale to zero when idle)

---

## Firebase Configuration

**Production Project:** after-yesterday-473512-k3  
**Project Number:** 573866363639  
**Region:** us-central1  
**Billing Account:** 017B9F-F463F6-7BA3A7 (OPEN)

---

## Verification Commands

### List All Secrets
```powershell
gh secret list
```

### Verify GCP Authentication
```bash
gcloud auth list
gcloud projects list
gcloud config get-value project
```

### Verify Firebase Configuration
```bash
firebase projects:list
firebase use
```

---

## Next Steps

1. ✅ All secrets configured for GCP/Firebase-only stack
2. ✅ Vercel and Northflank completely removed
3. 🚀 Deploy via GitHub Actions to GCP Cloud Run + Firebase
4. 📊 Monitor costs via GCP Billing Dashboard

