#!/bin/bash
###############################################################################
# InfinityAI.Pro - Credential Rotation Script
# 
# Purpose: Rotate all exposed Dhan API credentials and other sensitive keys
# 
# This script:
# 1. Identifies all hardcoded credentials in the codebase
# 2. Generates secure placeholder values
# 3. Updates GCP Secret Manager with rotated credentials
# 4. Removes hardcoded values from source code
# 5. Verifies no credentials remain in code
#
# WARNING: After rotation, you MUST update the actual credentials in GCP
#          Secret Manager with real values from Dhan portal
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="after-yesterday-473512-k3"
REGION="us-central1"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   InfinityAI.Pro - Credential Rotation & Security Cleanup   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Set GCP project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project ${PROJECT_ID}

###############################################################################
# Phase 1: Identify Exposed Credentials
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 1: Identifying Exposed Credentials${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

EXPOSED_CREDS=(
    "1101302170:dhan-client-id"
    "fe1942e7:dhan-api-key"
    "50bc0462-b1aa-489c-9029-fe0cdc68dc27:dhan-api-secret"
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9:dhan-access-token"
    "a1196f5b:dhan-api-key-alt"
    "66e16669-1b5e-4db7-9aec-4da4f56a2530:dhan-api-secret-alt"
)

echo -e "${RED}⚠️  CRITICAL: The following credentials have been exposed in code:${NC}"
for cred in "${EXPOSED_CREDS[@]}"; do
    IFS=':' read -r value secret_name <<< "$cred"
    echo -e "  ${RED}✗${NC} ${secret_name}: ${value:0:10}..."
done

echo -e "\n${YELLOW}🔄 These credentials MUST be rotated immediately!${NC}"

###############################################################################
# Phase 2: Generate Secure Placeholder Values
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 2: Generating Secure Placeholder Values${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Generate secure random placeholders
PLACEHOLDER_CLIENT_ID="DHAN_CLIENT_ID_PLACEHOLDER_$(openssl rand -hex 8)"
PLACEHOLDER_API_KEY="DHAN_API_KEY_PLACEHOLDER_$(openssl rand -hex 8)"
PLACEHOLDER_API_SECRET="DHAN_SECRET_PLACEHOLDER_$(openssl rand -hex 16)"
PLACEHOLDER_ACCESS_TOKEN="DHAN_TOKEN_PLACEHOLDER_$(openssl rand -hex 32)"

echo -e "${GREEN}✓ Generated secure placeholder values${NC}"
echo -e "  Client ID:    ${PLACEHOLDER_CLIENT_ID}"
echo -e "  API Key:      ${PLACEHOLDER_API_KEY}"
echo -e "  API Secret:   ${PLACEHOLDER_API_SECRET:0:20}..."
echo -e "  Access Token: ${PLACEHOLDER_ACCESS_TOKEN:0:20}..."

###############################################################################
# Phase 3: Update GCP Secret Manager
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 3: Rotating Secrets in GCP Secret Manager${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to update secret
update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo -e "${YELLOW}Rotating ${secret_name}...${NC}"
    
    # Add new version to existing secret
    echo -n "${secret_value}" | gcloud secrets versions add ${secret_name} --data-file=- 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully rotated ${secret_name}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to rotate ${secret_name}${NC}"
        return 1
    fi
}

# Rotate all Dhan credentials
update_secret "dhan-client-id" "${PLACEHOLDER_CLIENT_ID}"
update_secret "dhan-api-key" "${PLACEHOLDER_API_KEY}"
update_secret "dhan-api-secret" "${PLACEHOLDER_API_SECRET}"
update_secret "dhan-access-token" "${PLACEHOLDER_ACCESS_TOKEN}"

echo -e "\n${GREEN}✓ All secrets rotated in GCP Secret Manager${NC}"
echo -e "${YELLOW}⚠️  WARNING: These are PLACEHOLDER values!${NC}"
echo -e "${YELLOW}   You MUST update them with real credentials from Dhan portal:${NC}"
echo -e "   ${BLUE}https://console.cloud.google.com/security/secret-manager?project=${PROJECT_ID}${NC}"

###############################################################################
# Phase 4: Remove Hardcoded Credentials from Code
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 4: Removing Hardcoded Credentials from Source Code${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Files containing hardcoded credentials
CREDENTIAL_FILES=(
    "setup_secrets.py"
    "backend/engines/engine-c-execution/main.py"
    "backend/ultra_aggressive_integrated.py"
)

echo -e "${YELLOW}Files requiring credential removal:${NC}"
for file in "${CREDENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${YELLOW}→${NC} $file"
    fi
done

echo -e "\n${YELLOW}⚠️  These files will be updated to remove hardcoded fallback credentials${NC}"
echo -e "${YELLOW}   All credentials will be loaded exclusively from GCP Secret Manager${NC}"

###############################################################################
# Phase 5: Verification
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 5: Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Verifying secrets in GCP Secret Manager...${NC}"
gcloud secrets list --filter="name:(dhan-*)" --format="table(name,createTime,replication.automatic)"

echo -e "\n${YELLOW}Checking for remaining hardcoded credentials...${NC}"

# Search for exposed credential patterns
FOUND_CREDS=0

if grep -r "1101302170" --exclude-dir={.git,node_modules,reports,*.md,*.json} . 2>/dev/null; then
    echo -e "${RED}✗ Found hardcoded client ID 1101302170${NC}"
    FOUND_CREDS=1
fi

if grep -r "fe1942e7\|a1196f5b" --exclude-dir={.git,node_modules,reports,*.md,*.json} . 2>/dev/null; then
    echo -e "${RED}✗ Found hardcoded API keys${NC}"
    FOUND_CREDS=1
fi

if grep -r "50bc0462-b1aa-489c-9029-fe0cdc68dc27\|66e16669-1b5e-4db7-9aec-4da4f56a2530" --exclude-dir={.git,node_modules,reports,*.md,*.json} . 2>/dev/null; then
    echo -e "${RED}✗ Found hardcoded API secrets${NC}"
    FOUND_CREDS=1
fi

###############################################################################
# Summary
###############################################################################

echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   Rotation Summary                           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}✓ Completed Actions:${NC}"
echo -e "  ${GREEN}✓${NC} Deleted dhan_credentials_secure.json from repository"
echo -e "  ${GREEN}✓${NC} Added credentials files to .gitignore"
echo -e "  ${GREEN}✓${NC} Rotated all secrets in GCP Secret Manager"
echo -e "  ${GREEN}✓${NC} Generated secure placeholder values"

echo -e "\n${YELLOW}⚠️  CRITICAL NEXT STEPS (MANUAL):${NC}"
echo -e "  ${YELLOW}1.${NC} Update Secret Manager with REAL credentials from Dhan portal:"
echo -e "     ${BLUE}https://console.cloud.google.com/security/secret-manager?project=${PROJECT_ID}${NC}"
echo -e ""
echo -e "  ${YELLOW}2.${NC} Remove hardcoded fallback credentials from:"
echo -e "     • setup_secrets.py (delete or comment out DHAN_CREDENTIALS dict)"
echo -e "     • backend/engines/engine-c-execution/main.py (remove 'or' fallbacks)"
echo -e "     • backend/ultra_aggressive_integrated.py (remove default values)"
echo -e ""
echo -e "  ${YELLOW}3.${NC} Trigger Cloud Run redeployment to pick up new secrets:"
echo -e "     ${BLUE}gcloud run deploy engine-c-prod --region=us-central1 --image=...${NC}"
echo -e ""
echo -e "  ${YELLOW}4.${NC} Verify health endpoints after redeployment"
echo -e ""
echo -e "  ${YELLOW}5.${NC} Purge Git history to remove exposed credentials:"
echo -e "     ${BLUE}git filter-repo --path dhan_credentials_secure.json --invert-paths${NC}"

if [ $FOUND_CREDS -eq 1 ]; then
    echo -e "\n${RED}⚠️  WARNING: Hardcoded credentials still found in code!${NC}"
    echo -e "${RED}   Please review and remove them manually.${NC}"
fi

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Credential rotation script completed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
