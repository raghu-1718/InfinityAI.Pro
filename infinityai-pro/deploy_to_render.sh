#!/bin/bash
# InfinityAI.Pro Render Deployment Script
# This script helps deploy the application to Render.com

set -e

echo "🚀 InfinityAI.Pro Render Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    print_error "Please run this script from the infinityai-pro directory"
    exit 1
fi

print_status "Checking prerequisites..."

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Git working directory is not clean. Uncommitted changes detected."
    echo "Please commit your changes before deploying:"
    echo "  git add ."
    echo "  git commit -m 'Prepare for production deployment'"
    echo "  git push origin main"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if required files exist
required_files=("backend/main.py" "backend/requirements.txt" "frontend/package.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

print_success "Prerequisites check passed"

# Create deployment package
print_status "Creating deployment package..."

# Clean up any existing build artifacts
rm -rf dist/ build/ *.egg-info/

# Create a temporary deployment directory
DEPLOY_DIR="deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

# Copy backend files
print_status "Copying backend files..."
cp -r backend/ "$DEPLOY_DIR/"
cp -r docs/ "$DEPLOY_DIR/" 2>/dev/null || true

# Copy frontend files
print_status "Copying frontend files..."
cp -r frontend/ "$DEPLOY_DIR/"

# Copy root files
cp README.md LICENSE docker-compose.yml "$DEPLOY_DIR/" 2>/dev/null || true

# Create render.yaml for Render deployment
cat > "$DEPLOY_DIR/render.yaml" << 'EOF'
services:
  - type: web
    name: infinityai-pro-api
    runtime: python3
    buildCommand: "pip install -r requirements.txt"
    startCommand: "cd backend && python main.py"
    envVars:
      # Core Configuration
      - key: CAPITAL
        value: 11000.0
      - key: RISK_PER_TRADE_PCT
        value: 0.03
      - key: PAPER_MODE
        value: false

      # Azure AI (Primary)
      - key: AZURE_OPENAI_ENDPOINT
        sync: false
      - key: AZURE_OPENAI_KEY
        sync: false
      - key: AZURE_OPENAI_DEPLOYMENT
        value: gpt-4-turbo
      - key: AZURE_SPEECH_ENDPOINT
        sync: false
      - key: AZURE_SPEECH_KEY
        sync: false
      - key: AZURE_VISION_ENDPOINT
        sync: false
      - key: AZURE_VISION_KEY
        sync: false
      - key: AZURE_TEXT_ANALYTICS_ENDPOINT
        sync: false
      - key: AZURE_TEXT_ANALYTICS_KEY
        sync: false
      - key: AZURE_ML_ENDPOINT
        sync: false
      - key: AZURE_ML_KEY
        sync: false

      # AWS AI (Secondary)
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
      - key: AWS_REGION
        value: us-east-1
      - key: AWS_BEDROCK_MODEL_ID
        value: anthropic.claude-3-5-sonnet-20240620-v1:0
      - key: AWS_S3_BUCKET
        value: infinityai-models

      # Hugging Face
      - key: HUGGINGFACE_API_KEY
        sync: false

      # Storage
      - key: STORAGE_PROVIDER
        value: aws

      # Broker
      - key: BROKER_TYPE
        value: dhan
      - key: DHAN_ACCESS_TOKEN
        sync: false
      - key: DHAN_CLIENT_ID
        sync: false

  - type: static
    name: infinityai-pro-frontend
    runtime: node
    buildCommand: "npm install && npm run build"
    staticPublishPath: dist
    pullRequestPreviewsEnabled: true
EOF

# Create a deployment README
cat > "$DEPLOY_DIR/DEPLOYMENT_README.md" << 'EOF'
# InfinityAI.Pro Render Deployment

## 🚀 Quick Deploy to Render

### Option 1: Using Render Dashboard (Recommended)
1. Go to [Render.com](https://render.com) and sign in
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: infinityai-pro-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python main.py`

### Option 2: Using render.yaml
1. Push this `render.yaml` file to your repository
2. In Render dashboard, select "Blueprint" when creating a new service
3. Render will automatically configure services based on the blueprint

## 🔧 Environment Variables

Copy the environment variables from `RENDER_ENV_SETUP.md` into your Render service settings.

## ✅ Post-Deployment Verification

After deployment:

1. **Check service health**:
   ```bash
   curl https://your-service-url.onrender.com/health
   ```

2. **Run verification script**:
   ```bash
   python verify_deployment.py
   ```

3. **Test AI services**:
   ```bash
   # Test LLM
   curl -X POST https://your-service-url.onrender.com/ai/llm/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello AI"}'

   # Test signal generation
   curl -X POST https://your-service-url.onrender.com/ai/signal/generate \
     -H "Content-Type: application/json" \
     -d '{"symbol": "NIFTY", "price_data": {"close": [22000, 22050, 22100]}}'
   ```

## 🛠️ Troubleshooting

### Common Issues:

1. **Module not found**: Check if all dependencies are in `requirements.txt`
2. **Environment variables not set**: Verify all required vars are configured in Render
3. **Service won't start**: Check logs in Render dashboard for error messages
4. **AI services failing**: Verify Azure/AWS credentials and endpoints

### Logs:
- View logs in Render dashboard under "Logs" tab
- Use `print` statements in Python for debugging
- Check `/health` endpoint for service status

## 📊 Monitoring

After successful deployment:
- Monitor costs in Azure/AWS consoles
- Set up alerts for API failures
- Check trading performance regularly
- Update models and configurations as needed

## 🔄 Updates

To update your deployment:
1. Make changes to code
2. Commit and push to GitHub
3. Render will automatically redeploy (if auto-deploy is enabled)

## 🆘 Support

If you encounter issues:
1. Check the logs in Render dashboard
2. Run the verification script locally
3. Review environment variables
4. Check Azure/AWS service status
EOF

print_success "Deployment package created in: $DEPLOY_DIR"

# Create a git commit for deployment
print_status "Preparing git commit..."

# Check if we should create a commit
read -p "Create a deployment commit? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "🚀 Production deployment: Remove RunPod, add Azure/AWS AI services

- Remove all RunPod dependencies
- Add Azure OpenAI as primary AI provider
- Add AWS Bedrock as secondary AI provider
- Add Hugging Face for local models
- Update all AI services with multi-cloud failover
- Add comprehensive environment variables
- Prepare for Render deployment"

    print_success "Deployment commit created"

    # Ask to push
    read -p "Push to origin main? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin main
        print_success "Pushed to origin main"
    fi
fi

print_success "Deployment preparation complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Set environment variables in Render dashboard (see RENDER_ENV_SETUP.md)"
echo "2. Deploy to Render using the render.yaml blueprint"
echo "3. Run verification script: python verify_deployment.py"
echo "4. Test AI services and trading functionality"
echo ""
echo "📁 Deployment files created in: $DEPLOY_DIR"
echo "📖 See DEPLOYMENT_README.md for detailed instructions"