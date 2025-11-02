#!/bin/bash
# Engine D Recovery Script
echo "Starting Engine D Recovery..."

# Check current status
echo "1. Checking Engine D status..."
curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/health | jq .

# Restart Cloud Run service
echo "2. Restarting Engine D service..."
gcloud run services update infinityai-engine-d \
    --region=us-central1 \
    --project=after-yesterday-473512-k3 \
    --port=8080 \
    --memory=512Mi \
    --cpu=1000m \
    --timeout=300s \
    --concurrency=100

# Wait for deployment
echo "3. Waiting for deployment..."
sleep 30

# Test endpoints
echo "4. Testing Engine D endpoints..."
curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/health
echo ""
curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/api/status

echo "Engine D recovery completed!"
