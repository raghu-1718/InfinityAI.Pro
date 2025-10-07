# 🔧 CI/CD Troubleshooting Guide

Common issues and solutions for InfinityAI.Pro multi-cloud deployment.

## 🚨 Common Issues

### 1. Workflow Not Triggering

**Symptoms:**
- Push to main branch but no workflow runs
- Actions tab shows no activity

**Solutions:**
```bash
# Check if GitHub Actions is enabled
1. Go to repository Settings → Actions → General
2. Ensure "Allow all actions and reusable workflows" is selected
3. Save if changed

# Verify workflow file location
ls -la .github/workflows/multi-cloud-cicd.yml
# Must be at repository root in .github/workflows/

# Manually trigger workflow
1. Go to Actions tab
2. Select "🚀 InfinityAI.Pro Multi-Cloud CI/CD Pipeline"
3. Click "Run workflow"
```

### 2. Build & Test Job Fails

#### Error: "npm install failed"
```bash
# Solution 1: Check package.json exists
cd infinityai-pro/frontend
cat package.json

# Solution 2: Check for package-lock.json
# If missing, workflow will use 'npm ci' which requires lock file
# Change to 'npm install' in workflow if needed
```

#### Error: "pytest not found" or "flake8 failed"
```bash
# These are optional checks
# Workflow continues even if they fail
# To fix:
cd infinityai-pro/backend
pip install pytest flake8
pytest tests/ -v
```

#### Error: "Docker build failed"
```bash
# Check Dockerfile exists
ls infinityai-pro/Dockerfile

# Test Docker build locally
cd infinityai-pro
docker build -t test-build .
```

### 3. Azure Deployment Fails

#### Error: "Azure login failed"
```bash
# Check AZURE_CREDENTIALS secret
# Must be valid JSON from: az ad sp create-for-rbac --sdk-auth

# Recreate Service Principal
az ad sp create-for-rbac --name "InfinityAI-CI-CD" \
  --role contributor \
  --scopes /subscriptions/62fc147a-2efc-4494-be1f-faa521439799 \
  --sdk-auth

# Copy entire JSON output to AZURE_CREDENTIALS secret
```

#### Error: "ACR login failed"
```bash
# Verify registry credentials
az acr credential show --name infinityaiacr

# Update secrets:
# AZURE_REGISTRY_USERNAME = infinityaiacr
# AZURE_REGISTRY_PASSWORD = (password from command above)
```

#### Error: "Container app update failed"
```bash
# Check if container app exists
az containerapp show --name infinityai-app --resource-group infinityai-pro-rg

# If doesn't exist, create it first:
az containerapp create \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --image infinityaiacr.azurecr.io/infinityai-app:latest \
  --target-port 8000 \
  --ingress external
```

### 4. GCP Deployment Fails

#### Error: "GCP authentication failed"
```bash
# Check GCP_SERVICE_ACCOUNT_KEY secret
# Must be valid JSON service account key

# Recreate service account key
gcloud iam service-accounts keys create key.json \
  --iam-account=infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com

# Copy contents of key.json to GCP_SERVICE_ACCOUNT_KEY secret
cat key.json
```

#### Error: "Permission denied for Cloud Run"
```bash
# Grant required permissions
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

#### Error: "Docker push to GCR failed"
```bash
# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Grant storage admin permission
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### 5. AWS Deployment Fails

#### Error: "AWS credentials invalid"
```bash
# Verify credentials locally
aws sts get-caller-identity

# If fails, recreate IAM user access key:
# 1. AWS Console → IAM → Users → infinityai-cicd
# 2. Security credentials → Create access key
# 3. Update AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY secrets
```

#### Error: "ECR login failed"
```bash
# Check ECR repository exists
aws ecr describe-repositories --region us-east-1

# Create ECR repositories if missing
aws ecr create-repository --repository-name infinityai-engine-c --region us-east-1
aws ecr create-repository --repository-name infinityai-engine-d --region us-east-1
```

#### Error: "ECS service update failed"
```bash
# Check if ECS cluster exists
aws ecs describe-clusters --clusters infinityai-cluster

# Check if service exists
aws ecs describe-services --cluster infinityai-cluster --services infinityai-engine-c-service

# If service doesn't exist, create it:
aws ecs create-service \
  --cluster infinityai-cluster \
  --service-name infinityai-engine-c-service \
  --task-definition infinityai-engine-c \
  --desired-count 1 \
  --launch-type FARGATE
```

#### Error: "Task definition registration failed"
```bash
# Check task definition file exists
ls engine-c-task-def-fixed.json

# Validate JSON syntax
python3 -m json.tool engine-c-task-def-fixed.json

# Register manually to test
aws ecs register-task-definition --cli-input-json file://engine-c-task-def-fixed.json
```

### 6. Integration Tests Fail

#### Error: "Health check failed"
```bash
# Wait for services to fully start (can take 2-5 minutes)
# Then test manually:

# Azure
curl https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health

# If fails, check container logs:
az containerapp logs show --name infinityai-app --resource-group infinityai-pro-rg --tail 50
```

## 🛠️ Debugging Workflow

### View Detailed Logs
1. Go to Actions tab in GitHub
2. Click on failed workflow run
3. Click on failed job
4. Expand failed step to see error details

### Download Workflow Logs
```bash
# Using GitHub CLI
gh run list --workflow=multi-cloud-cicd.yml
gh run view <run-id> --log
```

### Enable Debug Logging
Add these secrets to enable verbose logging:
- `ACTIONS_RUNNER_DEBUG` = `true`
- `ACTIONS_STEP_DEBUG` = `true`

### Test Locally Before Pushing

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/multi-cloud-cicd.yml'))"

# Test Docker builds
cd infinityai-pro
docker build -t test-frontend .

cd backend/engines/engine-b
docker build -t test-engine-b .

cd ../engine-c
docker build -t test-engine-c .

cd ../engine-d
docker build -t test-engine-d .
```

## 📞 Getting Help

### Check These First
1. ✅ Run `./validate-cicd-setup.sh`
2. ✅ Verify all GitHub secrets are configured
3. ✅ Check workflow logs for specific error messages
4. ✅ Ensure cloud provider services are enabled

### Cloud Provider Consoles
- **Azure**: https://portal.azure.com
- **GCP**: https://console.cloud.google.com
- **AWS**: https://console.aws.amazon.com

### Useful Commands

```bash
# Check Azure resources
az containerapp list --resource-group infinityai-pro-rg

# Check GCP resources
gcloud run services list

# Check AWS resources
aws ecs list-services --cluster infinityai-cluster
aws ecs list-tasks --cluster infinityai-cluster
```

## 🔄 Recovery Steps

### Complete Reset (if everything fails)

```bash
# 1. Delete and recreate service principals/accounts
# Azure
az ad sp delete --id <app-id>
az ad sp create-for-rbac --name "InfinityAI-CI-CD-New" --sdk-auth

# GCP
gcloud iam service-accounts delete infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com
gcloud iam service-accounts create infinityai-cicd-new

# AWS
aws iam delete-access-key --user-name infinityai-cicd --access-key-id <old-key>
aws iam create-access-key --user-name infinityai-cicd

# 2. Update all GitHub secrets with new credentials

# 3. Manually trigger workflow
```

### Partial Deployment Recovery

If one cloud fails but others succeed:
1. Fix the failing cloud's credentials
2. Re-run the workflow (it will redeploy all, but that's safe)
3. Or manually deploy to the failed cloud using cloud-specific CLI

## 💡 Best Practices

1. **Test credentials locally before adding to GitHub**
   ```bash
   # Azure
   az login
   az account show
   
   # GCP
   gcloud auth activate-service-account --key-file=key.json
   gcloud projects list
   
   # AWS
   aws sts get-caller-identity
   ```

2. **Use minimal permissions**
   - Only grant necessary roles to service accounts
   - Rotate credentials regularly

3. **Monitor deployments**
   - Watch first few deployments closely
   - Set up cloud monitoring/alerts

4. **Keep secrets updated**
   - Azure tokens expire
   - Rotate AWS keys periodically
   - Update Dhan tokens when they expire

## ✅ Success Checklist

After fixing issues, verify:
- [ ] Workflow triggers on push to main
- [ ] All jobs complete successfully (green checkmarks)
- [ ] Services are accessible via URLs
- [ ] Health endpoints return 200 OK
- [ ] No error messages in logs

---

**Still having issues?** Check the detailed logs in GitHub Actions and cloud provider consoles for specific error messages.
