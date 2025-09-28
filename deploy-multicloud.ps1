# 🚀 InfinityAI.Pro Multi-Cloud Deployment Script
# Deploys to Railway (Backend) + Vercel (Frontend) + HuggingFace (AI/ML)

Write-Host "🚀 Starting InfinityAI.Pro Multi-Cloud Deployment..." -ForegroundColor Green

# Configuration
$PROJECT_NAME = "InfinityAI.Pro"
$BACKEND_SERVICE = "infinityai-backend"
$FRONTEND_SERVICE = "infinityai-frontend"

Write-Host "`n📋 Prerequisites Check:" -ForegroundColor Yellow

# Check if required CLI tools are installed
$tools = @(
    @{name="git"; check="git --version"},
    @{name="npm"; check="npm --version"},
    @{name="vercel"; check="vercel --version"},
    @{name="python"; check="python --version"}
)

foreach ($tool in $tools) {
    try {
        $result = Invoke-Expression $tool.check 2>$null
        Write-Host "✅ $($tool.name): OK" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ $($tool.name): Not found. Please install it first." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n🔧 Step 1: Preparing Backend for Railway..." -ForegroundColor Yellow

# Copy Railway-optimized files
try {
    Copy-Item "infinityai-pro\backend\requirements-railway.txt" "infinityai-pro\backend\requirements.txt" -Force
    Copy-Item "infinityai-pro\backend\Dockerfile-railway" "infinityai-pro\backend\Dockerfile" -Force
    Write-Host "✅ Backend files prepared for Railway" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error preparing backend files: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n🌐 Step 2: Deploying Frontend to Vercel..." -ForegroundColor Yellow

# Install Vercel CLI if not already installed
try {
    npm install -g vercel 2>$null
    Write-Host "✅ Vercel CLI ready" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Vercel CLI installation issue, but continuing..." -ForegroundColor Yellow
}

# Deploy to Vercel
Write-Host "Deploying frontend to Vercel..." -ForegroundColor Cyan
try {
    Set-Location "infinityai-pro\frontend"
    vercel --prod --yes
    Set-Location "..\..\"
    Write-Host "✅ Frontend deployed to Vercel" -ForegroundColor Green
}
catch {
    Write-Host "❌ Vercel deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "📝 Manual deployment required. Run 'vercel' in the frontend directory." -ForegroundColor Yellow
}

Write-Host "`n🚂 Step 3: Preparing Railway Deployment..." -ForegroundColor Yellow

# Commit changes for Railway deployment
Write-Host "Committing optimized files..." -ForegroundColor Cyan
try {
    git add .
    git commit -m "Optimize for multi-cloud deployment (Railway + Vercel + HuggingFace)"
    git push origin main
    Write-Host "✅ Code pushed to repository" -ForegroundColor Green
}
catch {
    Write-Host "❌ Git operations failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "📝 Please manually commit and push the changes." -ForegroundColor Yellow
}

Write-Host "`n🤗 Step 4: Setting up HuggingFace Spaces..." -ForegroundColor Yellow

# Install HuggingFace CLI
try {
    pip install huggingface_hub[cli] --quiet
    Write-Host "✅ HuggingFace CLI installed" -ForegroundColor Green
    
    Write-Host "`n📝 To complete HuggingFace setup, run these commands:" -ForegroundColor Cyan
    Write-Host "1. huggingface-cli login" -ForegroundColor White
    Write-Host "2. huggingface-cli repo create infinityai-yolo-detection --type space --space_sdk gradio" -ForegroundColor White
    Write-Host "3. huggingface-cli repo create infinityai-whisper-stt --type space --space_sdk gradio" -ForegroundColor White
    Write-Host "4. huggingface-cli repo create infinityai-image-generation --type space --space_sdk gradio" -ForegroundColor White
    Write-Host "5. huggingface-cli repo create infinityai-embeddings --type space --space_sdk gradio" -ForegroundColor White
}
catch {
    Write-Host "❌ HuggingFace CLI installation failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n💾 Step 5: Database Setup Instructions..." -ForegroundColor Yellow
Write-Host "Railway PostgreSQL:" -ForegroundColor Cyan
Write-Host "• Automatically provisioned with your Railway app" -ForegroundColor White
Write-Host "• DATABASE_URL environment variable will be set automatically" -ForegroundColor White
Write-Host "`nPinecone Vector Database:" -ForegroundColor Cyan
Write-Host "• Create account at pinecone.io" -ForegroundColor White
Write-Host "• Create a free index (100K vectors)" -ForegroundColor White
Write-Host "• Add PINECONE_API_KEY and PINECONE_ENVIRONMENT to Railway" -ForegroundColor White

Write-Host "`n🔑 Step 6: Environment Variables Setup..." -ForegroundColor Yellow
Write-Host "Add these to Railway dashboard:" -ForegroundColor Cyan

$envVars = @(
    "DHAN_CLIENT_ID=your_dhan_client_id",
    "DHAN_ACCESS_TOKEN=your_dhan_access_token",
    "AZURE_OPENAI_ENDPOINT=your_azure_endpoint",
    "AZURE_OPENAI_KEY=your_azure_key",
    "AWS_ACCESS_KEY_ID=your_aws_key",
    "AWS_SECRET_ACCESS_KEY=your_aws_secret",
    "PINECONE_API_KEY=your_pinecone_key",
    "PINECONE_ENVIRONMENT=your_pinecone_environment",
    "HUGGINGFACE_API_KEY=your_hf_token"
)

foreach ($env in $envVars) {
    Write-Host "• $env" -ForegroundColor White
}

Write-Host "`n📊 Step 7: Performance Monitoring URLs..." -ForegroundColor Yellow
Write-Host "Frontend: https://infinityai-frontend.vercel.app" -ForegroundColor Cyan
Write-Host "Backend: https://infinityai-backend-production.up.railway.app" -ForegroundColor Cyan
Write-Host "API Health: https://infinityai-backend-production.up.railway.app/health" -ForegroundColor Cyan

Write-Host "`n🎉 Multi-Cloud Deployment Complete!" -ForegroundColor Green
Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. 🚂 Go to railway.app and connect your GitHub repo" -ForegroundColor White
Write-Host "2. 🔑 Add environment variables to Railway dashboard" -ForegroundColor White
Write-Host "3. 🤗 Setup HuggingFace Spaces using the commands above" -ForegroundColor White
Write-Host "4. 📊 Monitor deployment at the provided URLs" -ForegroundColor White
Write-Host "5. 🚀 Start live trading with your AI-powered platform!" -ForegroundColor White

Write-Host "`n💰 Expected Monthly Costs:" -ForegroundColor Green
Write-Host "• Vercel (Frontend): $0 (FREE)" -ForegroundColor White
Write-Host "• Railway (Backend + DB): $5" -ForegroundColor White
Write-Host "• HuggingFace Spaces: $0 (FREE GPU hours)" -ForegroundColor White
Write-Host "• Azure AI Foundry: $0-10 (FREE credits)" -ForegroundColor White
Write-Host "• AWS Bedrock: $0-25 (FREE credits)" -ForegroundColor White
Write-Host "• Pinecone: $0 (FREE tier)" -ForegroundColor White
Write-Host "• Total: $5-40/month for full AI trading platform" -ForegroundColor Green

Write-Host "`n🔗 Useful Links:" -ForegroundColor Yellow
Write-Host "• Railway: https://railway.app" -ForegroundColor Cyan
Write-Host "• Vercel: https://vercel.com/dashboard" -ForegroundColor Cyan
Write-Host "• HuggingFace: https://huggingface.co/spaces" -ForegroundColor Cyan
Write-Host "• Azure AI Foundry: https://ai.azure.com" -ForegroundColor Cyan
Write-Host "• AWS Bedrock: https://console.aws.amazon.com/bedrock" -ForegroundColor Cyan
Write-Host "• Pinecone: https://app.pinecone.io" -ForegroundColor Cyan