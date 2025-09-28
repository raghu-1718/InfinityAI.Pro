# InfinityAI.Pro Cloud Deployment Guide

## Overview
This guide covers deploying InfinityAI.Pro to various cloud providers to resolve local disk space limitations and enable production URLs.

## Current Issue: Localhost vs Production URLs

### Why Localhost?
- Currently running in **development mode** with Docker Compose
- Environment variables point to `localhost` for local development
- Frontend configured with `REACT_APP_API_URL=http://localhost:8000`

### Production URL Configuration
When deployed to cloud, update these environment variables:
- `REACT_APP_API_URL`: Your backend service URL
- `VECTOR_DB_URL`: Your ChromaDB service URL
- `FRONTEND_URL`: Your frontend service URL (for CORS)

## Cloud Deployment Options

### 1. Render (Recommended for Simplicity)

**Pros:**
- Easy deployment with existing `render.yaml`
- Built-in SSL certificates
- Automatic scaling
- Managed databases

**Cons:**
- Limited free tier storage (1GB)
- Build time limits

**Updated Configuration:**
```yaml
# render.yaml (already updated)
- Increased disk space to 10GB
- Staged dependency installation
- Separate frontend service
- Production URLs configured
```

**Deployment Steps:**
```bash
# Install Render CLI
npm install -g @render/cli

# Deploy
render deploy
```

### 2. Azure Container Apps

**Pros:**
- Excellent for AI/ML workloads
- Auto-scaling based on HTTP traffic
- Integrated with Azure AI services
- Generous free tier

**Cons:**
- More complex setup
- Azure-specific knowledge required

**Deployment:**
```bash
# Install Azure CLI
# Deploy Bicep template
az deployment group create \
  --resource-group infinityai-rg \
  --template-file infra/azure-bicep/container-apps/main.bicep
```

### 3. Linode Kubernetes Engine (LKE)

**Pros:**
- Full Kubernetes control
- High-performance storage
- Competitive pricing
- GPU instances available

**Cons:**
- Steeper learning curve
- Manual scaling management

**Deployment:**
```bash
# Install Linode CLI and kubectl
# Apply Kubernetes manifests
kubectl apply -f infra/linode-k8s/deployment.yaml
```

### 4. DigitalOcean App Platform

**Pros:**
- Simple deployment like Render
- Good for containerized apps
- Competitive pricing

**Cons:**
- Limited AI/ML optimization

## Environment Configuration for Production

### Backend Environment Variables
```bash
# Production URLs (replace with actual service URLs)
VECTOR_DB_URL=https://your-chromadb-service.com
FRONTEND_URL=https://your-frontend-app.com

# Keep existing API keys and secrets
OPENAI_API_KEY=your_key
HF_TOKEN=your_token
# ... other secrets
```

### Frontend Environment Variables
```bash
REACT_APP_API_URL=https://your-backend-service.com
NODE_ENV=production
```

## Storage Solutions for AI Models

### Option 1: Cloud Object Storage
- **Azure Blob Storage** or **AWS S3** for model storage
- Load models on-demand to reduce container size
- Cache frequently used models

### Option 2: Managed Vector Databases
- **Pinecone**, **Weaviate Cloud**, or **Azure Cognitive Search**
- Offload vector storage to managed services
- Reduce local storage requirements

### Option 3: GPU Instances
- Use cloud GPU instances for model inference
- Keep lightweight containers for web services
- Use RunPod or Azure ML for heavy AI workloads

## Migration Steps

### Step 1: Choose Provider
Based on your needs:
- **Render**: Quick and simple
- **Azure**: Enterprise features
- **Linode**: Performance and control

### Step 2: Update Environment Variables
```bash
# Create production .env file
cp .env .env.production
# Edit URLs to point to production services
```

### Step 3: Build Optimized Images
```bash
# Use multi-stage builds to reduce image size
# Separate heavy dependencies installation
```

### Step 4: Deploy and Test
```bash
# Deploy to chosen provider
# Update DNS if needed
# Test all endpoints
```

## Cost Comparison

| Provider | Free Tier | Storage | AI/ML Support |
|----------|-----------|---------|----------------|
| Render | 750hrs/month | 1GB → 10GB | Limited |
| Azure | $200 credit | Unlimited | Excellent |
| Linode | - | High-performance | Good |
| DigitalOcean | - | Standard | Basic |

## Recommended Approach

1. **Start with Render** for quick deployment
2. **Migrate to Azure** if you need more AI capabilities
3. **Use Linode** for high-performance requirements

## Next Steps

1. Choose your preferred cloud provider
2. Update the environment variables in the respective deployment files
3. Deploy using the provided configurations
4. Test the production deployment
5. Monitor performance and scale as needed

This resolves both the localhost URL issue and the disk storage limitations by leveraging cloud infrastructure designed for AI/ML workloads.