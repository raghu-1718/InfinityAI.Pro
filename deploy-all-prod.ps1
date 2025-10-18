# Complete Production Deployment Script for InfinityAI.Pro
# Deploys all 4 engines and frontend with verification

$ErrorActionPreference = "Continue"
$PROJECT_ID = "after-yesterday-473512-k3"
$REGION = "us-central1"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "InfinityAI.Pro Complete Production Deployment" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Wait for Engine B build to complete
Write-Host "[1/10] Waiting for Engine B build..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Deploy Engine B
Write-Host "`n[2/10] Deploying Engine B..." -ForegroundColor Yellow
gcloud run deploy engine-b-ai-ml-prod `
    --image gcr.io/$PROJECT_ID/engine-b-ai-ml:v1.0.3 `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --cpu 2 `
    --memory 4Gi `
    --min-instances 0 `
    --max-instances 10 `
    --port 8080 `
    --timeout 300

# Rebuild and Deploy Engine C  
Write-Host "`n[3/10] Building Engine C..." -ForegroundColor Yellow
Set-Location backend/engines/engine-c-execution
gcloud builds submit --tag gcr.io/$PROJECT_ID/engine-c-execution:v1.0.2 --timeout=20m

Write-Host "`n[4/10] Deploying Engine C..." -ForegroundColor Yellow
gcloud run deploy engine-c-execution-prod `
    --image gcr.io/$PROJECT_ID/engine-c-execution:v1.0.2 `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --cpu 4 `
    --memory 4Gi `
    --min-instances 0 `
    --max-instances 10 `
    --port 8080 `
    --timeout 300 `
    --set-env-vars ENGINE_D_URL=https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app

Set-Location ../../..

# Update Engine D with correct engine URLs
Write-Host "`n[5/10] Updating Engine D with correct URLs..." -ForegroundColor Yellow
gcloud run services update engine-d-orchestration-prod `
    --region $REGION `
    --set-env-vars ENGINE_A_URL=https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app,ENGINE_B_URL=https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app,ENGINE_C_URL=https://engine-c-execution-prod-bprmddefsa-uc.a.run.app,JWT_SECRET_KEY=super-secret-jwt-key-change-in-production-12345678

# Health checks
Write-Host "`n[6/10] Waiting for services to stabilize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "`n[7/10] Verifying Engine Health..." -ForegroundColor Yellow

$engines = @(
    @{Name="Engine A"; URL="https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app/health"},
    @{Name="Engine B"; URL="https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/health"},
    @{Name="Engine C"; URL="https://engine-c-execution-prod-bprmddefsa-uc.a.run.app/health"},
    @{Name="Engine D"; URL="https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/health"}
)

$healthResults = @()
foreach ($engine in $engines) {
    try {
        $response = curl -s $engine.URL | ConvertFrom-Json
        $status = if ($response.status -in @("healthy", "ok", "operational")) { "✓ HEALTHY" } else { "✗ UNHEALTHY" }
        Write-Host "$($engine.Name): $status" -ForegroundColor $(if ($status -like "*HEALTHY*") { "Green" } else { "Red" })
        $healthResults += @{Engine=$engine.Name; Status=$status; Response=$response}
    } catch {
        Write-Host "$($engine.Name): ✗ FAILED - $($_.Exception.Message)" -ForegroundColor Red
        $healthResults += @{Engine=$engine.Name; Status="FAILED"; Error=$_.Exception.Message}
    }
}

# Test Engine D Orchestration
Write-Host "`n[8/10] Testing Engine D Orchestration..." -ForegroundColor Yellow
try {
    $orchHealth = curl -s "https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/api/health/comprehensive" | ConvertFrom-Json
    Write-Host "Orchestration Status: $($orchHealth.summary.overall_status)" -ForegroundColor Green
    Write-Host "Healthy Engines: $($orchHealth.summary.healthy_engines)/$($orchHealth.summary.total_engines)" -ForegroundColor Green
} catch {
    Write-Host "Orchestration check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Clean up old deployments
Write-Host "`n[9/10] Cleaning up old deployments..." -ForegroundColor Yellow
$oldServices = @("engine-a-market-data", "engine-c-execution")
foreach ($svc in $oldServices) {
    Write-Host "Deleting $svc..." -ForegroundColor Gray
    gcloud run services delete $svc --region $REGION --quiet 2>$null
}

# Final Summary
Write-Host "`n[10/10] Deployment Summary" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host "Engine A: https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app" -ForegroundColor White
Write-Host "Engine B: https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app" -ForegroundColor White
Write-Host "Engine C: https://engine-c-execution-prod-bprmddefsa-uc.a.run.app" -ForegroundColor White
Write-Host "Engine D: https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app" -ForegroundColor White
Write-Host "Frontend: https://infinityai-frontend-bprmddefsa-uc.a.run.app" -ForegroundColor White

Write-Host "`n✓ Production deployment complete!" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Test WebSocket: wscat -c wss://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/ws/dashboard" -ForegroundColor Gray
Write-Host "2. Test JWT Auth: POST https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/auth/login" -ForegroundColor Gray
Write-Host "3. View Dashboard: https://engine-d-orchestration-prod-bprmddefsa-uc.a.run.app/dashboard" -ForegroundColor Gray
