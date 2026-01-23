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
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# from cryptography.hazmat.primitives.ciphers.aead import AESGCM  <-- Removed
from google.cloud import firestore
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

# ... (get_encryption_key remains same) ...
# Get encryption key from Secret Manager or environment
def get_encryption_key() -> bytes:
    """Get or generate encryption key for user credentials"""
    # 1. Prioritize secure environment variable
    env_key = os.getenv("USER_CREDENTIALS_KEY") or os.getenv("ENCRYPTION_KEY")
    if env_key:
        try:
            # Check if it's a 64-char hex string (32 bytes) - standard for this project
            if len(env_key) == 64:
                 try:
                     return bytes.fromhex(env_key)
                 except ValueError:
                     pass # Not hex

            # Fallback checks (base64 or raw)
            return base64.urlsafe_b64decode(env_key) if len(env_key) > 64 else env_key.encode()
        except Exception as e:
            logger.warning(f"Failed to decode env var key: {e}")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logger.error("GOOGLE_CLOUD_PROJECT env var missing")
        return b"insecure_dev_key_fallback_32b_!!" # 32 bytes

    try:
        # 2. Try to get from Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/user-credentials-key/versions/latest"
        response = client.access_secret_version(request={"name": name})
        data = response.payload.data
        # Try hex decode if looks like hex
        try:
            val_str = data.decode('utf-8')
            if len(val_str) == 64:
                 return bytes.fromhex(val_str)
        except:
            pass
        return data
    except Exception as e:
        logger.warning(f"Could not get encryption key from Secret Manager: {e}")

    # 3. Generate a consistent key based on project ID (Fallback)
    logger.warning("⚠️ Using insecure derived key! Set USER_CREDENTIALS_KEY env var.")
    # Return a VALID 32-byte key for AES-256
    return b"J4z72_08-729048-70247-9082740927"


class UserCredentialsManager:
    """Manages encrypted user credentials in Firestore (AES-256-GCM)"""

    def __init__(self):
        self.db = firestore.Client()
        self.collection = "dhan_credentials" # Unified collection with Frontend!
        self.encryption_key = get_encryption_key()
        # Ensure key is 32 bytes for AES-256
        if len(self.encryption_key) != 32:
             logger.warning(f"Encryption key length {len(self.encryption_key)} != 32. Truncating or padding.")
             self.encryption_key = (self.encryption_key + b'0'*32)[:32]

        # self.aesgcm = AESGCM(self.encryption_key) <-- Removed
        logger.info("UserCredentialsManager initialized (AES-256-GCM / Cipher)")

    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data using AES-256-GCM (Frontend compatible)"""
        if not data: return None
        nonce = os.urandom(12) # Use 12 bytes standard IV

        # Explicit Cipher
        encryptor = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(nonce),
        ).encryptor()

        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        tag = encryptor.tag

        return f"{nonce.hex()}:{tag.hex()}:{ciphertext.hex()}"

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data (Supports AES-GCM and legacy Fernet)"""
        if not encrypted_data: return None

        # 1. Try AES-GCM (Format: iv:tag:ciphertext)
        try:
            parts = encrypted_data.split(':')
            if len(parts) == 3:
                iv = bytes.fromhex(parts[0])
                tag = bytes.fromhex(parts[1])
                ciphertext = bytes.fromhex(parts[2])

                # Explicit Cipher Decrypt
                decryptor = Cipher(
                    algorithms.AES(self.encryption_key),
                    modes.GCM(iv, tag),
                ).decryptor()

                data = decryptor.update(ciphertext) + decryptor.finalize()
                return data.decode()
        except Exception as e:
            # Not GCM or key mismatch
            logger.warning(f"GCM Decrypt failed: {e}")
            pass # Fallthrough to legacy

        # 2. Legacy Fallback (Fernet) - if applicable
        # This is unlikely to work with the AES key, but if keys were different:
        try:
            from cryptography.fernet import Fernet
            # Fernet needs urlsafe base64 key
            f_key = base64.urlsafe_b64encode(self.encryption_key)
            f = Fernet(f_key)
            return f.decrypt(encrypted_data.encode()).decode()
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
        Strips whitespace from tokens to prevent JWT parsing errors
        """
        try:
            # CRITICAL: Strip whitespace from sensitive tokens to prevent JWT header errors
            # User copy/paste might include accidental newlines
            access_token = access_token.strip() if access_token else access_token
            client_id = client_id.strip() if client_id else client_id
            api_key = api_key.strip() if api_key else api_key
            api_secret = api_secret.strip() if api_secret else api_secret
            user_id = user_id.strip() if user_id else user_id

            # Encrypt sensitive credentials
            encrypted_credentials = {
                "client_id": client_id,  # Client ID is not secret
                "access_token": self._encrypt(access_token),
                "api_key": self._encrypt(api_key) if api_key else None,
                "api_secret": self._encrypt(api_secret) if api_secret else None,
            }

            # Create document (Backend format)
            # To maintain compatibility with frontend, we should probably support both or migrate.
            # For now, we save as backend format (nested) but read both.
            doc_data = {
                "user_id": user_id,
                "credentials": encrypted_credentials,
                # Also save flat CamelCase for Frontend compatibility if needed?
                # Frontend writes flat. Backend writes nested.
                # Let's save flat too to be safe.
                "clientId": self._encrypt(client_id) if client_id else None, # Frontend encrypts ClientId too? Verify.
                # Frontend: clientId: encrypt(clientId)
                "accessToken": self._encrypt(access_token),
                "apiKey": self._encrypt(api_key) if api_key else None,
                "apiSecret": self._encrypt(api_secret) if api_secret else None,

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
        Retrieve and decrypt user's Dhan credentials.
        PRIORITY: Frontend's flat CamelCase format (clientId, accessToken, apiKey, apiSecret)
        All fields are encrypted with AES-256-GCM using ENCRYPTION_KEY env var.
        """
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"No credentials document found for user: {user_id}")
                return None

            data = doc.to_dict()
            logger.info(f"Retrieved credentials document for {user_id}, fields: {list(data.keys())}")

            # Frontend format (PRIORITY): clientId, accessToken, apiKey, apiSecret (all encrypted)
            # This is what submitDhanCredentialsV2 Cloud Function writes
            client_id = None
            access_token = None
            api_key = None
            api_secret = None

            # Try Frontend Format First (CamelCase, all encrypted)
            if data.get("clientId"):
                try:
                    client_id = self._decrypt(data.get("clientId"))
                    logger.info(f"✅ Decrypted clientId for {user_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to decrypt clientId: {e}")

            if data.get("accessToken"):
                try:
                    access_token = self._decrypt(data.get("accessToken"))
                    logger.info(f"✅ Decrypted accessToken for {user_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to decrypt accessToken: {e}")

            if data.get("apiKey"):
                try:
                    api_key = self._decrypt(data.get("apiKey"))
                    logger.info(f"✅ Decrypted apiKey for {user_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to decrypt apiKey: {e}")

            if data.get("apiSecret"):
                try:
                    api_secret = self._decrypt(data.get("apiSecret"))
                    logger.info(f"✅ Decrypted apiSecret for {user_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to decrypt apiSecret: {e}")

            # Fallback: Try nested backend format (credentials.client_id) if frontend format not found
            if not client_id:
                encrypted_creds = data.get("credentials", {})
                if encrypted_creds:
                    logger.info(f"Trying nested backend format for {user_id}")
                    try:
                        # Backend format may or may not encrypt client_id
                        client_id_val = encrypted_creds.get("client_id")
                        if client_id_val and ":" in str(client_id_val):
                            client_id = self._decrypt(client_id_val)
                        else:
                            client_id = client_id_val
                        
                        if encrypted_creds.get("access_token"):
                            access_token = self._decrypt(encrypted_creds.get("access_token"))
                        if encrypted_creds.get("api_key"):
                            api_key = self._decrypt(encrypted_creds.get("api_key"))
                        if encrypted_creds.get("api_secret"):
                            api_secret = self._decrypt(encrypted_creds.get("api_secret"))
                    except Exception as e:
                        logger.warning(f"Backend format decryption failed: {e}")

            # Validate we have minimum required credentials
            if not client_id:
                logger.error(f"❌ No client_id found for {user_id}")
                return {
                    "user_id": user_id,
                    "connection_status": "incomplete",
                    "is_active": False,
                    "credentials": {},
                    "error": "Missing client_id"
                }

            if not access_token and not api_key:
                logger.error(f"❌ No access_token or api_key found for {user_id}")
                return {
                    "user_id": user_id,
                    "connection_status": "incomplete",
                    "is_active": False,
                    "credentials": {"client_id": client_id},
                    "error": "Missing access_token and api_key"
                }

            # Return decrypted credentials
            decrypted = {
                "client_id": client_id,
                "access_token": access_token,
                "api_key": api_key,
                "api_secret": api_secret,
            }

            logger.info(f"✅ Successfully retrieved and decrypted credentials for {user_id}")

            return {
                "user_id": user_id,
                "credentials": decrypted,
                "is_active": data.get("is_active", True),
                "connection_status": "connected",
                "updated_at": data.get("updated_at") or data.get("lastUpdatedAt")
            }

        except Exception as e:
            logger.error(f"❌ Error retrieving credentials for {user_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def resolve_user_id(self, user_id: str) -> Optional[str]:
        """
        Resolve a user_id (which could be generated like 'user_1768802144009_1jvf3b')
        to the actual Firebase UID where credentials are stored.

        Strategy:
        1. Try direct lookup with user_id as document ID (since credentials are saved with user_id as doc ID)
        2. If not found and user_id is numeric, try as client_id
        3. Return the resolved Firebase UID or None
        """
        if not user_id:
            return None

        # Strategy 1: Try direct lookup first - credentials ARE saved with user_id as document ID
        # Since save_user_credentials() does: collection.document(user_id).set()
        try:
            doc = self.db.collection(self.collection).document(user_id).get()
            if doc.exists:
                logger.info(f"✅ Resolved user_id {user_id} directly as Firestore document")
                return user_id
            else:
                logger.debug(f"📍 No document found for {user_id} in collection {self.collection}")
        except Exception as e:
            logger.debug(f"Direct lookup failed for {user_id}: {e}")

        # Strategy 2: If user_id is numeric, try searching by client_id
        if user_id.isdigit():
            try:
                creds = await self.find_credentials_by_client_id(user_id)
                if creds:
                    resolved_id = creds.get("user_id")
                    logger.info(f"✅ Resolved numeric user_id {user_id} to Firebase UID {resolved_id}")
                    return resolved_id
            except Exception as e:
                logger.debug(f"Client ID lookup failed for {user_id}: {e}")

        # Strategy 3: If credentials were saved under a different document ID but have matching user_id field
        try:
            query = (
                self.db.collection(self.collection)
                .where("user_id", "==", user_id)
                .limit(1)
            )
            docs = list(query.stream())
            doc = docs[0] if docs else None
            if doc:
                logger.info(f"✅ Resolved user_id {user_id} via user_id field on document {doc.id}")
                return doc.id
        except Exception as e:
            logger.debug(f"user_id field lookup failed for {user_id}: {e}")

        logger.warning(f"⚠️ Could not resolve user_id: {user_id} in collection {self.collection}")
        return None

    async def find_credentials_by_client_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Locate credentials by stored Dhan client_id when the document ID is a Firebase UID.
        This allows numeric client IDs from the frontend to resolve to the correct record.
        """
        if not client_id:
            return None

        try:
            query = (
                self.db.collection(self.collection)
                .where("credentials.client_id", "==", client_id)
                .limit(1)
            )
            docs = list(query.stream())
            doc = docs[0] if docs else None

            if not doc:
                # Fallback to legacy flat field, in case nested credentials are missing
                query_flat = (
                    self.db.collection(self.collection)
                    .where("clientId", "==", client_id)
                    .limit(1)
                )
                docs_flat = list(query_flat.stream())
                doc = docs_flat[0] if docs_flat else None

            if doc:
                # Reuse the standard decrypt/normalize path
                return await self.get_user_credentials(doc.id)

        except Exception as e:
            logger.error(f"Error finding credentials by client_id {client_id}: {e}")

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
            docs = self.db.collection(self.collection).stream() # Scan all

            users = []
            for doc in docs:
                data = doc.to_dict()
                users.append({
                    "user_id": data.get("user_id") or doc.id,
                    "client_id": data.get("credentials", {}).get("client_id") or data.get("clientId"),
                    "connection_status": data.get("connection_status"),
                    "updated_at": data.get("updated_at")
                })

            return users

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    # ==================== USER TRADING SETTINGS (Keep separate) ====================

    async def save_trading_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save user's trading configuration settings in Firestore
        """
        try:
            # Validate and set defaults
            validated_settings = {
                "stop_loss_percent": float(settings.get("stop_loss_percent", 2.0)),
                "take_profit_percent": float(settings.get("take_profit_percent", 4.0)),
                "max_trades_per_day": int(settings.get("max_trades_per_day", 10)),
                "trading_amount": float(settings.get("trading_amount", 10000)),
                "min_capital": float(settings.get("min_capital", 5000)),
                "max_capital": float(settings.get("max_capital", 100000)),
                "risk_level": settings.get("risk_level", "moderate"),
                "max_risk_per_trade": float(settings.get("max_risk_per_trade", 0.02)),
                "min_confidence": float(settings.get("min_confidence", 0.75)),
                "selected_instruments": settings.get("selected_instruments", ["equities"]),
                "use_ai_signals": bool(settings.get("use_ai_signals", True)),
                "auto_rebalance": bool(settings.get("auto_rebalance", False)),
                "trailing_stop_loss": bool(settings.get("trailing_stop_loss", False)),
                "position_sizing_method": settings.get("position_sizing_method", "fixed"),
                "updated_at": datetime.utcnow(),
            }

            # Validate risk_level
            if validated_settings["risk_level"] not in ["conservative", "moderate", "aggressive"]:
                validated_settings["risk_level"] = "moderate"

            # Validate position_sizing_method
            if validated_settings["position_sizing_method"] not in ["fixed", "percentage", "kelly"]:
                validated_settings["position_sizing_method"] = "fixed"

            # Validate ranges
            validated_settings["stop_loss_percent"] = max(0.5, min(10.0, validated_settings["stop_loss_percent"]))
            validated_settings["take_profit_percent"] = max(1.0, min(20.0, validated_settings["take_profit_percent"]))
            validated_settings["max_trades_per_day"] = max(1, min(50, validated_settings["max_trades_per_day"]))
            validated_settings["max_risk_per_trade"] = max(0.005, min(0.10, validated_settings["max_risk_per_trade"]))
            validated_settings["min_confidence"] = max(0.5, min(0.99, validated_settings["min_confidence"]))

            # Save to Firestore in trading_settings collection
            doc_ref = self.db.collection("trading_settings").document(user_id)
            doc_ref.set(validated_settings, merge=True)

            logger.info(f"✅ Saved trading settings for user {user_id}")
            return {
                "status": "success",
                "message": "Trading settings saved successfully",
                "user_id": user_id,
                "settings": validated_settings
            }

        except Exception as e:
            logger.error(f"Error saving trading settings: {e}")
            raise ValueError(f"Failed to save trading settings: {str(e)}")

    async def get_trading_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user's trading configuration settings
        Returns default settings if none exist
        """
        try:
            doc_ref = self.db.collection("trading_settings").document(user_id)
            doc = doc_ref.get()

            # Default settings
            defaults = {
                "stop_loss_percent": 2.0,
                "take_profit_percent": 4.0,
                "max_trades_per_day": 10,
                "trading_amount": 10000,
                "min_capital": 5000,
                "max_capital": 100000,
                "risk_level": "moderate",
                "max_risk_per_trade": 0.02,
                "min_confidence": 0.75,
                "selected_instruments": ["equities"],
                "use_ai_signals": True,
                "auto_rebalance": False,
                "trailing_stop_loss": False,
                "position_sizing_method": "fixed",
            }

            if not doc.exists:
                logger.info(f"No trading settings found for {user_id}, returning defaults")
                return {
                    "user_id": user_id,
                    "settings": defaults,
                    "is_default": True
                }

            data = doc.to_dict()
            # Merge with defaults in case of missing fields
            settings = {**defaults, **data}
            # Remove Firestore timestamp fields
            settings.pop("updated_at", None)

            return {
                "user_id": user_id,
                "settings": settings,
                "is_default": False,
                "last_updated": data.get("updated_at")
            }

        except Exception as e:
            logger.error(f"Error retrieving trading settings: {e}")
            # Return defaults on error
            return {
                "user_id": user_id,
                "settings": {
                    "stop_loss_percent": 2.0,
                    "take_profit_percent": 4.0,
                    "max_trades_per_day": 10,
                    "trading_amount": 10000,
                    "min_capital": 5000,
                    "max_capital": 100000,
                    "risk_level": "moderate",
                    "max_risk_per_trade": 0.02,
                    "min_confidence": 0.75,
                    "selected_instruments": ["equities"],
                    "use_ai_signals": True,
                    "auto_rebalance": False,
                    "trailing_stop_loss": False,
                    "position_sizing_method": "fixed",
                },
                "is_default": True,
                "error": str(e)
            }

    async def delete_trading_settings(self, user_id: str) -> bool:
        """Delete user's trading settings (reset to defaults)"""
        try:
            doc_ref = self.db.collection("trading_settings").document(user_id)
            doc_ref.delete()
            logger.info(f"✅ Deleted trading settings for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting trading settings: {e}")
            return False


# Singleton instance
_credentials_manager: Optional[UserCredentialsManager] = None

def get_credentials_manager() -> UserCredentialsManager:
    """Get singleton instance of UserCredentialsManager"""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = UserCredentialsManager()
    return _credentials_manager
