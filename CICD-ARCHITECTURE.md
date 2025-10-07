# 🏗️ InfinityAI.Pro CI/CD Architecture

## Deployment Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitHub Repository                                │
│                  raghu-1718/InfinityAI.Pro                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Push to main/develop
                         │ or Manual Trigger
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   GitHub Actions Workflow                            │
│           .github/workflows/multi-cloud-cicd.yml                    │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         │ Step 1: Build & Test
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  📦 Build & Test Job (Ubuntu Runner)                                │
│  ├─ Checkout code                                                   │
│  ├─ Install Node.js dependencies                                    │
│  ├─ Build React frontend (npm run build)                           │
│  ├─ Run tests (pytest, optional)                                    │
│  └─ Code quality checks (flake8, optional)                         │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         │ On Success
                         ▼
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐     ┌────────┐     ┌────────┐
    │ Azure  │     │  GCP   │     │  AWS   │
    │ Deploy │     │ Deploy │     │ Deploy │
    └────────┘     └────────┘     └────────┘
         │               │               │
         │               │               │
         ▼               ▼               ▼

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  ☁️ AZURE       │ │  🌐 GOOGLE CLOUD │ │  🟠 AWS         │
│  Container Apps  │ │  Cloud Run       │ │  ECS Fargate    │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│                  │ │                  │ │                  │
│ 1. ACR Login     │ │ 1. GCloud Auth   │ │ 1. ECR Login     │
│ 2. Build Image   │ │ 2. Build Image   │ │ 2. Build Images  │
│ 3. Push to ACR   │ │ 3. Push to GCR   │ │ 3. Push to ECR   │
│ 4. Deploy App    │ │ 4. Deploy to Run │ │ 4. Update Tasks  │
│ 5. Health Check  │ │ 5. Health Check  │ │ 5. Deploy ECS    │
│                  │ │                  │ │                  │
│ Deployed:        │ │ Deployed:        │ │ Deployed:        │
│ • Frontend       │ │ • Engine B       │ │ • Engine C       │
│ • Engine A       │ │   (AI/ML)        │ │   (Trading)      │
│ • Main Backend   │ │                  │ │ • Engine D       │
│                  │ │                  │ │   (Voice)        │
└──────────────────┘ └──────────────────┘ └──────────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  🧪 Integration Tests                                               │
│  ├─ Test Azure endpoints                                            │
│  ├─ Test GCP endpoints                                              │
│  ├─ Test AWS endpoints                                              │
│  ├─ Test cross-cloud communication                                  │
│  └─ Verify Dhan API integration                                     │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ✅ Deployment Complete                                             │
│  Live URLs:                                                          │
│  • https://infinityai-app.agreeablemeadow-7375b1f7.eastus...       │
│  • https://engine-b-service.run.app                                 │
│  • https://infinityai-pro-alb.us-east-1.elb.amazonaws.com          │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 🎯 Engines Distribution

| Engine | Cloud | Purpose | Technology |
|--------|-------|---------|------------|
| **Frontend + Engine A** | Azure Container Apps | Main UI & Primary API | React + FastAPI |
| **Engine B** | Google Cloud Run | AI/ML Processing | Python + TensorFlow |
| **Engine C** | AWS ECS | Trading & Execution | Python + FastAPI |
| **Engine D** | AWS ECS | Voice Assistant | Python + Speech APIs |

### 🔄 Workflow Stages

#### Stage 1: Build & Test (3-5 minutes)
- Checkout repository code
- Install dependencies (npm, pip)
- Build React frontend production bundle
- Run unit tests (if available)
- Run linting/code quality checks

#### Stage 2: Deploy to Azure (5-8 minutes)
- Authenticate with Azure using Service Principal
- Login to Azure Container Registry (ACR)
- Build unified Docker image (frontend + backend)
- Push image to ACR with version tags
- Update Container App with new image
- Configure environment variables (Dhan credentials)
- Verify deployment health

#### Stage 3: Deploy to GCP (4-6 minutes)
- Authenticate with Google Cloud using Service Account
- Configure Docker for Google Container Registry
- Build Engine B Docker image
- Push to GCR with version tags
- Deploy to Cloud Run (serverless)
- Set environment variables
- Verify deployment health

#### Stage 4: Deploy to AWS (5-10 minutes)
- Configure AWS credentials
- Login to Elastic Container Registry (ECR)
- Build Engine C & D Docker images
- Push images to ECR
- Register new ECS task definitions
- Update ECS services (Fargate)
- Wait for service stability

#### Stage 5: Integration Tests (1-2 minutes)
- Test all health endpoints
- Verify cross-cloud communication
- Test Dhan API integration
- Generate deployment summary

### 🔐 Required Secrets

| Secret | Used By | Purpose |
|--------|---------|---------|
| `AZURE_CREDENTIALS` | Azure Deploy | Service Principal authentication |
| `AZURE_REGISTRY_USERNAME` | Azure Deploy | ACR access |
| `AZURE_REGISTRY_PASSWORD` | Azure Deploy | ACR credentials |
| `AZURE_APP_URL` | Integration Tests | Health check endpoint |
| `AWS_ACCESS_KEY_ID` | AWS Deploy | IAM authentication |
| `AWS_SECRET_ACCESS_KEY` | AWS Deploy | IAM credentials |
| `GCP_SERVICE_ACCOUNT_KEY` | GCP Deploy | Service account auth |
| `DHAN_*` (optional) | All engines | Trading API integration |

### 🚀 Trigger Conditions

The workflow runs when:
1. **Push to `main` branch** - Automatic production deployment
2. **Push to `develop` branch** - Automatic staging deployment
3. **Pull Request to `main`** - Build & test only (no deployment)
4. **Manual Trigger** - Via GitHub Actions UI

### 📊 Success Metrics

- ✅ All jobs complete with exit code 0
- ✅ Health checks return HTTP 200
- ✅ Docker images successfully pushed to all registries
- ✅ Services show "Running" status in cloud consoles
- ✅ No error messages in deployment logs

### 🔧 Rollback Strategy

If deployment fails:
1. Previous container versions remain running
2. No downtime for existing services
3. Fix issues and re-trigger deployment
4. Or manually rollback in cloud console:
   - Azure: `az containerapp revision list` → activate previous
   - GCP: Cloud Run revisions tab → rollback
   - AWS: Update service to previous task definition

### 🎯 Deployment Time

| Phase | Duration |
|-------|----------|
| Build & Test | 3-5 min |
| Azure Deploy | 5-8 min |
| GCP Deploy | 4-6 min |
| AWS Deploy | 5-10 min |
| Integration Tests | 1-2 min |
| **Total** | **~20-30 min** |

### 🌍 Geographic Distribution

- **Azure**: East US (Primary region)
- **GCP**: US-Central1 (AI processing)
- **AWS**: US-East-1 (Trading & voice)

### 📈 Auto-Scaling

- **Azure**: Automatic scaling 1-10 replicas
- **GCP**: Serverless auto-scaling (0-1000 instances)
- **AWS**: ECS Fargate auto-scaling 1-5 tasks

## Quick Start

```bash
# 1. Validate setup
./validate-cicd-setup.sh

# 2. Configure secrets in GitHub
# See: SECRETS-QUICK-REFERENCE.md

# 3. Trigger deployment
git push origin main

# 4. Monitor in GitHub Actions tab
# Watch real-time deployment progress
```

For detailed setup: See [QUICK-START-CICD.md](QUICK-START-CICD.md)
