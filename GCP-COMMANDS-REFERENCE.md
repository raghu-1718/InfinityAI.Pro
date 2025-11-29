# =====================================================================
# InfinityAI.Pro - Quick Reference: GCP Commands
# =====================================================================
# Essential commands for managing InfinityAI.Pro on Google Cloud
# =====================================================================

## 📌 Project Configuration

```bash
# Set active project
gcloud config set project after-yesterday-473512-k3

# Set default region
gcloud config set run/region us-central1

# View current config
gcloud config list
```

---

## 🧹 Cleanup Commands

### Delete Legacy Cloud Run Services

```bash
# Delete individual service
gcloud run services delete engine-d-orchestration-prod --region=us-central1 --quiet

# Delete multiple services
for service in engine-a engine-b-ai-ml-prod engine-c-execution-prod engine-d-orchestration-prod; do
  gcloud run services delete $service --region=us-central1 --quiet
done

# List all services
gcloud run services list --region=us-central1
```

### Delete Angel/TOTP Secrets

```bash
# Delete individual secret
gcloud secrets delete angel-api-key --quiet

# Delete all Angel secrets
for secret in angel-api-key angel-pin angel-totp-token angel-totp-secret angel-jwt-token; do
  gcloud secrets delete $secret --quiet 2>/dev/null || echo "Secret $secret not found"
done

# List remaining secrets
gcloud secrets list
```

---

## 🔐 Secret Management

### Create Dhan Secrets

```bash
# Create secret
echo -n "YOUR_VALUE" | gcloud secrets create dhan-client-id \
  --replication-policy="automatic" \
  --data-file=-

# Update existing secret (add new version)
echo -n "NEW_VALUE" | gcloud secrets versions add dhan-client-id --data-file=-

# View secret metadata (not the value)
gcloud secrets describe dhan-client-id

# Grant access to service account
gcloud secrets add-iam-policy-binding dhan-client-id \
  --member="serviceAccount:after-yesterday-473512-k3@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Access Secret Value (for testing)

```bash
# Get latest version
gcloud secrets versions access latest --secret="dhan-client-id"

# Get specific version
gcloud secrets versions access 1 --secret="dhan-client-id"
```

---

## 🚀 Cloud Run Deployment

### Build and Deploy Single Engine

```bash
# Set variables
export PROJECT_ID="after-yesterday-473512-k3"
export REGION="us-central1"
export SERVICE_NAME="engine-analytics"
export IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

# Build Docker image
cd backend/engine-analytics
docker build -t ${IMAGE} .

# Push to Google Container Registry
docker push ${IMAGE}

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE} \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_API_SECRET=dhan-api-secret:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"
```

### Update Service Configuration

```bash
# Update environment variables
gcloud run services update engine-analytics \
  --region=us-central1 \
  --set-env-vars="ENGINE_B_URL=https://engine-core-abc123.run.app"

# Update secrets
gcloud run services update engine-analytics \
  --region=us-central1 \
  --update-secrets="DHAN_ACCESS_TOKEN=dhan-access-token:latest"

# Update memory/CPU
gcloud run services update engine-analytics \
  --region=us-central1 \
  --memory=2Gi \
  --cpu=2
```

### Get Service Info

```bash
# Get service URL
gcloud run services describe engine-analytics \
  --region=us-central1 \
  --format='value(status.url)'

# Get full service details
gcloud run services describe engine-analytics --region=us-central1

# List all services with URLs
gcloud run services list --region=us-central1 --format='table(name,status.url)'
```

---

## 🌐 Domain Mapping

### Map Custom Domain

```bash
# Map domain to service
gcloud run domain-mappings create \
  --service=engine-analytics \
  --domain=infinityai.pro \
  --region=us-central1

# Get DNS configuration
gcloud run domain-mappings describe infinityai.pro \
  --region=us-central1 \
  --format='value(status.resourceRecords)'

# Check SSL certificate status
gcloud run domain-mappings describe infinityai.pro \
  --region=us-central1 \
  --format='value(status.conditions)'
```

### Update/Delete Domain Mapping

```bash
# Delete domain mapping
gcloud run domain-mappings delete infinityai.pro --region=us-central1

# List all domain mappings
gcloud run domain-mappings list --region=us-central1
```

---

## 📊 Monitoring & Logs

### View Logs

```bash
# Tail logs for a service (real-time)
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=engine-analytics"

# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-analytics" \
  --limit=50 \
  --format=json

# Filter logs by severity
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=engine-analytics AND severity>=ERROR" \
  --limit=20
```

### Service Metrics

```bash
# Get service revisions
gcloud run revisions list --service=engine-analytics --region=us-central1

# Get traffic split
gcloud run services describe engine-analytics \
  --region=us-central1 \
  --format='value(status.traffic)'

# Get container image
gcloud run services describe engine-analytics \
  --region=us-central1 \
  --format='value(spec.template.spec.containers[0].image)'
```

---

## 🔒 IAM & Security

### Service-to-Service Authentication

```bash
# Remove public access (require authentication)
gcloud run services update engine-core \
  --no-allow-unauthenticated \
  --region=us-central1

# Grant service account permission to invoke
gcloud run services add-iam-policy-binding engine-core \
  --member="serviceAccount:after-yesterday-473512-k3@appspot.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1

# List IAM policies
gcloud run services get-iam-policy engine-core --region=us-central1
```

### Service Account Management

```bash
# List service accounts
gcloud iam service-accounts list

# Create custom service account
gcloud iam service-accounts create infinityai-runner \
  --display-name="InfinityAI Cloud Run Service Account"

# Grant secret access
gcloud secrets add-iam-policy-binding dhan-client-id \
  --member="serviceAccount:infinityai-runner@after-yesterday-473512-k3.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 🔍 Troubleshooting

### Debug Service Issues

```bash
# Get service status
gcloud run services describe engine-analytics \
  --region=us-central1 \
  --format='value(status.conditions)'

# Get latest revision status
gcloud run revisions describe $(gcloud run services describe engine-analytics --region=us-central1 --format='value(status.latestReadyRevisionName)') \
  --region=us-central1

# Test service endpoint
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://engine-analytics-abc123.run.app/healthz
```

### Rollback Deployment

```bash
# List revisions
gcloud run revisions list --service=engine-analytics --region=us-central1

# Route traffic to previous revision
gcloud run services update-traffic engine-analytics \
  --to-revisions=engine-analytics-00002-abc=100 \
  --region=us-central1
```

---

## 🧪 Testing Commands

### Health Checks

```bash
# Engine A
curl https://infinityai.pro/healthz

# Engine B (get URL first)
ENGINE_B_URL=$(gcloud run services describe engine-core --region=us-central1 --format='value(status.url)')
curl ${ENGINE_B_URL}/healthz

# Engine C
ENGINE_C_URL=$(gcloud run services describe engine-execution --region=us-central1 --format='value(status.url)')
curl ${ENGINE_C_URL}/healthz
```

### API Testing

```bash
# Test signal generation
curl -X POST ${ENGINE_B_URL}/api/v1/signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE"}'

# Test orchestration
curl -X POST https://infinityai.pro/api/v1/trade/start \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "qty": 1}'
```

---

## 🎛️ Environment Variables Reference

### Common Environment Variables

```bash
# Engine A
GOOGLE_CLOUD_PROJECT=after-yesterday-473512-k3
ENGINE_B_URL=https://engine-core-<hash>.run.app
ENGINE_C_URL=https://engine-execution-<hash>.run.app
DHAN_REDIRECT_URI=https://infinityai.pro/api/auth/dhan/callback

# Engine B
GOOGLE_CLOUD_PROJECT=after-yesterday-473512-k3

# Engine C
GOOGLE_CLOUD_PROJECT=after-yesterday-473512-k3
```

### Secrets (via Secret Manager)

```bash
DHAN_CLIENT_ID=dhan-client-id:latest
DHAN_API_SECRET=dhan-api-secret:latest
DHAN_ACCESS_TOKEN=dhan-access-token:latest
DHAN_REDIRECT_URI=dhan-redirect-uri:latest
```

---

## 📦 Quick Deploy All Engines

```bash
#!/bin/bash
# Complete deployment script

export PROJECT_ID="after-yesterday-473512-k3"
export REGION="us-central1"

# Deploy Engine A
cd backend/engine-analytics
docker build -t gcr.io/${PROJECT_ID}/engine-analytics:latest .
docker push gcr.io/${PROJECT_ID}/engine-analytics:latest
gcloud run deploy engine-analytics \
  --image=gcr.io/${PROJECT_ID}/engine-analytics:latest \
  --platform=managed --region=${REGION} \
  --allow-unauthenticated --port=8080 \
  --memory=1Gi --cpu=1 --timeout=300 \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_API_SECRET=dhan-api-secret:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"

# Deploy Engine B
cd ../engine-core
docker build -t gcr.io/${PROJECT_ID}/engine-core:latest .
docker push gcr.io/${PROJECT_ID}/engine-core:latest
gcloud run deploy engine-core \
  --image=gcr.io/${PROJECT_ID}/engine-core:latest \
  --platform=managed --region=${REGION} \
  --allow-unauthenticated --port=8080 \
  --memory=2Gi --cpu=2 --timeout=300 \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"

# Deploy Engine C
cd ../engine-execution
docker build -t gcr.io/${PROJECT_ID}/engine-execution:latest .
docker push gcr.io/${PROJECT_ID}/engine-execution:latest
gcloud run deploy engine-execution \
  --image=gcr.io/${PROJECT_ID}/engine-execution:latest \
  --platform=managed --region=${REGION} \
  --allow-unauthenticated --port=8080 \
  --memory=1Gi --cpu=1 --timeout=300 \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"

# Get URLs
ENGINE_B_URL=$(gcloud run services describe engine-core --region=${REGION} --format='value(status.url)')
ENGINE_C_URL=$(gcloud run services describe engine-execution --region=${REGION} --format='value(status.url)')

# Update Engine A with service URLs
gcloud run services update engine-analytics \
  --region=${REGION} \
  --set-env-vars="ENGINE_B_URL=${ENGINE_B_URL},ENGINE_C_URL=${ENGINE_C_URL}"

echo "✅ Deployment complete!"
echo "Engine A: https://infinityai.pro"
echo "Engine B: ${ENGINE_B_URL}"
echo "Engine C: ${ENGINE_C_URL}"
```

---

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Domain Mapping Guide](https://cloud.google.com/run/docs/mapping-custom-domains)
- [DhanHQ API Docs](https://api.dhan.co)

---

**Last Updated**: November 28, 2025
**Project**: after-yesterday-473512-k3
**Region**: us-central1
