"""
User Credentials Management for InfinityAI.Pro
Handles secure storage and retrieval of user Dhan credentials in Supabase
"""
import os
import json
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from supabase import create_client, Client

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

    logger.warning("⚠️ Using insecure derived key! Set USER_CREDENTIALS_KEY env var.")
    return b"J4z72_08-729048-70247-9082740927"

class UserCredentialsManager:
    """Manages encrypted user credentials in Supabase (AES-256-GCM)"""

    def __init__(self):
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        if not url or not key:
            logger.error("SUPABASE_URL or SUPABASE_ANON_KEY missing!")
        
        self.db: Client = create_client(url, key) if url and key else None
        self.encryption_key = get_encryption_key()
        if len(self.encryption_key) != 32:
             logger.warning(f"Encryption key length {len(self.encryption_key)} != 32. Truncating or padding.")
             self.encryption_key = (self.encryption_key + b'0'*32)[:32]

        logger.info("UserCredentialsManager initialized (AES-256-GCM / Supabase)")

    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data using AES-256-GCM"""
        if not data: return None
        nonce = os.urandom(12)
        encryptor = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(nonce),
        ).encryptor()
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        tag = encryptor.tag
        return f"{nonce.hex()}:{tag.hex()}:{ciphertext.hex()}"

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data: return None
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
            pass

        try:
            from cryptography.fernet import Fernet
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
        """Save user's Dhan credentials securely in Supabase"""
        try:
            access_token = access_token.strip() if access_token else access_token
            client_id = client_id.strip() if client_id else client_id
            api_key = api_key.strip() if api_key else api_key
            api_secret = api_secret.strip() if api_secret else api_secret
            user_id = user_id.strip() if user_id else user_id

            encrypted_credentials = {
                "client_id": client_id,
                "access_token": self._encrypt(access_token),
                "api_key": self._encrypt(api_key) if api_key else None,
                "api_secret": self._encrypt(api_secret) if api_secret else None,
            }

            doc_data = {
                "user_uid": user_id,
                "broker_client_id": client_id,
                "broker_access_token": json.dumps(encrypted_credentials).encode('utf-8').hex(),
                "updated_at": datetime.utcnow().isoformat()
            }

            if self.db:
                try:
                    self.db.table("users").upsert({"uid": user_id}).execute()
                except Exception as user_e:
                    logger.warning(f"Failed to upsert user {user_id}: {user_e}")

                self.db.table("user_credentials").upsert(doc_data, on_conflict="user_uid").execute()
                
                self.db.table("users").update({
                    "dhan_connected": True,
                    "dhan_client_id": client_id
                }).eq("uid", user_id).execute()

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
        """Retrieve and decrypt user's Dhan credentials."""
        try:
            if not self.db: return None
            response = self.db.table("user_credentials").select("*").eq("user_uid", user_id).execute()
            if not response.data:
                logger.warning(f"No credentials document found for user: {user_id}")
                return None
            
            data = response.data[0]
            broker_access_token_hex = data.get("broker_access_token")
            
            if not broker_access_token_hex:
                return None
                
            try:
                if broker_access_token_hex.startswith('\\x'): # Postgres bytea format
                    broker_access_token_hex = broker_access_token_hex[2:]
                encrypted_json = bytes.fromhex(broker_access_token_hex).decode('utf-8')
                encrypted_credentials = json.loads(encrypted_json)
            except Exception as e:
                logger.error(f"Failed to decode token data: {e}")
                return None

            client_id = encrypted_credentials.get("client_id")
            access_token = self._decrypt(encrypted_credentials.get("access_token"))
            api_key = self._decrypt(encrypted_credentials.get("api_key")) if encrypted_credentials.get("api_key") else None
            api_secret = self._decrypt(encrypted_credentials.get("api_secret")) if encrypted_credentials.get("api_secret") else None

            if not client_id:
                return {"user_id": user_id, "connection_status": "incomplete", "is_active": False, "credentials": {}, "error": "Missing client_id"}

            if not access_token and not api_key:
                return {"user_id": user_id, "connection_status": "incomplete", "is_active": False, "credentials": {"client_id": client_id}, "error": "Missing access_token and api_key"}

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
                "is_active": True,
                "connection_status": "connected",
                "updated_at": data.get("updated_at")
            }

        except Exception as e:
            logger.error(f"❌ Error retrieving credentials for {user_id}: {e}")
            return None

    async def resolve_user_id(self, user_id: str) -> Optional[str]:
        """Resolve a user_id to Firebase UID."""
        if not user_id:
            return None
            
        if self.db:
            res = self.db.table("user_credentials").select("user_uid").eq("user_uid", user_id).execute()
            if res.data:
                return user_id
            
            if user_id.isdigit():
                res = self.db.table("user_credentials").select("user_uid").eq("broker_client_id", user_id).execute()
                if res.data:
                    return res.data[0].get("user_uid")
                    
        return None

    async def find_credentials_by_client_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Locate credentials by client_id."""
        if not client_id or not self.db:
            return None

        try:
            res = self.db.table("user_credentials").select("user_uid").eq("broker_client_id", client_id).execute()
            if res.data:
                return await self.get_user_credentials(res.data[0].get("user_uid"))
        except Exception as e:
            logger.error(f"Error finding credentials by client_id {client_id}: {e}")

        return None

    async def update_connection_status(self, user_id: str, status: str, account_info: Optional[Dict] = None):
        """Update the connection status after verification"""
        if self.db:
            self.db.table("users").update({"dhan_connected": status == "connected"}).eq("uid", user_id).execute()

    async def delete_user_credentials(self, user_id: str) -> bool:
        """Delete user's credentials"""
        try:
            if self.db:
                self.db.table("user_credentials").delete().eq("user_uid", user_id).execute()
                self.db.table("users").update({"dhan_connected": False, "dhan_client_id": None}).eq("uid", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting credentials: {e}")
            return False

    async def list_connected_users(self) -> list:
        """List all users with connected accounts (admin only)"""
        try:
            if not self.db: return []
            res = self.db.table("users").select("uid, dhan_connected, dhan_client_id, last_login_at").eq("dhan_connected", True).execute()
            users = []
            for doc in res.data:
                users.append({
                    "user_id": doc.get("uid"),
                    "client_id": doc.get("dhan_client_id"),
                    "connection_status": "connected" if doc.get("dhan_connected") else "disconnected",
                    "updated_at": doc.get("last_login_at")
                })
            return users
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    # ==================== USER TRADING SETTINGS (Keep separate) ====================

    async def save_trading_settings(self, user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Save user's trading configuration settings in Supabase users table JSONB"""
        try:
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
                "updated_at": datetime.utcnow().isoformat(),
            }

            if self.db:
                self.db.table("users").update({"settings": validated_settings}).eq("uid", user_id).execute()

            logger.info(f"✅ Saved trading settings for user {user_id}")
            return {"status": "success", "message": "Trading settings saved successfully", "user_id": user_id, "settings": validated_settings}

        except Exception as e:
            logger.error(f"Error saving trading settings: {e}")
            raise ValueError(f"Failed to save trading settings: {str(e)}")

    async def get_trading_settings(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user's trading configuration settings"""
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

        try:
            if not self.db: raise Exception("DB not initialized")
            res = self.db.table("users").select("settings").eq("uid", user_id).execute()
            
            if not res.data or not res.data[0].get("settings"):
                return {"user_id": user_id, "settings": defaults, "is_default": True}

            data = res.data[0].get("settings")
            settings = {**defaults, **data}
            settings.pop("updated_at", None)

            return {"user_id": user_id, "settings": settings, "is_default": False, "last_updated": data.get("updated_at")}

        except Exception as e:
            logger.error(f"Error retrieving trading settings: {e}")
            return {"user_id": user_id, "settings": defaults, "is_default": True, "error": str(e)}

    async def delete_trading_settings(self, user_id: str) -> bool:
        """Delete user's trading settings (reset to defaults)"""
        try:
            if self.db:
                self.db.table("users").update({"settings": {}}).eq("uid", user_id).execute()
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
