# Secrets & Safe Deploy Checklist


Required GitHub Secrets (place under repository Settings → Secrets):

GCP:

- `GCP_PROJECT_ID` - GCP project id
- `GCP_REGION` - region for Cloud Run (e.g., us-central1)
- `GCP_WORKLOAD_IDENTITY_PROVIDER` - Workload Identity Provider configured for repo
- `GCP_SERVICE_ACCOUNT` - service account email to impersonate

AWS:

- `AWS_OIDC_ROLE_ARN` - OIDC role to assume for GitHub Actions (recommended)
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `ECR_REPOSITORY` - ECR base repository name (if using auto-naming)

Security notes:

- Do NOT commit service account keys or AWS secret keys to the repository.
- Prefer OIDC/workload identity and short-lived credentials.

Safe deploy checklist (before you run a production deploy):

1. Configure secrets in the repo.
2. Validate builds with `ci-build.yml` on a branch or via workflow_dispatch.
3. Run deployment workflows with `dry_run: true` to confirm steps and logs.
4. Confirm services are deployed to staging environment and run health checks.
5. Only then set `dry_run: false` for production deploy.

Health checks (example):

- Use HTTP GET /lb/health or /lb/status on the load balancer service to assert readiness.
- Do NOT call any endpoints that perform trading activation in CI or deploy scripts.
