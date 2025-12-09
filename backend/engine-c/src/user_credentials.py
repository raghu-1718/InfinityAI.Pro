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

    # ==================== USER TRADING SETTINGS ====================

    async def save_trading_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save user's trading configuration settings in Firestore

        Settings include:
        - stop_loss_percent: Default stop loss percentage (e.g., 2.0)
        - take_profit_percent: Default take profit percentage (e.g., 4.0)
        - max_trades_per_day: Maximum trades allowed per day
        - trading_amount: Default amount per trade (in INR)
        - min_capital: Minimum capital required to trade
        - max_capital: Maximum capital to use for trading
        - risk_level: 'conservative' | 'moderate' | 'aggressive'
        - max_risk_per_trade: Max risk as fraction (e.g., 0.02 = 2%)
        - min_confidence: Minimum AI confidence to execute (e.g., 0.75)
        - selected_instruments: List of instruments to trade
        - use_ai_signals: Whether to use AI signals
        - auto_rebalance: Whether to auto-rebalance portfolio
        - trailing_stop_loss: Enable trailing stop loss
        - position_sizing_method: 'fixed' | 'percentage' | 'kelly'
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
