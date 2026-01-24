"""
User Credentials Management using GCP Secret Manager
Secure storage and retrieval of user Dhan credentials
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from google.cloud import secretmanager
from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    # Fail fast for core credentials module
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")


class SecretManagerCredentials:
    """Manages user credentials using GCP Secret Manager"""

    def __init__(self):
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = PROJECT_ID
        logger.info("✅ SecretManagerCredentials initialized")

    def _get_secret_name(self, user_id: str) -> str:
        """Get the full secret resource name"""
        return f"projects/{self.project_id}/secrets/user-creds-{user_id}"

    def _get_secret_version_name(self, user_id: str, version: str = "latest") -> str:
        """Get the full secret version resource name"""
        return f"{self._get_secret_name(user_id)}/versions/{version}"

    async def save_user_credentials(
        self,
        user_id: str,
        client_id: str,
        access_token: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save user's Dhan credentials to GCP Secret Manager

        Args:
            user_id: Unique user identifier (Dhan Client ID)
            client_id: Dhan Client ID
            access_token: Dhan Access Token
            api_key: Dhan API Key
            api_secret: Dhan API Secret
        """
        try:
            # Prepare credentials data
            credentials_data = {
                "client_id": client_id,
                "access_token": access_token,
                "api_key": api_key,
                "api_secret": api_secret,
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            }

            secret_data = json.dumps(credentials_data).encode("utf-8")
            secret_id = f"user-creds-{user_id}"

            # Check if secret exists
            try:
                self.client.get_secret(request={"name": self._get_secret_name(user_id)})
                secret_exists = True
            except gcp_exceptions.NotFound:
                secret_exists = False

            if not secret_exists:
                # Create new secret
                self.client.create_secret(
                    request={
                        "parent": f"projects/{self.project_id}",
                        "secret_id": secret_id,
                        "secret": {
                            "replication": {"automatic": {}},
                            "labels": {
                                "user_id": user_id.lower(),
                                "type": "dhan_credentials"
                            }
                        }
                    }
                )
                logger.info(f"✅ Created new secret for user {user_id}")

            # Add new version with credentials
            version = self.client.add_secret_version(
                request={
                    "parent": self._get_secret_name(user_id),
                    "payload": {"data": secret_data}
                }
            )

            logger.info(f"✅ Saved credentials for user {user_id} (version: {version.name})")
            return {
                "status": "success",
                "message": "Credentials saved to GCP Secret Manager",
                "user_id": user_id,
                "client_id": client_id,
                "version": version.name.split("/")[-1]
            }

        except Exception as e:
            logger.error(f"Error saving credentials to Secret Manager: {e}")
            raise ValueError(f"Failed to save credentials: {str(e)}")

    async def get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user's Dhan credentials from GCP Secret Manager

        Returns decrypted credentials or None if not found
        """
        try:
            # Access the latest version
            response = self.client.access_secret_version(
                request={"name": self._get_secret_version_name(user_id)}
            )

            # Decode and parse credentials
            credentials_data = json.loads(response.payload.data.decode("utf-8"))

            return {
                "user_id": user_id,
                "credentials": {
                    "client_id": credentials_data.get("client_id"),
                    "access_token": credentials_data.get("access_token"),
                    "api_key": credentials_data.get("api_key"),
                    "api_secret": credentials_data.get("api_secret"),
                },
                "is_active": credentials_data.get("is_active", True),
                "updated_at": credentials_data.get("updated_at")
            }

        except gcp_exceptions.NotFound:
            logger.info(f"No credentials found for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
            return None

    async def delete_user_credentials(self, user_id: str) -> bool:
        """Delete user's credentials from Secret Manager"""
        try:
            # Delete the secret (and all versions)
            self.client.delete_secret(
                request={"name": self._get_secret_name(user_id)}
            )
            logger.info(f"✅ Deleted credentials for user {user_id}")
            return True
        except gcp_exceptions.NotFound:
            logger.info(f"No credentials to delete for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting credentials: {e}")
            return False

    async def list_connected_users(self) -> list:
        """List all users with stored credentials"""
        try:
            users = []

            # List all secrets with the dhan_credentials label
            for secret in self.client.list_secrets(
                request={"parent": f"projects/{self.project_id}"}
            ):
                if secret.name.startswith(f"projects/{self.project_id}/secrets/user-creds-"):
                    user_id = secret.name.split("user-creds-")[-1]
                    labels = dict(secret.labels) if secret.labels else {}
                    users.append({
                        "user_id": user_id,
                        "client_id": labels.get("user_id", user_id),
                        "created": secret.create_time.isoformat() if secret.create_time else None
                    })

            return users

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    async def update_connection_status(self, user_id: str, status: str, account_data: dict = None) -> bool:
        """
        Update the connection status for a user.
        Note: This is a no-op for Secret Manager as we don't store status separately.
        The status is always derived from whether credentials exist and are valid.

        Args:
            user_id: The user ID
            status: Connection status (connected, failed, etc.)
            account_data: Optional account data from Dhan (ignored for Secret Manager)
        """
        logger.info(f"Connection status update for user {user_id}: {status}")
        # For Secret Manager, we don't need to store status separately
        # The credential existence implies connected status
        return True


# Singleton instance
_secret_manager_credentials: Optional[SecretManagerCredentials] = None


def get_secret_manager_credentials() -> SecretManagerCredentials:
    """Get singleton instance of SecretManagerCredentials"""
    global _secret_manager_credentials
    if _secret_manager_credentials is None:
        _secret_manager_credentials = SecretManagerCredentials()
    return _secret_manager_credentials
