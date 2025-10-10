# InfinityAI.Pro Google Cloud Engine B Deployment
# Configure gcloud first: gcloud auth login

echo "🔴 Setting up Google Cloud Engine B..."

# 1. Set project (replace with your project ID)
gcloud config set project YOUR_PROJECT_ID

# 2. Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 3. Create GKE cluster for Engine B
gcloud container clusters create infinityai-engine-b-cluster \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type e2-medium \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 4

# 4. Get cluster credentials
gcloud container clusters get-credentials infinityai-engine-b-cluster --zone us-central1-a

# 5. Build and push Engine B container
cd infinityai-pro
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/infinityai-engine-b:latest ./backend/engines/engine-b

# 6. Deploy to GKE
kubectl create deployment infinityai-engine-b \
  --image=gcr.io/YOUR_PROJECT_ID/infinityai-engine-b:latest \
  --port=8001

# 7. Expose as LoadBalancer service
kubectl expose deployment infinityai-engine-b \
  --type=LoadBalancer \
  --port=80 \
  --target-port=8001 \
  --name=infinityai-engine-b-service

# 8. Get external IP
kubectl get service infinityai-engine-b-service --output jsonpath='{.status.loadBalancer.ingress[0].ip}'

# 9. Alternative: Deploy to Cloud Run (serverless)
gcloud run deploy infinityai-engine-b \
  --image gcr.io/YOUR_PROJECT_ID/infinityai-engine-b:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8001

# 10. Get Cloud Run URL
gcloud run services describe infinityai-engine-b \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'

echo "✅ Google Cloud Engine B deployment commands ready"
echo "Update YOUR_PROJECT_ID with your actual GCP project ID"