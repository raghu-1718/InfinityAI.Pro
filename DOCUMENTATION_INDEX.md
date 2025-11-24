# Documentation Index - InfinityAI.Pro Restructuring

Complete navigation guide for all project documentation.

---

## 📋 Start Here

**New to the project?**
- 👉 Start with: [`README.md`](README.md) (Project overview)
- Then read: [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) (Common tasks)

**Need to deploy?**
- 👉 Start with: [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) (Step-by-step)

**Want to understand the restructuring?**
- 👉 Start with: [`PHASE1_COMPLETION_SUMMARY.md`](PHASE1_COMPLETION_SUMMARY.md) (What was done)
- Then read: [`RESTRUCTURING_PHASE1_COMPLETE.md`](RESTRUCTURING_PHASE1_COMPLETE.md) (Detailed breakdown)

---

## 📁 Project-Level Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [`README.md`](README.md) | **Project Overview** - Architecture, quick start, features, deployment | Everyone |
| [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) | **Complete Deployment** - GCP setup, Terraform, CI/CD, verification | DevOps, Backend |
| [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) | **Developer Cheat Sheet** - Common commands, troubleshooting, links | Developers |
| [`PHASE1_COMPLETION_SUMMARY.md`](PHASE1_COMPLETION_SUMMARY.md) | **Restructuring Summary** - What was delivered, metrics, next steps | Project Managers |
| [`RESTRUCTURING_PHASE1_COMPLETE.md`](RESTRUCTURING_PHASE1_COMPLETE.md) | **Detailed Restructuring** - Files created, improvements, checklist | Architects |

---

## 🏗️ Backend Documentation

### Architecture Overview
- **Location**: `backend/`
- **Structure**: `engine-{core,analytics,execution}/` + `shared/`
- **Overview**: [`backend/README.md`](backend/) (to be created in Phase 2)

### Individual Engines

#### Engine Core - Market Data Ingestion
- **Location**: `backend/engine-core/`
- **Port**: 8000 (local), Cloud Run (production)
- **Purpose**: NSE/BSE/MCX data aggregation, technical analysis
- **Docs**: [`backend/engine-core/README.md`](backend/engine-core/README.md)
- **Sections**:
  - Setup & environment variables
  - API endpoints (`/api/market-data/`, `/api/symbols/`)
  - Firestore integration
  - Health monitoring
  - Troubleshooting

#### Engine Analytics - ML/AI Signals
- **Location**: `backend/engine-analytics/`
- **Port**: 8001 (local), Cloud Run (production)
- **Purpose**: TensorFlow models, Gemini API, signal generation
- **Docs**: [`backend/engine-analytics/README.md`](backend/engine-analytics/README.md)
- **Sections**:
  - ML models location
  - API endpoints (`/api/ai-signals/`, `/api/predictions/`)
  - Gemini integration
  - Signal format specification
  - Troubleshooting

#### Engine Execution - Trade Execution & WebSocket
- **Location**: `backend/engine-execution/`
- **Port**: 8002 (local), Cloud Run (production)
- **Purpose**: Trade execution, WebSocket aggregation, chatbot (merged from Engine D)
- **Docs**: [`backend/engine-execution/README.md`](backend/engine-execution/README.md)
- **Sections**:
  - Dhan OAuth flow
  - Order management
  - WebSocket real-time feed
  - Chatbot service
  - Risk management rules
  - Multi-engine orchestration
  - Troubleshooting

### Shared Utilities Package
- **Location**: `backend/shared/`
- **Purpose**: Common Python utilities, clients, models
- **Docs**: [`backend/shared/README.md`](backend/shared/README.md)
- **Sections**:
  - Firestore client
  - Secret Manager integration
  - Logging configuration
  - Pydantic models
  - Configuration management
  - Usage examples
  - Contributing guidelines

---

## 🎨 Frontend Documentation

### Frontend - React + Vite + Firebase
- **Location**: `frontend/web/`
- **Port**: 5173 (local), Firebase Hosting (production)
- **Purpose**: Real-time trading dashboard
- **Docs**: [`frontend/web/README.md`](frontend/web/README.md)
- **Sections**:
  - React components architecture
  - WebSocket integration
  - Firebase authentication
  - API client usage
  - Build & deployment
  - Performance optimization
  - Troubleshooting

---

## ☁️ Infrastructure Documentation

### Firebase Configuration
- **Location**: `infra/firebase/`
- **Purpose**: Firestore rules, indexes, storage rules
- **Docs**: [`infra/firebase/README.md`](infra/firebase/README.md)
- **Includes**:
  - Firestore deployment
  - Index configuration
  - Security best practices
  - Storage rules

### Google Cloud Platform (Terraform)
- **Location**: `infra/gcp/`
- **Purpose**: Cloud Run, IAM, networking, secrets infrastructure-as-code
- **Docs**: [`infra/gcp/README.md`](infra/gcp/README.md)
- **Subdirectories**:
  - `cloudrun/` - Cloud Run service definitions
  - `iam/` - IAM roles and service accounts
  - `networking/` - Load balancer, DNS, domain mapping
  - `secrets/` - Secret Manager configuration
- **Includes**:
  - Service deployment info
  - Required secrets list
  - Environment variables
  - Health monitoring
  - Troubleshooting

### CI/CD Pipeline
- **Location**: `infra/ci-cd/`
- **Purpose**: GitHub Actions workflows, deployment automation
- **Docs**: [`infra/ci-cd/README.md`](infra/ci-cd/README.md)
- **Subdirectories**:
  - `github/workflows/` - GitHub Actions YAML files
  - `scripts/` - Bash/Python deployment helpers
- **Includes**:
  - Workflow triggers & automation
  - GitHub secrets configuration
  - Manual deployment procedures
  - CI/CD troubleshooting

---

## ✅ Verification & Testing

### Verification Suite
- **Location**: `verification/suite/`
- **Purpose**: End-to-end testing, health checks, deployment verification
- **Docs**: [`verification/suite/README.md`](verification/suite/README.md)
- **Sections**:
  - Individual check procedures
  - Environment configuration (dev/staging/prod)
  - Running verification suite
  - Output report format
  - CI/CD integration
  - Adding new checks

### Test Reports
- **Location**: `verification/reports/`
- **Subdirectories**:
  - `latest/` - Most recent test results
  - `archive/` - Historical test runs

---

## ⚙️ Configuration

### Environment Variables
- **Location**: `config/env/`
- **Development**: `config/env/dev/`
  - `engine-core.env.example` - Market data engine
  - `engine-analytics.env.example` - ML/AI engine
  - `engine-execution.env.example` - Trade execution
  - `firebase.env.example` - Frontend Firebase setup
- **Production**: `config/env/prod/`
  - Same files with Cloud Run URLs and Secret Manager paths

---

## 🔗 Quick Navigation by Role

### For Backend Developers
1. [`README.md`](README.md) - Overview
2. [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Commands
3. Relevant engine README (`backend/engine-{core,analytics,execution}/README.md`)
4. [`backend/shared/README.md`](backend/shared/README.md) - Utilities
5. [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - Deployment

### For Frontend Developers
1. [`README.md`](README.md) - Overview
2. [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Commands
3. [`frontend/web/README.md`](frontend/web/README.md) - Frontend guide
4. [`infra/ci-cd/README.md`](infra/ci-cd/README.md) - CI/CD
5. [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - Deployment

### For DevOps/Infrastructure
1. [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - Start here
2. [`infra/gcp/README.md`](infra/gcp/README.md) - Terraform
3. [`infra/firebase/README.md`](infra/firebase/README.md) - Firebase
4. [`infra/ci-cd/README.md`](infra/ci-cd/README.md) - CI/CD setup
5. [`verification/suite/README.md`](verification/suite/README.md) - Verification

### For QA/Testing
1. [`README.md`](README.md) - Overview
2. [`verification/suite/README.md`](verification/suite/README.md) - Test framework
3. [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Commands
4. [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - Deployment verification

### For Project Managers
1. [`PHASE1_COMPLETION_SUMMARY.md`](PHASE1_COMPLETION_SUMMARY.md) - What was done
2. [`README.md`](README.md) - Project overview
3. [`RESTRUCTURING_PHASE1_COMPLETE.md`](RESTRUCTURING_PHASE1_COMPLETE.md) - Detailed metrics

---

## 📚 Documentation Map

### Level 1: Orientation (5 minutes)
- [`README.md`](README.md) - What is this project?

### Level 2: Getting Started (15 minutes)
- [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - How do I set up locally?
- Relevant role-specific README

### Level 3: Deep Dive (1 hour)
- [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - How do I deploy?
- Component-specific README (engine, frontend, infra)

### Level 4: Mastery (ongoing)
- [`verification/suite/README.md`](verification/suite/README.md) - Testing strategy
- Individual file READMEs and code comments

---

## 🚀 Common Tasks - Where to Find Info

| Task | Resource | Audience |
|------|----------|----------|
| Local setup (5 min) | [`README.md`](README.md) Quick Start section | Developers |
| Run tests | [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) Testing section | QA, Developers |
| Deploy to production | [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) | DevOps |
| Fix a bug in Engine Core | [`backend/engine-core/README.md`](backend/engine-core/README.md) + Troubleshooting | Backend |
| Add new signal | [`backend/engine-analytics/README.md`](backend/engine-analytics/README.md) | Backend |
| Update dashboard UI | [`frontend/web/README.md`](frontend/web/README.md) | Frontend |
| Configure monitoring | [`infra/gcp/README.md`](infra/gcp/README.md) | DevOps |
| Run E2E tests | [`verification/suite/README.md`](verification/suite/README.md) | QA |
| Troubleshoot WebSocket | [`backend/engine-execution/README.md`](backend/engine-execution/README.md) | Backend, DevOps |

---

## 📋 File Structure for Documentation

```
/
├── README.md                                    # ⭐ START HERE
├── QUICK_REFERENCE.md                          # Common tasks
├── DEPLOYMENT_GUIDE.md                         # Deployment
├── PHASE1_COMPLETION_SUMMARY.md                # What was delivered
├── RESTRUCTURING_PHASE1_COMPLETE.md            # Detailed breakdown
├── DOCUMENTATION_INDEX.md                      # This file
│
├── backend/
│   ├── engine-core/README.md
│   ├── engine-analytics/README.md
│   ├── engine-execution/README.md
│   └── shared/README.md
├── frontend/web/README.md
├── infra/
│   ├── firebase/README.md
│   ├── gcp/README.md
│   └── ci-cd/README.md
├── verification/suite/README.md
│
└── config/env/
    ├── dev/{engine-*.env.example,firebase.env.example}
    └── prod/{engine-*.env.example,firebase.env.example}
```

---

## 🔍 Finding Documentation by Topic

### Deployment & Infrastructure
- [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - Complete walkthrough
- [`infra/gcp/README.md`](infra/gcp/README.md) - Terraform & Cloud Run
- [`infra/firebase/README.md`](infra/firebase/README.md) - Firebase setup
- [`infra/ci-cd/README.md`](infra/ci-cd/README.md) - GitHub Actions

### APIs & Integration
- [`backend/engine-core/README.md`](backend/engine-core/README.md) - Market data API
- [`backend/engine-analytics/README.md`](backend/engine-analytics/README.md) - Signals API
- [`backend/engine-execution/README.md`](backend/engine-execution/README.md) - Trading API
- [`frontend/web/README.md`](frontend/web/README.md) - Frontend integration

### Local Development
- [`README.md`](README.md) - Quick start
- [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Commands
- Relevant engine README for setup details

### Monitoring & Troubleshooting
- [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - Troubleshooting section
- [`backend/engine-{core,analytics,execution}/README.md`](backend/) - Engine-specific issues
- [`infra/ci-cd/README.md`](infra/ci-cd/README.md) - Deployment issues
- [`verification/suite/README.md`](verification/suite/README.md) - Health checks

### Architecture & Design
- [`README.md`](README.md) - Architecture section
- [`PHASE1_COMPLETION_SUMMARY.md`](PHASE1_COMPLETION_SUMMARY.md) - Design evolution
- Component READMEs for internal architecture

---

## ✨ Best Practices for Using This Documentation

1. **Always start with README.md** - Get oriented first
2. **Use QUICK_REFERENCE.md** - For command lookup
3. **Read component README** - Before modifying that component
4. **Check troubleshooting** - In relevant README before opening issues
5. **Link references** - If you find old/broken links, update them

---

## 📞 Support

- **General questions**: See relevant README
- **Deployment issues**: Check [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)
- **Bug/problem**: Check component README troubleshooting section
- **Feature request**: Discuss with team, then update relevant README
- **Documentation gap**: See [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md#-support) or create issue

---

**Documentation Version**: 1.0
**Last Updated**: 2025-01-15
**Purpose**: Complete navigation guide for InfinityAI.Pro restructuring
