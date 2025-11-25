# GCP IAM Configuration - InfinityAI.Pro

**Last Updated:** October 20, 2025

## Service Accounts

### 1. GitHub Actions Deployer Service Account

**Email:** `github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com`

### Assigned IAM Roles

The following roles are required for complete CI/CD pipeline functionality:

| Role | Purpose | Required For |
|------|---------|--------------|
| `roles/artifactregistry.reader` | Pull container images from Artifact Registry | Cloud Run deployments |
| `roles/artifactregistry.writer` | Push container images to Artifact Registry | Docker image builds |
| `roles/cloudbuild.builds.editor` | Create and manage Cloud Build jobs | Source deployments |
| `roles/iam.serviceAccountUser` | Impersonate service accounts | Cloud Run service execution |
| `roles/run.admin` | Full Cloud Run service management | Deploy and update services |
| `roles/storage.admin` | Create buckets and upload source code | Cloud Run source deployments |

## Configuration Commands

All roles were granted using the following commands:

```bash
# Artifact Registry Reader
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

# Artifact Registry Writer
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Cloud Build Editor
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

# Service Account User
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Cloud Run Admin
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Storage Admin
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

## Verification

To verify the current IAM configuration:

```bash
gcloud projects get-iam-policy infinity-ai-5ec7c \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:github-actions-deployer@infinity-ai-5ec7c.iam.gserviceaccount.com"
```

## CI/CD Pipeline Components

This service account is used by GitHub Actions workflows:
- `.github/workflows/deploy-frontend.yml` - Frontend deployment to Firebase Hosting
- `.github/workflows/engine-a.yaml` - Engine A deployment to Cloud Run
- `.github/workflows/engine-b.yaml` - Engine B deployment to Cloud Run
- `.github/workflows/engine-c.yaml` - Engine C deployment to Cloud Run
- `.github/workflows/engine-d.yaml` - Engine D deployment to Cloud Run
- `.github/workflows/monorepo-ci-clean.yml` - Build validation

## Security Notes

- Service account key is stored as GitHub repository secret: `GCP_SA_KEY`
- Credentials are automatically cleaned up after each workflow run
- All deployments use the principle of least privilege where possible
- Storage Admin role is required for Cloud Run source deployments (creates temporary GCS buckets)

### 2. Cloud Build Service Account

**Email:** `26140490557@cloudbuild.gserviceaccount.com`

**Purpose:** Used by Cloud Build for building and deploying containers during Cloud Run source deployments.

#### Assigned IAM Roles

| Role | Purpose | Required For |
|------|---------|--------------|
| `roles/cloudbuild.builds.builder` | Execute build operations | Default Cloud Build role |
| `roles/iam.serviceAccountUser` | Impersonate service accounts | Cloud Run service execution |
| `roles/run.admin` | Full Cloud Run service management | Deploy and update services |
| `roles/storage.admin` | Create buckets and upload artifacts | Build artifacts and source code |
| `roles/serviceusage.serviceUsageConsumer` | Use Google Cloud services | API access during builds |

#### Configuration Commands

```bash
# Cloud Run Admin
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:26140490557@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Service Account User
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:26140490557@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Storage Admin
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member="serviceAccount:26140490557@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"
```

#### Verification

```bash
gcloud projects get-iam-policy infinity-ai-5ec7c \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:26140490557@cloudbuild.gserviceaccount.com"
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors (GitHub Actions)**
   - Verify all roles are assigned to `github-actions-deployer` using the verification command
   - Check that the service account key in GitHub secrets is current

2. **Permission Denied Errors (Cloud Build)**
   - Error: "Build failed because the default service account is missing required IAM permissions"
   - Solution: Grant `roles/run.admin`, `roles/iam.serviceAccountUser`, and `roles/storage.admin` to Cloud Build service account
   - Verify with: `gcloud projects get-iam-policy infinity-ai-5ec7c --filter="bindings.members:26140490557@cloudbuild.gserviceaccount.com"`

3. **Storage Access Errors**
   - Ensure `roles/storage.admin` is granted to both service accounts
   - Cloud Run source deployments require bucket creation permissions
   - Error: "storage.buckets.create access denied"

4. **Artifact Registry Errors**
   - Both reader and writer roles are needed
   - Reader: for pulling base images
   - Writer: for pushing built images

## Related Documentation

- [GCP Identity Alignment](./GCP_IDENTITY_LOG.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Architecture Documentation](./docs/ARCHITECTURE.md)
