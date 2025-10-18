#!/usr/bin/env python3
"""
InfinityAI.Pro - Google Cloud Secret Manager Setup
Store Dhan credentials securely in Google Secret Manager
"""

import subprocess
import sys
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SECRET-MANAGER - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ⚠️ SECURITY: Credentials are now stored in GCP Secret Manager
# DO NOT hardcode credentials here. Instead:
# 1. Create secrets in Secret Manager: https://console.cloud.google.com/security/secret-manager
# 2. Use the secret names below to reference them
# 3. Get real Dhan API credentials from: https://dhanhq.co/

DHAN_SECRET_NAMES = {
    'dhan-client-id': 'Dhan Client ID from https://dhanhq.co/',
    'dhan-api-key': 'Dhan API Key from https://dhanhq.co/',
    'dhan-api-secret': 'Dhan API Secret from https://dhanhq.co/',
    'dhan-access-token': 'Dhan Access Token (auto-generated after OAuth)'
}

# Example: To add credentials to Secret Manager manually:
# gcloud secrets create dhan-client-id --replication-policy="automatic"
# echo -n "YOUR_REAL_CLIENT_ID" | gcloud secrets versions add dhan-client-id --data-file=-

def run_gcloud_command(command: str) -> bool:
    """Execute gcloud command and return success status"""
    try:
        logger.info(f"Executing: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Command succeeded: {command}")
            return True
        else:
            logger.error(f"❌ Command failed: {command}")
            logger.error(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exception running command '{command}': {e}")
        return False

def create_secret(secret_id: str, secret_value: str) -> bool:
    """Create a secret in Google Secret Manager"""
    
    # First, try to create the secret (ignore if it already exists)
    create_cmd = f'gcloud secrets create {secret_id} --replication-policy="automatic"'
    subprocess.run(create_cmd, shell=True, capture_output=True)
    
    # Add the secret version with the actual value
    add_version_cmd = f'echo -n "{secret_value}" | gcloud secrets versions add {secret_id} --data-file=-'
    
    if run_gcloud_command(add_version_cmd):
        logger.info(f"✅ Secret '{secret_id}' created/updated successfully")
        return True
    else:
        logger.error(f"❌ Failed to create/update secret '{secret_id}'")
        return False

def setup_all_secrets():
    """Setup all Dhan credentials in Google Secret Manager"""
    logger.info("🔐 Setting up Dhan credentials in Google Secret Manager...")
    
    logger.error("⚠️ This script has been disabled for security reasons.")
    logger.error("📋 Dhan credentials must be manually added to GCP Secret Manager:")
    logger.error("")
    for secret_name, description in DHAN_SECRET_NAMES.items():
        logger.error(f"  • {secret_name}: {description}")
    logger.error("")
    logger.error("� Visit: https://console.cloud.google.com/security/secret-manager")
    logger.error("🔗 Get credentials from: https://dhanhq.co/")
    return False

def verify_secrets():
    """Verify that all secrets are accessible"""
    logger.info("🔍 Verifying secret accessibility...")
    
    success_count = 0
    
    for secret_id in DHAN_SECRET_NAMES.keys():
        verify_cmd = f'gcloud secrets versions access latest --secret="{secret_id}" --limit=10'
        
        if run_gcloud_command(verify_cmd):
            logger.info(f"✅ Secret '{secret_id}' is accessible")
            success_count += 1
        else:
            logger.error(f"❌ Secret '{secret_id}' is not accessible")
    
    return success_count == len(DHAN_SECRET_NAMES)

def display_setup_instructions():
    """Display manual setup instructions"""
    logger.info("📋 Manual Google Cloud Secret Manager Setup Instructions:")
    logger.info("=" * 60)
    logger.info("Run these commands in Google Cloud Shell or with gcloud CLI:")
    logger.info("")
    
    for secret_id, description in DHAN_SECRET_NAMES.items():
        logger.info(f"# Create secret: {secret_id}")
        logger.info(f"# Description: {description}")
        logger.info(f'gcloud secrets create {secret_id} --replication-policy="automatic"')
        logger.info(f'echo -n "YOUR_REAL_{secret_id.upper().replace("-", "_")}" | gcloud secrets versions add {secret_id} --data-file=-')
        logger.info("")
    
    logger.info("🔗 Get real Dhan credentials from: https://dhanhq.co/")

def main():
    """Main setup function"""
    logger.info("🚀 InfinityAI.Pro - Secret Manager Setup Starting...")
    
    # Check if gcloud is available
    if run_gcloud_command("gcloud --version"):
        logger.info("✅ Google Cloud CLI is available")
        
        # Try to setup secrets automatically
        if setup_all_secrets():
            logger.info("🎉 Automatic setup completed successfully!")
            
            # Verify the secrets
            if verify_secrets():
                logger.info("✅ All secrets verified and accessible")
            else:
                logger.warning("⚠️ Some secrets may not be accessible")
        else:
            logger.warning("⚠️ Automatic setup had issues")
            
    else:
        logger.warning("❌ Google Cloud CLI not available")
        logger.info("🔧 Please run this in Google Cloud Shell or install gcloud CLI")
    
    # Always show manual instructions as backup
    logger.info("\n" + "="*60)
    display_setup_instructions()
    
    logger.info("🏁 Secret Manager Setup Complete!")
    logger.info("Next steps:")
    logger.info("1. Verify secrets are created in Google Cloud Console")
    logger.info("2. Deploy Engine C with the updated code")
    logger.info("3. Run production verification tests")

if __name__ == "__main__":
    main()