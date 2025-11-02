#!/bin/bash
# InfinityAI.Pro - Deploy Missing Endpoints Script
# Generated: 2025-10-24 12:18:58

echo "🚀 Deploying InfinityAI.Pro Missing Endpoints"
echo "Project: infinity-ai-5ec7c"
echo "Region: us-central1"

# Deploy Engine A with missing market-data endpoint
echo "📊 Deploying Engine A (Market Data)..."
cd engines/engine-a
gcloud run deploy infinityai-engine-a \
    --source . \
    --region us-central1 \
    --project infinity-ai-5ec7c \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=infinity-ai-5ec7c"

# Deploy Engine D with missing status endpoint  
echo "🎛️ Deploying Engine D (Orchestration)..."
cd ../engine-d
gcloud run deploy infinityai-engine-d \
    --source . \
    --region us-central1 \
    --project infinity-ai-5ec7c \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=infinity-ai-5ec7c"

echo "✅ Deployment complete!"
echo "🔗 Test endpoints:"
echo "   Engine A Market Data: https://infinityai-engine-a-26140490557.us-central1.run.app/api/market-data/NIFTY"
echo "   Engine D Status: https://infinityai-engine-d-26140490557.us-central1.run.app/api/status"
