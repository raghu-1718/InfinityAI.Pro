# ⚡ Quick Start: Enable CI/CD in 5 Minutes

Follow these steps to enable automated deployment to Azure, AWS, and Google Cloud.

## ✅ Pre-Deployment Checklist

### Step 1: Validate Setup (30 seconds)
```bash
./validate-cicd-setup.sh
```
**Expected Result:** All checks should pass ✅

### Step 2: Configure GitHub Secrets (3 minutes)

Go to: https://github.com/raghu-1718/InfinityAI.Pro/settings/secrets/actions

**Add these 7 required secrets:**

| Secret Name | Where to Get It | Required? |
|------------|----------------|-----------|
| `AZURE_CREDENTIALS` | Run: `az ad sp create-for-rbac --sdk-auth` | ✅ Yes |
| `AZURE_REGISTRY_USERNAME` | Value: `infinityaiacr` | ✅ Yes |
| `AZURE_REGISTRY_PASSWORD` | Run: `az acr credential show --name infinityaiacr` | ✅ Yes |
| `AZURE_APP_URL` | Your Azure app URL | ✅ Yes |
| `AWS_ACCESS_KEY_ID` | AWS IAM Console → Create user | ✅ Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM Console → Access key | ✅ Yes |
| `GCP_SERVICE_ACCOUNT_KEY` | Run: `gcloud iam service-accounts keys create` | ✅ Yes |

**Optional secrets (for trading features):**
- `DHAN_CLIENT_ID`
- `DHAN_ACCESS_TOKEN` 
- `DHAN_API_KEY`
- `DHAN_API_SECRET`

📖 **Detailed instructions:** See [SECRETS-QUICK-REFERENCE.md](SECRETS-QUICK-REFERENCE.md)

### Step 3: Enable GitHub Actions (30 seconds)
1. Go to your repository's **Actions** tab
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. You should see the workflow: **🚀 InfinityAI.Pro Multi-Cloud CI/CD Pipeline**

### Step 4: Test Deployment (1 minute)

**Option A: Manual Trigger (Recommended for first run)**
1. Go to Actions → Select the CI/CD workflow
2. Click **"Run workflow"** button
3. Select branch: `main`
4. Click **"Run workflow"**
5. Watch the deployment progress in real-time

**Option B: Automatic Trigger**
```bash
git add .
git commit -m "🚀 Test CI/CD deployment"
git push origin main
```

## 📊 Monitor Deployment

### In GitHub
1. Go to **Actions** tab
2. Click on the running workflow
3. Expand each job to see detailed logs

### Deployment Jobs
- ✅ **Build & Test** - Validates code and builds artifacts
- ☁️ **Deploy to Azure** - Deploys frontend and Engine A
- 🌐 **Deploy to GCP** - Deploys Engine B (AI processing)
- 🟠 **Deploy to AWS** - Deploys Engines C & D (Trading & Voice)
- 🧪 **Integration Tests** - Validates all services

## 🎯 Expected Timeline

| Phase | Duration | What Happens |
|-------|----------|--------------|
| Build & Test | 3-5 min | Code validation, npm install, docker builds |
| Azure Deploy | 5-8 min | Container build & deploy to Azure |
| GCP Deploy | 4-6 min | Container build & deploy to Google Cloud |
| AWS Deploy | 5-10 min | Multi-container deploy to ECS |
| Integration Tests | 1-2 min | Health checks across all clouds |
| **Total** | **~20-30 min** | Complete multi-cloud deployment |

## ✅ Verify Deployment Success

### Check Deployment Status
All jobs should show green checkmarks ✅ in the Actions tab.

### Test Your Deployed Services

**Azure (Engine A):**
```bash
curl https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health
```

**Expected:** `{"status": "healthy"}` or HTTP 200

**GCP (Engine B):**
```bash
# Get URL from Cloud Run console or workflow logs
gcloud run services describe infinityai-engine-b --region=us-central1 --format='value(status.url)'
```

**AWS (Engines C & D):**
```bash
# Check ECS console for service status
aws ecs describe-services --cluster infinityai-cluster --services infinityai-engine-c-service
```

## 🔧 Troubleshooting

### Deployment Fails at Build Step
- **Check:** Package.json and requirements.txt are present
- **Fix:** Ensure all dependencies are correctly specified

### Deployment Fails at Azure Login
- **Check:** `AZURE_CREDENTIALS` secret is valid JSON
- **Fix:** Re-create service principal with correct permissions

### Deployment Fails at Docker Push
- **Check:** Registry credentials are correct
- **Fix:** Verify `AZURE_REGISTRY_PASSWORD`, `AWS_ACCESS_KEY_ID`, etc.

### Need Help?
1. Check workflow logs in Actions tab (detailed error messages)
2. Review [CI-CD-SETUP-GUIDE.md](CI-CD-SETUP-GUIDE.md) for detailed troubleshooting
3. Verify all secrets are configured correctly

## 🎉 Success Indicators

✅ All workflow jobs completed successfully  
✅ Green checkmarks in GitHub Actions  
✅ Services respond to health checks  
✅ No error messages in logs  

## 🚀 Next Steps After Successful Deployment

1. **Set up custom domain** (optional)
2. **Configure monitoring & alerts**
3. **Enable auto-scaling** for production traffic
4. **Set up staging environment** (use `develop` branch)

---

**🎊 Congratulations! Your InfinityAI.Pro platform is now automatically deployed to Azure, AWS, and Google Cloud!**

Every push to `main` will trigger automatic deployment. Changes go live in ~20-30 minutes.
