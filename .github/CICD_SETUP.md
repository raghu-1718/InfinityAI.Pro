# CI/CD Setup Guide for Trading Signals Functions

This guide explains how to set up automated deployment for the trading signals Cloud Functions.

## Prerequisites

1. **GitHub Repository** with the InfinityAI.Pro codebase
2. **Google Cloud Project** (galvanic-pulsar-482815-h0)
3. **Workload Identity Federation** configured for GitHub Actions

## Setup Steps

### 1. Configure Workload Identity Federation

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-actions-pool" \
  --project="galvanic-pulsar-482815-h0" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="galvanic-pulsar-482815-h0" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create Service Account for GitHub Actions
gcloud iam service-accounts create github-actions-deployer \
  --project="galvanic-pulsar-482815-h0" \
  --display-name="GitHub Actions Deployer"

# Grant necessary permissions
gcloud projects add-iam-policy-binding galvanic-pulsar-482815-h0 \
  --member="serviceAccount:github-actions-deployer@galvanic-pulsar-482815-h0.iam.gserviceaccount.com" \
  --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding galvanic-pulsar-482815-h0 \
  --member="serviceAccount:github-actions-deployer@galvanic-pulsar-482815-h0.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Allow GitHub to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deployer@galvanic-pulsar-482815-h0.iam.gserviceaccount.com \
  --project="galvanic-pulsar-482815-h0" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/YOUR_GITHUB_USERNAME/InfinityAI.Pro"
```

### 2. Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

- **GCP_WORKLOAD_IDENTITY_PROVIDER**:

  ```
  projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
  ```

- **GCP_SERVICE_ACCOUNT**:
  ```
  github-actions-deployer@galvanic-pulsar-482815-h0.iam.gserviceaccount.com
  ```

### 3. Test the Workflow

```bash
# Make a change to functions/trading-signals/main.py
# Commit and push to main branch
git add functions/trading-signals/
git commit -m "feat: update trading signals logic"
git push origin main

# Or trigger manually from GitHub Actions UI
```

### 4. Monitor Deployment

- Go to GitHub Actions tab in your repository
- Watch the "Deploy Trading Signals Functions" workflow
- Check logs for any errors

## Deployment Settings

The workflow is configured to:

- Deploy on pushes to `main` branch that modify `functions/trading-signals/**`
- Can be manually triggered via `workflow_dispatch`
- Uses Python 3.12 runtime
- Deploys to `asia-south1` region

## Function Configurations

### detect-momentum-signals

- Max instances: 3
- Memory: 512MB
- Timeout: 300s

### get-latest-signals

- Max instances: 6
- Memory: 256MB
- Timeout: 60s

## Troubleshooting

### Permission Denied

- Verify service account has `cloudfunctions.developer` role
- Check Workload Identity binding is correct

### Deployment Timeout

- Increase timeout in workflow file
- Check function dependencies in requirements.txt

### Function Not Found After Deployment

- Verify entry point names match function names
- Check deployment logs for errors
