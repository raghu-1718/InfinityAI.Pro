#!/bin/bash

# Engine A - Market Data Service - GCP Cloud Run Deployment Script

set -e

echo "🎯 Deploying Engine A - Market Data Service to GCP Cloud Run..."

# Configuration
PROJECT_ID="infinityai-pro"
SERVICE_NAME="engine-a-market-data"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Build and push Docker image
echo "🔧 Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo "📤 Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=1 \
    --max-instances=10 \
    --port=8000 \
    --set-env-vars="DHAN_ACCESS_TOKEN=${DHAN_ACCESS_TOKEN},DHAN_CLIENT_ID=${DHAN_CLIENT_ID}" \
    --timeout=300s

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo "✅ Engine A deployed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🔍 Health Check: ${SERVICE_URL}/health"
echo "📊 Signals API: ${SERVICE_URL}/api/signals"