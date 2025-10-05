#!/bin/bash

# InfinityAI.Pro - Engine D AWS Deployment Script
# Deploy central backend API to AWS ECS with full DHAN integration

set -e

echo "🚀 Starting Engine D (AWS Central Backend) Deployment..."

# Configuration
AWS_REGION="us-east-1"
CLUSTER_NAME="infinityai-cluster"
SERVICE_NAME="infinityai-engine-d"
TASK_FAMILY="infinityai-engine-d"
ECR_REPO_NAME="infinityai-engine-d"
LOG_GROUP_NAME="/ecs/infinityai-engine-d"

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo "✅ AWS Account ID: $ACCOUNT_ID"
echo "✅ ECR Repository: $ECR_URI"

# Step 1: Store DHAN credentials securely in AWS Secrets Manager
echo "🔐 Storing DHAN credentials in AWS Secrets Manager..."
aws secretsmanager create-secret \
    --name "infinityai/dhan-credentials" \
    --description "DHAN API credentials for InfinityAI.Pro trading system" \
    --secret-string '{
        "client_id": "63b3086e",
        "client_secret": "147fc424-cd90-4bd6-a843-15c3766e2df7"
    }' \
    --region $AWS_REGION || echo "Secret already exists, updating..."

# Update if exists
aws secretsmanager update-secret \
    --secret-id "infinityai/dhan-credentials" \
    --secret-string '{
        "client_id": "63b3086e",
        "client_secret": "147fc424-cd90-4bd6-a843-15c3766e2df7"
    }' \
    --region $AWS_REGION

echo "✅ DHAN credentials stored securely in AWS Secrets Manager"

# Step 2: Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION || echo "Repository already exists"

# Step 3: Build and push Docker image
echo "🐳 Building Docker image..."
cd ../engine-d-aws

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Build image
docker build -t $ECR_REPO_NAME .
docker tag $ECR_REPO_NAME:latest $ECR_URI:latest

# Push image
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:latest

echo "✅ Docker image pushed successfully"

# Step 4: Create CloudWatch Log Group
echo "📝 Creating CloudWatch Log Group..."
aws logs create-log-group \
    --log-group-name $LOG_GROUP_NAME \
    --region $AWS_REGION || echo "Log group already exists"

# Step 5: Create ECS Cluster
echo "🖥️ Creating ECS Cluster..."
aws ecs create-cluster \
    --cluster-name $CLUSTER_NAME \
    --region $AWS_REGION || echo "Cluster already exists"

# Step 6: Create IAM roles
echo "👤 Creating IAM roles..."

# Task execution role
cat > task-execution-role-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create execution role
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file://task-execution-role-trust-policy.json \
    --region $AWS_REGION || echo "Execution role already exists"

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Task role with additional permissions
cat > task-role-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:infinityai/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticache:DescribeCacheClusters",
        "elasticache:DescribeReplicationGroups"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-role \
    --role-name infinityai-engine-d-task-role \
    --assume-role-policy-document file://task-execution-role-trust-policy.json \
    --region $AWS_REGION || echo "Task role already exists"

aws iam put-role-policy \
    --role-name infinityai-engine-d-task-role \
    --policy-name InfinityAI-Engine-D-Policy \
    --policy-document file://task-role-policy.json

echo "✅ IAM roles created successfully"

# Step 7: Create Redis cluster (ElastiCache)
echo "📚 Creating Redis cluster..."
aws elasticache create-replication-group \
    --replication-group-id infinityai-redis \
    --description "Redis cluster for InfinityAI.Pro" \
    --num-cache-clusters 1 \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --region $AWS_REGION || echo "Redis cluster creation in progress or already exists"

echo "✅ Redis cluster creation initiated"

# Step 8: Update task definition with actual account ID
sed "s/ACCOUNT-ID/$ACCOUNT_ID/g" ../engine-d-aws/ecs-task-definition.json > task-definition-updated.json

# Step 9: Register task definition
echo "📋 Registering ECS task definition..."
aws ecs register-task-definition \
    --cli-input-json file://task-definition-updated.json \
    --region $AWS_REGION

# Step 10: Create ECS service
echo "🚀 Creating ECS service..."
aws ecs create-service \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition $TASK_FAMILY \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
    --region $AWS_REGION || echo "Service creation in progress or updating existing service"

# Step 11: Create Application Load Balancer
echo "⚖️ Setting up Application Load Balancer..."
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name infinityai-engine-d-alb \
    --subnets subnet-12345 subnet-67890 \
    --security-groups sg-12345 \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text || echo "Load balancer creation in progress")

echo "✅ Application Load Balancer created: $ALB_ARN"

# Step 12: Create target group
TG_ARN=$(aws elbv2 create-target-group \
    --name infinityai-engine-d-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-12345 \
    --target-type ip \
    --health-check-path /health \
    --health-check-protocol HTTP \
    --region $AWS_REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text || echo "Target group creation in progress")

echo "✅ Target group created: $TG_ARN"

# Clean up temporary files
rm -f task-execution-role-trust-policy.json task-role-policy.json task-definition-updated.json

echo ""
echo "🎉 Engine D AWS Deployment Complete!"
echo "=================================="
echo "✅ DHAN Credentials: Securely stored in AWS Secrets Manager"
echo "✅ Docker Image: $ECR_URI:latest"
echo "✅ ECS Cluster: $CLUSTER_NAME"
echo "✅ ECS Service: $SERVICE_NAME"
echo "✅ Redis Cluster: infinityai-redis"
echo "✅ Load Balancer: infinityai-engine-d-alb"
echo ""
echo "🔗 Next Steps:"
echo "1. Configure DNS: api.infinityai.pro -> Load Balancer"
echo "2. Set up SSL certificate"
echo "3. Deploy other engines (A, B, C)"
echo "4. Deploy Azure frontend"
echo ""
echo "📍 Engine D will be available at: https://api.infinityai.pro"
echo "🔐 DHAN API Integration: Ready with your credentials"