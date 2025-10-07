# 🚀 InfinityAI.Pro CI/CD Setup Guide

This guide will help you set up automated CI/CD deployment to Azure, Google Cloud Platform (GCP), and Amazon Web Services (AWS).

## 📋 Overview

Your repository is configured with GitHub Actions workflows that automatically deploy to:
- **Azure Container Apps** - Frontend and Engine A
- **Google Cloud Run** - Engine B (AI Processing)
- **AWS ECS** - Engines C & D (Trading and Voice)

## 🔐 Required GitHub Secrets

To enable CI/CD, you need to add the following secrets to your GitHub repository:

### Step 1: Navigate to Repository Secrets
Go to: `https://github.com/raghu-1718/InfinityAI.Pro/settings/secrets/actions`

### Step 2: Add the Following Secrets

#### 🔵 Azure Secrets

```
AZURE_CREDENTIALS
```
Value (JSON format):
```json
{
  "clientId": "YOUR_AZURE_SP_CLIENT_ID",
  "clientSecret": "YOUR_AZURE_SP_SECRET",
  "subscriptionId": "62fc147a-2efc-4494-be1f-faa521439799",
  "tenantId": "YOUR_AZURE_TENANT_ID"
}
```

```
AZURE_REGISTRY_USERNAME
```
Value: `infinityaiacr`

```
AZURE_REGISTRY_PASSWORD
```
Value: `YOUR_ACR_PASSWORD`

```
AZURE_APP_URL
```
Value: `https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io`

#### 🟠 AWS Secrets

```
AWS_ACCESS_KEY_ID
```
Value: `YOUR_AWS_ACCESS_KEY`

```
AWS_SECRET_ACCESS_KEY
```
Value: `YOUR_AWS_SECRET_KEY`

#### 🌐 Google Cloud Secrets

```
GCP_SERVICE_ACCOUNT_KEY
```
Value (JSON format):
```json
{
  "type": "service_account",
  "project_id": "after-yesterday-473512-k3",
  "private_key_id": "YOUR_KEY_ID",
  "private_key": "YOUR_PRIVATE_KEY",
  "client_email": "YOUR_SERVICE_ACCOUNT_EMAIL",
  "client_id": "YOUR_CLIENT_ID",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

#### 🔑 Dhan Production Secrets (Optional - for trading features)

```
DHAN_CLIENT_ID
```
Value: `1101302170`

```
DHAN_ACCESS_TOKEN
```
Value: `YOUR_DHAN_ACCESS_TOKEN`

```
DHAN_API_KEY
```
Value: `YOUR_DHAN_API_KEY`

```
DHAN_API_SECRET
```
Value: `YOUR_DHAN_API_SECRET`

## 🎯 How to Get Your Cloud Credentials

### Azure Credentials

1. **Create a Service Principal:**
   ```bash
   az ad sp create-for-rbac --name "InfinityAI-CI-CD" \
     --role contributor \
     --scopes /subscriptions/62fc147a-2efc-4494-be1f-faa521439799 \
     --sdk-auth
   ```

2. **Get ACR Password:**
   ```bash
   az acr credential show --name infinityaiacr --query "passwords[0].value" -o tsv
   ```

### AWS Credentials

1. **Create IAM User for CI/CD:**
   - Go to AWS IAM Console
   - Create a new user: `infinityai-cicd`
   - Attach policies: `AmazonEC2ContainerRegistryFullAccess`, `AmazonECS_FullAccess`
   - Create Access Key and save the credentials

### Google Cloud Credentials

1. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create infinityai-cicd \
     --display-name="InfinityAI CI/CD"
   ```

2. **Grant Permissions:**
   ```bash
   gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
     --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
     --member="serviceAccount:infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   ```

3. **Create Key:**
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=infinityai-cicd@after-yesterday-473512-k3.iam.gserviceaccount.com
   ```

## 🚀 Activating CI/CD

Once all secrets are configured:

### Option 1: Manual Trigger
1. Go to the **Actions** tab in your GitHub repository
2. Select the **"🚀 InfinityAI.Pro Multi-Cloud CI/CD Pipeline"** workflow
3. Click **"Run workflow"**
4. Select the branch (usually `main`)
5. Click **"Run workflow"**

### Option 2: Automatic Trigger (Recommended)
Simply push changes to the `main` or `develop` branch:

```bash
git add .
git commit -m "🚀 Enable CI/CD deployment"
git push origin main
```

The workflow will automatically:
1. ✅ Build and test the application
2. ☁️ Deploy to Azure Container Apps
3. 🌐 Deploy to Google Cloud Run
4. 🟠 Deploy to AWS ECS
5. 🧪 Run integration tests

## 📊 Monitoring Deployments

### View Deployment Status
- Go to the **Actions** tab in your GitHub repository
- Click on the running workflow to see real-time logs

### Access Deployed Services

After successful deployment, your services will be available at:

- **Azure (Engine A)**: https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io
- **Google Cloud (Engine B)**: Check Cloud Run console for the URL
- **AWS (Engines C & D)**: Check ECS console for the load balancer URL

### Health Checks

Test your deployments:

```bash
# Azure
curl https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health

# Check deployment logs
az containerapp logs show --name infinityai-app --resource-group infinityai-pro-rg
```

## 🔧 Troubleshooting

### Common Issues

1. **Workflow fails during build:**
   - Check that all paths in the Dockerfile are correct
   - Ensure dependencies are properly installed

2. **Authentication errors:**
   - Verify all secrets are correctly configured
   - Check that service accounts have necessary permissions

3. **Deployment fails:**
   - Check cloud provider quotas
   - Verify container registries are accessible
   - Review workflow logs for specific errors

### Getting Help

- Review workflow logs in the Actions tab
- Check individual cloud provider consoles for detailed errors
- Ensure all required services are enabled in each cloud platform

## 🎉 Success!

Once configured, every push to `main` will automatically deploy your application to all three cloud providers, ensuring your InfinityAI.Pro platform is always up-to-date across Azure, GCP, and AWS.

---

**Note:** For security, never commit secrets directly to the repository. Always use GitHub Secrets for sensitive credentials.
