#!/bin/bash
# =====================================================================
# InfinityAI.Pro - GCP Legacy Resource Cleanup Script
# =====================================================================
# Purpose: Delete all Angel/TOTP components and legacy duplicate engines
# Project: gen-lang-client-0779271931
# Date: November 28, 2025
# =====================================================================

set -e

PROJECT_ID="gen-lang-client-0779271931"
REGION="us-central1"

echo "🧹 Starting GCP Resource Cleanup for InfinityAI.Pro"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# =====================================================================
# Step 1: Delete Legacy/Duplicate Cloud Run Services
# =====================================================================
echo "📦 Step 1: Deleting legacy Cloud Run services..."

LEGACY_SERVICES=(
  "engine-a"
  "engine-b-ai-ml-prod"
  "engine-c-execution-prod"
  "engine-d-orchestration-prod"
  "engine-analytics"
  "engine-core"
  "engine-execution"
)

for service in "${LEGACY_SERVICES[@]}"; do
  echo "  Checking service: $service"
  if gcloud run services describe "$service" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ❌ Deleting: $service"
    gcloud run services delete "$service" --region="$REGION" --project="$PROJECT_ID" --quiet
  else
    echo "  ✅ Not found (already deleted or never existed): $service"
  fi
done

echo ""
echo "✅ Cloud Run service cleanup complete!"

# =====================================================================
# Step 2: Delete Angel/TOTP Secrets from Secret Manager
# =====================================================================
echo ""
echo "🔐 Step 2: Deleting Angel/TOTP secrets from Google Secret Manager..."

ANGEL_SECRETS=(
  "angel-api-key"
  "angel-pin"
  "angel-totp-token"
  "angel-totp-secret"
  "angel-jwt-token"
  "angel-client-id"
  "angel-password"
  "smartapi-key"
  "smartapi-secret"
)

for secret in "${ANGEL_SECRETS[@]}"; do
  echo "  Checking secret: $secret"
  if gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ❌ Deleting: $secret"
    gcloud secrets delete "$secret" --project="$PROJECT_ID" --quiet
  else
    echo "  ✅ Not found (already deleted or never existed): $secret"
  fi
done

echo ""
echo "✅ Secret Manager cleanup complete!"

# =====================================================================
# Step 3: Delete Legacy Gemini API Secrets (Optional - if not needed)
# =====================================================================
echo ""
echo "🤖 Step 3: Cleaning up unused Gemini API secrets..."

GEMINI_SECRETS=(
  "gemini-api-key-primary"
  "gemini-api-key-secondary"
  "gemini-api-key"
)

for secret in "${GEMINI_SECRETS[@]}"; do
  echo "  Checking secret: $secret"
  if gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ⚠️  Found: $secret (Review if still needed for future AI features)"
    # Uncomment to delete:
    # gcloud secrets delete "$secret" --project="$PROJECT_ID" --quiet
  else
    echo "  ✅ Not found: $secret"
  fi
done

echo ""

# =====================================================================
# Step 4: List Remaining Cloud Run Services (Verification)
# =====================================================================
echo ""
echo "🔍 Step 4: Listing remaining Cloud Run services..."
echo ""
gcloud run services list --region="$REGION" --project="$PROJECT_ID"

# =====================================================================
# Step 5: List Remaining Secrets (Verification)
# =====================================================================
echo ""
echo "🔍 Step 5: Listing remaining secrets..."
echo ""
gcloud secrets list --project="$PROJECT_ID" --format="table(name,createTime)"

# =====================================================================
# Final Report
# =====================================================================
echo ""
echo "✅ GCP Resource Cleanup Complete!"
echo ""
echo "📋 Summary:"
echo "  • Legacy Cloud Run services deleted"
echo "  • Angel/TOTP secrets removed"
echo "  • Gemini secrets reviewed (preserved for future use)"
echo ""
echo "🎯 Next Steps:"
echo "  1. Deploy the new 3-engine architecture (engine-analytics, engine-core, engine-execution)"
echo "  2. Configure Dhan OAuth credentials in Secret Manager"
echo "  3. Verify custom domain mappings point to new services"
echo "  4. Test end-to-end flow: OAuth → Signal → Execution"
echo ""
echo "🚀 Ready for production deployment!"
