# infra/ci-cd/README.md

## Continuous Integration & Deployment (CI/CD)

This directory contains GitHub Actions workflows, deployment scripts, and build configuration for automating InfinityAI.Pro deployment pipeline.

### Directory Structure

```
ci-cd/
├── github/
│   └── workflows/      # GitHub Actions workflow YAML files
├── scripts/            # Shell/Python helper scripts for deployment
├── cloudbuild.yaml     # Google Cloud Build configuration
└── README.md           # This file
```

### GitHub Actions Workflows

Workflows automatically trigger on:

1. **Push to main/master**: Deploy to production
2. **Push to feature branch**: Run tests and linting
3. **Pull request**: Run unit tests and security checks
4. **Manual dispatch**: Trigger health checks, deployments

### Automated Workflows

#### Build & Test (`test.yml`)
- Runs on: Pull requests, feature branch pushes
- Actions: Lint, unit tests (pytest, jest), security scans

#### Deploy to Staging (`deploy-staging.yml`)
- Runs on: Push to `develop` branch
- Actions: Build engines, deploy to staging Cloud Run, run E2E tests

#### Deploy to Production (`deploy-prod.yml`)
- Runs on: Push to `main` branch
- Actions: Build engines, deploy to production Cloud Run, run smoke tests, notify team

#### Health Check (`health-check.yml`)
- Runs on: Schedule (every 5 minutes), manual dispatch
- Actions: Check `/health` endpoints, Firestore availability, Firebase Hosting, alert on failure

### Deployment Scripts

```bash
# Deploy single engine to Cloud Run
./infra/ci-cd/scripts/deploy-engine.sh engine-core

# Deploy all engines
./infra/ci-cd/scripts/deploy-all-engines.sh

# Run health checks
./infra/ci-cd/scripts/health-check.sh

# Automated daily verification
./infra/ci-cd/scripts/daily-verification.sh
```

### GitHub Secrets Required

All secrets must be configured in GitHub repository settings under **Settings > Secrets and variables > Actions**:

- `GCP_PROJECT_ID`: `after-yesterday-473512-k3`
- `GCP_SERVICE_ACCOUNT_KEY`: JSON key for Cloud Build and Cloud Run deployment
- `DHAN_CLIENT_ID`, `DHAN_CLIENT_SECRET`: Dhan broker OAuth credentials
- `GEMINI_API_KEY`: Google Gemini API key
- `JWT_SECRET_KEY`: JWT signing secret
- `FIREBASE_CONFIG`: Firebase web SDK configuration (JSON)
- `SLACK_WEBHOOK_URL`: (Optional) Slack notifications on deployment

### Manual Deployment

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project after-yesterday-473512-k3

# Build and push Engine Core
docker build -t gcr.io/after-yesterday-473512-k3/engine-core:latest backend/engine-core/
docker push gcr.io/after-yesterday-473512-k3/engine-core:latest
gcloud run deploy engine-core --image gcr.io/after-yesterday-473512-k3/engine-core:latest --region us-central1

# Repeat for engine-analytics and engine-execution
```

### Troubleshooting CI/CD

- **Workflow not triggering**: Check branch protection rules and event filters in workflow YAML
- **Build fails**: Review Cloud Build logs: `gcloud builds log --stream [BUILD_ID]`
- **Deploy fails**: Check Cloud Run service quota and IAM permissions
- **Secrets not available**: Verify secrets exist in GitHub Actions settings (not git-committed)
