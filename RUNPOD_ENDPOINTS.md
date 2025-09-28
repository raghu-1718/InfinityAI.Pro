# RunPod Endpoint Management (DEPRECATED)

⚠️ **This file is deprecated.** InfinityAI.Pro has migrated from RunPod to AWS SageMaker and Azure ML for GPU services.

## Migration Information

The system now uses multi-cloud AI with the following priority:
1. **AWS SageMaker** (Primary GPU provider)
2. **Azure ML** (Secondary GPU provider)
3. **RunPod** (Legacy fallback - still supported but deprecated)

## Legacy RunPod Endpoints (No longer used)

- Stable Diffusion: https://ga4sxq6i6mrw72-8888.proxy.runpod.net
- YOLO: https://s2415wou493ooq-8888.proxy.runpod.net
- Whisper: https://wmca1dz5qqm7kn-8888.proxy.runpod.net

## New Configuration

Update your environment variables to use AWS/Azure instead:

```bash
# AWS SageMaker (Primary)
AWS_SAGEMAKER_ENDPOINT=https://your-sagemaker-endpoint.amazonaws.com
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Azure ML (Secondary)
AZURE_ML_ENDPOINT=https://your-azure-ml-endpoint.azure.com
AZURE_ML_KEY=your_azure_ml_key
```

## Migration Steps

1. Deploy your models to AWS SageMaker or Azure ML
2. Update environment variables
3. Test the new endpoints
4. Remove RunPod dependencies

For detailed setup instructions, see the main README.md.</content>
<parameter name="filePath">/workspaces/InfinityAI.Pro/RUNPOD_ENDPOINTS.md