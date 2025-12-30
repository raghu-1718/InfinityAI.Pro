#!/usr/bin/env bash
set -e

echo "🚀 Deploying InfinityAI.Pro (Canonical Script)"

PROJECT_ID=$(gcloud config get-value project)
# Extract region from truth file (requires jq or grep/sed hack if jq missing, simplified here)
if [ -f "infra_snapshot/infra_truth.json" ]; then
  REGION=$(grep -o '"region": "[^"]*"' infra_snapshot/infra_truth.json | head -1 | cut -d'"' -f4)
else
  REGION="us-central1"
fi
[ -z "$REGION" ] && REGION="us-central1"

echo "Target: $PROJECT_ID ($REGION)"

# --- Backend (Cloud Run) ---
echo "Deploying Backend Engines..."
gcloud run deploy engine-a --source backend/engine-a --region "$REGION" --project "$PROJECT_ID" --quiet
gcloud run deploy engine-b --source backend/engine-b --region "$REGION" --project "$PROJECT_ID" --quiet
gcloud run deploy engine-c --source backend/engine-c --region "$REGION" --project "$PROJECT_ID" --quiet

# --- Firebase Functions ---
echo "Deploying Firebase Functions..."
firebase deploy --only functions --project "$PROJECT_ID"

# --- Frontend (Firebase Hosting) ---
echo "Deploying Frontend..."
firebase deploy --only hosting --project "$PROJECT_ID"

echo "✅ Deployment complete"
