#!/bin/bash
# InfinityAI.Pro Environment Variables Setup Script
# This script helps configure environment variables for Render deployment

set -e

echo "🔧 InfinityAI.Pro Environment Variables Setup"
echo "============================================="

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

# Function to prompt for input with default
prompt_with_default() {
    local prompt=$1
    local default=$2
    local response

    read -p "$prompt [$default]: " response
    echo "${response:-$default}"
}

# Function to prompt for secret input
prompt_secret() {
    local prompt=$1
    local response

    read -s -p "$prompt: " response
    echo
    echo "$response"
}

# Create .env file for local development
create_env_file() {
    print_status "Creating .env file for local development..."

    cat > .env << EOF
# InfinityAI.Pro Environment Variables
# Copy these to Render dashboard → Environment settings

# Core Trading Configuration
CAPITAL=11000.0
RISK_PER_TRADE_PCT=0.03
MAX_DAILY_LOSS_PCT=0.10
MAX_DAILY_PROFIT_PCT=0.25
MAX_CONSECUTIVE_LOSSES=3
COOLDOWN_AFTER_LOSSES_SEC=300
CYCLE_SECONDS=15
WEIGHT_ML=0.60
WEIGHT_RULE=0.30
WEIGHT_VOL=0.10
MIN_TRADE_SCORE=0.45
PAPER_MODE=true

# Azure AI (Primary Provider)
AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo
AZURE_SPEECH_ENDPOINT=$AZURE_SPEECH_ENDPOINT
AZURE_SPEECH_KEY=$AZURE_SPEECH_KEY
AZURE_VISION_ENDPOINT=$AZURE_VISION_ENDPOINT
AZURE_VISION_KEY=$AZURE_VISION_KEY
AZURE_TEXT_ANALYTICS_ENDPOINT=$AZURE_TEXT_ANALYTICS_ENDPOINT
AZURE_TEXT_ANALYTICS_KEY=$AZURE_TEXT_ANALYTICS_KEY
AZURE_ML_ENDPOINT=$AZURE_ML_ENDPOINT
AZURE_ML_KEY=$AZURE_ML_KEY

# AWS AI (Secondary Provider)
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
AWS_S3_BUCKET=infinityai-models
AWS_SAGEMAKER_ENDPOINT=$AWS_SAGEMAKER_ENDPOINT
AWS_FRAUD_DETECTOR_ID=$AWS_FRAUD_DETECTOR_ID

# Hugging Face
HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY
HUGGINGFACE_MODEL_CACHE=/tmp/huggingface

# Storage Configuration
STORAGE_PROVIDER=aws
AZURE_STORAGE_ACCOUNT=$AZURE_STORAGE_ACCOUNT
AZURE_STORAGE_KEY=$AZURE_STORAGE_KEY
AZURE_CONTAINER=infinityai-models

# Broker Configuration
BROKER_TYPE=dhan
DHAN_BASE_URL=https://api.dhan.co
DHAN_ACCESS_TOKEN=$DHAN_ACCESS_TOKEN
DHAN_CLIENT_ID=$DHAN_CLIENT_ID
COINSWITCH_BASE_URL=https://api.coinswitch.co
COINSWITCH_API_KEY=$COINSWITCH_API_KEY
COINSWITCH_API_SECRET=$COINSWITCH_API_SECRET

# Model URLs (Cloud Storage)
YOLO_MODEL_URL=https://$AWS_S3_BUCKET.s3.amazonaws.com/models/yolov8n.pt
EMBEDDING_MODEL_URL=https://$AWS_S3_BUCKET.s3.amazonaws.com/models/embeddings

# External APIs
OPENAI_API_KEY=$OPENAI_API_KEY
PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY
TRADINGVIEW_API_KEY=$TRADINGVIEW_API_KEY
EOF

    print_success ".env file created"
}

# Interactive setup
interactive_setup() {
    print_status "Starting interactive environment variable setup..."
    echo ""

    # Trading Configuration
    echo "🎯 Trading Configuration:"
    CAPITAL=$(prompt_with_default "Trading capital amount" "11000.0")
    RISK_PER_TRADE_PCT=$(prompt_with_default "Risk per trade (%)" "0.03")
    PAPER_MODE=$(prompt_with_default "Paper trading mode (true/false)" "true")
    echo ""

    # Azure AI Setup
    echo "☁️  Azure AI Configuration (Primary):"
    AZURE_OPENAI_ENDPOINT=$(prompt_with_default "Azure OpenAI endpoint" "")
    AZURE_OPENAI_KEY=$(prompt_secret "Azure OpenAI API key")
    AZURE_SPEECH_ENDPOINT=$(prompt_with_default "Azure Speech endpoint" "")
    AZURE_SPEECH_KEY=$(prompt_secret "Azure Speech API key")
    AZURE_VISION_ENDPOINT=$(prompt_with_default "Azure Vision endpoint" "")
    AZURE_VISION_KEY=$(prompt_secret "Azure Vision API key")
    AZURE_TEXT_ANALYTICS_ENDPOINT=$(prompt_with_default "Azure Text Analytics endpoint" "")
    AZURE_TEXT_ANALYTICS_KEY=$(prompt_secret "Azure Text Analytics API key")
    AZURE_ML_ENDPOINT=$(prompt_with_default "Azure ML endpoint" "")
    AZURE_ML_KEY=$(prompt_secret "Azure ML API key")
    echo ""

    # AWS AI Setup
    echo "☁️  AWS AI Configuration (Secondary):"
    AWS_ACCESS_KEY_ID=$(prompt_secret "AWS Access Key ID")
    AWS_SECRET_ACCESS_KEY=$(prompt_secret "AWS Secret Access Key")
    AWS_REGION=$(prompt_with_default "AWS Region" "us-east-1")
    AWS_S3_BUCKET=$(prompt_with_default "AWS S3 bucket name" "infinityai-models")
    echo ""

    # Hugging Face Setup
    echo "🤗 Hugging Face Configuration:"
    HUGGINGFACE_API_KEY=$(prompt_secret "Hugging Face API key")
    echo ""

    # Broker Setup
    echo "🏦 Broker Configuration:"
    BROKER_TYPE=$(prompt_with_default "Broker type (dhan/coinswitch)" "dhan")
    if [ "$BROKER_TYPE" = "dhan" ]; then
        DHAN_ACCESS_TOKEN=$(prompt_secret "Dhan Access Token")
        DHAN_CLIENT_ID=$(prompt_with_default "Dhan Client ID" "")
    else
        COINSWITCH_API_KEY=$(prompt_secret "CoinSwitch API Key")
        COINSWITCH_API_SECRET=$(prompt_secret "CoinSwitch API Secret")
    fi
    echo ""

    # Optional APIs
    echo "🔗 Optional External APIs:"
    OPENAI_API_KEY=$(prompt_secret "OpenAI API key (optional)")
    PERPLEXITY_API_KEY=$(prompt_secret "Perplexity API key (optional)")
    TRADINGVIEW_API_KEY=$(prompt_secret "TradingView API key (optional)")
    echo ""

    create_env_file
}

# Generate Render environment variables list
generate_render_env_list() {
    print_status "Generating Render environment variables list..."

    cat > render_env_vars.txt << EOF
# Copy these variables to Render Dashboard → Environment

# Core Trading Configuration
CAPITAL=$CAPITAL
RISK_PER_TRADE_PCT=$RISK_PER_TRADE_PCT
MAX_DAILY_LOSS_PCT=0.10
MAX_DAILY_PROFIT_PCT=0.25
MAX_CONSECUTIVE_LOSSES=3
COOLDOWN_AFTER_LOSSES_SEC=300
CYCLE_SECONDS=15
WEIGHT_ML=0.60
WEIGHT_RULE=0.30
WEIGHT_VOL=0.10
MIN_TRADE_SCORE=0.45
PAPER_MODE=$PAPER_MODE

# Azure AI (Primary)
AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo
AZURE_SPEECH_ENDPOINT=$AZURE_SPEECH_ENDPOINT
AZURE_SPEECH_KEY=$AZURE_SPEECH_KEY
AZURE_VISION_ENDPOINT=$AZURE_VISION_ENDPOINT
AZURE_VISION_KEY=$AZURE_VISION_KEY
AZURE_TEXT_ANALYTICS_ENDPOINT=$AZURE_TEXT_ANALYTICS_ENDPOINT
AZURE_TEXT_ANALYTICS_KEY=$AZURE_TEXT_ANALYTICS_KEY
AZURE_ML_ENDPOINT=$AZURE_ML_ENDPOINT
AZURE_ML_KEY=$AZURE_ML_KEY

# AWS AI (Secondary)
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_REGION=$AWS_REGION
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
AWS_S3_BUCKET=$AWS_S3_BUCKET
AWS_SAGEMAKER_ENDPOINT=$AWS_SAGEMAKER_ENDPOINT
AWS_FRAUD_DETECTOR_ID=$AWS_FRAUD_DETECTOR_ID

# Hugging Face
HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY
HUGGINGFACE_MODEL_CACHE=/tmp/huggingface

# Storage
STORAGE_PROVIDER=aws
AZURE_STORAGE_ACCOUNT=$AZURE_STORAGE_ACCOUNT
AZURE_STORAGE_KEY=$AZURE_STORAGE_KEY
AZURE_CONTAINER=infinityai-models

# Broker
BROKER_TYPE=$BROKER_TYPE
DHAN_ACCESS_TOKEN=$DHAN_ACCESS_TOKEN
DHAN_CLIENT_ID=$DHAN_CLIENT_ID
COINSWITCH_API_KEY=$COINSWITCH_API_KEY
COINSWITCH_API_SECRET=$COINSWITCH_API_SECRET

# External APIs
OPENAI_API_KEY=$OPENAI_API_KEY
PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY
TRADINGVIEW_API_KEY=$TRADINGVIEW_API_KEY
EOF

    print_success "Render environment variables saved to: render_env_vars.txt"
}

# Main menu
main() {
    echo "Choose an option:"
    echo "1. Interactive setup (recommended)"
    echo "2. Generate from existing .env file"
    echo "3. Show required variables list"
    echo ""

    read -p "Enter your choice (1-3): " choice

    case $choice in
        1)
            interactive_setup
            generate_render_env_list
            ;;
        2)
            if [ -f ".env" ]; then
                print_status "Loading from existing .env file..."
                source .env
                generate_render_env_list
            else
                print_error "No .env file found. Run option 1 first."
                exit 1
            fi
            ;;
        3)
            print_status "Required environment variables:"
            echo ""
            echo "📋 Core Trading:"
            echo "   - CAPITAL, RISK_PER_TRADE_PCT, PAPER_MODE"
            echo ""
            echo "☁️  Azure AI (Primary):"
            echo "   - AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY"
            echo "   - AZURE_SPEECH_ENDPOINT, AZURE_SPEECH_KEY"
            echo "   - AZURE_VISION_ENDPOINT, AZURE_VISION_KEY"
            echo "   - AZURE_TEXT_ANALYTICS_ENDPOINT, AZURE_TEXT_ANALYTICS_KEY"
            echo "   - AZURE_ML_ENDPOINT, AZURE_ML_KEY"
            echo ""
            echo "☁️  AWS AI (Secondary):"
            echo "   - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
            echo "   - AWS_REGION, AWS_S3_BUCKET"
            echo ""
            echo "🤗 Hugging Face:"
            echo "   - HUGGINGFACE_API_KEY"
            echo ""
            echo "🏦 Broker:"
            echo "   - BROKER_TYPE, DHAN_ACCESS_TOKEN, DHAN_CLIENT_ID"
            echo ""
            echo "📖 See RENDER_ENV_SETUP.md for detailed instructions"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    print_success "Environment setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Copy variables from render_env_vars.txt"
    echo "2. Go to Render dashboard → Your service → Environment"
    echo "3. Add each variable (one per line)"
    echo "4. Save and redeploy"
    echo ""
    echo "🔐 Important: Never commit .env file to version control!"
}

main