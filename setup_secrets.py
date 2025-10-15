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

# Dhan credentials provided by user
DHAN_CREDENTIALS = {
    'dhan-client-id': '1101302170',
    'dhan-api-key': 'fe1942e7',
    'dhan-api-secret': '50bc0462-b1aa-489c-9029-fe0cdc68dc27',
    'dhan-access-token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NjA2MDM3NTEsImlhdCI6MTc2MDUxNzM1MSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtNTczODY2MzYzNjM5LTU3Mzg2NjM2MzYzOS51cy1jZW50cmFsMS5ydW4uYXBwL2FwaS9kaGFuL3Bvc3RiYWNrIiwiZGhhbkNsaWVudElkIjoiMTEwMTMwMjE3MCJ9.cRhYjn044i_CrOwTV5ZxQOPnR_iWNnWcGHWF_q41wSdh02-wLQBFOLeD8TQPaIKdZBXqxQvwKDm6Y0DEfs0JZA'
}

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
    
    success_count = 0
    total_secrets = len(DHAN_CREDENTIALS)
    
    for secret_id, secret_value in DHAN_CREDENTIALS.items():
        if create_secret(secret_id, secret_value):
            success_count += 1
        else:
            logger.error(f"❌ Failed to setup secret: {secret_id}")
    
    logger.info(f"📊 Setup complete: {success_count}/{total_secrets} secrets configured")
    
    if success_count == total_secrets:
        logger.info("🎉 All secrets configured successfully!")
        return True
    else:
        logger.warning("⚠️ Some secrets failed to configure")
        return False

def verify_secrets():
    """Verify that all secrets are accessible"""
    logger.info("🔍 Verifying secret accessibility...")
    
    success_count = 0
    
    for secret_id in DHAN_CREDENTIALS.keys():
        verify_cmd = f'gcloud secrets versions access latest --secret="{secret_id}" --limit=10'
        
        if run_gcloud_command(verify_cmd):
            logger.info(f"✅ Secret '{secret_id}' is accessible")
            success_count += 1
        else:
            logger.error(f"❌ Secret '{secret_id}' is not accessible")
    
    return success_count == len(DHAN_CREDENTIALS)

def display_setup_instructions():
    """Display manual setup instructions"""
    logger.info("📋 Manual Google Cloud Secret Manager Setup Instructions:")
    logger.info("=" * 60)
    logger.info("Run these commands in Google Cloud Shell or with gcloud CLI:")
    logger.info("")
    
    for secret_id, secret_value in DHAN_CREDENTIALS.items():
        logger.info(f"# Create secret: {secret_id}")
        logger.info(f'gcloud secrets create {secret_id} --replication-policy="automatic"')
        logger.info(f'echo -n "{secret_value}" | gcloud secrets versions add {secret_id} --data-file=-')
        logger.info("")

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