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
        """Decrypt sensitive data with raw fallback"""
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

        # Fallback to raw string if unencrypted
        return encrypted_data

    async def save_user_credentials(
        self,
        user_id: str,
        client_id: str,
        access_token: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save user's Dhan credentials securely in Firestore"""
        user_id = await self.resolve_user_id(user_id)
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
                # Sync status with main user document
                try:
                    self.db.collection("users").document(user_id).set({
                        "dhanConnected": True,
                        "dhanClientId": client_id,
                        "updatedAt": datetime.utcnow().isoformat()
                    }, merge=True)
                except Exception as ue:
                    logger.warning(f"Failed to sync users doc: {ue}")
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
        target_id = user_id or "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

        if self.db and target_id:
            try:
                doc_ref = self.db.collection("user_credentials").document(target_id)
                doc = doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    raw_token = data.get("dhan_access_token") or data.get("access_token")
                    raw_secret = data.get("api_secret")
                    dec_token = self._decrypt(raw_token) if raw_token else None
                    dec_secret = self._decrypt(raw_secret) if raw_secret else None
                    client_id = data.get("dhan_client_id") or data.get("client_id")
                    return {
                        "user_id": target_id,
                        "dhan_client_id": client_id,
                        "client_id": client_id,
                        "dhan_access_token": dec_token,
                        "access_token": dec_token,
                        "api_key": data.get("api_key"),
                        "api_secret": dec_secret,
                        "connection_status": data.get("connection_status", "connected" if client_id else "not_configured"),
                        "is_verified": data.get("is_verified", False),
                        "updated_at": data.get("updated_at")
                    }
            except Exception as e:
                logger.error(f"Error reading credentials from Firestore: {e}")

        # If document under target_id not found, resolve fallback user ID
        resolved_id = await self.resolve_user_id(user_id)
        if self.db and resolved_id and resolved_id != target_id:
            try:
                doc_ref = self.db.collection("user_credentials").document(resolved_id)
                doc = doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    raw_token = data.get("dhan_access_token") or data.get("access_token")
                    raw_secret = data.get("api_secret")
                    dec_token = self._decrypt(raw_token) if raw_token else None
                    dec_secret = self._decrypt(raw_secret) if raw_secret else None
                    client_id = data.get("dhan_client_id") or data.get("client_id")
                    return {
                        "user_id": resolved_id,
                        "dhan_client_id": client_id,
                        "client_id": client_id,
                        "dhan_access_token": dec_token,
                        "access_token": dec_token,
                        "api_key": data.get("api_key"),
                        "api_secret": dec_secret,
                        "connection_status": data.get("connection_status", "connected" if client_id else "not_configured"),
                        "is_verified": data.get("is_verified", False),
                        "updated_at": data.get("updated_at")
                    }
            except Exception as e:
                logger.error(f"Error reading fallback credentials from Firestore: {e}")

        # Fallback to env vars if testing
        env_client_id = os.getenv("DHAN_CLIENT_ID")
        env_token = os.getenv("DHAN_ACCESS_TOKEN")
        if env_client_id and env_token:
            return {
                "user_id": target_id,
                "dhan_client_id": env_client_id,
                "client_id": env_client_id,
                "dhan_access_token": env_token,
                "access_token": env_token,
                "connection_status": "connected",
                "is_verified": True,
                "updated_at": datetime.utcnow().isoformat()
            }
        return None

    async def find_credentials_by_client_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Find credentials by Dhan client ID"""
        if self.db:
            try:
                users_ref = self.db.collection("user_credentials")
                query = users_ref.where("dhan_client_id", "==", client_id).limit(1)
                docs = query.stream()
                for doc in docs:
                    return await self.get_user_credentials(doc.id)
            except Exception as e:
                logger.error(f"Error querying Firestore by client_id: {e}")
        return None

    async def resolve_user_id(self, user_id: str) -> str:
        """Resolve a generic ID, client ID, or unknown ID to the actual user_id holding valid credentials"""
        if not self.db:
            return user_id or "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

        # 1. Check if the provided user_id document exists directly
        if user_id and user_id not in ["guest", "default", "unknown", "null", "undefined"]:
            try:
                doc = self.db.collection("user_credentials").document(user_id).get()
                if doc.exists:
                    return user_id
            except Exception:
                pass

        # 2. Check if user_id is a 10-digit Dhan Client ID
        if user_id and user_id.isdigit():
            creds = await self.find_credentials_by_client_id(user_id)
            if creds and creds.get("user_id"):
                return creds.get("user_id")

        # 3. Check for default owner UID document
        try:
            doc = self.db.collection("user_credentials").document("znyNtT2lW3MKHqFrVA6E0A2Iv3N2").get()
            if doc.exists:
                return "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
        except Exception:
            pass

        # 4. Fallback to any active credentials document in single-user system
        try:
            docs = list(self.db.collection("user_credentials").limit(5).stream())
            for d in docs:
                if d.exists and d.id:
                    return d.id
        except Exception as e:
            logger.error(f"Error resolving fallback user_id in Firestore: {e}")

        return "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

    async def delete_user_credentials(self, user_id: str) -> bool:
        """Delete user's Dhan credentials from Firestore"""
        user_id = await self.resolve_user_id(user_id)
        if self.db:
            try:
                doc_ref = self.db.collection("user_credentials").document(user_id)
                doc_ref.delete()
                try:
                    self.db.collection("users").document(user_id).set({
                        "dhanConnected": False,
                        "updatedAt": datetime.utcnow().isoformat()
                    }, merge=True)
                except Exception:
                    pass
                logger.info(f"✅ Credentials deleted from Firestore for user: {user_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete credentials from Firestore: {e}")
                return False
        return True

    async def update_connection_status(
        self,
        user_id: str,
        connection_status: str,
        account_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update connection status (connected, failed, not_configured) and account data in Firestore"""
        user_id = await self.resolve_user_id(user_id)
        if self.db:
            try:
                doc_ref = self.db.collection("user_credentials").document(user_id)
                update_payload = {
                    "connection_status": connection_status,
                    "is_verified": connection_status == "connected",
                    "updated_at": datetime.utcnow().isoformat()
                }
                if account_data:
                    update_payload["account_summary"] = account_data
                doc_ref.set(update_payload, merge=True)

                # Sync with users doc
                try:
                    self.db.collection("users").document(user_id).set({
                        "dhanConnected": connection_status == "connected",
                        "updatedAt": datetime.utcnow().isoformat()
                    }, merge=True)
                except Exception:
                    pass

                logger.info(f"✅ User connection status updated to '{connection_status}' for user {user_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to update connection status in Firestore: {e}")
        return False

_credentials_manager: Optional[UserCredentialsManager] = None

def get_credentials_manager() -> UserCredentialsManager:
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = UserCredentialsManager()
    return _credentials_manager
