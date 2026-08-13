"""
DhanHQ Client Wrapper with Sandbox Support

This module provides a wrapper around the dhanhq library that supports
both sandbox and production environments.
"""
import os
import logging
from typing import Optional
from dhanhq import dhanhq

logger = logging.getLogger(__name__)


class DhanEnvironment:
    """Environment configuration for DhanHQ"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"
    
    # Base URLs
    SANDBOX_URL = "https://sandbox.dhan.co/v2"
    PRODUCTION_URL = "https://api.dhan.co/v2"


class DhanClient:
    """
    Enhanced DhanHQ client with sandbox support.
    
    This wrapper automatically configures the dhanhq library to use
    sandbox or production endpoints based on the environment setting.
    """
    
    def __init__(self, client_id: str, access_token: str, environment: str = None):
        """
        Initialize DhanHQ client with environment support.
        
        Args:
            client_id: Dhan client ID
            access_token: Dhan access token (JWT)
            environment: 'sandbox' or 'production'. If None, reads from DHAN_ENVIRONMENT env var
        """
        self.client_id = client_id
        self.access_token = access_token
        
        # Determine environment
        if environment is None:
            environment = os.getenv("DHAN_ENVIRONMENT", DhanEnvironment.PRODUCTION)
        
        self.environment = environment.lower()
        self.is_sandbox = (self.environment == DhanEnvironment.SANDBOX)
        
        # Log environment selection
        env_label = "SANDBOX" if self.is_sandbox else "PRODUCTION"
        logger.info(f"🔧 Initializing DhanHQ client in {env_label} mode")
        
        # Initialize the underlying dhanhq client
        self._client = dhanhq(client_id, access_token)
        
        # Override the base URL if in sandbox mode
        if self.is_sandbox:
            self._configure_sandbox()
    
    def _configure_sandbox(self):
        """Configure the client for sandbox environment."""
        # The dhanhq library typically uses a base_url attribute
        # We need to override it to point to the sandbox URL
        if hasattr(self._client, 'base_url'):
            original_url = getattr(self._client, 'base_url', 'unknown')
            self._client.base_url = DhanEnvironment.SANDBOX_URL
            logger.info(f"✅ Configured sandbox mode: {original_url} → {DhanEnvironment.SANDBOX_URL}")
        elif hasattr(self._client, '_base_url'):
            original_url = getattr(self._client, '_base_url', 'unknown')
            self._client._base_url = DhanEnvironment.SANDBOX_URL
            logger.info(f"✅ Configured sandbox mode: {original_url} → {DhanEnvironment.SANDBOX_URL}")
        else:
            logger.warning("⚠️ Could not override base URL - dhanhq library may not support it")
            logger.warning("⚠️ Please ensure you're using sandbox credentials for sandbox environment")
    
    def __getattr__(self, name):
        """Proxy all method calls to the underlying dhanhq client."""
        return getattr(self._client, name)
    
    def get_environment(self) -> str:
        """Get the current environment (sandbox or production)."""
        return self.environment
    
    def is_sandbox_mode(self) -> bool:
        """Check if client is in sandbox mode."""
        return self.is_sandbox


def create_dhan_client(
    client_id: str,
    access_token: str,
    environment: Optional[str] = None,
    force_production: bool = False
) -> DhanClient:
    """
    Factory function to create a DhanHQ client with environment support.
    
    Args:
        client_id: Dhan client ID
        access_token: Dhan access token
        environment: 'sandbox' or 'production' (optional)
        force_production: If True, always use production regardless of environment settings
    
    Returns:
        DhanClient instance configured for the specified environment
    """
    if force_production:
        environment = DhanEnvironment.PRODUCTION
        logger.warning("⚠️ Force production mode enabled - ignoring environment settings")
    
    return DhanClient(client_id, access_token, environment)
