"""
Cryptography utilities for InfinityAI.Pro
Handles secure encryption/decryption of broker tokens and sensitive data
"""

import os
import base64
import secrets
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

logger = structlog.get_logger(__name__)

# Get encryption key from environment
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    # For development only - generate a key
    logger.warning("FERNET_KEY not set in environment, generating temporary key")
    FERNET_KEY = Fernet.generate_key().decode()

# Initialize Fernet cipher
try:
    fernet = Fernet(FERNET_KEY.encode())
except Exception as e:
    logger.error("Failed to initialize Fernet cipher", error=str(e))
    raise RuntimeError(f"Invalid FERNET_KEY: {e}")


class TokenEncryption:
    """Handle encryption and decryption of broker tokens"""
    
    @staticmethod
    def encrypt_token(plaintext: str) -> Tuple[bytes, Optional[bytes]]:
        """
        Encrypt a broker token with Fernet encryption
        Returns (encrypted_data, iv) tuple
        """
        try:
            if not plaintext:
                raise ValueError("Cannot encrypt empty string")
            
            # Fernet handles IV internally, so we don't need a separate IV
            encrypted = fernet.encrypt(plaintext.encode('utf-8'))
            logger.info("Token encrypted successfully", length=len(plaintext))
            return encrypted, None
            
        except Exception as e:
            logger.error("Token encryption failed", error=str(e))
            raise
    
    @staticmethod
    def decrypt_token(encrypted_data: bytes, iv: Optional[bytes] = None) -> str:
        """
        Decrypt a broker token
        """
        try:
            if not encrypted_data:
                raise ValueError("Cannot decrypt empty data")
            
            # Decrypt using Fernet
            decrypted = fernet.decrypt(encrypted_data)
            token = decrypted.decode('utf-8')
            logger.info("Token decrypted successfully")
            return token
            
        except Exception as e:
            logger.error("Token decryption failed", error=str(e))
            raise ValueError("Invalid or corrupted token data")
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt (handled by passlib)"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, hashed)


class SecureStorage:
    """Handle secure storage operations"""
    
    @staticmethod
    def encrypt_data(data: str, key: Optional[str] = None) -> bytes:
        """Encrypt arbitrary data"""
        cipher = fernet if not key else Fernet(key.encode())
        return cipher.encrypt(data.encode('utf-8'))
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: Optional[str] = None) -> str:
        """Decrypt arbitrary data"""
        cipher = fernet if not key else Fernet(key.encode())
        return cipher.decrypt(encrypted_data).decode('utf-8')
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key"""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> str:
        """Derive a key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()
    
    @staticmethod
    def generate_salt() -> bytes:
        """Generate a random salt"""
        return secrets.token_bytes(16)


class JWTSecurity:
    """Handle JWT token security"""
    
    @staticmethod
    def generate_jwt_secret() -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def create_token_hash(token: str) -> str:
        """Create a hash of JWT token for session storage"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()


def validate_encryption_setup() -> dict:
    """Validate the encryption setup"""
    try:
        # Test encryption/decryption
        test_data = "test_broker_token_12345"
        encrypted, iv = TokenEncryption.encrypt_token(test_data)
        decrypted = TokenEncryption.decrypt_token(encrypted, iv)
        
        if decrypted != test_data:
            return {
                "status": "error",
                "message": "Encryption test failed - data mismatch"
            }
        
        return {
            "status": "healthy",
            "message": "Encryption system operational",
            "key_length": len(FERNET_KEY)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Encryption validation failed: {e}"
        }


def get_crypto_health() -> dict:
    """Get cryptography system health"""
    return validate_encryption_setup()


# Utility functions for backward compatibility
def encrypt_bytes(plaintext: str) -> bytes:
    """Legacy function - encrypt string to bytes"""
    encrypted, _ = TokenEncryption.encrypt_token(plaintext)
    return encrypted


def decrypt_bytes(ciphertext: bytes) -> str:
    """Legacy function - decrypt bytes to string"""
    return TokenEncryption.decrypt_token(ciphertext)


# Initialize and validate on import
if __name__ == "__main__":
    # Test the encryption system
    result = validate_encryption_setup()
    print(f"Encryption test: {result}")
else:
    # Validate setup on import
    try:
        validation = validate_encryption_setup()
        if validation["status"] != "healthy":
            logger.error("Encryption system validation failed", result=validation)
    except Exception as e:
        logger.error("Failed to validate encryption system", error=str(e))