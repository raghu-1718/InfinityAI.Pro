# CI/CD Secrets & Environment

## GitHub Actions (Repository Secrets)

- VERCEL_TOKEN: Personal token with access to the Vercel org/team
- VERCEL_ORG_ID: Vercel team/org ID (team_xxx)
- VERCEL_PROJECT_ID_FRONTEND: Vercel project ID for frontend (prj_*)
- VERCEL_PROJECT_ID_WEBHOOKS: Vercel project ID for webhooks API (prj_*)
- FIREBASE_TOKEN: CI token for firebase-tools deploy
- NORTHFLANK_API_TOKEN: Northflank API token with project write permissions
- NORTHFLANK_PROJECT: Northflank project slug (e.g., infinity-ai)
- NF_SERVICE_ENGINE_A: Northflank service slug for engine-a
- NF_SERVICE_ENGINE_B: Northflank service slug for engine-b
- NF_SERVICE_ENGINE_C: Northflank service slug for engine-c
- NF_SERVICE_ENGINE_D: Northflank service slug for engine-d

## Vercel Project Environment Variables

- Frontend (frontend):
  - VITE_API_BASE = <https://engines.infinityai.pro>
  - VITE_WS_BASE = <wss://engines.infinityai.pro>
  - VITE_FIREBASE_AUTH_DOMAIN, VITE_FIREBASE_PROJECT_ID, etc. (as applicable)

- Webhooks (api-webhooks):
  - DHAN_WEBHOOK_SECRET: shared secret to validate broker webhooks
  - ENGINE_C_INTERNAL_URL = <https://engines.infinityai.pro/engine-c>
  - FRONTEND_VERCEL_URL = <https://infinityai.pro>

## Notes

- Engines C/D no longer deploy on Vercel. All engines should be hosted on Northflank.
- Ensure lowercase key naming when code expects it (e.g., gcp_project_id). Avoid case mismatches.
- Northflank API Gateway should expose engines.infinityai.pro with routes:
  - /engine-a, /engine-b, /engine-c, /engine-d -> respective services.
- After creating the gateway, add a CNAME in DNS for engines.infinityai.pro pointing to the Northflank-provided CNAME target.
