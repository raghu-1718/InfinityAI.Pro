# Deployment Guide - InfinityAI.Pro

Complete step-by-step deployment guide for InfinityAI.Pro on Google Cloud Run, Firebase, and Cloud Build.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [GCP Project Setup](#gcp-project-setup)
4. [Secrets Management](#secrets-management)
5. [Terraform Deployment](#terraform-deployment)
6. [Manual Cloud Run Deployment](#manual-cloud-run-deployment)
7. [CI/CD Pipeline Setup](#cicd-pipeline-setup)
8. [Verification & Testing](#verification--testing)
9. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Check versions
python --version        # 3.9+
node --version         # 18+
npm --version          # 8+
gcloud --version       # 400+
terraform --version    # 1.0+
docker --version       # 20.10+
```

### GCP Permissions Required

Ensure your GCP account has these roles:
- `roles/owner` or
- `roles/iam.securityAdmin`
- `roles/run.admin`
- `roles/iam.serviceAccountAdmin`
- `roles/secretmanager.admin`
- `roles/compute.admin`
- `roles/storage.admin`

### GitHub Setup

- Repository: https://github.com/raghu-1718/InfinityAI.Pro
- Collaborators with push access
- GitHub Secrets configured (see [CI/CD Pipeline Setup](#cicd-pipeline-setup))

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/raghu-1718/InfinityAI.Pro.git
cd InfinityAI.Pro
git checkout main
```

### 2. Setup Backend Engines

```bash
# Engine Core
cd backend/engine-core
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../../config/env/dev/engine-core.env.example .env

# Engine Analytics
cd ../engine-analytics
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../../config/env/dev/engine-analytics.env.example .env

# Engine Execution
cd ../engine-execution
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../../config/env/dev/engine-execution.env.example .env
```

### 3. Setup Frontend

```bash
cd frontend/web
npm install
cp ../../config/env/dev/firebase.env.example .env.development

# Update .env.development with local backend URLs:
# VITE_API_ENGINE_CORE=http://localhost:8000
# VITE_API_ENGINE_ANALYTICS=http://localhost:8001
# VITE_API_ENGINE_EXECUTION=http://localhost:8002
# VITE_WS_ENGINE_EXECUTION=ws://localhost:8002
```

### 4. Run Locally (Docker Compose)

```bash
# From project root
docker-compose -f docker-compose.engines.yml up -d

# Wait for startup
sleep 10

# Verify health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Run frontend
cd frontend/web && npm run dev
# Open http://localhost:5173
```

---

## GCP Project Setup

### 1. Authenticate with GCP

```bash
gcloud auth login
gcloud config set project after-yesterday-473512-k3
gcloud auth application-default login
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  firebase.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  compute.googleapis.com \
  storage-api.googleapis.com
```

### 3. Create Service Account (if not exists)

```bash
# Create service account
gcloud iam service-accounts create infinityai-deployment \
  --display-name="InfinityAI Deployment"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member=serviceAccount:infinityai-deployment@after-yesterday-473512-k3.iam.gserviceaccount.com \
  --role=roles/run.admin

# Grant Secret Manager access
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member=serviceAccount:infinityai-deployment@after-yesterday-473512-k3.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Grant Firestore access
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member=serviceAccount:infinityai-deployment@after-yesterday-473512-k3.iam.gserviceaccount.com \
  --role=roles/datastore.user
```

### 4. Create Service Account Key

```bash
gcloud iam service-accounts keys create ~/gcp-key.json \
  --iam-account=infinityai-deployment@after-yesterday-473512-k3.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/gcp-key.json"
```

---

## Secrets Management

### 1. Create Secrets in Secret Manager

```bash
# Dhan broker credentials
echo -n "YOUR_DHAN_API_KEY" | gcloud secrets create dhan-api-key \
  --data-file=-

echo -n "YOUR_DHAN_CLIENT_SECRET" | gcloud secrets create dhan-client-secret \
  --data-file=-

# Gemini API key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
  --data-file=-

# JWT secret
echo -n "YOUR_JWT_SECRET_KEY" | gcloud secrets create jwt-secret-key \
  --data-file=-

# Firebase config
cat <<EOF | gcloud secrets create firebase-config --data-file=-
{
  "apiKey": "YOUR_API_KEY",
  "authDomain": "YOUR_AUTH_DOMAIN",
  "projectId": "after-yesterday-473512-k3",
  "storageBucket": "YOUR_STORAGE_BUCKET",
  "messagingSenderId": "YOUR_MESSAGING_SENDER_ID",
  "appId": "YOUR_APP_ID"
}
EOF
```

### 2. Grant Service Account Access to Secrets

```bash
# For each secret
for secret in dhan-api-key dhan-client-secret gemini-api-key jwt-secret-key firebase-config; do
  gcloud secrets add-iam-policy-binding $secret \
    --member=serviceAccount:infinityai-deployment@after-yesterday-473512-k3.iam.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
done
```

### 3. Verify Secrets

```bash
gcloud secrets list --format="table(name,created)"
gcloud secrets versions list dhan-api-key
```

---

## Terraform Deployment

### 1. Initialize Terraform

```bash
cd infra/gcp
terraform init

# Verify state
terraform state list
```

### 2. Create terraform.tfvars

```bash
cat > terraform.tfvars <<EOF
project_id = "after-yesterday-473512-k3"
region = "us-central1"
environment = "production"

# Service configurations
engine_core_memory = "512Mi"
engine_core_cpu = "1"

engine_analytics_memory = "1Gi"
engine_analytics_cpu = "2"

engine_execution_memory = "512Mi"
engine_execution_cpu = "1"

# Database
db_user = "infinityai"
db_password = "$(gcloud secrets versions access latest --secret=db-password)"
db_instance = "infinityai-db"

# Secrets
secrets = {
  dhan_api_key = "projects/after-yesterday-473512-k3/secrets/dhan-api-key/versions/latest"
  dhan_client_secret = "projects/after-yesterday-473512-k3/secrets/dhan-client-secret/versions/latest"
  gemini_api_key = "projects/after-yesterday-473512-k3/secrets/gemini-api-key/versions/latest"
  jwt_secret_key = "projects/after-yesterday-473512-k3/secrets/jwt-secret-key/versions/latest"
}
EOF
```

### 3. Plan Deployment

```bash
terraform plan -var-file=terraform.tfvars -out=tfplan
```

### 4. Apply Configuration

```bash
terraform apply tfplan

# Verify
terraform show
gcloud run services list --region us-central1
```

---

## Manual Cloud Run Deployment

Alternative to Terraform (if needed):

### 1. Build Engine Core

```bash
cd backend/engine-core

# Build image
gcloud builds submit \
  --tag gcr.io/after-yesterday-473512-k3/engine-core:latest \
  .

# Deploy to Cloud Run
gcloud run deploy engine-core \
  --image gcr.io/after-yesterday-473512-k3/engine-core:latest \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars="FIRESTORE_PROJECT=after-yesterday-473512-k3,ENVIRONMENT=production"
```

### 2. Build Engine Analytics

```bash
cd backend/engine-analytics

gcloud builds submit \
  --tag gcr.io/after-yesterday-473512-k3/engine-analytics:latest \
  .

gcloud run deploy engine-analytics \
  --image gcr.io/after-yesterday-473512-k3/engine-analytics:latest \
  --region us-central1 \
  --memory 1Gi \
  --cpu 2 \
  --allow-unauthenticated \
  --set-env-vars="FIRESTORE_PROJECT=after-yesterday-473512-k3,ENVIRONMENT=production"
```

### 3. Build Engine Execution

```bash
cd backend/engine-execution

gcloud builds submit \
  --tag gcr.io/after-yesterday-473512-k3/engine-execution:latest \
  .

gcloud run deploy engine-execution \
  --image gcr.io/after-yesterday-473512-k3/engine-execution:latest \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars="FIRESTORE_PROJECT=after-yesterday-473512-k3,ENVIRONMENT=production"
```

### 4. Deploy Frontend

```bash
cd frontend/web

# Build
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting
```

---

## CI/CD Pipeline Setup

### 1. GitHub Secrets Configuration

Add these secrets in GitHub repository settings (Settings > Secrets and variables > Actions):

```
GCP_PROJECT_ID=after-yesterday-473512-k3
GCP_SERVICE_ACCOUNT_KEY=<content of ~/gcp-key.json>
GCP_REGION=us-central1
DHAN_CLIENT_ID=<from Dhan dashboard>
DHAN_CLIENT_SECRET=<from Secret Manager>
GEMINI_API_KEY=<from Secret Manager>
JWT_SECRET_KEY=<from Secret Manager>
FIREBASE_CONFIG=<from Secret Manager>
```

### 2. Configure GitHub Actions Workflows

All workflows located in `.github/workflows/`:

- `test.yml`: Runs on PR, branch push
- `deploy-staging.yml`: Runs on push to `develop` branch
- `deploy-prod.yml`: Runs on push to `main` branch
- `health-check.yml`: Runs every 5 minutes (scheduled)

### 3. Verify Workflows

```bash
# View workflow status
gh workflow list

# Manually trigger workflow
gh workflow run health-check.yml

# View run status
gh run list
```

---

## Verification & Testing

### 1. Local Verification

```bash
cd verification/suite

# Install test dependencies
pip install -r requirements-test.txt

# Run development environment checks
python infinityai_verification_suite.py --environment development
```

### 2. Production Verification

```bash
cd verification/suite

# Run production checks (requires GCP credentials)
python infinityai_verification_suite.py --environment production

# Check specific engine
pytest checks/check_engine_core.py -v
```

### 3. Check Deployment Status

```bash
# List all deployed services
gcloud run services list --region us-central1

# Check service details
gcloud run services describe engine-core --region us-central1

# Test service endpoints
curl https://infinityai-engine-core-{hash}.a.run.app/health
curl https://infinityai-engine-analytics-{hash}.a.run.app/health
curl https://infinityai-engine-execution-{hash}.a.run.app/health
```

---

## Monitoring & Troubleshooting

### 1. View Logs

```bash
# Real-time logs
gcloud run services log read engine-core --follow

# Last 50 lines
gcloud run services log read engine-core --limit 50

# Filter by severity
gcloud run services log read engine-core \
  --filter='severity>=ERROR' \
  --limit 20
```

### 2. Monitor Performance

```bash
# Cloud Run metrics
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision"'

# View in Cloud Console
# https://console.cloud.google.com/run
```

### 3. Common Issues & Fixes

#### Service fails to deploy

```bash
# Check Cloud Build logs
gcloud builds log <BUILD_ID> --stream

# Verify service account permissions
gcloud projects get-iam-policy after-yesterday-473512-k3 \
  --flatten="bindings[].members" \
  --filter="bindings.members:infinityai-deployment*"
```

#### Health check fails (404)

```bash
# Verify PORT environment variable
gcloud run services describe engine-core \
  --format='value(spec.template.spec.containers[0].env[].name)' \
  | grep PORT

# Check service startup logs
gcloud run services log read engine-core --limit 30
```

#### Firestore permission denied

```bash
# Verify service account has Datastore role
gcloud projects get-iam-policy after-yesterday-473512-k3 \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/datastore.user"

# Grant if missing
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member=serviceAccount:infinityai-deployment@after-yesterday-473512-k3.iam.gserviceaccount.com \
  --role=roles/datastore.user
```

#### WebSocket connection fails

```bash
# Check Cloud Run memory allocation (min 512Mi for WebSocket)
gcloud run services describe engine-execution \
  --format='value(spec.template.spec.containers[0].resources.limits.memory)'

# Update if needed
gcloud run deploy engine-execution \
  --update-env-vars=ENVIRONMENT=production \
  --memory=1Gi
```

### 4. Scaling Configuration

```bash
# Set minimum instances
gcloud run services update engine-core \
  --min-instances=1

# Set maximum instances
gcloud run services update engine-core \
  --max-instances=10

# Set concurrency
gcloud run services update engine-core \
  --concurrency=80
```

---

## Post-Deployment Checklist

- [ ] All 3 engines health endpoints return 200
- [ ] Frontend loads at https://infinityai.pro
- [ ] WebSocket connects successfully
- [ ] Firestore read/write working
- [ ] Firebase authentication functional
- [ ] Market data flowing to Firestore
- [ ] AI signals being generated
- [ ] Orders can be placed and tracked
- [ ] Health checks passing (CI/CD job)
- [ ] Monitoring and alerts configured
- [ ] Logs visible in Cloud Logging
- [ ] DNS records updated (if domain changed)
- [ ] SSL certificates valid

---

## Rollback Procedure

If deployment fails:

```bash
# Revert to previous Cloud Run revision
gcloud run services update-traffic engine-core \
  --to-revisions=<PREVIOUS_REVISION_ID>=100%

# Revert code
git revert <COMMIT_HASH>
git push origin main  # Triggers automatic redeploy

# Or rebuild from known-good image tag
gcloud run deploy engine-core \
  --image gcr.io/after-yesterday-473512-k3/engine-core:v1.0.0
```

---

## Disaster Recovery

### Backup Firestore

```bash
# Export Firestore database
gcloud firestore export gs://infinityai-backup/$(date +%Y%m%d)
```

### Restore Firestore

```bash
# Import from backup
gcloud firestore import gs://infinityai-backup/YYYYMMDD/
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Maintainer**: InfinityAI Team
