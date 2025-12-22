#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Grant Firebase secret access to Cloud Run services
.DESCRIPTION
    This script grants the necessary permissions for Cloud Run services to access
    the firebase-service-account secret stored in Google Secret Manager.
.EXAMPLE
    .\grant-firebase-secret-access.ps1
#>

$PROJECT_ID = "gen-lang-client-0779271931"
$SECRET_NAME = "firebase-service-account"
$REGION = "us-central1"

# List of Cloud Run services that need access to Firebase
$SERVICES = @(
    "engine-a",
    "engine-b-ai-ml-prod",
    "engine-c-execution-prod",
    "engine-c-execution  # Engine D merged-prod"
)

Write-Host "🔐 Granting Firebase Secret Access to Cloud Run Services" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

foreach ($service in $SERVICES) {
    Write-Host "Processing service: $service" -ForegroundColor Yellow
    
    try {
        # Get the service account for this Cloud Run service
        $serviceAccount = gcloud run services describe $service `
            --region=$REGION `
            --format="value(spec.template.spec.serviceAccountName)" `
            2>$null
        
        if ([string]::IsNullOrEmpty($serviceAccount)) {
            Write-Host "  ⚠️  Could not get service account (service may not exist)" -ForegroundColor Yellow
            continue
        }
        
        Write-Host "  Service Account: $serviceAccount" -ForegroundColor Gray
        
        # Grant Secret Manager Secret Accessor role
        $result = gcloud secrets add-iam-policy-binding $SECRET_NAME `
            --member="serviceAccount:$serviceAccount" `
            --role="roles/secretmanager.secretAccessor" `
            --project=$PROJECT_ID `
            2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Access granted successfully" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Failed to grant access: $result" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Firebase secret access configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To verify, run:" -ForegroundColor Cyan
Write-Host "  gcloud secrets get-iam-policy $SECRET_NAME" -ForegroundColor White
