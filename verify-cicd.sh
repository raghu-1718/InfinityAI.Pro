#!/bin/bash

# InfinityAI.Pro - AWS and Google Cloud CI/CD Verification Script
# This script verifies that AWS and Google Cloud CI/CD configurations are correct

set -e

echo "🔍 InfinityAI.Pro - AWS & Google Cloud CI/CD Verification"
echo "============================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️  WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌ FAIL]${NC} $1"
}

# Track overall status
OVERALL_STATUS=0
TOTAL_CHECKS=0
PASSED_CHECKS=0

run_check() {
    local check_name="$1"
    local check_command="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    print_status "$check_name"
    
    if eval "$check_command" &>/dev/null; then
        print_success "$check_name"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        print_error "$check_name"
        OVERALL_STATUS=1
        return 1
    fi
}

echo "📋 WORKFLOW FILE VERIFICATION"
echo "=============================="

# Check if workflow files exist
print_status "Checking for multi-cloud CI/CD workflow"
if [ -f "infinityai-pro/.github/workflows/multi-cloud-cicd.yml" ]; then
    print_success "Multi-cloud CI/CD workflow exists"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Multi-cloud CI/CD workflow NOT found"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking for deploy-live-trading workflow"
if [ -f "infinityai-pro/.github/workflows/deploy-live-trading.yml" ]; then
    print_success "Deploy-live-trading workflow exists"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Deploy-live-trading workflow NOT found"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "🔧 AWS CI/CD CONFIGURATION VERIFICATION"
echo "========================================"

# Check AWS workflow configuration
print_status "Checking AWS deployment job in multi-cloud workflow"
if grep -q "deploy-aws:" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "AWS deployment job configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "AWS deployment job NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking AWS credentials configuration"
if grep -q "aws-actions/configure-aws-credentials" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "AWS credentials step configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "AWS credentials step NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking AWS ECR login configuration"
if grep -q "aws-actions/amazon-ecr-login" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "AWS ECR login configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "AWS ECR login NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking AWS Engine C deployment"
if grep -q "infinityai-engine-c" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Engine C deployment configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Engine C deployment NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking AWS Engine D deployment"
if grep -q "infinityai-engine-d" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Engine D deployment configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Engine D deployment NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking AWS ECS task definition updates"
if grep -q "ecs register-task-definition\|ecs update-service" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "ECS task definition and service update configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "ECS task definition and service update NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "🌐 GOOGLE CLOUD CI/CD CONFIGURATION VERIFICATION"
echo "================================================="

# Check Google Cloud workflow configuration
print_status "Checking GCP deployment job in multi-cloud workflow"
if grep -q "deploy-gcp:" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "GCP deployment job configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "GCP deployment job NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking Google Cloud authentication"
if grep -q "google-github-actions/auth" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Google Cloud authentication configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Google Cloud authentication NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking GCP Cloud SDK setup"
if grep -q "google-github-actions/setup-gcloud" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Cloud SDK setup configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Cloud SDK setup NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking GCR Docker configuration"
if grep -q "gcloud auth configure-docker" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "GCR Docker configuration found"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "GCR Docker configuration NOT found"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking Cloud Run deployment"
if grep -q "gcloud run deploy" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Cloud Run deployment configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Cloud Run deployment NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking Engine B deployment to GCP"
if grep -q "infinityai-engine-b" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Engine B deployment to GCP configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "Engine B deployment to GCP NOT configured"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "🔐 REQUIRED SECRETS VERIFICATION"
echo "================================="

# Check for required secrets references in workflows
print_status "Checking AWS_ACCESS_KEY_ID reference"
if grep -q "AWS_ACCESS_KEY_ID" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "AWS_ACCESS_KEY_ID secret referenced"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_warning "AWS_ACCESS_KEY_ID secret NOT referenced (may be using OIDC)"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking AWS_SECRET_ACCESS_KEY reference"
if grep -q "AWS_SECRET_ACCESS_KEY" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "AWS_SECRET_ACCESS_KEY secret referenced"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_warning "AWS_SECRET_ACCESS_KEY secret NOT referenced (may be using OIDC)"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking GCP_SERVICE_ACCOUNT_KEY reference"
if grep -q "GCP_SERVICE_ACCOUNT_KEY" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "GCP_SERVICE_ACCOUNT_KEY secret referenced"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "GCP_SERVICE_ACCOUNT_KEY secret NOT referenced"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "📦 ENVIRONMENT VARIABLES VERIFICATION"
echo "======================================"

print_status "Checking AWS_REGION environment variable"
if grep -q "AWS_REGION:" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    AWS_REGION=$(grep "AWS_REGION:" infinityai-pro/.github/workflows/multi-cloud-cicd.yml | head -1 | awk '{print $2}')
    print_success "AWS_REGION set to: $AWS_REGION"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "AWS_REGION NOT set"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking GCP_PROJECT_ID environment variable"
if grep -q "GCP_PROJECT_ID:" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    GCP_PROJECT_ID=$(grep "GCP_PROJECT_ID:" infinityai-pro/.github/workflows/multi-cloud-cicd.yml | head -1 | awk '{print $2}')
    print_success "GCP_PROJECT_ID set to: $GCP_PROJECT_ID"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "GCP_PROJECT_ID NOT set"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "🔄 INTEGRATION TESTS VERIFICATION"
echo "=================================="

print_status "Checking integration tests job"
if grep -q "integration-tests:" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Integration tests job configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_warning "Integration tests job NOT configured"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Checking multi-cloud deployment dependencies"
if grep -q "needs: \[deploy-azure, deploy-gcp, deploy-aws\]" infinityai-pro/.github/workflows/multi-cloud-cicd.yml; then
    print_success "Integration tests depend on all cloud deployments"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_warning "Integration tests dependencies incomplete"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "🚀 DEPLOYMENT SCRIPT VERIFICATION"
echo "=================================="

print_status "Checking AWS OIDC automation script"
if [ -f "infinityai-pro/automate-infinityai-cicd.sh" ]; then
    print_success "AWS OIDC automation script exists"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    
    # Check if script is executable
    if [ -x "infinityai-pro/automate-infinityai-cicd.sh" ]; then
        print_success "Automation script is executable"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_warning "Automation script is not executable (chmod +x needed)"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
else
    print_error "AWS OIDC automation script NOT found"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "📄 WORKFLOW SYNTAX VERIFICATION"
echo "================================"

# Check YAML syntax (basic check)
print_status "Validating multi-cloud-cicd.yml syntax"
if python3 -c "import yaml; yaml.safe_load(open('infinityai-pro/.github/workflows/multi-cloud-cicd.yml'))" 2>/dev/null; then
    print_success "multi-cloud-cicd.yml has valid YAML syntax"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "multi-cloud-cicd.yml has INVALID YAML syntax"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

print_status "Validating deploy-live-trading.yml syntax"
if python3 -c "import yaml; yaml.safe_load(open('infinityai-pro/.github/workflows/deploy-live-trading.yml'))" 2>/dev/null; then
    print_success "deploy-live-trading.yml has valid YAML syntax"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "deploy-live-trading.yml has INVALID YAML syntax"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
echo "📊 VERIFICATION SUMMARY"
echo "======================="
echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo "Passed: $PASSED_CHECKS"
echo "Failed: $((TOTAL_CHECKS - PASSED_CHECKS))"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    print_success "🎉 ALL CRITICAL CHECKS PASSED! AWS and Google Cloud CI/CD are properly configured."
else
    print_error "⚠️  SOME CHECKS FAILED. Please review the errors above."
fi

echo ""
echo "📋 NEXT STEPS"
echo "============="
echo ""
echo "1. Ensure GitHub repository secrets are configured:"
echo "   - AWS_ACCESS_KEY_ID (or use OIDC)"
echo "   - AWS_SECRET_ACCESS_KEY (or use OIDC)"
echo "   - GCP_SERVICE_ACCOUNT_KEY"
echo "   - DHAN_CLIENT_ID"
echo "   - DHAN_ACCESS_TOKEN"
echo "   - DHAN_API_KEY"
echo "   - DHAN_API_SECRET"
echo ""
echo "2. For AWS OIDC (recommended), run:"
echo "   cd infinityai-pro && ./automate-infinityai-cicd.sh"
echo ""
echo "3. Test the workflow by pushing to main branch or running manually:"
echo "   gh workflow run multi-cloud-cicd.yml"
echo ""
echo "4. Monitor deployment status:"
echo "   https://github.com/raghu-1718/InfinityAI.Pro/actions"
echo ""

exit $OVERALL_STATUS
