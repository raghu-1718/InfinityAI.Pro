# AWS S3 Bucket Setup Script
#!/bin/bash

# InfinityAI.Pro - AWS S3 Bucket Setup
# Creates S3 bucket and uploads AI models for cloud-based inference

set -e

# Configuration
BUCKET_NAME="infinityai-models"
REGION="us-east-1"
PROFILE="${AWS_PROFILE:-default}"

echo "🚀 Setting up AWS S3 bucket for InfinityAI.Pro models..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity --profile "$PROFILE" >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure --profile $PROFILE'"
    exit 1
fi

# Create S3 bucket
echo "📦 Creating S3 bucket: $BUCKET_NAME"
if aws s3 ls "s3://$BUCKET_NAME" --profile "$PROFILE" >/dev/null 2>&1; then
    echo "✅ Bucket $BUCKET_NAME already exists"
else
    aws s3 mb "s3://$BUCKET_NAME" --region "$REGION" --profile "$PROFILE"
    echo "✅ Created bucket: $BUCKET_NAME"
fi

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled \
    --profile "$PROFILE"

# Set up lifecycle policy for cost optimization
cat > lifecycle_policy.json << EOF
{
    "Rules": [
        {
            "ID": "Delete old model versions",
            "Status": "Enabled",
            "Prefix": "models/",
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 30
            }
        }
    ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket "$BUCKET_NAME" \
    --lifecycle-configuration file://lifecycle_policy.json \
    --profile "$PROFILE"

rm lifecycle_policy.json

# Upload AI models
echo "⬆️ Uploading AI models to S3..."

# YOLOv8 model
if [ -f "models/yolov8n.pt" ]; then
    aws s3 cp models/yolov8n.pt "s3://$BUCKET_NAME/models/yolov8n.pt" --profile "$PROFILE"
    echo "✅ Uploaded YOLOv8 model"
fi

# LightGBM model
if [ -f "models/lightgbm_small.pkl" ]; then
    aws s3 cp models/lightgbm_small.pkl "s3://$BUCKET_NAME/models/lightgbm_small.pkl" --profile "$PROFILE"
    echo "✅ Uploaded LightGBM model"
fi

# Create model URLs file
cat > model_urls.env << EOF
# InfinityAI.Pro Model URLs
YOLO_MODEL_URL=https://$BUCKET_NAME.s3.$REGION.amazonaws.com/models/yolov8n.pt
LIGHTGBM_MODEL_URL=https://$BUCKET_NAME.s3.$REGION.amazonaws.com/models/lightgbm_small.pkl
EOF

echo "📋 Model URLs saved to model_urls.env"
echo "🔗 YOLO Model: https://$BUCKET_NAME.s3.$REGION.amazonaws.com/models/yolov8n.pt"
echo "🔗 LightGBM Model: https://$BUCKET_NAME.s3.$REGION.amazonaws.com/models/lightgbm_small.pkl"

echo "🎉 AWS S3 setup complete!"
echo "💡 Next: Set these URLs as environment variables in your deployment"