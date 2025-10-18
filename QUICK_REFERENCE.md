# 🚀 InfinityAI.Pro - Quick Reference Guide

## 📌 Production Service URLs

```
Engine A: https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app
Engine B: https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app
Engine C: https://engine-c-execution-prod-bprmddefsa-uc.a.run.app
Engine D: https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app
Frontend: https://infinityai-frontend-bprmddefsa-uc.a.run.app
```

## ⚡ Quick Health Checks

```bash
# Check all engines at once
curl https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app/health
curl https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/health
curl https://engine-c-execution-prod-bprmddefsa-uc.a.run.app/health
curl https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/health

# Comprehensive orchestration status
curl https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/api/health/comprehensive
```

## 🔧 Common Commands

### View All Services
```bash
gcloud run services list --region us-central1 --filter="metadata.name:*-prod"
```

### View Logs
```bash
gcloud run services logs read engine-a-market-data-prod --region us-central1 --limit 50
gcloud run services logs read engine-b-ai-ml-prod --region us-central1 --limit 50
gcloud run services logs read engine-c-execution-prod --region us-central1 --limit 50
gcloud run services logs read engine-d-orchestration-prod --region us-central1 --limit 50
```

### Update Service Configuration
```bash
# Example: Update environment variables
gcloud run services update engine-d-orchestration-prod \
  --region us-central1 \
  --set-env-vars NEW_VAR=value
```

### Redeploy Service
```bash
# Example: Redeploy Engine B with new image
gcloud run deploy engine-b-ai-ml-prod \
  --image gcr.io/after-yesterday-473512-k3/engine-b-ai-ml:v1.0.6 \
  --region us-central1 \
  --cpu 2 --memory 4Gi \
  --min-instances 0 --max-instances 5
```

## 🧪 Testing

### Test AI Predictions (Engine B)
```bash
curl https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/api/predict/NIFTY
curl https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/api/ai-signals
curl https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/api/models/status
```

### Test WebSocket (requires wscat)
```bash
npm install -g wscat
wscat -c wss://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/ws/dashboard
wscat -c wss://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/ws/trades
```

## 📊 Current Deployment Status

| Service | Version | Status | CPU | Memory |
|---------|---------|--------|-----|--------|
| Engine A | v1.0.1 | ✅ HEALTHY | 2 | 4Gi |
| Engine B | v1.0.5 | ✅ HEALTHY | 2 | 4Gi |
| Engine C | v1.0.2 | ✅ HEALTHY | 2 | 4Gi |
| Engine D | v1.0.0 | ✅ HEALTHY | 2 | 4Gi |
| Frontend | latest | ✅ DEPLOYED | 1 | 2Gi |

## 🔐 Environment Variables

### Engine D Integration URLs
```
ENGINE_A_URL=https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app
ENGINE_B_URL=https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app
ENGINE_C_URL=https://engine-c-execution-prod-bprmddefsa-uc.a.run.app
JWT_SECRET_KEY=[configured]
```

### Engine C Broadcast URL
```
ENGINE_D_URL=https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app
```

## 📝 Next Steps

1. **Update Frontend Environment Variables**
   ```bash
   gcloud run services update infinityai-frontend \
     --region us-central1 \
     --set-env-vars \
   REACT_APP_ENGINE_D_URL=https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app
   ```

2. **Test WebSocket Connectivity**
   - Connect frontend to Engine D WebSocket channels
   - Test real-time data flow

3. **Migrate Secrets to Secret Manager**
   - Move JWT_SECRET_KEY to Google Secret Manager
   - Store Dhan credentials securely

4. **End-to-End Integration Test**
   - Test complete data flow: A → B → C → D → Frontend
   - Validate trade execution and broadcasting

## 🆘 Troubleshooting

### Service Not Responding
```bash
# Check service status
gcloud run services describe <service-name> --region us-central1

# Check logs
gcloud run services logs read <service-name> --region us-central1 --limit 100

# Restart service (trigger new revision)
gcloud run services update <service-name> --region us-central1 --clear-env-vars DUMMY
gcloud run services update <service-name> --region us-central1 --remove-env-vars DUMMY
```

### Health Check Failing
```bash
# Test directly
curl -v https://<service-url>/health

# Check if container is running
gcloud run revisions list --service <service-name> --region us-central1
```

## 📚 Documentation

- **Full Deployment Report:** `FINAL_PRODUCTION_VERIFICATION_REPORT.md`
- **Architecture Docs:** `docs/ARCHITECTURE.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`

## 🎯 Project Info

- **Project ID:** after-yesterday-473512-k3
- **Region:** us-central1
- **Container Registry:** gcr.io/after-yesterday-473512-k3
- **Platform:** Google Cloud Run

---

**Last Updated:** October 18, 2025  
**Status:** 🟢 All Systems Operational  
**Deployment:** 100% Complete
