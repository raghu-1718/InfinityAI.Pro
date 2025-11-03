# Northflank Service Setup Guide

## Services Need to Be Created

Your Northflank project `infinity-ai` exists but has no services yet. You need to create 4 services via the Northflank UI.

## Creating Services in Northflank UI

### 1. Go to Northflank Dashboard
- URL: https://app.northflank.com/projects/infinity-ai
- Login with your account

### 2. Create Each Service

Click **"Create Service"** and configure each as follows:

---

#### **Engine A - Market Data**

**Service Name:** `engine-a`

**Repository:**
- GitHub: `raghu-1718/InfinityAI.Pro`
- Branch: `recovery/v4.6-stabilization`

**Build Settings:**
- Build Method: `Dockerfile`
- Dockerfile Path: `engines/engine-a/Dockerfile`
- Build Context: `engines/engine-a`

**Deployment:**
- Port: `8080`
- Instances: `1`
- Plan: `nf-compute-20` (or your preferred plan)

**Environment Variables:** (Add later via Northflank Secrets)
- `GCP_PROJECT_ID`
- `MARKET_DATA_API_KEY`
- etc.

---

#### **Engine B - AI/ML**

**Service Name:** `engine-b`

**Repository:**
- GitHub: `raghu-1718/InfinityAI.Pro`
- Branch: `recovery/v4.6-stabilization`

**Build Settings:**
- Build Method: `Dockerfile`
- Dockerfile Path: `engines/engine-b/Dockerfile`
- Build Context: `engines/engine-b`

**Deployment:**
- Port: `8080`
- Instances: `1`

---

#### **Engine C - Execution**

**Service Name:** `engine-c-execution`

**Repository:**
- GitHub: `raghu-1718/InfinityAI.Pro`
- Branch: `recovery/v4.6-stabilization`

**Build Settings:**
- Build Method: `Dockerfile`
- Dockerfile Path: `engines/engine-c-execution/Dockerfile`
- Build Context: `engines/engine-c-execution`

**Deployment:**
- Port: `8080`
- Instances: `1`

**Environment Variables:** (Critical - set these in Northflank)
- `DHAN_CLIENT_ID`
- `DHAN_ACCESS_TOKEN`
- `DHAN_API_SECRET`
- `GCP_PROJECT_ID`

---

#### **Engine D - Orchestrator**

**Service Name:** `engine-d`

**Repository:**
- GitHub: `raghu-1718/InfinityAI.Pro`
- Branch: `recovery/v4.6-stabilization`

**Build Settings:**
- Build Method: `Dockerfile`
- Dockerfile Path: `engines/engine-d/Dockerfile`
- Build Context: `engines/engine-d`

**Deployment:**
- Port: `8080`
- Instances: `1`

**Environment Variables:**
- `DHAN_CLIENT_ID`
- `DHAN_ACCESS_TOKEN`
- `DHAN_FEED`

---

## After Creating Services

### 3. Set GitHub Secrets

Once all 4 services are created, run these commands:

```powershell
# Set service IDs (use the actual service IDs from Northflank)
gh secret set NF_SERVICE_ENGINE_A --body "engine-a"
gh secret set NF_SERVICE_ENGINE_B --body "engine-b"
gh secret set NF_SERVICE_ENGINE_C --body "engine-c-execution"
gh secret set NF_SERVICE_ENGINE_D --body "engine-d"
```

### 4. Create API Gateway

Run the gateway setup script:

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

### 5. Configure DNS

After gateway creation, add CNAME in Namecheap:

```
engines.infinityai.pro → [CNAME from script output]
```

### 6. Deploy

Push to trigger deployment:

```bash
git push origin recovery/v4.6-stabilization
```

---

## Quick Start (If services already exist)

If you've already created the services manually:

```powershell
# 1. Set GitHub secrets
gh secret set NF_SERVICE_ENGINE_A --body "engine-a"
gh secret set NF_SERVICE_ENGINE_B --body "engine-b"
gh secret set NF_SERVICE_ENGINE_C --body "engine-c-execution"
gh secret set NF_SERVICE_ENGINE_D --body "engine-d"

# 2. Create gateway (if not exists)
./scripts/setup_northflank_gateway.ps1 `
  -ApiToken $env:NORTHFLANK_API_TOKEN `
  -Project "infinity-ai" `
  -GatewaySlug "infinityai-gateway" `
  -Domain "engines.infinityai.pro" `
  -EngineAService "engine-a" `
  -EngineBService "engine-b" `
  -EngineCService "engine-c-execution" `
  -EngineDService "engine-d"

# 3. Push to deploy
git push origin recovery/v4.6-stabilization
```

---

## Verification

Check service status:
```powershell
curl -H "Authorization: Bearer $env:NORTHFLANK_API_TOKEN" https://api.northflank.com/v1/projects/infinity-ai/services | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object -ExpandProperty services | Select-Object id, name
```

Expected output:
```
id                  name
--                  ----
engine-a            engine-a
engine-b            engine-b
engine-c-execution  engine-c-execution
engine-d            engine-d
```
