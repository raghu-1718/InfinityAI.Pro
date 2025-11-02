# Grant required permissions to GitHub Actions service account for Cloud Build
$project = "infinitygt-b2287"
$sa = "github-actions-service-account@infinitygt-b2287.iam.gserviceaccount.com"

Write-Host "`n=== Granting Cloud Build Permissions ===" -ForegroundColor Cyan

# Service Usage Consumer
Write-Host "Adding Service Usage Consumer role..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa" `
  --role="roles/serviceusage.serviceUsageConsumer"

# Cloud Build Builds Builder
Write-Host "Adding Cloud Build Builder role..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa" `
  --role="roles/cloudbuild.builds.builder"

# Artifact Registry Writer
Write-Host "Adding Artifact Registry Writer role..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa" `
  --role="roles/artifactregistry.writer"

# Storage Admin (for Cloud Build staging buckets)
Write-Host "Adding Storage Admin role..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $project `
  --member="serviceAccount:$sa" `
  --role="roles/storage.admin"

Write-Host "`n✓ All permissions granted. IAM propagation may take 1-2 minutes." -ForegroundColor Green
Write-Host "Ready to redeploy Engine B to Cloud Run." -ForegroundColor White
