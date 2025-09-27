# Azure AI Foundry Migration Guide for InfinityAI.Pro

## Overview

This guide provides step-by-step instructions for migrating InfinityAI.Pro's AI services to Azure AI Foundry as part of the hybrid cloud architecture. The hybrid approach combines:

- **Linode**: Storage, compute, and lightweight AI services
- **Azure AI Foundry**: Managed AI services (GPT-4, DALL-E, Whisper, Embeddings)

## Prerequisites

### 1. Azure Account Setup
- Active Azure subscription with sufficient credits
- Azure CLI installed (`curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`)
- Access to Azure AI services in South India region

### 2. Linode Instance
- Running InfinityAI.Pro backend
- PostgreSQL database configured
- Docker and Docker Compose installed

### 3. Environment Variables
Ensure your `.env` file has the necessary Azure configurations (will be added by setup script).

## Step-by-Step Migration

### Step 1: Azure CLI Setup and Authentication

```bash
# Install Azure CLI (if not already installed)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login --use-device-code

# Verify login
az account show
```

### Step 2: Run Automated Setup Script

Navigate to your project directory and run the Azure AI setup script:

```bash
cd /workspaces/InfinityAI.Pro/infinityai-pro
python setup_azure_ai.py
```

This script will:
- Create resource group `infinityai-rg` in South India
- Set up Azure AI Foundry project `infinityai-pro`
- Deploy GPT-4, DALL-E 3, and Whisper models
- Configure endpoints and API keys
- Update your `.env` file with Azure credentials

### Step 3: Verify Azure AI Configuration

After running the setup script, verify the configuration:

```bash
# Check environment variables
grep AZURE .env

# Test Azure AI connection (optional)
python -c "
import asyncio
from services.ai.azure_ai_client import get_azure_ai_client

async def test():
    client = await get_azure_ai_client()
    async with client as c:
        result = await c.health_check()
        print('Azure AI Health:', result)

asyncio.run(test())
"
```

### Step 4: Update Docker Configuration

Update your `docker-compose.yml` to optimize for hybrid cloud:

```yaml
version: '3.8'

services:
  infinityai-backend:
    build: .
    environment:
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
      - AZURE_AI_PROJECT=${AZURE_AI_PROJECT}
      # Disable heavy local AI models to save space
      - OLLAMA_MODEL=llama3.2:latest  # Keep lightweight LLM
      - WHISPER_MODEL=tiny
      - DIFFUSERS_MODEL=stabilityai/sd-turbo
      - YOLO_MODEL=yolov8n.pt
      - SBERT_MODEL=all-MiniLM-L6-v2
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./trade_logs:/app/trade_logs
    depends_on:
      - postgres
    ports:
      - "8000:8000"

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=infinityai
      - POSTGRES_USER=infinityai
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Step 5: Deploy to Linode

Deploy the updated configuration to your Linode instance:

```bash
# On your Linode instance
cd /path/to/infinityai-pro

# Pull latest changes
git pull origin main

# Update environment variables
nano .env  # Add Azure AI variables

# Rebuild and restart services
docker-compose down
docker-compose up --build -d

# Check logs
docker-compose logs -f infinityai-backend
```

### Step 6: Test Hybrid AI Services

Test that both local and Azure AI services work:

```bash
# Test health check
curl http://localhost:8000/api/ai/health

# Test chat completion (should use Azure AI)
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test the hybrid AI setup"}'

# Test image generation (should use Azure DALL-E)
curl -X POST http://localhost:8000/api/ai/generate-image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic trading dashboard"}'
```

## Cost Optimization

### Azure AI Foundry Pricing (South India)
- **GPT-4**: $0.03/1K input tokens, $0.06/1K output tokens
- **DALL-E 3**: $0.04 - $0.08 per image
- **Whisper**: $0.006/minute
- **Embeddings**: $0.0001/1K tokens

### Linode Instance (Mumbai)
- **Shared CPU**: $6/month (2GB RAM, 1 CPU)
- **Dedicated CPU**: $12/month (4GB RAM, 2 CPUs)
- **Storage**: $0.10/GB/month

### Estimated Monthly Costs
- **Full Azure AI**: ~$50-100/month (depending on usage)
- **Linode Storage**: ~$20/month (200GB)
- **Total Hybrid**: ~$70-120/month

## Monitoring and Maintenance

### Azure Portal Monitoring
1. Go to Azure Portal → AI Foundry projects
2. Monitor usage and costs in the "Cost Management" section
3. Check model performance and latency metrics

### Application Monitoring
```bash
# Check AI service health
curl http://localhost:8000/api/ai/health

# Monitor logs for Azure AI usage
docker-compose logs infinityai-backend | grep -i azure
```

### Cost Alerts
Set up cost alerts in Azure Portal:
1. Go to Cost Management → Budgets
2. Create budget alert for $100/month
3. Configure email notifications

## Troubleshooting

### Common Issues

1. **Azure Authentication Failed**
   ```bash
   # Re-login to Azure
   az logout
   az login --use-device-code
   ```

2. **Model Deployment Failed**
   ```bash
   # Check Azure quotas
   az quota show --scope /subscriptions/<subscription-id>/providers/Microsoft.MachineLearning --quota Quota1
   ```

3. **API Key Issues**
   ```bash
   # Regenerate API keys
   az ml workspace keys regenerate --workspace infinityai-pro --resource-group infinityai-rg --key primary
   ```

4. **Endpoint Connection Failed**
   - Check firewall settings
   - Verify endpoint URLs in Azure Portal
   - Ensure correct region (South India)

### Performance Optimization

1. **Caching**: Implement response caching for frequent queries
2. **Batch Processing**: Use batch APIs for multiple requests
3. **Model Selection**: Choose appropriate model sizes for cost-performance balance

## Backup and Recovery

### Data Backup
- Database backups remain on Linode
- Model artifacts cached locally
- Azure AI configurations backed up in `.env`

### Service Failover
- If Azure AI is unavailable, services automatically fall back to local models
- Monitor service health endpoints for automatic alerts

## Security Considerations

1. **API Key Management**
   - Store keys securely in environment variables
   - Rotate keys regularly
   - Use Azure Key Vault for production

2. **Network Security**
   - Configure Azure Virtual Networks
   - Use Azure Private Endpoints for secure access
   - Implement rate limiting and DDoS protection

3. **Data Privacy**
   - Ensure data residency compliance
   - Use Azure's data encryption features
   - Implement proper access controls

## Next Steps

1. **Production Deployment**
   - Set up staging environment
   - Implement CI/CD pipelines
   - Configure monitoring and alerting

2. **Advanced Features**
   - Custom model fine-tuning
   - Batch processing pipelines
   - Integration with Azure Cognitive Services

3. **Cost Optimization**
   - Implement usage analytics
   - Set up auto-scaling
   - Optimize model selection based on use case

## Support

For issues with Azure AI Foundry integration:
- Azure AI Documentation: https://learn.microsoft.com/en-us/azure/ai/
- Azure Support: https://azure.microsoft.com/en-in/support/
- InfinityAI.Pro Documentation: Check project README and docs/

---

**Migration completed successfully!** 🎉

Your InfinityAI.Pro now runs on a cost-effective hybrid cloud architecture with unlimited storage on Linode and managed AI services on Azure.