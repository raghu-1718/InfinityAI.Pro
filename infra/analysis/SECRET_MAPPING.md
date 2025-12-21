# Secret Mapping Analysis

| Secret Name | Source (`.env.example`) | GCP Secret Manager | Cloud Run Usage | Status |
|-------------|-------------------------|-------------------|-----------------|--------|
| `DHAN_CLIENT_ID` | ❌ (Not in env.example) | ✅ Found | `engine-a`, `engine-b`, `engine-c` | ✅ Mapped |
| `DHAN_API_SECRET` | ❌ (Not in env.example) | ✅ Found | `engine-a`, `engine-b`, `engine-c` | ✅ Mapped |
| `DHAN_ACCESS_TOKEN` | ❌ (Not in env.example) | ✅ Found | `engine-a`, `engine-b`, `engine-c` | ✅ Mapped |
| `GEMINI_API_KEY` | ❌ (Not in env.example) | ❌ **MISSING** | `engine-b` | ❌ **CRITICAL MISSING** |
| `ENCRYPTION_KEY` | ❌ (Not in env.example) | ❌ **MISSING** | `engine-c` | ❌ **CRITICAL MISSING** |
| `API_SECRET_KEY` | ✅ Present | ❌ Missing | None | ⚠️ Unused / Legacy? |
| `JWT_SECRET` | ✅ Present | ❌ Missing | None | ⚠️ Unused / Legacy? |
| `GCP_PROJECT_ID` | ✅ Present | N/A (Env Var) | `engine-a`, etc. (via Deployment) | ✅ Env Var |
| `ENGINE_C_URL` | ✅ Present | N/A (Env Var) | `engine-a` | ✅ Env Var |

## Findings
1. **Critical Gaps**: `GEMINI_API_KEY` and `ENCRYPTION_KEY` are required by Cloud Run services (mapped in `deploy-production.yml`) but currently **do not exist** in GCP Secret Manager. This will cause deployment or runtime failures.
2. **Legacy Config**: `.env.example` appears outdated, referencing `API_SECRET_KEY` and `JWT_SECRET` which are not used in the modern `deploy-production.yml` pipeline.
3. **Dhan Integration**: Fully configured and mapped in GCP Secret Manager.
