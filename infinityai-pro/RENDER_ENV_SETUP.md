# InfinityAI.Pro Environment Variables for Render Deployment

## 🚀 Complete Environment Variables Setup

Copy and paste these into your Render dashboard under Environment settings.

### Core Application Settings
```
# Trading Configuration
CAPITAL=11000.0
RISK_PER_TRADE_PCT=0.03
MAX_DAILY_LOSS_PCT=0.10
MAX_DAILY_PROFIT_PCT=0.25
MAX_CONSECUTIVE_LOSSES=3
COOLDOWN_AFTER_LOSSES_SEC=300
CYCLE_SECONDS=15

# Scoring Weights
WEIGHT_ML=0.60
WEIGHT_RULE=0.30
WEIGHT_VOL=0.10
MIN_TRADE_SCORE=0.45

# Trading Mode (Set to false for LIVE TRADING)
PAPER_MODE=false
```

### Azure AI (Primary Provider - GPU & AI)
```
# Azure OpenAI (Primary LLM)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo

# Azure Speech Services
AZURE_SPEECH_ENDPOINT=https://your-region.cognitiveservices.azure.com/
AZURE_SPEECH_KEY=your_azure_speech_key_here

# Azure Vision Services
AZURE_VISION_ENDPOINT=https://your-region.cognitiveservices.azure.com/
AZURE_VISION_KEY=your_azure_vision_key_here

# Azure Text Analytics
AZURE_TEXT_ANALYTICS_ENDPOINT=https://your-region.cognitiveservices.azure.com/
AZURE_TEXT_ANALYTICS_KEY=your_azure_text_analytics_key_here

# Azure ML (for signal generation)
AZURE_ML_ENDPOINT=https://your-ml-workspace.services.azureml.net/
AZURE_ML_KEY=your_azure_ml_key_here
```

### AWS AI (Secondary Provider - GPU & AI)
```
# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1

# AWS Bedrock (Secondary LLM)
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# AWS SageMaker (for signal generation)
AWS_SAGEMAKER_ENDPOINT=your-sagemaker-endpoint-name

# AWS Fraud Detector (for risk assessment)
AWS_FRAUD_DETECTOR_ID=your-fraud-detector-id

# AWS S3 (for model storage)
AWS_S3_BUCKET=infinityai-models
```

### Hugging Face (Local AI Models)
```
# Hugging Face API (for downloading models)
HUGGINGFACE_API_KEY=your_huggingface_api_key

# Model Cache Directory
HUGGINGFACE_MODEL_CACHE=/tmp/huggingface
```

### Cloud Storage Configuration
```
# Storage Provider (aws or azure)
STORAGE_PROVIDER=aws

# Azure Storage (if using Azure)
AZURE_STORAGE_ACCOUNT=your_storage_account
AZURE_STORAGE_KEY=your_storage_key
AZURE_CONTAINER=infinityai-models
```

### Broker Configuration
```
# Broker Type (dhan or coinswitch)
BROKER_TYPE=dhan

# Dhan Broker (Primary)
DHAN_BASE_URL=https://api.dhan.co
DHAN_ACCESS_TOKEN=your_dhan_access_token
DHAN_CLIENT_ID=your_dhan_client_id

# CoinSwitch PRO (Alternative)
COINSWITCH_BASE_URL=https://api.coinswitch.co
COINSWITCH_API_KEY=your_coinswitch_api_key
COINSWITCH_API_SECRET=your_coinswitch_api_secret
```

### Model URLs (Cloud Downloads)
```
# Pre-trained model URLs in cloud storage
YOLO_MODEL_URL=https://your-bucket.s3.amazonaws.com/models/yolov8n.pt
EMBEDDING_MODEL_URL=https://your-bucket.s3.amazonaws.com/models/embeddings
```

### External API Keys
```
# News and Social Sentiment
OPENAI_API_KEY=your_openai_key_for_legacy_support
PERPLEXITY_API_KEY=your_perplexity_key_for_research
TRADINGVIEW_API_KEY=your_tradingview_key
```

---

## 🔧 How to Set Up in Render

### Step 1: Go to Render Dashboard
1. Login to [Render.com](https://render.com)
2. Select your InfinityAI.Pro service
3. Go to **Environment** tab

### Step 2: Add Environment Variables
1. Click **Add Environment Variable**
2. Copy each variable from above
3. Set the appropriate values for your accounts

### Step 3: Verify Configuration
After setting all variables, redeploy your service and check the logs for:
```
✅ Multi-cloud AI Service initialized
✅ Router initialized with providers: ['azure', 'aws']
```

---

## 🛠️ Getting API Keys

### Azure Setup
1. **Create Azure Account**: [portal.azure.com](https://portal.azure.com)
2. **OpenAI Service**: Create "Azure OpenAI" resource
3. **Cognitive Services**: Create "Cognitive Services" for Speech/Vision/Text
4. **Machine Learning**: Create "Machine Learning" workspace

### AWS Setup
1. **Create AWS Account**: [aws.amazon.com](https://aws.amazon.com)
2. **IAM User**: Create user with programmatic access
3. **Bedrock Access**: Enable models in Amazon Bedrock
4. **S3 Bucket**: Create bucket for model storage

### Hugging Face
1. **Create Account**: [huggingface.co](https://huggingface.co)
2. **API Token**: Generate token in settings

### Broker Setup
1. **Dhan**: Get API credentials from Dhan HQ
2. **CoinSwitch**: Get API keys from CoinSwitch PRO

---

## ✅ Verification Checklist

After deployment, check these endpoints:

### Health Checks
```bash
# Overall health
curl https://api.infinityai.pro/health

# AI services health
curl https://api.infinityai.pro/ai/health

# Individual services
curl https://api.infinityai.pro/ai/llm/health
curl https://api.infinityai.pro/ai/vision/health
curl https://api.infinityai.pro/ai/sentiment/health
```

### Test AI Services
```bash
# Test LLM
curl -X POST https://api.infinityai.pro/ai/llm/chat \
  -d '{"message": "Analyze NIFTY trend"}'

# Test Signal Generation
curl -X POST https://api.infinityai.pro/ai/signal/generate \
  -d '{"symbol": "NIFTY", "price_data": {"close": [22000, 22050, 22100]}}'

# Test Risk Assessment
curl -X POST https://api.infinityai.pro/ai/risk/assess \
  -d '{"symbol": "NIFTY", "action": "BUY", "quantity": 50, "price": 22000}'
```

---

## 🚨 Important Notes

1. **Never commit API keys** to version control
2. **Use environment-specific keys** (dev/staging/prod)
3. **Monitor costs** - Azure/AWS bill regularly
4. **Set up alerts** for API failures
5. **Backup configurations** securely

---

## 🎯 Cost Optimization

### Azure Costs (Estimated)
- OpenAI GPT-4 Turbo: $0.01/1K tokens
- Vision API: $0.002/image
- Speech API: $0.016/minute
- **Monthly**: $50-200

### AWS Costs (Estimated)
- Bedrock Claude 3.5: $0.015/1K tokens
- Rekognition: $0.001/image
- S3 Storage: $0.023/GB
- **Monthly**: $30-150

### Total AI Costs: $80-350/month

**Optimization Tips:**
- Use Azure as primary (cheaper GPT-4)
- Cache frequent requests
- Monitor usage in Azure/AWS consoles
- Set up billing alerts