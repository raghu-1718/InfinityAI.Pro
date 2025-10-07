#!/bin/bash
# CI/CD Workflow Validation Script
# This script validates that all prerequisites are in place for CI/CD deployment

set -e

echo "🔍 InfinityAI.Pro CI/CD Validation"
echo "===================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} Found: $1"
    else
        echo -e "${RED}❌${NC} Missing: $1"
        ((ERRORS++))
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} Found: $1"
    else
        echo -e "${RED}❌${NC} Missing: $1"
        ((ERRORS++))
    fi
}

# Function to check optional file
check_optional() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} Found: $1"
    else
        echo -e "${YELLOW}⚠️${NC}  Optional: $1 (not critical)"
        ((WARNINGS++))
    fi
}

echo "1. Checking GitHub Actions Workflow Files..."
check_file ".github/workflows/multi-cloud-cicd.yml"
echo ""

echo "2. Checking Documentation..."
check_file "CI-CD-SETUP-GUIDE.md"
check_file "SECRETS-QUICK-REFERENCE.md"
check_file "README.md"
echo ""

echo "3. Checking Project Structure..."
check_dir "infinityai-pro"
check_dir "infinityai-pro/frontend"
check_dir "infinityai-pro/backend"
check_dir "infinityai-pro/backend/engines"
echo ""

echo "4. Checking Dockerfiles..."
check_file "infinityai-pro/Dockerfile"
check_file "infinityai-pro/backend/engines/engine-b/Dockerfile"
check_file "infinityai-pro/backend/engines/engine-c/Dockerfile"
check_file "infinityai-pro/backend/engines/engine-d/Dockerfile"
echo ""

echo "5. Checking Frontend Files..."
check_file "infinityai-pro/frontend/package.json"
check_dir "infinityai-pro/frontend/src"
echo ""

echo "6. Checking Backend Files..."
check_file "infinityai-pro/backend/main.py"
check_optional "infinityai-pro/backend/requirements.txt"
echo ""

echo "7. Checking AWS Task Definitions..."
check_optional "engine-c-task-def-fixed.json"
check_optional "engine-d-task-def.json"
echo ""

echo "8. Validating YAML Syntax..."
if command -v python3 &> /dev/null; then
    python3 -c "
import yaml
import sys
try:
    with open('.github/workflows/multi-cloud-cicd.yml') as f:
        yaml.safe_load(f)
    print('${GREEN}✅${NC} Workflow YAML is valid')
except Exception as e:
    print('${RED}❌${NC} Workflow YAML has errors:', e)
    sys.exit(1)
" || ((ERRORS++))
else
    echo -e "${YELLOW}⚠️${NC}  Python3 not found, skipping YAML validation"
    ((WARNINGS++))
fi
echo ""

echo "===================================="
echo "Validation Summary:"
echo "===================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo -e "${GREEN}✅ CI/CD workflow is ready to use${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Configure GitHub Secrets (see SECRETS-QUICK-REFERENCE.md)"
    echo "2. Enable GitHub Actions in your repository"
    echo "3. Push to main branch or manually trigger the workflow"
else
    echo -e "${RED}❌ Found $ERRORS error(s)${NC}"
    echo "Please fix the errors above before using CI/CD"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s) - these are not critical${NC}"
fi

echo ""
echo "For detailed setup instructions, see: CI-CD-SETUP-GUIDE.md"
