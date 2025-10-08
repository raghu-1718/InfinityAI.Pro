# InfinityAI.Pro Architecture

Generated: 2025-10-08

Overview
- Frontend: React SPA hosted on S3; CloudFront + Route 53 custom domain `infinityai.pro` (ACM TLS us-east-1)
- Engines:
  - Engine A (GCP Cloud Run): Market data, charts, events
  - Engine B (GCP Cloud Run): AI/ML insights and models
  - Engine C (AWS ECS/Fargate behind ALB path /engine-c): Trading + Dhan integration
  - Engine D (AWS ECS/Fargate behind ALB path /engine-d): Aggregator/proxy, status, WebSockets
- CDN/DNS: CloudFront default to S3, path-based routing to ALB for /engine-c and /engine-d

Data Flow
1) Browser → CloudFront (https://infinityai.pro)
2) Static assets → S3 website origin (cacheable)
3) API calls
   - Default: `/engine-d/*` → ALB → Engine D
   - Trading: `/engine-c/*` → ALB → Engine C
   - Engine D proxies upstream to Engine A/B/C as needed
4) WebSockets
   - `/engine-d/ws/*` and `/engine-c/ws/*` pass through CloudFront to ALB → Engines
5) Dhan
   - Redirect: `https://infinityai.pro/engine-c/auth/dhan/callback`
   - Postback: `https://infinityai.pro/engine-c/webhooks/dhan/postback`

Security & Secrets
- Secrets stored in AWS Secrets Manager and GCP Secret Manager; repo excludes local secrets
- CORS avoided by same-origin API via Engine D; CloudFront enforces TLS

Health & Observability
- Health endpoints: `/engine-*/health` respond 200 via ALB
- Scripts: `scripts/verify-backend-extended.ps1`, `scripts/fetch-todays-analysis.ps1`

Deployment
- AWS: ECS Fargate services for Engines C/D; ALB path routing; CloudFront + Route 53 + ACM
- GCP: Cloud Run services for Engines A/B
