# 🔐 GitHub Secrets Quick Reference

Add these secrets to: `https://github.com/raghu-1718/InfinityAI.Pro/settings/secrets/actions`

## Required Secrets Checklist

### ☁️ Azure (4 secrets)
- [ ] `AZURE_CREDENTIALS` - Azure Service Principal JSON
- [ ] `AZURE_REGISTRY_USERNAME` - infinityaiacr
- [ ] `AZURE_REGISTRY_PASSWORD` - Your ACR password
- [ ] `AZURE_APP_URL` - https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io

### ☁️ AWS (2 secrets)
- [ ] `AWS_ACCESS_KEY_ID` - Your AWS access key
- [ ] `AWS_SECRET_ACCESS_KEY` - Your AWS secret key

### ☁️ Google Cloud (1 secret)
- [ ] `GCP_SERVICE_ACCOUNT_KEY` - Service account JSON key

### 🔑 Dhan Trading API (4 secrets - Optional)
- [ ] `DHAN_CLIENT_ID` - 1101302170
- [ ] `DHAN_ACCESS_TOKEN` - Your Dhan access token
- [ ] `DHAN_API_KEY` - Your Dhan API key
- [ ] `DHAN_API_SECRET` - Your Dhan API secret

## Total Secrets Needed
- **Minimum (for deployment)**: 7 secrets (Azure + AWS + GCP)
- **Full (with trading)**: 11 secrets (All above)

## Quick Setup Commands

### Get Azure Credentials
```bash
# Login to Azure
az login

# Create Service Principal (save output as AZURE_CREDENTIALS)
az ad sp create-for-rbac --name "InfinityAI-CI-CD" \
  --role contributor \
  --scopes /subscriptions/62fc147a-2efc-4494-be1f-faa521439799 \
  --sdk-auth

# Get ACR password (use as AZURE_REGISTRY_PASSWORD)
az acr credential show --name infinityaiacr --query "passwords[0].value" -o tsv
```

### Get AWS Credentials
```bash
# Use AWS Console or CLI to create IAM user with:
# - AmazonEC2ContainerRegistryFullAccess
# - AmazonECS_FullAccess
# Save Access Key ID and Secret Access Key
```

### Get GCP Credentials
```bash
# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project after-yesterday-473512-k3

# Create service account
gcloud iam service-accounts create infinityai-cicd \
  --display-name="InfinityAI CI/CD"

# Grant permissions
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
  --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key (use as GCP_SERVICE_ACCOUNT_KEY)
gcloud iam service-accounts keys create key.json \
  --iam-account=infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com

# Copy the contents of key.json as the secret value
cat key.json
```

## Verification

After adding all secrets, verify in GitHub:
1. Go to `Settings` → `Secrets and variables` → `Actions`
2. You should see all the secrets listed (values are hidden)
3. Secrets are ready when the count matches your checklist

## Next Steps

Once secrets are configured:
1. Go to the **Actions** tab
2. Enable workflows if not already enabled
3. Push a commit to `main` branch to trigger deployment
4. Monitor the workflow execution in the Actions tab

---

**Security Note**: Never share or commit these credentials. They provide full access to your cloud resources.
