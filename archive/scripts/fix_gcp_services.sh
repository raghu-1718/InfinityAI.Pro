#!/bin/bash
# GCP Service Configuration Fixes

echo "🔧 Applying GCP service fixes..."

# 1. Fix Engine D configuration
echo "1. Fixing Engine D Cloud Run configuration..."
gcloud run services update infinityai-engine-d \
    --region=us-central1 \
    --project=after-yesterday-473512-k3 \
    --port=8080 \
    --memory=1Gi \
    --cpu=2 \
    --timeout=900s \
    --concurrency=1000 \
    --min-instances=0 \
    --max-instances=10 \
    --set-env-vars="PORT=8080,NODE_ENV=production"

# 2. Fix Firebase Functions timeout issues
echo "2. Updating Firebase Functions configuration..."
firebase functions:config:set \
    timeout.default=540 \
    memory.default=512MB \
    --project=infinity-ai-5ec7c

# 3. Update IAM permissions for cross-service communication
echo "3. Updating IAM permissions..."
gcloud projects add-iam-policy-binding after-yesterday-473512-k3 \
    --member="serviceAccount:infinity-ai-5ec7c@appspot.gserviceaccount.com" \
    --role="roles/run.invoker"

# 4. Restart all services in correct order
echo "4. Restarting services in order..."

# Start with Engine A (data source)
gcloud run services update infinityai-engine-a \
    --region=us-central1 \
    --project=after-yesterday-473512-k3

sleep 10

# Then Engine B (AI processing)
gcloud run services update infinityai-engine-b \
    --region=us-central1 \
    --project=after-yesterday-473512-k3

sleep 10

# Then Engine C (execution)
gcloud run services update infinityai-engine-c-execution \
    --region=us-central1 \
    --project=after-yesterday-473512-k3

sleep 10

# Finally Engine D (orchestration)
gcloud run services update infinityai-engine-d \
    --region=us-central1 \
    --project=after-yesterday-473512-k3

echo "✅ GCP service fixes completed!"
echo ""
echo "🧪 Testing services..."
curl -s https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app/health | jq .
curl -s https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app/health | jq .
curl -s https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app/health | jq .
curl -s https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/health | jq .

echo ""
echo "🎯 Next steps:"
echo "1. Wait 2-3 minutes for all services to fully restart"
echo "2. Refresh the dashboard at https://infinity-ai-5ec7c.web.app"
echo "3. Check engine status in the Engines page"
echo "4. Verify AI analysis components load properly"
