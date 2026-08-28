"""
User Credentials Management for InfinityAI.Pro
Single-Tenant Dhan Vault & AES-256-GCM Credential Auto-Resolution in Google Cloud Firestore.
Primary Owner Client ID: 1101302170 (raghu_primary)
"""
import os
import json
import base64
import hashlib
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)

PRIMARY_USER_ID = os.getenv("PRIMARY_USER_ID", "raghu_primary")
PRIMARY_CLIENT_ID = os.getenv("PRIMARY_CLIENT_ID", "1101302170")

def get_encryption_key() -> bytes:
    """
    Load the AES-256 encryption key from the environment.

    Key resolution order:
      1. USER_CREDENTIALS_KEY  (preferred, set via GCP Secret Manager injection)
      2. ENCRYPTION_KEY        (legacy alias)

    Key formats accepted:
      - 64-char hex string  → decoded as 32 raw bytes
      - Base64url string    → decoded as bytes (must be ≥ 32 bytes after decode)
      - Raw 32-byte string  → used directly

    Production: raises RuntimeError if no key env var is set.
    Local dev (ENV=local): generates a random ephemeral key (logged as warning).
    """
    env_key = os.getenv("USER_CREDENTIALS_KEY") or os.getenv("ENCRYPTION_KEY")
    if not env_key:
        try:
            from google.cloud import secretmanager
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            sm = secretmanager.SecretManagerServiceClient()
            sec_name = f"projects/{project_id}/secrets/USER_CREDENTIALS_KEY/versions/latest"
            resp = sm.access_secret_version(request={"name": sec_name})
            env_key = resp.payload.data.decode("utf-8").strip()
            logger.info("✅ Dynamically resolved USER_CREDENTIALS_KEY from GCP Secret Manager.")
        except Exception as e:
            logger.debug(f"SecretManager USER_CREDENTIALS_KEY lookup skipped: {e}")

    if env_key:
        try:
            # 64-char hex → 32 raw bytes
            if len(env_key) == 64:
                try:
                    decoded = bytes.fromhex(env_key)
                    if len(decoded) == 32:
                        return decoded
                except ValueError:
                    pass

            # Base64url-encoded → raw bytes (must decode to ≥ 32 bytes)
            if len(env_key) > 43:  # base64url of 32 bytes = 44 chars (with padding)
                try:
                    decoded = base64.urlsafe_b64decode(env_key + "=" * (-len(env_key) % 4))
                    if len(decoded) >= 32:
                        return decoded[:32]
                except Exception:
                    pass

            # Raw string fallback — pad/truncate to exactly 32 bytes
            raw = env_key.encode()
            if len(raw) >= 32:
                return raw[:32]

            logger.warning("USER_CREDENTIALS_KEY is too short; padding to 32 bytes.")
            return (raw + b'\x00' * 32)[:32]

        except Exception as e:
            logger.error(f"Failed to decode USER_CREDENTIALS_KEY: {e}")
            # Fall through to the missing-key guard below

    # ── No key provided ──────────────────────────────────────────────────────
    is_local = os.getenv("ENV", "production").lower() in ("local", "development", "dev")

    if not is_local:
        raise RuntimeError(
            "CRITICAL: USER_CREDENTIALS_KEY environment variable is not set. "
            "Engine C cannot start without an AES-256 encryption key. "
            "Provision it via GCP Secret Manager and inject as an env var."
        )

    # Local dev only — ephemeral random key (NOT usable to decrypt Firestore data)
    logger.warning(
        "⚠️  ENV=local: No USER_CREDENTIALS_KEY set. "
        "Using a random ephemeral key — Firestore-encrypted credentials will NOT be readable. "
        "Set USER_CREDENTIALS_KEY or DHAN_ACCESS_TOKEN env vars for local testing."
    )
    return os.urandom(32)

class UserCredentialsManager:
    """Manages encrypted user credentials in Firebase Firestore & Secret Manager (AES-256-GCM)"""

    def __init__(self):
        self.db = None
        self._init_firestore()
        self.encryption_key = get_encryption_key()
        if len(self.encryption_key) != 32:
            self.encryption_key = (self.encryption_key + b'\x00' * 32)[:32]
        self._cached_creds: Optional[Dict[str, Any]] = None
        self._cached_creds_time: float = 0.0

        key_source = "USER_CREDENTIALS_KEY" if os.getenv("USER_CREDENTIALS_KEY") else (
            "ENCRYPTION_KEY" if os.getenv("ENCRYPTION_KEY") else "EPHEMERAL (local dev)"
        )
        # Log a SHA-256 fingerprint (first 16 hex chars) so key rotations are
        # immediately traceable in Cloud Logging without exposing the raw key.
        key_fingerprint = hashlib.sha256(self.encryption_key).hexdigest()[:16]
        logger.info(
            f"UserCredentialsManager initialized "
            f"(Single-Tenant AES-256-GCM / Firebase Firestore Vault) "
            f"| key_source={key_source} | key_fingerprint=sha256:{key_fingerprint}"
        )

    def _init_firestore(self):
        try:
            from google.cloud import firestore
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            
            # Omit the database argument to hit the default instance
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
        """Decrypt sensitive data with JWT and raw fallback"""
        if not encrypted_data:
            return None
        
        # Direct JWT check: if it is an unencrypted standard JWT access token
        if isinstance(encrypted_data, str) and (encrypted_data.strip().startswith("eyJ") or encrypted_data.strip().startswith("dhan_")):
            return encrypted_data.strip()

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
                # CRITICAL: Strip trailing \r\n from decrypted tokens.
                # Token renewal responses may inject trailing newlines that
                # cause HTTP header errors when passed to DhanHQ SDK.
                return data.decode().strip()
        except Exception as e:
            logger.warning(
                f"GCM Decrypt notice: payload format mismatch ({e}). Checking raw string..."
            )
            if isinstance(encrypted_data, str) and encrypted_data.strip().startswith("eyJ"):
                return encrypted_data.strip()

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
        resolved_id = await self.resolve_user_id(user_id)
        # CRITICAL: Strip whitespace from token before encryption.
        # Prevents \r\n from being encrypted into the vault.
        enc_token = self._encrypt(access_token.strip() if access_token else access_token)
        enc_secret = self._encrypt(api_secret) if api_secret else None

        doc_data = {
            "user_id": resolved_id,
            "dhan_client_id": client_id or PRIMARY_CLIENT_ID,
            "dhan_access_token": enc_token,
            "api_key": api_key,
            "api_secret": enc_secret,
            "updated_at": datetime.utcnow().isoformat()
        }

        if self.db:
            try:
                self.db.collection("user_credentials").document(resolved_id).set(doc_data, merge=True)

                try:
                    self.db.collection("users").document(resolved_id).set({
                        "dhanConnected": True,
                        "dhanClientId": client_id or PRIMARY_CLIENT_ID,
                        "updatedAt": datetime.utcnow().isoformat()
                    }, merge=True)
                except Exception as ue:
                    logger.warning(f"Failed to sync users doc: {ue}")

                # Invalidate memory cache
                self._cached_creds = None
                logger.info(f"✅ Credentials saved to Firestore for user: {resolved_id}")
            except Exception as e:
                logger.error(f"Failed to write to Firestore: {e}")

        return {
            "success": True,
            "user_id": resolved_id,
            "dhan_client_id": client_id or PRIMARY_CLIENT_ID,
            "updated_at": doc_data["updated_at"]
        }

    async def get_user_credentials(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt user's Dhan credentials from Firestore (Single-Tenant high-performance cached auto-resolution)"""
        now = time.time()
        # Serve cached credentials if fresh (< 60s)
        if self._cached_creds and (now - self._cached_creds_time) < 60.0:
            return self._cached_creds

        resolved_id = await self.resolve_user_id(user_id)

        if self.db:
            # 1. Check primary known doc IDs in order: PRIMARY_USER_ID -> resolved_id -> PRIMARY_CLIENT_ID
            for target in [PRIMARY_USER_ID, resolved_id, PRIMARY_CLIENT_ID]:
                if not target:
                    continue
                try:
                    doc = self.db.collection("user_credentials").document(target).get()
                    if doc.exists:
                        data = doc.to_dict()
                        raw_token = data.get("dhan_access_token") or data.get("access_token")
                        raw_secret = data.get("api_secret")
                        dec_token = self._decrypt(raw_token) if raw_token else None
                        dec_secret = self._decrypt(raw_secret) if raw_secret else None
                        client_id = data.get("dhan_client_id") or data.get("client_id") or PRIMARY_CLIENT_ID
                        if dec_token:
                            creds = {
                                "user_id": resolved_id,
                                "dhan_client_id": client_id,
                                "client_id": client_id,
                                "dhan_access_token": dec_token,
                                "access_token": dec_token,
                                "api_key": data.get("api_key"),
                                "api_secret": dec_secret,
                                "connection_status": data.get("connection_status", "connected"),
                                "is_verified": data.get("is_verified", True),
                                "updated_at": data.get("updated_at")
                            }
                            self._cached_creds = creds
                            self._cached_creds_time = now
                            return creds
                except Exception as e:
                    logger.error(f"Error reading credentials document '{target}': {e}")

            # 2. Check by client ID query
            by_client = await self.find_credentials_by_client_id(PRIMARY_CLIENT_ID)
            if by_client and by_client.get("access_token"):
                self._cached_creds = by_client
                self._cached_creds_time = now
                return by_client

        # 3. Fallback to env vars if testing locally
        env_client_id = os.getenv("DHAN_CLIENT_ID", PRIMARY_CLIENT_ID)
        env_token = os.getenv("DHAN_ACCESS_TOKEN")
        if env_client_id and env_token:
            creds = {
                "user_id": resolved_id,
                "dhan_client_id": env_client_id,
                "client_id": env_client_id,
                "dhan_access_token": env_token,
                "access_token": env_token,
                "connection_status": "connected",
                "is_verified": True,
                "updated_at": datetime.utcnow().isoformat()
            }
            self._cached_creds = creds
            self._cached_creds_time = now
            return creds
        return None

    async def find_credentials_by_client_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Find credentials by Dhan client ID"""
        if self.db:
            try:
                users_ref = self.db.collection("user_credentials")
                query = users_ref.where(filter=FieldFilter("dhan_client_id", "==", str(client_id))).limit(1)
                docs = list(query.stream())
                for doc in docs:
                    data = doc.to_dict()
                    raw_token = data.get("dhan_access_token") or data.get("access_token")
                    if raw_token:
                        return {
                            "user_id": doc.id,
                            "dhan_client_id": client_id,
                            "client_id": client_id,
                            "dhan_access_token": self._decrypt(raw_token),
                            "access_token": self._decrypt(raw_token),
                            "api_key": data.get("api_key"),
                            "api_secret": self._decrypt(data.get("api_secret")),
                            "connection_status": data.get("connection_status", "connected"),
                            "is_verified": data.get("is_verified", True),
                            "updated_at": data.get("updated_at")
                        }
            except Exception as e:
                logger.error(f"Error querying Firestore by client_id: {e}")
        return None

    async def resolve_user_id(self, user_id: Optional[str] = None) -> str:
        """Instantly resolve single-tenant primary user ID"""
        return PRIMARY_USER_ID

    async def delete_user_credentials(self, user_id: str) -> bool:
        """Delete user's Dhan credentials from Firestore"""
        resolved_id = await self.resolve_user_id(user_id)
        if self.db:
            try:
                doc_ref = self.db.collection("user_credentials").document(resolved_id)
                doc_ref.delete()
                self._cached_creds = None
                logger.info(f"✅ Credentials deleted from Firestore for user: {resolved_id}")
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
        resolved_id = await self.resolve_user_id(user_id)
        if self.db:
            try:
                doc_ref = self.db.collection("user_credentials").document(resolved_id)
                update_payload = {
                    "connection_status": connection_status,
                    "is_verified": connection_status == "connected",
                    "updated_at": datetime.utcnow().isoformat()
                }
                if account_data:
                    update_payload["account_summary"] = account_data
                doc_ref.set(update_payload, merge=True)
                self._cached_creds = None
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