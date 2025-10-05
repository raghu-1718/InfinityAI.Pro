"""
Encryption and secure vault utility for Engine C
InfinityAI.Pro Trading Platform

Secure storage and encryption for sensitive data like API keys,
credentials, and configuration parameters.
"""

import os
import base64
import json
import hashlib
import secrets
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Configuration for secure vault"""
    vault_key_env: str = "INFINITYAI_VAULT_KEY"
    salt_env: str = "INFINITYAI_VAULT_SALT"
    iterations: int = 100000
    key_length: int = 32


class EncryptionError(Exception):
    """Exception raised for encryption/decryption errors"""
    pass


class SecureVault:
    """Secure vault for encrypting and storing sensitive data"""
    
    def __init__(self, config: VaultConfig = None):
        self.config = config or VaultConfig()
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with key derivation"""
        try:
            # Get vault key from environment
            vault_key = os.getenv(self.config.vault_key_env)
            if not vault_key:
                logger.warning(f"Vault key not found in {self.config.vault_key_env}, generating temporary key")
                vault_key = self._generate_key()
                os.environ[self.config.vault_key_env] = vault_key
            
            # Get salt from environment or generate
            salt_b64 = os.getenv(self.config.salt_env)
            if salt_b64:
                salt = base64.urlsafe_b64decode(salt_b64)
            else:
                salt = secrets.token_bytes(32)
                salt_b64 = base64.urlsafe_b64encode(salt).decode()
                os.environ[self.config.salt_env] = salt_b64
                logger.info(f"Generated new vault salt, set {self.config.salt_env} environment variable")
            
            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.config.key_length,
                salt=salt,
                iterations=self.config.iterations,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(vault_key.encode()))
            self._fernet = Fernet(key)
            
            logger.info("Secure vault initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize secure vault: {e}")
            raise EncryptionError(f"Failed to initialize encryption: {e}")
    
    def _generate_key(self) -> str:
        """Generate a secure random key"""
        return secrets.token_urlsafe(32)
    
    def encrypt(self, data: Union[str, Dict[str, Any]]) -> str:
        """
        Encrypt data
        
        Args:
            data: Data to encrypt (string or dict)
            
        Returns:
            Base64 encoded encrypted data
        """
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            
            encrypted = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Decryption failed: {e}")
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt data and parse as JSON
        
        Args:
            encrypted_data: Base64 encoded encrypted JSON data
            
        Returns:
            Decrypted dictionary
        """
        try:
            decrypted_str = self.decrypt(encrypted_data)
            return json.loads(decrypted_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse decrypted JSON: {e}")
            raise EncryptionError(f"Failed to parse decrypted JSON: {e}")
    
    def hash_data(self, data: str, salt: str = None) -> str:
        """
        Hash data with optional salt
        
        Args:
            data: Data to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Base64 encoded hash
        """
        try:
            if salt is None:
                salt = secrets.token_hex(16)
            
            salted_data = f"{data}{salt}"
            hash_obj = hashlib.sha256(salted_data.encode())
            return base64.urlsafe_b64encode(hash_obj.digest()).decode()
            
        except Exception as e:
            logger.error(f"Hashing failed: {e}")
            raise EncryptionError(f"Hashing failed: {e}")
    
    def verify_hash(self, data: str, hashed_data: str, salt: str) -> bool:
        """
        Verify hashed data
        
        Args:
            data: Original data
            hashed_data: Hash to verify against
            salt: Salt used for hashing
            
        Returns:
            True if hash matches
        """
        try:
            computed_hash = self.hash_data(data, salt)
            return secrets.compare_digest(hashed_data, computed_hash)
            
        except Exception as e:
            logger.error(f"Hash verification failed: {e}")
            return False


class SecretManager:
    """Manager for handling encrypted secrets"""
    
    def __init__(self, vault: SecureVault = None):
        self.vault = vault or SecureVault()
        self._secrets: Dict[str, str] = {}
    
    def store_secret(self, name: str, value: str) -> str:
        """
        Store encrypted secret
        
        Args:
            name: Secret name
            value: Secret value
            
        Returns:
            Encrypted secret data
        """
        try:
            encrypted = self.vault.encrypt(value)
            self._secrets[name] = encrypted
            logger.info(f"Secret '{name}' stored successfully")
            return encrypted
            
        except Exception as e:
            logger.error(f"Failed to store secret '{name}': {e}")
            raise
    
    def get_secret(self, name: str) -> Optional[str]:
        """
        Get decrypted secret
        
        Args:
            name: Secret name
            
        Returns:
            Decrypted secret value or None if not found
        """
        try:
            encrypted = self._secrets.get(name)
            if not encrypted:
                logger.warning(f"Secret '{name}' not found")
                return None
            
            decrypted = self.vault.decrypt(encrypted)
            return decrypted
            
        except Exception as e:
            logger.error(f"Failed to get secret '{name}': {e}")
            return None
    
    def store_json_secret(self, name: str, value: Dict[str, Any]) -> str:
        """
        Store encrypted JSON secret
        
        Args:
            name: Secret name
            value: Secret dictionary
            
        Returns:
            Encrypted secret data
        """
        try:
            encrypted = self.vault.encrypt(value)
            self._secrets[name] = encrypted
            logger.info(f"JSON secret '{name}' stored successfully")
            return encrypted
            
        except Exception as e:
            logger.error(f"Failed to store JSON secret '{name}': {e}")
            raise
    
    def get_json_secret(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get decrypted JSON secret
        
        Args:
            name: Secret name
            
        Returns:
            Decrypted secret dictionary or None if not found
        """
        try:
            encrypted = self._secrets.get(name)
            if not encrypted:
                logger.warning(f"JSON secret '{name}' not found")
                return None
            
            decrypted = self.vault.decrypt_json(encrypted)
            return decrypted
            
        except Exception as e:
            logger.error(f"Failed to get JSON secret '{name}': {e}")
            return None
    
    def remove_secret(self, name: str) -> bool:
        """
        Remove secret
        
        Args:
            name: Secret name
            
        Returns:
            True if removed, False if not found
        """
        if name in self._secrets:
            del self._secrets[name]
            logger.info(f"Secret '{name}' removed")
            return True
        
        logger.warning(f"Secret '{name}' not found for removal")
        return False
    
    def list_secrets(self) -> list:
        """List all secret names"""
        return list(self._secrets.keys())
    
    def export_secrets(self) -> Dict[str, str]:
        """
        Export all encrypted secrets
        
        Returns:
            Dictionary of encrypted secrets
        """
        return self._secrets.copy()
    
    def import_secrets(self, secrets: Dict[str, str]):
        """
        Import encrypted secrets
        
        Args:
            secrets: Dictionary of encrypted secrets
        """
        self._secrets.update(secrets)
        logger.info(f"Imported {len(secrets)} secrets")


class ConfigurationEncryption:
    """Utility for encrypting configuration values"""
    
    def __init__(self, vault: SecureVault = None):
        self.vault = vault or SecureVault()
    
    def encrypt_config(self, config: Dict[str, Any], 
                      sensitive_keys: set = None) -> Dict[str, Any]:
        """
        Encrypt sensitive configuration values
        
        Args:
            config: Configuration dictionary
            sensitive_keys: Set of keys to encrypt (defaults to common sensitive keys)
            
        Returns:
            Configuration with encrypted sensitive values
        """
        if sensitive_keys is None:
            sensitive_keys = {
                'password', 'secret', 'key', 'token', 'api_key',
                'access_token', 'client_secret', 'private_key',
                'database_url', 'redis_url'
            }
        
        encrypted_config = config.copy()
        
        for key, value in config.items():
            # Check if key should be encrypted
            key_lower = key.lower()
            should_encrypt = any(sensitive_key in key_lower for sensitive_key in sensitive_keys)
            
            if should_encrypt and isinstance(value, str) and value:
                try:
                    encrypted_config[key] = {
                        '_encrypted': True,
                        '_value': self.vault.encrypt(value)
                    }
                    logger.debug(f"Encrypted configuration key: {key}")
                    
                except Exception as e:
                    logger.warning(f"Failed to encrypt config key '{key}': {e}")
        
        return encrypted_config
    
    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt configuration values
        
        Args:
            config: Configuration with encrypted values
            
        Returns:
            Configuration with decrypted values
        """
        decrypted_config = {}
        
        for key, value in config.items():
            if (isinstance(value, dict) and 
                value.get('_encrypted') is True and 
                '_value' in value):
                
                try:
                    decrypted_config[key] = self.vault.decrypt(value['_value'])
                    logger.debug(f"Decrypted configuration key: {key}")
                    
                except Exception as e:
                    logger.error(f"Failed to decrypt config key '{key}': {e}")
                    decrypted_config[key] = None
            else:
                decrypted_config[key] = value
        
        return decrypted_config


# Global instances
_global_vault = None
_global_secret_manager = None
_global_config_encryption = None


def get_vault() -> SecureVault:
    """Get global vault instance"""
    global _global_vault
    if _global_vault is None:
        _global_vault = SecureVault()
    return _global_vault


def get_secret_manager() -> SecretManager:
    """Get global secret manager instance"""
    global _global_secret_manager
    if _global_secret_manager is None:
        _global_secret_manager = SecretManager(get_vault())
    return _global_secret_manager


def get_config_encryption() -> ConfigurationEncryption:
    """Get global configuration encryption instance"""
    global _global_config_encryption
    if _global_config_encryption is None:
        _global_config_encryption = ConfigurationEncryption(get_vault())
    return _global_config_encryption


# Convenience functions
def encrypt_string(data: str) -> str:
    """Encrypt a string using global vault"""
    return get_vault().encrypt(data)


def decrypt_string(encrypted_data: str) -> str:
    """Decrypt a string using global vault"""
    return get_vault().decrypt(encrypted_data)


def store_secret(name: str, value: str) -> str:
    """Store a secret using global secret manager"""
    return get_secret_manager().store_secret(name, value)


def get_secret(name: str) -> Optional[str]:
    """Get a secret using global secret manager"""
    return get_secret_manager().get_secret(name)


def setup_vault_from_env():
    """Setup vault with environment variables if they exist"""
    try:
        vault = get_vault()
        
        # Common secrets to load from environment
        secret_mappings = {
            'DHAN_ACCESS_TOKEN': 'dhan_access_token',
            'DHAN_CLIENT_ID': 'dhan_client_id',
            'DATABASE_URL': 'database_url',
            'REDIS_URL': 'redis_url',
            'SECRET_KEY': 'secret_key'
        }
        
        secret_manager = get_secret_manager()
        
        for env_var, secret_name in secret_mappings.items():
            value = os.getenv(env_var)
            if value:
                secret_manager.store_secret(secret_name, value)
                logger.debug(f"Loaded secret '{secret_name}' from environment")
        
        logger.info("Vault setup from environment completed")
        
    except Exception as e:
        logger.error(f"Failed to setup vault from environment: {e}")


# Export commonly used classes and functions
__all__ = [
    "SecureVault",
    "SecretManager", 
    "ConfigurationEncryption",
    "VaultConfig",
    "EncryptionError",
    "get_vault",
    "get_secret_manager",
    "get_config_encryption",
    "encrypt_string",
    "decrypt_string",
    "store_secret",
    "get_secret",
    "setup_vault_from_env"
]