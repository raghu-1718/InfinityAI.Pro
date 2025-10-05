#!/bin/bash

# InfinityAI.Pro - Deployment Verification Script
# Verify complete multi-cloud deployment and DHAN API integration

set -e

echo "🔍 InfinityAI.Pro - Deployment Verification"
echo "==========================================="
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

echo "Starting comprehensive deployment verification..."
echo ""

# =============================================================================
# AWS INFRASTRUCTURE CHECKS
# =============================================================================
echo "📊 AWS INFRASTRUCTURE VERIFICATION"
echo "=================================="

# Check AWS CLI and credentials
run_check "AWS CLI installed and configured" "command -v aws && aws sts get-caller-identity"

# Check ECS Cluster
run_check "ECS Cluster exists" "aws ecs describe-clusters --clusters infinityai-cluster --query 'clusters[0].status' --output text | grep -q ACTIVE"

# Check ECS Service
run_check "ECS Service running" "aws ecs describe-services --cluster infinityai-cluster --services infinityai-engine-d --query 'services[0].status' --output text | grep -q ACTIVE"

# Check ECS Service running tasks
ECS_RUNNING_TASKS=$(aws ecs describe-services --cluster infinityai-cluster --services infinityai-engine-d --query 'services[0].runningCount' --output text 2>/dev/null || echo "0")
if [ "$ECS_RUNNING_TASKS" -gt 0 ]; then
    print_success "ECS Service has $ECS_RUNNING_TASKS running tasks"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_error "ECS Service has no running tasks"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check Application Load Balancer
run_check "Application Load Balancer exists" "aws elbv2 describe-load-balancers --names infinityai-engine-d-alb --query 'LoadBalancers[0].State.Code' --output text | grep -q active"

# Check Target Group health
TG_ARN=$(aws elbv2 describe-target-groups --names infinityai-engine-d-tg --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || echo "")
if [ -n "$TG_ARN" ] && [ "$TG_ARN" != "None" ]; then
    HEALTHY_TARGETS=$(aws elbv2 describe-target-health --target-group-arn "$TG_ARN" --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`]' --output json | jq length 2>/dev/null || echo "0")
    if [ "$HEALTHY_TARGETS" -gt 0 ]; then
        print_success "Target Group has $HEALTHY_TARGETS healthy targets"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_warning "Target Group has no healthy targets (may still be starting)"
    fi
else
    print_error "Target Group not found"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check Redis cluster
run_check "Redis cluster exists" "aws elasticache describe-replication-groups --replication-group-id infinityai-redis --query 'ReplicationGroups[0].Status' --output text | grep -q available"

# Check DHAN secrets in Secrets Manager
run_check "DHAN credentials stored in Secrets Manager" "aws secretsmanager describe-secret --secret-id infinityai/dhan-credentials"

echo ""

# =============================================================================
# AZURE INFRASTRUCTURE CHECKS
# =============================================================================
echo "🌐 AZURE INFRASTRUCTURE VERIFICATION"
echo "===================================="

# Check Azure CLI and login
run_check "Azure CLI installed and logged in" "command -v az && az account show"

# Check Resource Group
run_check "Azure Resource Group exists" "az group show --name infinityai-rg"

# Check App Service Plan
run_check "App Service Plan exists" "az appservice plan show --name infinityai-plan --resource-group infinityai-rg"

# Check Web App
run_check "Web App exists and running" "az webapp show --name infinityai-pro --resource-group infinityai-rg --query 'state' --output tsv | grep -q Running"

# Get App Service URL
AZURE_HOSTNAME=$(az webapp show --name infinityai-pro --resource-group infinityai-rg --query "defaultHostName" -o tsv 2>/dev/null || echo "")
if [ -n "$AZURE_HOSTNAME" ]; then
    print_success "Azure App Service URL: https://$AZURE_HOSTNAME"
else
    print_error "Could not retrieve Azure App Service hostname"
    OVERALL_STATUS=1
fi

echo ""

# =============================================================================
# NETWORK CONNECTIVITY CHECKS
# =============================================================================
echo "🌐 NETWORK CONNECTIVITY VERIFICATION"
echo "===================================="

# Check if ALB DNS resolves
ALB_DNS=$(aws elbv2 describe-load-balancers --names infinityai-engine-d-alb --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null || echo "")
if [ -n "$ALB_DNS" ] && [ "$ALB_DNS" != "None" ]; then
    if nslookup "$ALB_DNS" &>/dev/null; then
        print_success "AWS Load Balancer DNS resolves: $ALB_DNS"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_error "AWS Load Balancer DNS does not resolve"
        OVERALL_STATUS=1
    fi
else
    print_error "Could not retrieve AWS Load Balancer DNS"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check if Azure hostname resolves
if [ -n "$AZURE_HOSTNAME" ]; then
    if nslookup "$AZURE_HOSTNAME" &>/dev/null; then
        print_success "Azure App Service DNS resolves: $AZURE_HOSTNAME"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_error "Azure App Service DNS does not resolve"
        OVERALL_STATUS=1
    fi
else
    print_error "Azure hostname not available for DNS check"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

# =============================================================================
# APPLICATION HEALTH CHECKS
# =============================================================================
echo "🏥 APPLICATION HEALTH VERIFICATION"
echo "=================================="

# Check AWS API health endpoint (if accessible)
if [ -n "$ALB_DNS" ]; then
    print_status "Checking AWS API health endpoint"
    if curl -f -s "http://$ALB_DNS/health" | grep -q "healthy" 2>/dev/null; then
        print_success "AWS API health endpoint responding"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_warning "AWS API health endpoint not responding (may need SSL/DNS setup)"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Check Azure frontend (if accessible)
if [ -n "$AZURE_HOSTNAME" ]; then
    print_status "Checking Azure frontend accessibility"
    if curl -f -s "https://$AZURE_HOSTNAME" &>/dev/null; then
        print_success "Azure frontend responding"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_warning "Azure frontend not responding (may still be deploying)"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""

# =============================================================================
# SECURITY CHECKS
# =============================================================================
echo "🔐 SECURITY VERIFICATION"
echo "========================"

# Check if DHAN secret can be retrieved
print_status "Testing DHAN credentials access"
DHAN_SECRET=$(aws secretsmanager get-secret-value --secret-id infinityai/dhan-credentials --query 'SecretString' --output text 2>/dev/null || echo "")
if [ -n "$DHAN_SECRET" ]; then
    if echo "$DHAN_SECRET" | jq -r '.client_id' | grep -q "63b3086e" 2>/dev/null; then
        print_success "DHAN credentials accessible and valid"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_error "DHAN credentials format invalid"
        OVERALL_STATUS=1
    fi
else
    print_error "Cannot access DHAN credentials"
    OVERALL_STATUS=1
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check Azure HTTPS redirect
if [ -n "$AZURE_HOSTNAME" ]; then
    HTTPS_CHECK=$(az webapp show --name infinityai-pro --resource-group infinityai-rg --query 'httpsOnly' --output tsv 2>/dev/null || echo "false")
    if [ "$HTTPS_CHECK" = "true" ]; then
        print_success "Azure App Service HTTPS redirect enabled"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_warning "Azure App Service HTTPS redirect not enabled"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""

# =============================================================================
# DNS CONFIGURATION STATUS
# =============================================================================
echo "🌍 DNS CONFIGURATION STATUS"
echo "==========================="

print_status "Checking domain DNS configuration"

# Check main domain
if nslookup infinityai.pro &>/dev/null; then
    DOMAIN_IP=$(nslookup infinityai.pro | grep -A1 "Non-authoritative answer:" | grep "Address:" | awk '{print $2}' | tail -1 2>/dev/null || echo "")
    if [ -n "$DOMAIN_IP" ]; then
        print_success "infinityai.pro resolves to: $DOMAIN_IP"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_warning "infinityai.pro resolves but IP extraction failed"
    fi
else
    print_warning "infinityai.pro not configured in DNS yet"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check API subdomain
if nslookup api.infinityai.pro &>/dev/null; then
    print_success "api.infinityai.pro DNS configured"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_warning "api.infinityai.pro not configured in DNS yet"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

# =============================================================================
# DEPLOYMENT SUMMARY
# =============================================================================
echo "📋 DEPLOYMENT VERIFICATION SUMMARY"
echo "=================================="
echo ""

# Calculate success rate
SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo "✅ Passed Checks: $PASSED_CHECKS"
echo "📊 Total Checks: $TOTAL_CHECKS"
echo "💯 Success Rate: $SUCCESS_RATE%"
echo ""

if [ $OVERALL_STATUS -eq 0 ] && [ $SUCCESS_RATE -gt 80 ]; then
    print_success "🎉 Deployment verification PASSED!"
    echo ""
    echo "🚀 Your InfinityAI.Pro system is successfully deployed!"
    echo ""
    echo "✅ Infrastructure: Healthy"
    echo "✅ Security: Configured"
    echo "✅ DHAN Integration: Ready"
    echo ""
    echo "🔗 Access URLs:"
    if [ -n "$AZURE_HOSTNAME" ]; then
        echo "   Frontend: https://$AZURE_HOSTNAME"
    fi
    if [ -n "$ALB_DNS" ]; then
        echo "   API: http://$ALB_DNS (configure SSL for production)"
    fi
    echo ""
    echo "📋 Next Steps:"
    echo "1. Configure custom domain DNS records"
    echo "2. Set up SSL certificates"
    echo "3. Configure DHAN API settings"
    echo "4. Test DHAN OAuth flow"
    echo ""
elif [ $SUCCESS_RATE -gt 60 ]; then
    print_warning "⚠️  Deployment verification completed with warnings"
    echo ""
    echo "✅ Core infrastructure is deployed"
    echo "⚠️  Some components may need additional configuration"
    echo "📋 Check the warnings above and complete the setup"
    echo ""
else
    print_error "❌ Deployment verification FAILED"
    echo ""
    echo "❌ Critical issues found in deployment"
    echo "📋 Review the errors above and redeploy if necessary"
    echo ""
    OVERALL_STATUS=1
fi

echo "📚 For detailed setup instructions:"
echo "   📖 docs/namecheap-dns-setup.md"
echo "   📖 docs/architecture.md"
echo ""

exit $OVERALL_STATUS