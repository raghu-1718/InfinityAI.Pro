#!/bin/bash

# Engine B - AI/ML Service - GCP Cloud Run Deployment Script

set -e

echo "🤖 Deploying Engine B - AI/ML Service to GCP Cloud Run..."

# Configuration
PROJECT_ID="infinityai-pro"
SERVICE_NAME="engine-b-ai-ml"
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
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --port=8001 \
    --timeout=300s

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo "✅ Engine B deployed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🔍 Health Check: ${SERVICE_URL}/health"
echo "🤖 AI Signals API: ${SERVICE_URL}/api/ai-signals"