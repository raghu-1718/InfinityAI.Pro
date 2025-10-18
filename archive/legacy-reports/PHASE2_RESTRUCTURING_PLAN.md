# Phase 2: Backend Reorganization Plan
**Status:** 📋 READY TO EXECUTE  
**Prerequisites:** Phase 1 ✅ COMPLETED

---

## 🎯 Objectives
1. Clean 4-engine architecture (A/B/C/D only)
2. Remove all Ultra-Aggressive engine references
3. Consolidate duplicate engine directories
4. Organize project structure for clarity
5. Update all configuration files

---

## 📁 Proposed New Structure

### Backend Organization
```
backend/
├── engines/
│   ├── engine-a-market-data/          # Keep and standardize
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── engine-b-ai-ml/                # Keep and standardize
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── engine-c-execution/            # Keep (Dhan integration)
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── engine-d-chatbot/              # Keep and standardize
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   └── shared/                        # Shared utilities
│       ├── performance_config.py
│       └── security_middleware.py
├── tests/                             # Keep test files here
│   ├── integration_test.py
│   ├── full_app_test.py
│   └── performance_test.py
├── utils/                             # Utility scripts
│   ├── dhan_credential_manager.py
│   └── dhan_webhook_handler.py
└── requirements.txt                   # Common requirements
```

### Root Directory Organization
```
InfinityAI.Pro/
├── backend/                           # Backend engines
├── frontend/                          # React frontend
├── infrastructure/                    # Cloud infrastructure
│   ├── aws/
│   ├── gcp/
│   └── k8s/
├── scripts/                           # Deployment scripts
│   ├── deployment/                    # Deployment automation
│   ├── health-checks/                # Health verification
│   └── utilities/                     # Utility scripts
├── config/                            # Configuration files
│   ├── production/
│   └── development/
├── docs/                              # Documentation
│   ├── architecture/
│   ├── deployment/
│   └── api/
├── tests/                             # Integration tests
├── .github/                           # GitHub workflows
├── docker-compose.yml                 # Local development
├── package.json                       # Root package config
├── README.md                          # Main documentation
└── .gitignore                         # Git ignore rules
```

---

## 🗑️ Files to Delete

### Engine Ultra-Aggressive Related
```
backend/
├── ultra_aggressive_integrated.py     ❌ DELETE
├── ultra_aggressive_main.py           ❌ DELETE
├── ultra_aggressive_trader.py         ❌ DELETE
├── multi_cloud_ultra_aggressive.py    ❌ DELETE
├── real_ultra_aggressive_trader.py    ❌ DELETE
├── Dockerfile.ultra-aggressive        ❌ DELETE
└── engines/
    └── engine-ultra-aggressive/       ❌ DELETE (entire directory)
```

### Duplicate Engine Directories
```
backend/engines/
├── engine-a/                          ❌ DELETE (consolidate into engine-a-market-data)
├── engine-b/                          ❌ DELETE (consolidate into engine-b-ai-ml)
└── engine-d/                          ❌ DELETE (consolidate into engine-d-chatbot)
```

### Unused Dockerfiles
```
backend/
├── Dockerfile.multi-cloud             ❌ DELETE
├── Dockerfile.engine-d-frontend       ❌ DELETE
└── Dockerfile (root)                  ❌ REVIEW (may be obsolete)
```

### Old Test Files (Root Backend)
```
backend/
├── test_api_windows.py                ↪ MOVE to backend/tests/
├── test_dhan_sandbox.py               ↪ MOVE to backend/tests/
├── test_integration.py                ↪ MOVE to backend/tests/
├── integration_test.py                ↪ MOVE to backend/tests/
├── full_app_test.py                   ↪ MOVE to backend/tests/
├── performance_test.py                ↪ MOVE to backend/tests/
├── live_trading_test.py               ↪ MOVE to backend/tests/
└── continuous_app_analysis.py         ↪ MOVE to backend/utils/ or DELETE
```

### Old Trading Scripts (Evaluate)
```
backend/
├── advanced_ai_trader.py              ⚠️ REVIEW (may be legacy)
├── autonomous_trader.py               ⚠️ REVIEW
├── auto_trading_system.py             ⚠️ REVIEW
├── continuous_monitor.py              ⚠️ REVIEW
├── dynamic_funds_trader.py            ⚠️ REVIEW
├── integrated_live_trader.py          ⚠️ REVIEW
├── live_autonomous_trader.py          ⚠️ REVIEW
├── profit_switcher.py                 ⚠️ REVIEW
├── real_trade_executor.py             ⚠️ REVIEW
└── trading_dashboard.py               ⚠️ REVIEW
```

### Root Directory Cleanup
```
InfinityAI.Pro/
├── dispatch-deploy-production.ps1     ↪ MOVE to scripts/deployment/
├── deploy-complete-platform.ps1       ↪ MOVE to scripts/deployment/
├── guided-deployment.ps1              ↪ MOVE to scripts/deployment/
├── verify-platform-health.ps1         ↪ MOVE to scripts/health-checks/
├── docker-compose.engines.yml         ❌ DELETE or CONSOLIDATE
└── dhan_credentials_secure.json       ⚠️ SECURE (should not be in repo)
```

---

## 📝 Configuration Files to Update

### 1. docker-compose.yml
**Changes Required:**
- Remove `engine-ultra-aggressive` service definition
- Update service names to match new structure
- Remove any ultra-aggressive environment variables
- Update volume mounts if needed

### 2. Frontend: nginx.conf
**Location:** `frontend/web/nginx.conf`  
**Changes Required:**
```nginx
# REMOVE these proxy rules:
location /api/engine-ultra/ {
    proxy_pass http://engine-ultra-aggressive-backend;
}

# KEEP only these:
location /api/engine-a/ { ... }  # Market Data
location /api/engine-b/ { ... }  # AI/ML Strategy
location /api/engine-c/ { ... }  # Dhan Integration
location /api/engine-d/ { ... }  # Chatbot
```

### 3. Frontend: ApiService.js
**Location:** `frontend/web/src/services/ApiService.js`  
**Changes Required:**
- Remove `REACT_APP_ENGINE_ULTRA_URL` references
- Remove ultra-aggressive API endpoints
- Update emotional feedback routing to Engine D only

### 4. Frontend: .env.production
**Location:** `frontend/web/.env.production`  
**Changes Required:**
```bash
# REMOVE:
REACT_APP_ENGINE_ULTRA_URL=...

# KEEP:
REACT_APP_ENGINE_A_URL=...
REACT_APP_ENGINE_B_URL=...
REACT_APP_ENGINE_C_URL=...
REACT_APP_ENGINE_D_URL=...
```

### 5. Backend: requirements.txt
**Action:** Consolidate common dependencies, remove ultra-specific ones

---

## 🔧 Consolidation Strategy

### Engine Directory Consolidation

#### Engine A (Market Data)
1. Compare `engine-a/` vs `engine-a-market-data/`
2. Keep the more complete/recent version
3. Merge any unique code from the other
4. Standardize naming to `engine-a-market-data/`

#### Engine B (AI/ML)
1. Compare `engine-b/` vs `engine-b-ai-ml/`
2. Keep the more complete/recent version
3. Merge any unique code
4. Standardize naming to `engine-b-ai-ml/`

#### Engine D (Chatbot)
1. Compare `engine-d/` vs `engine-d-chatbot/`
2. Keep the more complete/recent version
3. Merge any unique code
4. Standardize naming to `engine-d-chatbot/`

#### Engine C (Execution)
- Already correctly named `engine-c-execution/`
- No changes needed except verification

---

## 📦 Migration Steps

### Step 1: Backup Current State
```powershell
# Create backup branch
git checkout -b pre-phase2-backup
git add -A
git commit -m "Backup before Phase 2 reorganization"
git checkout main
```

### Step 2: Engine Consolidation
1. Analyze each duplicate pair
2. Merge code into primary directory
3. Delete duplicate directories
4. Update imports and references

### Step 3: File Reorganization
1. Create new directory structure
2. Move files to appropriate locations
3. Update all import statements
4. Update Dockerfile COPY paths

### Step 4: Configuration Updates
1. Update docker-compose.yml
2. Update frontend nginx.conf
3. Update ApiService.js
4. Update .env.production
5. Update any deployment scripts

### Step 5: Testing
1. Verify directory structure
2. Check for broken imports
3. Validate configuration syntax
4. Test local Docker builds

---

## ⚠️ Critical Considerations

1. **Code Dependencies:** Some files might import from ultra-aggressive modules. Need to refactor or remove these imports.

2. **Shared Utilities:** `performance_config.py` and `security_middleware.py` are in `engines/` but should be in `engines/shared/`.

3. **Dhan Credentials:** The file `dhan_credentials_secure.json` should NOT be in the repository. It should be removed and rely on Google Secret Manager only.

4. **Docker Images:** After reorganization, all Dockerfiles need to be updated for new paths.

5. **Environment Variables:** Any ultra-aggressive specific env vars need to be removed from all configs.

---

## ✅ Phase 2 Success Criteria

- [ ] Only 4 engine directories exist: A, B, C, D
- [ ] No ultra-aggressive references in any file
- [ ] All configuration files updated
- [ ] Project structure follows new organization
- [ ] All imports and paths are correct
- [ ] Docker builds succeed for all 4 engines
- [ ] No duplicate code or directories
- [ ] Documentation reflects new structure

---

## 🚀 Ready to Execute?

**Estimated Time:** 30-45 minutes  
**Risk Level:** Medium (code reorganization)  
**Rollback Plan:** Git backup branch created in Step 1

**Awaiting Confirmation to Proceed to Phase 2 Execution...**
