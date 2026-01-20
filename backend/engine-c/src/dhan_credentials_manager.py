"""
DhanHQ Credentials Manager - DEPRECATED

⚠️ THIS FILE IS NO LONGER USED ⚠️

The system has been simplified to use per-user Firestore credentials only.
All user DhanHQ credentials are managed via UserCredentialsManager in user_credentials.py.

This file is kept for reference but is not imported or used in production.
If you need platform-wide credentials, use environment variables in config.py.

Migration Date: January 20, 2026
Architecture: Multi-tenant per-user credentials in Firestore
"""

import os
import logging
from typing import Optional, Dict
from functools import lru_cache
import asyncio

try:
    from google.cloud import secretmanager
    HAS_SECRET_MANAGER = True
except ImportError:
    HAS_SECRET_MANAGER = False

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "galvanic-pulsar-482815-h0"))


class DhanCredentialsManager:
    """DEPRECATED - Use UserCredentialsManager from user_credentials.py instead"""
    """
    Manages DhanHQ credentials securely from Google Secret Manager
    Falls back to environment variables if Secret Manager is unavailable
    """

    def __init__(self):
        self.project_id = PROJECT_ID
        self.use_secret_manager = HAS_SECRET_MANAGER and self._has_secret_manager_access()
        self._credentials_cache = {}

        if self.use_secret_manager:
            logger.info("✅ Using Google Secret Manager for credentials")
        else:
            logger.warning("⚠️  Secret Manager not available, using environment variables")

    def _has_secret_manager_access(self) -> bool:
        """Check if Secret Manager is accessible"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            # Try to list secrets in project
            client.list_secrets(request={"parent": f"projects/{self.project_id}"})
            return True
        except Exception as e:
            logger.warning(f"Secret Manager access failed: {e}")
            return False

    def _get_secret_value(self, secret_name: str) -> Optional[str]:
        """Retrieve secret value from Secret Manager"""
        if not HAS_SECRET_MANAGER:
            return None

        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8").strip()
        except Exception as e:
            logger.warning(f"Failed to retrieve secret '{secret_name}': {e}")
            return None

    @lru_cache(maxsize=1)
    def get_api_key(self) -> str:
        """Get DhanHQ API Key"""
        if self.use_secret_manager:
            value = self._get_secret_value("dhan-api-key")
            if value:
                return value

        # Fallback to environment variable
        value = os.getenv("DHAN_API_KEY")
        if value:
            return value

        raise ValueError("❌ DHAN_API_KEY not found in Secret Manager or environment")

    @lru_cache(maxsize=1)
    def get_api_secret(self) -> str:
        """Get DhanHQ API Secret"""
        if self.use_secret_manager:
            value = self._get_secret_value("dhan-api-secret")
            if value:
                return value

        # Fallback to environment variable
        value = os.getenv("DHAN_API_SECRET")
        if value:
            return value

        raise ValueError("❌ DHAN_API_SECRET not found in Secret Manager or environment")

    @lru_cache(maxsize=1)
    def get_client_id(self) -> str:
        """Get DhanHQ Client ID"""
        if self.use_secret_manager:
            value = self._get_secret_value("dhan-client-id")
            if value:
                return value

        # Fallback to environment variable
        value = os.getenv("DHAN_CLIENT_ID")
        if value:
            return value

        raise ValueError("❌ DHAN_CLIENT_ID not found in Secret Manager or environment")

    @lru_cache(maxsize=1)
    def get_access_token(self) -> str:
        """Get DhanHQ Access Token"""
        if self.use_secret_manager:
            value = self._get_secret_value("dhan-access-token")
            if value:
                return value

        # Fallback to environment variable
        value = os.getenv("DHAN_ACCESS_TOKEN")
        if value:
            return value

        raise ValueError("❌ DHAN_ACCESS_TOKEN not found in Secret Manager or environment")

    def get_all_credentials(self) -> Dict[str, str]:
        """Get all DhanHQ credentials as a dictionary"""
        return {
            "api_key": self.get_api_key(),
            "api_secret": self.get_api_secret(),
            "client_id": self.get_client_id(),
            "access_token": self.get_access_token()
        }

    def verify_credentials(self) -> bool:
        """Verify all required credentials are available"""
        try:
            credentials = self.get_all_credentials()
            logger.info("✅ All DhanHQ credentials verified and accessible")
            return True
        except ValueError as e:
            logger.error(f"❌ Credential verification failed: {e}")
            return False


# Global credentials manager instance
_credentials_manager: Optional[DhanCredentialsManager] = None


def get_credentials_manager() -> DhanCredentialsManager:
    """Get or create the global credentials manager"""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = DhanCredentialsManager()
    return _credentials_manager


async def verify_dhan_credentials_async() -> bool:
    """Async verification of DhanHQ credentials (for startup checks)"""
    manager = get_credentials_manager()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, manager.verify_credentials)
