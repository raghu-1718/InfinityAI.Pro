# ⚡ InfinityAI.Pro - Quick Deployment Guide

## 🎯 Current Status
✅ All GitHub secrets configured  
✅ CI/CD workflow ready (Vercel + Northflank + Firebase)  
✅ Code verified (production Dhan integrations)  
⚠️ **NEXT:** Create 4 Northflank services via UI  

---

## 🚀 3-Step Go-Live Process

### Step 1: Create Northflank Services (15 min)
**URL:** https://app.northflank.com/projects/infinity-ai

For each engine, click "Create Service":

| Service ID | Dockerfile Path | Port |
|------------|----------------|------|
| `engine-a` | `engines/engine-a/Dockerfile` | 8080 |
| `engine-b` | `engines/engine-b/Dockerfile` | 8080 |
| `engine-c-execution` | `engines/engine-c-execution/Dockerfile` | 8080 |
| `engine-d` | `engines/engine-d/Dockerfile` | 8080 |

**Repository:** `raghu-1718/InfinityAI.Pro` (branch: `recovery/v4.6-stabilization`)  
**Build Context:** Same as Dockerfile directory  

### Step 2: Create API Gateway (2 min)
```powershell
./scripts/setup_northflank_gateway.ps1 `
  -ApiToken $env:NORTHFLANK_API_TOKEN `
  -Project "infinity-ai" `
  -GatewaySlug "infinityai-gateway" `
  -Domain "engines.infinityai.pro" `
  -EngineAService "engine-a" `
  -EngineBService "engine-b" `
  -EngineCService "engine-c-execution" `
  -EngineDService "engine-d"
```

**Copy CNAME from output**

### Step 3: Add DNS & Deploy (10 min)
1. **DNS:** Namecheap → Add CNAME `engines` → [from Step 2]
2. **Deploy:** `git push origin recovery/v4.6-stabilization`
3. **Monitor:** https://github.com/raghu-1718/InfinityAI.Pro/actions

---

## ✅ Verification

### Services Created?
```powershell
curl -H "Authorization: Bearer $env:NORTHFLANK_API_TOKEN" https://api.northflank.com/v1/projects/infinity-ai/services | ConvertFrom-Json | Select -ExpandProperty data | Select -ExpandProperty services | Measure-Object
```
**Expected:** Count = 4

### Gateway Working?
```powershell
curl https://engines.infinityai.pro/engine-a/health
```
**Expected:** `{"status":"healthy"}`

### Full Stack Live?
```bash
curl https://infinityai.pro  # Frontend
curl https://api.infinityai.pro/health  # Webhooks
curl https://engines.infinityai.pro/engine-d/health  # Engines
```

---

## 📚 Documentation
- **Full Guide:** `DEPLOYMENT_READY.md`
- **Status:** `DEPLOYMENT_STATUS.md`
- **Northflank:** `docs/NORTHFLANK_SETUP.md`
- **Secrets:** `docs/CI_SECRETS.md`

---

## 🆘 Troubleshooting

**Services won't create?**  
→ Use Northflank UI (API has validation issues)

**Gateway fails?**  
→ Check service IDs match exactly: `engine-a`, `engine-b`, `engine-c-execution`, `engine-d`

**Deployment fails?**  
→ Check GitHub Actions logs → Verify all secrets set → Check Northflank service status

**DNS not resolving?**  
→ Wait 5 min for propagation → Verify CNAME with `nslookup engines.infinityai.pro`

---

**Time to Go-Live:** ~30 minutes  
**Next Action:** Create services at https://app.northflank.com/projects/infinity-ai
