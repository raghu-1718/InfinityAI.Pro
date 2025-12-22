# =====================================================================
# InfinityAI.Pro - GCP Legacy Resource Cleanup Script (PowerShell)
# =====================================================================
# Purpose: Delete all Angel/TOTP components and legacy duplicate engines
# Project: gen-lang-client-0779271931
# Date: November 28, 2025
# =====================================================================

$ErrorActionPreference = "Stop"

$PROJECT_ID = "gen-lang-client-0779271931"
$REGION = "us-central1"

Write-Host "🧹 Starting GCP Resource Cleanup for InfinityAI.Pro" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host ""

# =====================================================================
# Step 1: Delete Legacy/Duplicate Cloud Run Services
# =====================================================================
Write-Host "📦 Step 1: Deleting legacy Cloud Run services..." -ForegroundColor Yellow

$LEGACY_SERVICES = @(
    "engine-a",
    "engine-b-ai-ml-prod",
    "engine-c-execution-prod",
    "engine-d-orchestration-prod",
    "engine-analytics",
    "engine-core",
    "engine-execution"
)

foreach ($service in $LEGACY_SERVICES) {
    Write-Host "  Checking service: $service"
    try {
        $null = gcloud run services describe $service --region=$REGION --project=$PROJECT_ID 2>&1
        Write-Host "  ❌ Deleting: $service" -ForegroundColor Red
        gcloud run services delete $service --region=$REGION --project=$PROJECT_ID --quiet
    }
    catch {
        Write-Host "  ✅ Not found (already deleted or never existed): $service" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✅ Cloud Run service cleanup complete!" -ForegroundColor Green

# =====================================================================
# Step 2: Delete Angel/TOTP Secrets from Secret Manager
# =====================================================================
Write-Host ""
Write-Host "🔐 Step 2: Deleting Angel/TOTP secrets from Google Secret Manager..." -ForegroundColor Yellow

$ANGEL_SECRETS = @(
    "angel-api-key",
    "angel-pin",
    "angel-totp-token",
    "angel-totp-secret",
    "angel-jwt-token",
    "angel-client-id",
    "angel-password",
    "smartapi-key",
    "smartapi-secret"
)

foreach ($secret in $ANGEL_SECRETS) {
    Write-Host "  Checking secret: $secret"
    try {
        $null = gcloud secrets describe $secret --project=$PROJECT_ID 2>&1
        Write-Host "  ❌ Deleting: $secret" -ForegroundColor Red
        gcloud secrets delete $secret --project=$PROJECT_ID --quiet
    }
    catch {
        Write-Host "  ✅ Not found (already deleted or never existed): $secret" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✅ Secret Manager cleanup complete!" -ForegroundColor Green

# =====================================================================
# Step 3: Delete Legacy Gemini API Secrets (Optional - if not needed)
# =====================================================================
Write-Host ""
Write-Host "🤖 Step 3: Cleaning up unused Gemini API secrets..." -ForegroundColor Yellow

$GEMINI_SECRETS = @(
    "gemini-api-key-primary",
    "gemini-api-key-secondary",
    "gemini-api-key"
)

foreach ($secret in $GEMINI_SECRETS) {
    Write-Host "  Checking secret: $secret"
    try {
        $null = gcloud secrets describe $secret --project=$PROJECT_ID 2>&1
        Write-Host "  ⚠️  Found: $secret (Review if still needed for future AI features)" -ForegroundColor Yellow
        # Uncomment to delete:
        # gcloud secrets delete $secret --project=$PROJECT_ID --quiet
    }
    catch {
        Write-Host "  ✅ Not found: $secret" -ForegroundColor Green
    }
}

Write-Host ""

# =====================================================================
# Step 4: List Remaining Cloud Run Services (Verification)
# =====================================================================
Write-Host ""
Write-Host "🔍 Step 4: Listing remaining Cloud Run services..." -ForegroundColor Cyan
Write-Host ""
gcloud run services list --region=$REGION --project=$PROJECT_ID

# =====================================================================
# Step 5: List Remaining Secrets (Verification)
# =====================================================================
Write-Host ""
Write-Host "🔍 Step 5: Listing remaining secrets..." -ForegroundColor Cyan
Write-Host ""
gcloud secrets list --project=$PROJECT_ID --format="table(name,createTime)"

# =====================================================================
# Final Report
# =====================================================================
Write-Host ""
Write-Host "✅ GCP Resource Cleanup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "  • Legacy Cloud Run services deleted"
Write-Host "  • Angel/TOTP secrets removed"
Write-Host "  • Gemini secrets reviewed (preserved for future use)"
Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Deploy the new 3-engine architecture (engine-analytics, engine-core, engine-execution)"
Write-Host "  2. Configure Dhan OAuth credentials in Secret Manager"
Write-Host "  3. Verify custom domain mappings point to new services"
Write-Host "  4. Test end-to-end flow: OAuth → Signal → Execution"
Write-Host ""
Write-Host "🚀 Ready for production deployment!" -ForegroundColor Green
