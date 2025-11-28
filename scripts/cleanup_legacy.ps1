# scripts/cleanup_legacy.ps1
Write-Host "Starting Legacy Cleanup..." -ForegroundColor Yellow

# 1. Delete Legacy Cloud Run Services
$services = @("engine-a", "engine-b-ai-ml-prod", "engine-c-execution-prod", "engine-d-orchestration-prod")
foreach ($service in $services) {
    Write-Host "Deleting service: $service"
    gcloud run services delete $service --region us-central1 --quiet
}

# 2. Delete Legacy Secrets
$secrets = @("angel-api-key", "angel-pin", "angel-totp-token", "angel-jwt-token")
foreach ($secret in $secrets) {
    Write-Host "Deleting secret: $secret"
    gcloud secrets delete $secret --quiet
}

# 3. Warning about Project Deletion
Write-Host "NOTE: To delete the legacy project 'infinitygt-b2287', run:" -ForegroundColor Red
Write-Host "gcloud projects delete infinitygt-b2287" -ForegroundColor Red

Write-Host "Cleanup Complete." -ForegroundColor Green
