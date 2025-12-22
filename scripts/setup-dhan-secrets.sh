#!/bin/bash
# =====================================================================
# InfinityAI.Pro - Dhan OAuth Secret Configuration Script
# =====================================================================
# Purpose: Set up DhanHQ OAuth credentials in Google Secret Manager
# Project: gen-lang-client-0779271931
# Date: November 28, 2025
# =====================================================================

set -e

PROJECT_ID="gen-lang-client-0779271931"

echo "🔐 InfinityAI.Pro - Dhan OAuth Secret Setup"
echo "Project: $PROJECT_ID"
echo ""

# =====================================================================
# Step 1: Prompt for Dhan Credentials
# =====================================================================
echo "📋 Step 1: Enter your DhanHQ OAuth credentials"
echo ""

read -p "Enter Dhan Client ID: " DHAN_CLIENT_ID
read -sp "Enter Dhan API Secret: " DHAN_API_SECRET
echo ""
read -sp "Enter Dhan Access Token (from OAuth flow): " DHAN_ACCESS_TOKEN
echo ""
read -p "Enter Dhan Redirect URI (default: https://infinityai.pro/api/auth/dhan/callback): " DHAN_REDIRECT_URI
DHAN_REDIRECT_URI=${DHAN_REDIRECT_URI:-"https://infinityai.pro/api/auth/dhan/callback"}

echo ""
echo "✅ Credentials collected"
echo ""

# =====================================================================
# Step 2: Create Secrets in Google Secret Manager
# =====================================================================
echo "🔐 Step 2: Creating secrets in Google Secret Manager..."
echo ""

# Create DHAN_CLIENT_ID
echo "Creating secret: dhan-client-id"
echo -n "$DHAN_CLIENT_ID" | gcloud secrets create dhan-client-id \
  --replication-policy="automatic" \
  --data-file=- \
  --project="$PROJECT_ID" || echo "Secret already exists, creating new version..."

echo -n "$DHAN_CLIENT_ID" | gcloud secrets versions add dhan-client-id \
  --data-file=- \
  --project="$PROJECT_ID" 2>/dev/null || true

# Create DHAN_API_SECRET
echo "Creating secret: dhan-api-secret"
echo -n "$DHAN_API_SECRET" | gcloud secrets create dhan-api-secret \
  --replication-policy="automatic" \
  --data-file=- \
  --project="$PROJECT_ID" || echo "Secret already exists, creating new version..."

echo -n "$DHAN_API_SECRET" | gcloud secrets versions add dhan-api-secret \
  --data-file=- \
  --project="$PROJECT_ID" 2>/dev/null || true

# Create DHAN_ACCESS_TOKEN
echo "Creating secret: dhan-access-token"
echo -n "$DHAN_ACCESS_TOKEN" | gcloud secrets create dhan-access-token \
  --replication-policy="automatic" \
  --data-file=- \
  --project="$PROJECT_ID" || echo "Secret already exists, creating new version..."

echo -n "$DHAN_ACCESS_TOKEN" | gcloud secrets versions add dhan-access-token \
  --data-file=- \
  --project="$PROJECT_ID" 2>/dev/null || true

# Create DHAN_REDIRECT_URI
echo "Creating secret: dhan-redirect-uri"
echo -n "$DHAN_REDIRECT_URI" | gcloud secrets create dhan-redirect-uri \
  --replication-policy="automatic" \
  --data-file=- \
  --project="$PROJECT_ID" || echo "Secret already exists, creating new version..."

echo -n "$DHAN_REDIRECT_URI" | gcloud secrets versions add dhan-redirect-uri \
  --data-file=- \
  --project="$PROJECT_ID" 2>/dev/null || true

echo ""
echo "✅ All Dhan secrets created successfully!"

# =====================================================================
# Step 3: Grant Cloud Run Service Account Access
# =====================================================================
echo ""
echo "🔑 Step 3: Granting Cloud Run service account access to secrets..."
echo ""

SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

SECRETS=("dhan-client-id" "dhan-api-secret" "dhan-access-token" "dhan-redirect-uri")

for secret in "${SECRETS[@]}"; do
  echo "Granting access to: $secret"
  gcloud secrets add-iam-policy-binding "$secret" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID" --quiet
done

echo ""
echo "✅ Service account access granted!"

# =====================================================================
# Step 4: Verify Secret Creation
# =====================================================================
echo ""
echo "🔍 Step 4: Verifying secrets..."
echo ""
gcloud secrets list --project="$PROJECT_ID" --filter="name:dhan-*" --format="table(name,createTime)"

# =====================================================================
# Final Report
# =====================================================================
echo ""
echo "✅ Dhan OAuth Secret Setup Complete!"
echo ""
echo "📋 Secrets Created:"
echo "  • dhan-client-id"
echo "  • dhan-api-secret"
echo "  • dhan-access-token"
echo "  • dhan-redirect-uri"
echo ""
echo "🎯 Next Steps:"
echo "  1. Deploy engines with these secrets configured"
echo "  2. Test OAuth flow: /api/auth/dhan/login"
echo "  3. Exchange authorization code for access token"
echo "  4. Update dhan-access-token secret after OAuth completion"
echo ""
echo "🚀 Ready for deployment!"
