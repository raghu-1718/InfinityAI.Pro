"""
User Credentials Management for InfinityAI.Pro
Handles secure storage and retrieval of user Dhan credentials in Firestore
"""
import os
import json
import base64
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.fernet import Fernet
from google.cloud import firestore
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

# Get encryption key from Secret Manager or environment
def get_encryption_key() -> bytes:
    """Get or generate encryption key for user credentials"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0779271931")
    try:
        # Try to get from Secret Manager first
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/user-credentials-key/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data
    except Exception as e:
        logger.warning(f"Could not get encryption key from Secret Manager: {e}")
        # Fallback to environment variable or generate one
        key = os.getenv("USER_CREDENTIALS_KEY")
        if key:
            return base64.urlsafe_b64decode(key)
        # Generate a consistent key based on project ID (for development only)
        return base64.urlsafe_b64encode(hashlib.sha256(project_id.encode()).digest())


class UserCredentialsManager:
    """Manages encrypted user credentials in Firestore"""

    def __init__(self):
        self.db = firestore.Client()
        self.collection = "user_credentials"
        self.encryption_key = get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        logger.info("✅ UserCredentialsManager initialized")

    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt credentials")

    async def save_user_credentials(
        self,
        user_id: str,
        client_id: str,
        access_token: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save user's Dhan credentials securely in Firestore

        Args:
            user_id: Unique user identifier (Firebase UID or email)
            client_id: Dhan Client ID
            access_token: Dhan Access Token
            api_key: Optional Dhan API Key (not typically needed for users)
            api_secret: Optional Dhan API Secret (not typically needed for users)
        """
        try:
            # Encrypt sensitive credentials
            encrypted_credentials = {
                "client_id": client_id,  # Client ID is not secret
                "access_token": self._encrypt(access_token),
                "api_key": self._encrypt(api_key) if api_key else None,
                "api_secret": self._encrypt(api_secret) if api_secret else None,
            }

            # Create document
            doc_data = {
                "user_id": user_id,
                "credentials": encrypted_credentials,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "connection_status": "pending_verification"
            }

            # Save to Firestore
            doc_ref = self.db.collection(self.collection).document(user_id)
            doc_ref.set(doc_data, merge=True)

            logger.info(f"✅ Saved credentials for user {user_id}")
            return {
                "status": "success",
                "message": "Credentials saved successfully",
                "user_id": user_id,
                "client_id": client_id
            }

        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            raise ValueError(f"Failed to save credentials: {str(e)}")

    async def get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt user's Dhan credentials

        Returns decrypted credentials or None if not found
        """
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()
            encrypted_creds = data.get("credentials", {})

            # Decrypt credentials
            decrypted = {
                "client_id": encrypted_creds.get("client_id"),
                "access_token": self._decrypt(encrypted_creds["access_token"]) if encrypted_creds.get("access_token") else None,
                "api_key": self._decrypt(encrypted_creds["api_key"]) if encrypted_creds.get("api_key") else None,
                "api_secret": self._decrypt(encrypted_creds["api_secret"]) if encrypted_creds.get("api_secret") else None,
            }

            return {
                "user_id": user_id,
                "credentials": decrypted,
                "is_active": data.get("is_active", False),
                "connection_status": data.get("connection_status", "unknown"),
                "updated_at": data.get("updated_at")
            }

        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
            return None

    async def update_connection_status(
        self,
        user_id: str,
        status: str,
        account_info: Optional[Dict] = None
    ):
        """Update the connection status after verification"""
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            update_data = {
                "connection_status": status,
                "updated_at": datetime.utcnow()
            }
            if account_info:
                update_data["account_info"] = account_info

            doc_ref.update(update_data)
            logger.info(f"✅ Updated connection status for {user_id}: {status}")

        except Exception as e:
            logger.error(f"Error updating status: {e}")

    async def delete_user_credentials(self, user_id: str) -> bool:
        """Delete user's credentials"""
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            doc_ref.delete()
            logger.info(f"✅ Deleted credentials for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting credentials: {e}")
            return False

    async def list_connected_users(self) -> list:
        """List all users with connected accounts (admin only)"""
        try:
            docs = self.db.collection(self.collection).where(
                "is_active", "==", True
            ).stream()

            users = []
            for doc in docs:
                data = doc.to_dict()
                users.append({
                    "user_id": data.get("user_id"),
                    "client_id": data.get("credentials", {}).get("client_id"),
                    "connection_status": data.get("connection_status"),
                    "updated_at": data.get("updated_at")
                })

            return users

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []


# Singleton instance
_credentials_manager: Optional[UserCredentialsManager] = None

def get_credentials_manager() -> UserCredentialsManager:
    """Get singleton instance of UserCredentialsManager"""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = UserCredentialsManager()
    return _credentials_manager
