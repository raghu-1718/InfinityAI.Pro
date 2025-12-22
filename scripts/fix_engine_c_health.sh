#!/bin/bash
# Quick Deploy Script for Engine C Health Fix
# Redeploys Engine C with latest code to fix /health endpoint

set -e

PROJECT_ID="gen-lang-client-0779271931"
REGION="us-central1"
SERVICE_NAME="engine-c-execution-prod"
IMAGE_NAME="engine-c-oauth:latest"
REPO_PATH="us-central1-docker.pkg.dev/${PROJECT_ID}/infinityai-repo"

echo "============================================"
echo "🔧 Engine C Health Endpoint Fix Deployment"
echo "============================================"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Not authenticated to gcloud"
    echo "Run: gcloud auth login"
    exit 1
fi

echo "✅ Authenticated to GCP"
echo ""

# Build and push new image
echo "📦 Building Engine C container..."
cd /workspaces/InfinityAI.Pro/backend/engines/engine-c-execution

# Authenticate Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build image
docker build -t ${REPO_PATH}/${IMAGE_NAME} -f Dockerfile .

if [ $? -eq 0 ]; then
    echo "✅ Build successful"
else
    echo "❌ Build failed"
    exit 1
fi

echo ""
echo "🚀 Pushing image to Artifact Registry..."
docker push ${REPO_PATH}/${IMAGE_NAME}

if [ $? -eq 0 ]; then
    echo "✅ Push successful"
else
    echo "❌ Push failed"
    exit 1
fi

echo ""
echo "🔄 Deploying to Cloud Run..."

gcloud run deploy ${SERVICE_NAME} \
    --image=${REPO_PATH}/${IMAGE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --platform=managed \
    --allow-unauthenticated \
    --cpu=2 \
    --memory=2Gi \
    --max-instances=5 \
    --timeout=300s \
    --service-account=vertex-express@${PROJECT_ID}.iam.gserviceaccount.com

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful"
else
    echo "❌ Deployment failed"
    exit 1
fi

echo ""
echo "🏥 Testing health endpoint..."
sleep 5  # Wait for service to stabilize

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format="value(status.url)")
HEALTH_URL="${SERVICE_URL}/health"

echo "Testing: ${HEALTH_URL}"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "${HEALTH_URL}")

if [ "${HTTP_CODE}" = "200" ]; then
    echo "✅ Health check passed (HTTP ${HTTP_CODE})"
    echo ""
    echo "🎉 Engine C health endpoint fix complete!"
else
    echo "⚠️  Health check returned HTTP ${HTTP_CODE}"
    echo "Expected 200, please investigate"
fi

echo ""
echo "Service URL: ${SERVICE_URL}"
echo "Health URL: ${HEALTH_URL}"
echo ""
