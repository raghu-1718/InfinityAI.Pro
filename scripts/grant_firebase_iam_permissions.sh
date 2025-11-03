#!/bin/bash

# Grant Firebase/RuntimeConfig IAM Permissions
# This fixes 403 errors blocking Firebase Functions deployment
# Date: November 3, 2025

set -euo pipefail

PROJECT_ID="after-yesterday-473512-k3"

# Get GitHub deployer service account email
# Replace with your actual GitHub deployer SA email
GITHUB_SA_EMAIL="${GITHUB_SA_EMAIL:-github-deployer@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "==================================================================="
echo "Granting Firebase IAM Permissions"
echo "==================================================================="
echo "Project: $PROJECT_ID"
echo "Service Account: $GITHUB_SA_EMAIL"
echo ""

# Set project context
gcloud config set project "$PROJECT_ID"

echo "1. Granting Cloud Functions Admin..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${GITHUB_SA_EMAIL}" \
    --role="roles/cloudfunctions.admin" \
    --quiet

echo "2. Granting Cloud Functions Service Agent..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${GITHUB_SA_EMAIL}" \
    --role="roles/cloudfunctions.serviceAgent" \
    --quiet

echo "3. Granting Runtime Config Admin..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${GITHUB_SA_EMAIL}" \
    --role="roles/runtimeconfig.admin" \
    --quiet

echo "4. Granting Viewer (for log streaming)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${GITHUB_SA_EMAIL}" \
    --role="roles/viewer" \
    --quiet

echo "5. Granting Service Usage Consumer..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${GITHUB_SA_EMAIL}" \
    --role="roles/serviceusage.serviceUsageConsumer" \
    --quiet

echo ""
echo "==================================================================="
echo "IAM Permissions Granted Successfully"
echo "==================================================================="
echo ""
echo "Verifying permissions..."
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${GITHUB_SA_EMAIL}" \
    --format="table(bindings.role)"

echo ""
echo "Next steps:"
echo "1. Trigger new deployment: git commit --allow-empty -m 'trigger: redeploy with IAM fixes' && git push"
echo "2. Monitor deployment: gh run watch"
echo "3. Verify all engines and functions deploy successfully"
