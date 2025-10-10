# Final Multi-Cloud Data Flow Report

Date: 2025-10-08

## Overview
- Frontend: React app in S3 (`infinityai-pro-frontend`) with planned CloudFront + Route53 for `infinityai.pro`
- Engines:
  - A (GCP Cloud Run): Market data, charts, events
  - B (GCP Cloud Run): AI/ML insights
  - C (AWS ECS behind ALB /engine-c): Trading + Dhan integration (auth callback, webhook, portfolio/orders)
  - D (AWS ECS behind ALB /engine-d): Aggregator + proxy + status + WebSockets
- CDN/DNS: CloudFront in front of S3 (default) and ALB (for API paths). Route 53 apex + www → CloudFront. ACM TLS.

## Data Flow
1) Browser → CloudFront (https://infinityai.pro)
2) Static assets → S3 website origin (cacheable)
3) API calls
   - Default: `/engine-d/...` → ALB → Engine D
   - Trading: `/engine-c/...` → ALB → Engine C
   - Engine D proxies upstream to Engine A/B/C as needed
4) WebSockets
   - `/engine-d/ws/*` and `/engine-c/ws/*` pass through CloudFront to ALB → Engines
5) Dhan
   - Redirect: `https://infinityai.pro/engine-c/auth/dhan/callback`
   - Postback: `https://infinityai.pro/engine-c/webhooks/dhan/postback`

## Verified Endpoints (ALB)
Using `scripts/verify-backend-extended.ps1` against the ALB:

- engine-d-status: 200
- engine-d-health: 200
- engine-c-health: 200
- dhan-status-proxy (GET): 200
- dhan-token-proxy (POST dry_run): 200

Results file: `scripts/verify-results-extended.json`

## Frontend Configuration
- `frontend/src/config/api-config.js` now uses `window.location.origin` for the primary API base, ensuring same-origin calls via the custom domain/CDN.
- Fallbacks remain to ALB and Cloud Run endpoints.

## Secrets and Personal Use
- Use `scripts/store-dhan-secrets.ps1` to store API key/secret (and optional webhook secret) in AWS Secrets Manager (and GCP if desired).
- Provide your Dhan access token via the UI (Settings → Brokers → Dhan → Update). It is stored server-side; the frontend does not persist it.

## Domain/CDN Deployment
- Stack template: `deploy/aws/cloudfront-route53.yaml`
- Deploy script: `deploy/aws/deploy-cloudfront.ps1`
- Docs: `docs/DOMAIN_SETUP.md`

Current status: Attempt to deploy failed due to IAM (cloudformation:CreateChangeSet denied). Attach the IAM policy at `deploy/aws/iam/cloudfront-route53-deploy-policy.json` to your deploy user/role and re-run the deploy script. Once provisioned, we will re-run verification against https://infinityai.pro.

## Next Steps
1) Attach IAM policy and deploy CloudFront/Route53 stack
2) Wait for ACM validation and CloudFront propagation
3) Re-run verification script with `-BaseUrl https://infinityai.pro`
4) In Dhan developer portal, set Redirect/Postback URLs shown above
5) Optionally map Cloud Run services to subdomains (`a.infinityai.pro`, `b.infinityai.pro`)

## Edge Cases and Operational Notes
- Downtime risk during DNS cutover is minimal; CloudFront and Route 53 aliases can be created while S3/ALB remain live.
- API caching is disabled at CloudFront for `/engine-*/` paths; static assets use optimized caching.
- WebSocket upgrades are supported through CloudFront to the ALB.
- For auth-required endpoints, ensure you Sign In in the UI; otherwise requests will 401.

## Success Criteria
- Frontend loads via https://infinityai.pro with TLS
- Header chips show system OK and Dhan Connected (after token)
- Market widgets and charts update without CORS issues (same-origin)
- Trading/Portfolio tabs load and stream via WebSockets

---
Prepared for: infinityai.pro
Prepared by: Deployment automation in repo
