# InfinityAI.Pro

Production-focused multi-cloud trading platform across AWS and GCP.

[![Live](https://img.shields.io/badge/Live-infinityai.pro-blue)](https://infinityai.pro)

## Overview

Accurate as of 2025-10-08:
- Frontend: React on AWS S3 behind CloudFront + Route 53 (`infinityai.pro`, ACM us-east-1)
- Engine A (GCP Cloud Run): Market data, charts, events
- Engine B (GCP Cloud Run): AI insights and models
- Engine C (AWS ECS/Fargate via ALB path /engine-c): Trading + Dhan integration
- Engine D (AWS ECS/Fargate via ALB path /engine-d): Aggregator/proxy + WebSockets

CloudFront default routes to S3; path-based rules route `/engine-c/*` and `/engine-d/*` to the ALB. The frontend uses same-origin API via `/engine-d` to avoid CORS.

See `docs/ARCHITECTURE.md` for a deeper diagram and data flow.

## Live Platform
- Frontend: https://infinityai.pro (HTTPS will be active once ACM is ISSUED and attached)

## Local Development
```bash
# Clone
git clone https://github.com/raghu-1718/InfinityAI.Pro.git
cd InfinityAI.Pro

# Frontend
cd infinityai-pro/frontend
npm install
npm start

# Verify backend (ALB)
cd ../../
pwsh -NoProfile -File scripts/verify-backend-extended.ps1 -BaseUrl "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com"
```

## Configuration

Use cloud Secret Managers; do not commit secrets.
- AWS Secrets Manager (Engine C/D):
  - DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN (auto-refresh service available)
- GCP Secret Manager (Engine A/B): upstream API keys as needed

Environment (examples):
```
ENGINE_A_URL=https://<engine-a>.run.app
ENGINE_B_URL=https://<engine-b>.run.app
PORT=8004 # engine-d, 8003 # engine-c
```

## Deployment

### AWS (Engines C/D + Frontend)
1) IAM (if needed): `pwsh -File fix-aws-iam.ps1`
2) Deploy engines and verify: `deploy-aws-engines.ps1`, `scripts/verify-backend-extended.ps1`
3) CloudFront + Route 53: see `docs/DOMAIN_SETUP.md` and deploy/aws scripts

### GCP (Engines A/B)
Cloud Run deploy references under `infinityai-pro/gcp`.

## Performance & Status
- ALB Engine D/C health: 200 OK
- Domain TLS: ACM certificate pending validation; automation will attach and finalize CloudFront
- Frontend assets served from S3; CloudFront enabled after cert issuance

## Advantages / Limitations
Advantages:
- Multi-cloud split reduces blast radius; Engine D aggregation simplifies frontend
- CDN + same-origin API avoids CORS; health checks and scripts provided

Limitations:
- TLS pending until ACM is ISSUED
- Legacy directories (Vercel/Azure) still present; scheduled for removal

## Housekeeping
- `.gitignore` excludes node_modules, caches, generated artifacts, and local secrets
- Cleanup details: `docs/CLEANUP_REPORT.md`
- Deep analysis: `docs/ANALYSIS_REPORT.md`

Built with ❤️ by the InfinityAI.Pro team.