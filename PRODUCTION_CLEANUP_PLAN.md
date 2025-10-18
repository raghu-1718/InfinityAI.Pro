# InfinityAI.Pro - Production Cleanup & Reorganization Plan

**Date:** October 17, 2025  
**Status:** 🚀 READY TO EXECUTE  
**Objective:** Clean, GCP-only, 4-engine production architecture

---

## 🎯 Production-Critical Resources (PRESERVE)

### GCP Configuration
- **Project:** after-yesterday-473512-k3
- **Region:** us-central1
- **Domain:** infinityai.pro

### Production URLs (GCP Cloud Run)
```
Frontend:  https://infinityai-frontend-bprmddefsa-uc.a.run.app
Engine A:  https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app
Engine B:  https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app
Engine C:  https://engine-c-prod-bprmddefsa-uc.a.run.app
Engine D:  https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app
```

### Files to Keep
- `.env` (with GCP URLs)
- `backend/engines/engine-a/` (canonical)
- `backend/engines/engine-b/` (canonical)
- `backend/engines/engine-c-execution/` (canonical)
- `backend/engines/engine-d/` (canonical)
- `backend/engine-a/main.py` (thin entrypoint)
- `backend/engine-b/main.py` (thin entrypoint)
- `backend/engine-c/main.py` (thin entrypoint)
- `backend/engine-d/main.py` (thin entrypoint)
- `backend/services/engine_c/` (shared lib)
- `frontend/app-v4.5/` (modern Vite app)
- `frontend/web/` (backup CRA app)
- `docker-compose.yml` (local dev)
- `README.md`, `ARCHITECTURE_v4.5.md`, `ARCHIVE_PLAN.md`

---

## 🗑️ Phase 1: Archive Legacy Reports & Verification Files

### Move to /archive/legacy-reports/
- All `*_REPORT.md` files (40+ files)
- All `*_STATUS.md` files
- All `*_verification_*.json` files
- All `*.log` files (except current engine logs)
- `PHASE1_CLEANUP_REPORT.md`
- `PHASE2_RESTRUCTURING_PLAN.md`
- `POST_AUDIT_*.md`
- `MILESTONE_ACHIEVEMENT.md`
- `IMPLEMENTATION_COMPLETE.md`
- `NAMECHEAP_DNS_*.md`
- `DOMAIN_*.md`
- `ENGINE_A_*.md`

---

## 🚫 Phase 2: Remove AWS/Vercel/Azure References

### Files to Archive/Delete
- `backend/Dockerfile.multi-cloud` → archive
- `infrastructure/aws/` → archive entire folder
- `scripts/deploy-aws-engines.ps1` → archive
- `scripts/fix_aws_alb_rules.ps1` → archive
- `engine-c-arn.txt` (AWS ECS ARN) → archive
- Any `ecs-*.ps1` scripts → archive

### Code Changes Required
- Remove AWS imports from all Python files
- Remove Vercel/Azure references from docs
- Update README.md to "100% GCP-native"
- Remove multi-cloud references from ARCHITECTURE.md

---

## ❌ Phase 3: Remove Engine Ultra-Aggressive

### Directories to Archive
- `backend/engines/engine-ultra-aggressive/` → archive
- Any `ultra_aggressive_*.py` files → archive (already done)

### Files to Update
- `docker-compose.yml` - Remove ultra service
- `docker-compose.engines.yml` - Remove ultra service
- `.env` - Remove ULTRA_AGGRESSIVE_URL
- `README.md` - Update to 4 engines
- `ARCHITECTURE_v4.5.md` - Remove ultra references
- Frontend configs - Remove ultra URLs

### GCP Cloud Run
- Delete `engine-ultra-aggressive-prod` service (if exists)

---

## 🐳 Phase 4: Docker Cleanup

### Commands to Execute
```powershell
# Stop all containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)

# Remove all images
docker rmi $(docker images -q) -f

# Remove all volumes
docker volume rm $(docker volume ls -q)

# System prune
docker system prune -af --volumes

# Remove build cache
docker builder prune -af
```

---

## ✅ Phase 5: Verify 4-Engine Integration

### Integration Flow
```
Frontend (Vite/React)
    ↓
Engine D (Orchestrator/Chatbot)
    ↓ ↑
Engine A (Market Data) → Engine B (AI/ML) → Engine C (Execution)
```

### Health Checks
- `curl https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app/health`
- `curl https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/health`
- `curl https://engine-c-prod-bprmddefsa-uc.a.run.app/health`
- `curl https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app/health`

### API Integration Tests
- Engine A → Engine B (market data to AI)
- Engine B → Engine C (AI signals to execution)
- Engine D → All engines (orchestration)
- Frontend → Engine D (user interface)

---

## 📊 Expected Disk Space Savings

- Docker images/volumes: ~10-20 GB
- Legacy reports: ~50 MB
- AWS/Azure configs: ~100 MB
- Engine Ultra code: ~200 MB
- **Total estimated:** ~10-15 GB freed

---

## 🎯 Final Architecture

```
InfinityAI.Pro/
├── backend/
│   ├── engine-a/          (thin entrypoint)
│   ├── engine-b/          (thin entrypoint)
│   ├── engine-c/          (thin entrypoint)
│   ├── engine-d/          (thin entrypoint)
│   ├── engines/
│   │   ├── engine-a/      (canonical)
│   │   ├── engine-b/      (canonical)
│   │   ├── engine-c-execution/  (canonical)
│   │   └── engine-d/      (canonical)
│   └── services/
│       └── engine_c/      (shared lib)
├── frontend/
│   ├── app-v4.5/          (modern Vite app - PRIMARY)
│   └── web/               (backup CRA app)
├── archive/               (all legacy code)
├── .env                   (GCP URLs only)
├── docker-compose.yml     (4 engines only)
├── README.md              (updated for 4 engines)
└── ARCHITECTURE_v4.5.md   (GCP-only)
```

---

## ✅ Success Criteria

- [ ] All legacy reports archived
- [ ] Zero AWS/Vercel/Azure references
- [ ] Engine Ultra completely removed
- [ ] Docker completely cleaned
- [ ] All 4 engines health checks pass
- [ ] Frontend integrates with all 4 engines
- [ ] Documentation updated
- [ ] 10+ GB disk space freed

---

**Ready to execute cleanup!** 🚀
