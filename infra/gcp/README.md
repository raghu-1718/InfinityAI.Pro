# infra/gcp/README.md

## Google Cloud Platform Infrastructure

This directory contains Infrastructure-as-Code (Terraform) and configuration for deploying InfinityAI.Pro to Google Cloud Run, Firestore, and Secret Manager.

### Directory Structure

```
gcp/
├── cloudrun/           # Cloud Run service configurations
├── iam/                # IAM roles and service account bindings
├── networking/         # Load balancer, domain mapping, DNS
├── secrets/            # Secret Manager references and setup
├── terraform.tfvars    # Terraform variables (git-ignored)
└── main.tf             # Main Terraform configuration
```

### Services Deployed

1. **Engine Core** (engine-a): Market data ingestion
   - URL: https://engine-a-429140669077.asia-south1.run.app

2. **Engine Analytics** (engine-b): ML/AI signals
   - URL: https://engine-b-429140669077.asia-south1.run.app

3. **Engine Execution** (engine-c): Trade execution + WebSocket
   - URL: https://engine-c-429140669077.asia-south1.run.app

4. **Frontend** (React): User dashboard
   - URL: https://infinityai.pro

### Deployment Steps

```bash
# 1. Set GCP project
gcloud config set project project-841b7f97-5ee3-4fbe-920

# 2. Initialize Terraform
cd infra/gcp
terraform init

# 3. Review plan
terraform plan -var-file=terraform.tfvars

# 4. Apply infrastructure
terraform apply -var-file=terraform.tfvars
```

### Required Secrets in Secret Manager

- `dhan-api-key`: Dhan broker OAuth credentials
- `dhan-client-secret`: Dhan OAuth client secret
- `gemini-api-key`: Google Gemini API key
- `jwt-secret-key`: JWT signing key for authentication
- `firestore-credentials`: Firestore service account JSON
- `firebase-config`: Firebase web SDK configuration

### Environment Variables

Each Cloud Run service receives environment variables from `config/env/prod/` files. See config directory for templates.

### Health Monitoring

All services expose `/health` endpoint monitored by CI/CD and `verification/suite/`.

```bash
# Check all services
curl https://engine-a-429140669077.asia-south1.run.app/health
curl https://engine-b-429140669077.asia-south1.run.app/health
curl https://engine-c-429140669077.asia-south1.run.app/health
```

### Troubleshooting

- **Service fails to deploy**: Check `gcloud run services list` and review Cloud Build logs
- **Health endpoint 404**: Verify `PORT` environment variable matches Cloud Run configuration
- **Firestore permission denied**: Ensure service account has `roles/datastore.user` and `roles/datastore.importExportAdmin`
- **OAuth callback issues**: Verify `OAUTH_CALLBACK_URL` matches Dhan console settings
