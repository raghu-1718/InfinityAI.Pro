"""
Azure Key Vault integration for InfinityAI.Pro
Provides secure secret management and automatic key rotation
"""

import os
import logging
from typing import Dict, Optional, Any, List
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.exceptions import ResourceNotFoundError
import json
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

class AzureKeyVaultManager:
    def __init__(self):
        self.vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        
        self.client = None
        self.credential = None
        
        if self.vault_url:
            self._initialize_client()
        else:
            logger.warning("🔑 Azure Key Vault URL not provided, secret management disabled")
    
    def _initialize_client(self):
        """Initialize Azure Key Vault client with appropriate credentials"""
        try:
            # Try different credential methods
            if self.client_id and self.client_secret and self.tenant_id:
                # Use service principal authentication
                self.credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                logger.info("🔑 Using service principal authentication for Key Vault")
            else:
                # Use default Azure credential (Managed Identity, Azure CLI, etc.)
                self.credential = DefaultAzureCredential()
                logger.info("🔑 Using default Azure credentials for Key Vault")
            
            self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
            
            # Test the connection
            try:
                # Try to list secrets to verify access
                secrets = list(self.client.list_properties_of_secrets())
                logger.info(f"✅ Azure Key Vault connected successfully - {len(secrets)} secrets found")
                return True
            except Exception as e:
                logger.error(f"❌ Key Vault access test failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Key Vault client: {e}")
            self.client = None
            return False
    
    def is_available(self) -> bool:
        """Check if Key Vault is available and accessible"""
        return self.client is not None
    
    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Key Vault with caching"""
        if not self.is_available():
            logger.debug(f"Key Vault unavailable, checking environment for {secret_name}")
            return os.getenv(secret_name)
        
        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"✅ Retrieved secret {secret_name} from Key Vault")
            return secret.value
        except ResourceNotFoundError:
            logger.warning(f"🔍 Secret {secret_name} not found in Key Vault, checking environment")
            return os.getenv(secret_name)
        except Exception as e:
            logger.error(f"❌ Error retrieving secret {secret_name}: {e}")
            return os.getenv(secret_name)
    
    def set_secret(self, secret_name: str, secret_value: str, tags: Optional[Dict[str, str]] = None) -> bool:
        """Store secret in Key Vault"""
        if not self.is_available():
            logger.warning(f"Key Vault unavailable, cannot store secret {secret_name}")
            return False
        
        try:
            # Add default tags
            if tags is None:
                tags = {}
            
            tags.update({
                "created_by": "infinityai_pro",
                "created_at": datetime.utcnow().isoformat(),
                "environment": os.getenv("ENVIRONMENT", "development")
            })
            
            self.client.set_secret(secret_name, secret_value, tags=tags)
            logger.info(f"✅ Secret {secret_name} stored in Key Vault")
            
            # Clear cache for this secret
            self.get_secret.cache_clear()
            
            return True
        except Exception as e:
            logger.error(f"❌ Error storing secret {secret_name}: {e}")
            return False
    
    def delete_secret(self, secret_name: str) -> bool:
        """Delete secret from Key Vault"""
        if not self.is_available():
            logger.warning(f"Key Vault unavailable, cannot delete secret {secret_name}")
            return False
        
        try:
            self.client.begin_delete_secret(secret_name).wait()
            logger.info(f"✅ Secret {secret_name} deleted from Key Vault")
            
            # Clear cache for this secret
            self.get_secret.cache_clear()
            
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting secret {secret_name}: {e}")
            return False
    
    def list_secrets(self) -> List[Dict[str, Any]]:
        """List all secrets in Key Vault"""
        if not self.is_available():
            return []
        
        try:
            secrets = []
            for secret_properties in self.client.list_properties_of_secrets():
                secrets.append({
                    "name": secret_properties.name,
                    "enabled": secret_properties.enabled,
                    "created_on": secret_properties.created_on.isoformat() if secret_properties.created_on else None,
                    "updated_on": secret_properties.updated_on.isoformat() if secret_properties.updated_on else None,
                    "expires_on": secret_properties.expires_on.isoformat() if secret_properties.expires_on else None,
                    "tags": secret_properties.tags or {}
                })
            
            logger.debug(f"📋 Listed {len(secrets)} secrets from Key Vault")
            return secrets
        except Exception as e:
            logger.error(f"❌ Error listing secrets: {e}")
            return []
    
    def sync_environment_to_keyvault(self, secrets_map: Dict[str, str]) -> Dict[str, bool]:
        """Sync environment variables to Key Vault"""
        results = {}
        
        if not self.is_available():
            logger.warning("Key Vault unavailable, skipping sync")
            return results
        
        for env_var, secret_name in secrets_map.items():
            env_value = os.getenv(env_var)
            if env_value and env_value not in ["your_api_key_here", "your_secret_here", ""]:
                results[secret_name] = self.set_secret(
                    secret_name, 
                    env_value,
                    tags={"source": "environment_sync", "env_var": env_var}
                )
                logger.info(f"🔄 Synced {env_var} -> {secret_name}: {'✅' if results[secret_name] else '❌'}")
            else:
                logger.debug(f"⏭️ Skipping {env_var} (empty or placeholder value)")
                results[secret_name] = False
        
        return results
    
    def get_secrets_bulk(self, secret_names: List[str]) -> Dict[str, Optional[str]]:
        """Get multiple secrets efficiently"""
        results = {}
        for secret_name in secret_names:
            results[secret_name] = self.get_secret(secret_name)
        return results
    
    def create_api_key_mapping(self) -> Dict[str, str]:
        """Create mapping between environment variables and Key Vault secret names"""
        return {
            # AI Service API Keys
            "OPENAI_API_KEY": "openai-api-key",
            "ANTHROPIC_API_KEY": "anthropic-api-key",
            "PERPLEXITY_API_KEY": "perplexity-api-key",
            "HUGGINGFACE_API_KEY": "huggingface-api-key",
            
            # Azure AI Keys
            "AZURE_OPENAI_KEY": "azure-openai-key",
            "AZURE_SPEECH_KEY": "azure-speech-key",
            "AZURE_VISION_KEY": "azure-vision-key",
            "AZURE_TEXT_ANALYTICS_KEY": "azure-text-analytics-key",
            
            # Vector Database
            "PINECONE_API_KEY": "pinecone-api-key",
            
            # Financial Data APIs
            "ALPHA_VANTAGE_API_KEY": "alpha-vantage-api-key",
            "POLYGON_API_KEY": "polygon-api-key",
            "TWELVE_DATA_API_KEY": "twelve-data-api-key",
            
            # Trading APIs
            "COINSWITCH_API_KEY": "coinswitch-api-key",
            "COINSWITCH_API_SECRET": "coinswitch-api-secret",
            "ZERODHA_API_KEY": "zerodha-api-key",
            "ZERODHA_API_SECRET": "zerodha-api-secret",
            
            # External Integrations
            "TELEGRAM_BOT_TOKEN": "telegram-bot-token",
            "DISCORD_WEBHOOK_URL": "discord-webhook-url",
            "SLACK_BOT_TOKEN": "slack-bot-token",
            
            # Monitoring
            "SENTRY_DSN": "sentry-dsn",
            "DATADOG_API_KEY": "datadog-api-key",
            "LOGROCKET_APP_ID": "logrocket-app-id",
            
            # Security
            "JWT_SECRET_KEY": "jwt-secret-key",
            "API_KEY_ENCRYPTION_KEY": "api-key-encryption-key",
            "REDIS_PASSWORD": "redis-password"
        }

# Global Key Vault instance
vault_manager = AzureKeyVaultManager()

class SecureConfig:
    """Secure configuration management using Key Vault or environment fallback"""
    
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value from Key Vault or environment"""
        # Convert environment variable name to Key Vault secret name
        secret_name = key.lower().replace("_", "-")
        
        value = vault_manager.get_secret(secret_name)
        if value is None:
            value = vault_manager.get_secret(key)  # Try original key name
        if value is None:
            value = os.getenv(key, default)
        
        return value
    
    @staticmethod
    def get_required(key: str) -> str:
        """Get required configuration value, raise exception if not found"""
        value = SecureConfig.get(key)
        if value is None:
            raise ValueError(f"Required configuration {key} not found")
        return value
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = SecureConfig.get(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = SecureConfig.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}")
            return default
    
    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        value = SecureConfig.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Invalid float value for {key}: {value}")
            return default

# Configuration instance
config = SecureConfig()

async def initialize_key_vault():
    """Initialize Key Vault and sync secrets"""
    if vault_manager.is_available():
        logger.info("🔑 Initializing Azure Key Vault secret sync...")
        
        # Get the API key mapping
        secrets_map = vault_manager.create_api_key_mapping()
        
        # Sync environment variables to Key Vault
        results = vault_manager.sync_environment_to_keyvault(secrets_map)
        
        # Log results
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"🔄 Key Vault sync completed: {successful}/{total} secrets synced")
        
        return {"synced": successful, "total": total, "results": results}
    else:
        logger.warning("🔑 Key Vault not available, using environment variables only")
        return {"synced": 0, "total": 0, "results": {}}

async def health_check():
    """Health check for Key Vault service"""
    if vault_manager.is_available():
        try:
            secrets = vault_manager.list_secrets()
            return {
                "service": "azure_keyvault",
                "status": "healthy",
                "secrets_count": len(secrets),
                "vault_url": vault_manager.vault_url
            }
        except Exception as e:
            return {
                "service": "azure_keyvault",
                "status": "unhealthy",
                "error": str(e)
            }
    else:
        return {
            "service": "azure_keyvault",
            "status": "disabled",
            "message": "Key Vault not configured"
        }