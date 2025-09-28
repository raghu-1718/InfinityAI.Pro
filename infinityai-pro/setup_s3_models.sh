#!/bin/bash

# InfinityAI.Pro - S3 Model Upload Script
# This script sets up an S3 bucket and uploads AI models for cloud-based deployment

set -e

# Configuration
BUCKET_NAME="infinityai-models-${RANDOM}"
REGION="us-east-1"  # Change to your preferred region

echo "🚀 Setting up S3 bucket for InfinityAI.Pro models..."
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run:"
    echo "aws configure"
    echo ""
    echo "You'll need:"
    echo "- AWS Access Key ID"
    echo "- AWS Secret Access Key"
    echo "- Default region name: $REGION"
    exit 1
fi

# Create S3 bucket
echo "📦 Creating S3 bucket..."
if [ "$REGION" = "us-east-1" ]; then
    aws s3 mb s3://$BUCKET_NAME
else
    aws s3 mb s3://$BUCKET_NAME --region $REGION
fi

# Set bucket policy for public read access (adjust as needed for security)
echo "🔒 Setting bucket policy..."
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/models/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json
rm bucket-policy.json

# Create models directory structure
echo "📁 Creating models directory..."
aws s3api put-object --bucket $BUCKET_NAME --key models/

# Upload existing models
echo "⬆️  Uploading models..."

# YOLO model
if [ -f "backend/yolov8n.pt" ]; then
    echo "Uploading YOLOv8 nano model..."
    aws s3 cp backend/yolov8n.pt s3://$BUCKET_NAME/models/yolov8n.pt
else
    echo "⚠️  YOLO model not found at backend/yolov8n.pt"
fi

# LightGBM model
if [ -f "backend/models/lightgbm_small.pkl" ]; then
    echo "Uploading LightGBM model..."
    aws s3 cp backend/models/lightgbm_small.pkl s3://$BUCKET_NAME/models/lightgbm_small.pkl
else
    echo "⚠️  LightGBM model not found at backend/models/lightgbm_small.pkl"
fi

# Download and upload sentence-transformers model
echo "⬇️  Downloading sentence-transformers model..."
if command -v python3 &> /dev/null && python3 -c "import sentence_transformers" &> /dev/null; then
    mkdir -p temp_models
    cd temp_models
    
    echo "Downloading all-MiniLM-L6-v2..."
    python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('all-MiniLM-L6-v2')
" 2>/dev/null || echo "Failed to download model - will skip"

    if [ -d "all-MiniLM-L6-v2" ]; then
        echo "Creating zip archive..."
        zip -r all-MiniLM-L6-v2.zip all-MiniLM-L6-v2/ 2>/dev/null || echo "Failed to zip - will skip"
        
        if [ -f "all-MiniLM-L6-v2.zip" ]; then
            echo "Uploading sentence-transformers model..."
            aws s3 cp all-MiniLM-L6-v2.zip s3://$BUCKET_NAME/models/all-MiniLM-L6-v2.zip
        fi
    fi
    
    cd ..
    rm -rf temp_models
else
    echo "⚠️  sentence-transformers not available - skipping model download"
    echo "You can manually download from: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2"
    echo "And upload the zip to: s3://$BUCKET_NAME/models/all-MiniLM-L6-v2.zip"
fi

# List uploaded files
echo ""
echo "📋 Uploaded models:"
aws s3 ls s3://$BUCKET_NAME/models/ --recursive

# Generate URLs
echo ""
echo "🔗 Model URLs for Render environment variables:"
echo "YOLO_MODEL=https://$BUCKET_NAME.s3.amazonaws.com/models/yolov8n.pt"
echo "SBERT_MODEL=https://$BUCKET_NAME.s3.amazonaws.com/models/all-MiniLM-L6-v2.zip"
echo "LIGHTGBM_MODEL=https://$BUCKET_NAME.s3.amazonaws.com/models/lightgbm_small.pkl"
echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy the model URLs above"
echo "2. Go to Render dashboard → Your services → Environment"
echo "3. Add the environment variables"
echo "4. Redeploy your services"
echo ""
echo "🗑️  To clean up (optional):"
echo "aws s3 rb s3://$BUCKET_NAME --force"