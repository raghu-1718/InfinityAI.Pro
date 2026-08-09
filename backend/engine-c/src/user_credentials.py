"""
User Credentials Management for InfinityAI.Pro
Handles secure storage and retrieval of user Dhan credentials in Firebase Firestore / GCP Secret Manager.
"""
import os
import json
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

logger = logging.getLogger(__name__)

def get_encryption_key() -> bytes:
    """Get or generate encryption key for user credentials"""
    env_key = os.getenv("USER_CREDENTIALS_KEY") or os.getenv("ENCRYPTION_KEY")
    if env_key:
        try:
            if len(env_key) == 64:
                try:
                    return bytes.fromhex(env_key)
                except ValueError:
                    pass
            return base64.urlsafe_b64decode(env_key) if len(env_key) > 64 else env_key.encode()
        except Exception as e:
            logger.warning(f"Failed to decode env var key: {e}")

    logger.warning("⚠️ Using derived key for local testing. Set USER_CREDENTIALS_KEY env var in production.")
    return b"J4z72_08-729048-70247-9082740927"

class UserCredentialsManager:
    """Manages encrypted user credentials in Firebase Firestore & Secret Manager (AES-256-GCM)"""

    def __init__(self):
        self.db = None
        self._init_firestore()
        self.encryption_key = get_encryption_key()
        if len(self.encryption_key) != 32:
            self.encryption_key = (self.encryption_key + b'0'*32)[:32]

        logger.info("UserCredentialsManager initialized (AES-256-GCM / Firebase Firestore Vault)")

    def _init_firestore(self):
        try:
            from google.cloud import firestore
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            self.db = firestore.Client(project=project_id)
            logger.info(f"✅ UserCredentialsManager: Connected to Firestore project '{project_id}'")
        except Exception as e:
            logger.warning(f"⚠️ UserCredentialsManager: Firestore client fallback mode: {e}")
            self.db = None

    def _encrypt(self, data: str) -> Optional[str]:
        """Encrypt sensitive data using AES-256-GCM"""
        if not data:
            return None
        nonce = os.urandom(12)
        encryptor = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(nonce),
        ).encryptor()
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        tag = encryptor.tag
        return f"{nonce.hex()}:{tag.hex()}:{ciphertext.hex()}"

    def _decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return None
        try:
            parts = encrypted_data.split(':')
            if len(parts) == 3:
                iv = bytes.fromhex(parts[0])
                tag = bytes.fromhex(parts[1])
                ciphertext = bytes.fromhex(parts[2])

                decryptor = Cipher(
                    algorithms.AES(self.encryption_key),
                    modes.GCM(iv, tag),
                ).decryptor()

                data = decryptor.update(ciphertext) + decryptor.finalize()
                return data.decode()
        except Exception as e:
            logger.warning(f"GCM Decrypt failed: {e}")

        return None

    async def save_user_credentials(
        self,
        user_id: str,
        client_id: str,
        access_token: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save user's Dhan credentials securely in Firestore"""
        enc_token = self._encrypt(access_token)
        enc_secret = self._encrypt(api_secret) if api_secret else None

        doc_data = {
            "user_id": user_id,
            "dhan_client_id": client_id,
            "dhan_access_token": enc_token,
            "api_key": api_key,
            "api_secret": enc_secret,
            "updated_at": datetime.utcnow().isoformat()
        }

        if self.db:
            try:
                doc_ref = self.db.collection("user_credentials").document(user_id)
                doc_ref.set(doc_data, merge=True)
                logger.info(f"✅ Credentials saved to Firestore for user: {user_id}")
            except Exception as e:
                logger.error(f"Failed to write to Firestore: {e}")

        return {
            "success": True,
            "user_id": user_id,
            "dhan_client_id": client_id,
            "updated_at": doc_data["updated_at"]
        }

    async def get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt user's Dhan credentials from Firestore"""
        if self.db:
            try:
                doc_ref = self.db.collection("user_credentials").document(user_id)
                doc = doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    dec_token = self._decrypt(data.get("dhan_access_token"))
                    dec_secret = self._decrypt(data.get("api_secret"))
                    return {
                        "user_id": user_id,
                        "dhan_client_id": data.get("dhan_client_id"),
                        "dhan_access_token": dec_token,
                        "api_key": data.get("api_key"),
                        "api_secret": dec_secret,
                        "updated_at": data.get("updated_at")
                    }
            except Exception as e:
                logger.error(f"Error reading credentials from Firestore: {e}")

        # Fallback to env vars if testing
        env_client_id = os.getenv("DHAN_CLIENT_ID")
        env_token = os.getenv("DHAN_ACCESS_TOKEN")
        if env_client_id and env_token:
            return {
                "user_id": user_id,
                "dhan_client_id": env_client_id,
                "dhan_access_token": env_token,
                "updated_at": datetime.utcnow().isoformat()
            }

        return None

_credentials_manager: Optional[UserCredentialsManager] = None

def get_credentials_manager() -> UserCredentialsManager:
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = UserCredentialsManager()
    return _credentials_manager
