#!/bin/bash

set -e

# Configuration for your repository
GITHUB_OWNER="raghu-1718"
GITHUB_REPO="InfinityAI.Pro"
ACCOUNT_ID="152687308610"
REGION="us-east-1"
CLUSTER_NAME="infinityai-pro-cluster"

echo "🚀 Automating CI/CD Pipeline for InfinityAI.Pro..."
echo "Repository: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to create GitHub OIDC provider
setup_github_oidc() {
    print_info "Setting up GitHub OIDC provider..."
    
    aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
        --region $REGION 2>/dev/null || print_warning "OIDC provider already exists"
    
    print_status "GitHub OIDC provider configured"
}

# Function to create IAM roles for GitHub Actions
create_github_roles() {
    local service_name=$1
    local role_name="InfinityAI-GitHubActions-${service_name}-Role"
    
    print_info "Creating IAM role for $service_name..."
    
    # Trust policy for GitHub Actions
    cat > /tmp/github-trust-${service_name}.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_OWNER}/${GITHUB_REPO}:*"
        }
      }
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name $role_name \
        --assume-role-policy-document file:///tmp/github-trust-${service_name}.json \
        --description "GitHub Actions role for InfinityAI ${service_name}" 2>/dev/null || print_warning "Role $role_name already exists"

    # Permissions policy
    cat > /tmp/github-permissions-${service_name}.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRFullAccess",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:DescribeImages"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECSDeployment",
      "Effect": "Allow",
      "Action": [
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:ListTasks",
        "ecs:DescribeTasks"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMPassRole",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole",
        "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskRole"
      ]
    },
    {
      "Sid": "LogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    }
  ]
}
EOF

    # Attach policy
    aws iam put-role-policy \
        --role-name $role_name \
        --policy-name InfinityAI-GitHubActions-Policy \
        --policy-document file:///tmp/github-permissions-${service_name}.json

    print_status "Created IAM role: $role_name"
    echo "Role ARN: arn:aws:iam::${ACCOUNT_ID}:role/${role_name}"
}

# Main execution function
main() {
    print_info "Starting InfinityAI.Pro CI/CD Automation..."
    print_info "Repository: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}"
    
    # Setup AWS resources
    setup_github_oidc
    create_github_roles "engine-c"
    create_github_roles "engine-d"
    create_github_roles "live-trader"
    
    # Cleanup temporary files
    rm -f /tmp/github-trust-*.json /tmp/github-permissions-*.json
    
    print_status "🎉 InfinityAI.Pro CI/CD Pipeline Automation Complete!"
    
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. 📁 Create GitHub workflows"
    echo "2. 🔐 Configure OIDC authentication"
    echo "3. 📤 Deploy live trading system"
    echo "4. 🔍 Monitor deployments"
    echo ""
    echo -e "${GREEN}🔗 Important URLs:${NC}"
    echo "Repository: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}"
    echo "Actions: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/actions"
    echo ""
    echo -e "${YELLOW}⚡ IAM Roles Created:${NC}"
    echo "Engine C: arn:aws:iam::${ACCOUNT_ID}:role/InfinityAI-GitHubActions-engine-c-Role"
    echo "Engine D: arn:aws:iam::${ACCOUNT_ID}:role/InfinityAI-GitHubActions-engine-d-Role"
    echo "Live Trader: arn:aws:iam::${ACCOUNT_ID}:role/InfinityAI-GitHubActions-live-trader-Role"
}

# Run the main function
main "$@"