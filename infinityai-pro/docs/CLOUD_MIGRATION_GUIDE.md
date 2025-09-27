# Azure vs Linode Migration Plan for InfinityAI.Pro

## Current Situation
- **Platform**: Render (limited disk space: 271MB free)
- **Architecture**: Docker Compose with FastAPI backend, React frontend, Ollama, ChromaDB
- **AI Services**: RunPod GPU endpoints, local models (Whisper, YOLO, SD)
- **Storage Needs**: ~500MB+ for AI models, vector databases, trading data
- **GPU Needs**: Stable Diffusion, YOLO object detection, Whisper STT

## Azure Options

### Azure Container Apps (Recommended for Current Setup)
```yaml
# azure-bicep/container-apps/deploy.yml
services:
  - name: infinityai-backend
    image: infinityai/backend:latest
    cpu: 2.0
    memory: 4Gi
    env:
      - name: RUNPOD_API_KEY
        value: "@Microsoft.KeyVault(SecretUri=https://infinityai-kv.vault.azure.net/secrets/RUNPOD-API-KEY/)"
    scale:
      minReplicas: 1
      maxReplicas: 10
      rules:
        - name: cpu
          metric: cpu
          threshold: 70

  - name: infinityai-frontend
    image: infinityai/frontend:latest
    cpu: 1.0
    memory: 2Gi

  - name: ollama-service
    image: ollama/ollama:latest
    cpu: 4.0
    memory: 8Gi
    gpu: 1  # NVIDIA A100 or V100
    storage:
      - name: ollama-models
        size: 100Gi
        type: Premium_LRS
```

**Pricing Estimate**:
- Container Apps: $0.04/hour per vCPU + $0.00001/GB-s memory
- GPU VM (if needed): $3.67/hour (NC6s_v3 with Tesla K80)
- Storage: $0.15/GiB/month (Premium SSD)
- **Monthly Cost**: $800-1500 (depending on usage)

### Azure VM with GPU
- **NC-series**: Tesla K80, P100, V100, A100 GPUs
- **NV-series**: RTX 2080 Ti, RTX 3080 GPUs
- **Storage**: 1TB+ SSD, Azure Blob Storage for backups

## Linode Options

### Linode GPU Instances (Recommended)
```yaml
# Recommended: RTX4000 Ada x1 Large
instance_type: g2-gpu-rtx4000a1-l
specs:
  - GPU: RTX 4000 Ada (48GB VRAM)
  - CPU: 16 vCPUs
  - RAM: 64GB
  - Storage: 512GB NVMe SSD
  - Price: $638/month ($0.96/hour)

# Alternative: RTX4000 Ada x2 Medium
instance_type: g2-gpu-rtx4000a2-m
specs:
  - GPU: 2x RTX 4000 Ada (96GB VRAM total)
  - CPU: 16 vCPUs
  - RAM: 64GB
  - Storage: 1TB NVMe SSD
  - Price: $892/month ($1.34/hour)
```

### Linode Kubernetes Engine (LKE)
- Managed Kubernetes with GPU node pools
- RTX4000 Ada GPUs available
- S3-compatible Object Storage
- **Monthly Cost**: $600-1200

## Migration Strategy

### Phase 1: Quick Migration (Linode Recommended)
1. **Provision Linode GPU Instance**:
   ```bash
   # Create RTX4000 Ada x1 Large instance
   linode-cli linodes create \
     --type g2-gpu-rtx4000a1-l \
     --region us-east \
     --image linode/ubuntu22.04 \
     --label infinityai-gpu \
     --tags ai,trading,gpu
   ```

2. **Setup Docker Environment**:
   ```bash
   # Install Docker and NVIDIA drivers
   apt update && apt install -y docker.io nvidia-docker2
   systemctl enable docker
   ```

3. **Deploy Current Stack**:
   ```bash
   cd /infinityai-pro
   docker-compose up -d
   ```

4. **Configure GPU Support**:
   ```yaml
   # Add to docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

### Phase 2: Azure Migration (Scalable)
1. **Create Azure Resource Group**:
   ```bash
   az group create --name infinityai-rg --location eastus
   ```

2. **Deploy Container Apps**:
   ```bash
   az containerapp create \
     --name infinityai-backend \
     --resource-group infinityai-rg \
     --environment infinityai-env \
     --image infinityai/backend:latest \
     --cpu 2.0 \
     --memory 4Gi \
     --min-replicas 1 \
     --max-replicas 10 \
     --env-vars RUNPOD_API_KEY=secretref:runpod-api-key
   ```

## Cost Comparison

| Provider | Instance | GPU | RAM | Storage | Monthly Cost | Notes |
|----------|----------|-----|-----|---------|--------------|-------|
| **Linode** | RTX4000 Ada x1 Large | 1x RTX4000 | 64GB | 512GB NVMe | $638 | Best value, dedicated GPU |
| **Linode** | RTX4000 Ada x2 Medium | 2x RTX4000 | 64GB | 1TB NVMe | $892 | Multi-GPU option |
| **Azure** | NC6s_v3 | 1x Tesla K80 | 112GB | 736GB SSD | ~$800 | Older GPU, good for basic AI |
| **Azure** | NC12s_v3 | 2x Tesla K80 | 224GB | 1.5TB SSD | ~$1600 | Dual GPU option |
| **Azure** | Container Apps + GPU VM | Varies | Varies | Blob Storage | $600-2000 | More flexible scaling |

## Recommendation

**Go with Linode RTX4000 Ada x1 Large ($638/month)**

### Why Linode?
1. **Cost Effective**: $638 vs Azure's $800+ for similar specs
2. **Dedicated GPU**: Full access to RTX4000 Ada (better than Azure's shared GPUs)
3. **Storage**: 512GB NVMe SSD (expandable to 2TB+)
4. **Performance**: RTX4000 Ada has 48GB VRAM - perfect for your AI workloads
5. **Simplicity**: Single instance vs Azure's complex resource management

### Migration Steps:
1. Create Linode account and provision RTX4000 Ada instance
2. Install Docker and NVIDIA drivers
3. Clone your repository and deploy with docker-compose
4. Configure domain DNS to point to Linode IP
5. Test AI services with local GPU acceleration
6. Optionally migrate from RunPod to local GPU for cost savings

### Expected Benefits:
- ✅ **Unlimited disk space** (vs Render's 271MB limit)
- ✅ **Dedicated GPU** for faster AI processing
- ✅ **Cost savings** vs current RunPod + Render setup
- ✅ **Full control** over infrastructure
- ✅ **Scalability** with Linode's larger instances if needed