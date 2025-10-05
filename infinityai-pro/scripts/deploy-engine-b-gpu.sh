#!/bin/bash
# Deploy Engine B with GPU acceleration to Google Cloud Run
# InfinityAI.Pro Trading Platform

set -e  # Exit on error

# Configuration
PROJECT_ID="after-yesterday-473512-k3"
SERVICE_NAME="infinityai-engine-b-gpu"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Engine B with GPU acceleration to Google Cloud"
echo "Project ID: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"

# Step 1: Build and push the Docker image
echo "📦 Building Docker image with GPU support..."
gcloud builds submit \
  --config=backend/engines/engine-b/cloudbuild.yaml \
  --project=${PROJECT_ID} \
  backend/engines/engine-b

echo "✅ Docker image built and pushed successfully"

# Step 2: Deploy to Cloud Run with GPU
echo "🚀 Deploying to Cloud Run with GPU..."

gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME}:latest \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --port=8000 \
  --memory=8Gi \
  --cpu=4 \
  --gpu=1 \
  --gpu-type=nvidia-tesla-t4 \
  --max-instances=10 \
  --min-instances=1 \
  --concurrency=50 \
  --timeout=300 \
  --execution-environment=gen2 \
  --set-env-vars="USE_GPU=true,CUDA_VISIBLE_DEVICES=0,NVIDIA_VISIBLE_DEVICES=all,NVIDIA_DRIVER_CAPABILITIES=compute,utility" \
  --project=${PROJECT_ID}

# Step 3: Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform=managed \
  --region=${REGION} \
  --format="value(status.url)" \
  --project=${PROJECT_ID})

echo "🎉 Deployment completed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🔍 Health check: ${SERVICE_URL}/health"

# Step 4: Test the deployment
echo "🧪 Testing the deployment..."
sleep 10  # Wait for service to be ready

HEALTH_RESPONSE=$(curl -s "${SERVICE_URL}/health" | head -c 500)
echo "Health check response: ${HEALTH_RESPONSE}"

if echo "${HEALTH_RESPONSE}" | grep -q "healthy"; then
    echo "✅ Health check passed!"
    echo "🔥 GPU acceleration status: $(echo "${HEALTH_RESPONSE}" | grep -o '"available":[^,]*')"
else
    echo "❌ Health check failed"
    exit 1
fi

# Step 5: Update load balancer configuration
echo "🔄 Updating load balancer configuration..."

# Read current config
LOAD_BALANCER_CONFIG="load-balancer-config.json"
if [ -f "${LOAD_BALANCER_CONFIG}" ]; then
    # Update Engine B endpoint with GPU-enabled service
    TEMP_CONFIG=$(mktemp)
    jq ".load_balancer_configuration.engines.engine_b.endpoint = \"${SERVICE_URL}\"" \
       "${LOAD_BALANCER_CONFIG}" > "${TEMP_CONFIG}"
    jq ".load_balancer_configuration.engines.engine_b.status = \"operational-gpu\"" \
       "${TEMP_CONFIG}" > "${LOAD_BALANCER_CONFIG}"
    rm "${TEMP_CONFIG}"
    
    echo "✅ Load balancer configuration updated"
else
    echo "⚠️  Load balancer config not found, skipping update"
fi

echo ""
echo "🎯 GPU-accelerated Engine B deployment summary:"
echo "   • Service URL: ${SERVICE_URL}"
echo "   • GPU Type: NVIDIA Tesla T4"
echo "   • Memory: 8GB"
echo "   • CPU: 4 cores"
echo "   • Max instances: 10"
echo "   • Region: ${REGION}"
echo ""
echo "🚀 Engine B is now GPU-accelerated and ready for high-performance AI processing!"