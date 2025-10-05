#!/bin/bash

# InfinityAI.Pro - Master Deployment Script
# Deploy complete multi-cloud architecture with DHAN integration

set -e

echo "🚀 InfinityAI.Pro - Complete Multi-Cloud Deployment"
echo "=================================================="
echo ""
echo "This script will deploy:"
echo "✅ Engine D (AWS ECS) - Central Backend API"
echo "✅ Frontend (Azure App Service) - React Application"
echo "✅ DHAN API Integration - Secure credentials management"
echo "✅ DNS Configuration Guide"
echo ""

# Color codes for output
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

# Check prerequisites
echo ""
print_status "Checking prerequisites..."

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install and configure AWS CLI first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if Azure CLI is installed and configured
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install and configure Azure CLI first."
    exit 1
fi

# Check Azure login status
if ! az account show &> /dev/null; then
    print_error "Azure not logged in. Please run 'az login' first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "All prerequisites met!"

# Prompt for confirmation
echo ""
print_warning "⚠️  IMPORTANT: This deployment will:"
echo "   • Store DHAN API credentials securely in AWS Secrets Manager"
echo "   • Create AWS resources (ECS, ALB, ElastiCache)"
echo "   • Create Azure resources (App Service, Resource Group)"
echo "   • Configure production environments"
echo ""
read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled."
    exit 0
fi

echo ""
print_status "Starting deployment process..."

# Step 1: Deploy Engine D to AWS
echo ""
echo "=========================================="
print_status "Step 1/2: Deploying Engine D to AWS"
echo "=========================================="

if [ -f "./deploy-engine-d-aws.sh" ]; then
    chmod +x ./deploy-engine-d-aws.sh
    if ./deploy-engine-d-aws.sh; then
        print_success "Engine D (AWS) deployment completed successfully!"
    else
        print_error "Engine D (AWS) deployment failed!"
        exit 1
    fi
else
    print_error "deploy-engine-d-aws.sh not found!"
    exit 1
fi

# Wait for AWS resources to be ready
print_status "Waiting for AWS resources to initialize..."
sleep 30

# Step 2: Deploy Frontend to Azure
echo ""
echo "=========================================="
print_status "Step 2/2: Deploying Frontend to Azure"
echo "=========================================="

if [ -f "./deploy-frontend-azure.sh" ]; then
    chmod +x ./deploy-frontend-azure.sh
    if ./deploy-frontend-azure.sh; then
        print_success "Frontend (Azure) deployment completed successfully!"
    else
        print_error "Frontend (Azure) deployment failed!"
        exit 1
    fi
else
    print_error "deploy-frontend-azure.sh not found!"
    exit 1
fi

# Step 3: Get deployment information
echo ""
echo "=========================================="
print_status "Gathering Deployment Information"
echo "=========================================="

# Get AWS ALB DNS name
print_status "Retrieving AWS Application Load Balancer DNS name..."
ALB_DNS=$(aws elbv2 describe-load-balancers --names infinityai-engine-d-alb --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null || echo "Not found")

# Get Azure App Service hostname
print_status "Retrieving Azure App Service hostname..."
AZURE_HOSTNAME=$(az webapp show --name infinityai-pro --resource-group infinityai-rg --query "defaultHostName" -o tsv 2>/dev/null || echo "Not found")

# Get Azure App Service IP
print_status "Retrieving Azure App Service IP address..."
if [ "$AZURE_HOSTNAME" != "Not found" ]; then
    AZURE_IP=$(nslookup $AZURE_HOSTNAME | grep -A1 "Non-authoritative answer:" | grep "Address:" | awk '{print $2}' | tail -1 || echo "Not found")
else
    AZURE_IP="Not found"
fi

# Step 4: Display deployment summary
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
print_success "✅ Engine D (AWS Backend): Deployed successfully"
print_success "✅ Frontend (Azure React): Deployed successfully" 
print_success "✅ DHAN API Integration: Configured with secure credentials"
echo ""

# AWS Information
echo "📊 AWS DEPLOYMENT DETAILS"
echo "-------------------------"
echo "🔗 ECS Cluster: infinityai-cluster"
echo "🔗 ECS Service: infinityai-engine-d"
echo "🔗 Load Balancer DNS: $ALB_DNS"
echo "🔗 API Endpoint: https://api.infinityai.pro (after DNS setup)"
echo "🔐 DHAN Credentials: Stored in AWS Secrets Manager"
echo ""

# Azure Information
echo "🌐 AZURE DEPLOYMENT DETAILS"
echo "---------------------------"
echo "🔗 Resource Group: infinityai-rg"
echo "🔗 App Service: infinityai-pro"
echo "🔗 Default URL: https://$AZURE_HOSTNAME"
echo "🔗 Custom Domain: https://infinityai.pro (after DNS setup)"
echo "🔗 App Service IP: $AZURE_IP"
echo ""

# DHAN Configuration
echo "🔐 DHAN API CONFIGURATION"
echo "------------------------"
echo "Configure these URLs in your DHAN API settings:"
echo "🔗 Redirect URI: https://infinityai.pro/auth/callback"
echo "🔗 Postback URL: https://api.infinityai.pro/auth/dhan/postback"
echo ""

# DNS Configuration
echo "🌍 DNS CONFIGURATION REQUIRED"
echo "-----------------------------"
echo "Configure these DNS records in Namecheap:"
echo ""
echo "A Record:"
echo "  Host: @"
echo "  Value: $AZURE_IP"
echo "  TTL: 300"
echo ""
echo "CNAME Record (WWW):"
echo "  Host: www"
echo "  Value: $AZURE_HOSTNAME"
echo "  TTL: 300"
echo ""
echo "CNAME Record (API):"
echo "  Host: api" 
echo "  Value: $ALB_DNS"
echo "  TTL: 300"
echo ""

# Next Steps
echo "📋 NEXT STEPS"
echo "-------------"
echo "1. 🌍 Configure DNS records in Namecheap (see details above)"
echo "2. 🔐 Set up SSL certificates in Azure Portal and AWS Certificate Manager"
echo "3. 🔑 Configure DHAN API settings with the provided URLs"
echo "4. ✅ Test the complete system:"
echo "   • Frontend: https://infinityai.pro"
echo "   • API Health: https://api.infinityai.pro/health"
echo "   • API Docs: https://api.infinityai.pro/docs"
echo "5. 🎯 Access token management in the dashboard"
echo ""

# Documentation
echo "📚 DOCUMENTATION"
echo "----------------"
echo "📖 Complete DNS setup guide: docs/namecheap-dns-setup.md"
echo "📖 Architecture overview: docs/architecture.md"
echo "📖 DHAN API integration: docs/dhan-integration.md"
echo ""

# Final Status
print_success "🚀 InfinityAI.Pro multi-cloud deployment completed successfully!"
print_warning "⏳ DNS propagation may take 24-48 hours to complete globally"
print_status "🔧 Monitor deployments in AWS CloudWatch and Azure Monitor"

echo ""
echo "Happy Trading with InfinityAI.Pro! 🚀📈"