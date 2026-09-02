"""
Unified GCP Secret Manager Client for InfinityAI.Pro
Handles dynamic resolution of API keys, DB credentials, and broker tokens.
"""
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("secret_manager")

DEFAULT_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")


class SecretManagerVault:
    """
    Unified Secret Manager accessor with support for dependency injection
    (e.g., MockSecretManagerClient for CI/CD) and caching.
    """

    def __init__(self, project_id: str = DEFAULT_PROJECT, client: Any = None):
        self.project_id = project_id
        self._cache: Dict[str, str] = {}
        self._client = client

    @property
    def client(self):
        if self._client is None:
            try:
                from google.cloud import secretmanager
                self._client = secretmanager.SecretManagerServiceClient()
            except Exception as e:
                logger.warning(f"GCP Secret Manager SDK not available ({e}); using mock/env fallback.")
                from vault.mock_vault import MockSecretManagerClient
                self._client = MockSecretManagerClient()
        return self._client

    def get_secret(self, secret_id: str, version: str = "latest", use_cache: bool = True) -> str:
        """
        Retrieve a secret payload by secret_id.
        Key lookup order:
          1. Local in-memory cache
          2. Secret Manager client (or Mock client in CI)
          3. Environment variable fallback
        """
        if use_cache and secret_id in self._cache:
            return self._cache[secret_id]

        # 1. Attempt Secret Manager
        if self.client is not None:
            try:
                sec_path = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
                resp = self.client.access_secret_version(request={"name": sec_path})
                secret_val = resp.payload.data.decode("utf-8").strip()
                self._cache[secret_id] = secret_val
                logger.info(f"Resolved secret '{secret_id}' from Secret Manager.")
                return secret_val
            except Exception as e:
                logger.debug(f"Secret Manager resolution failed for '{secret_id}': {e}")

        # 2. Fallback to Environment Variable
        env_val = os.getenv(secret_id)
        if env_val:
            self._cache[secret_id] = env_val
            return env_val

        raise KeyError(f"Secret '{secret_id}' could not be resolved from Secret Manager or environment.")


# Global vault instance
secrets_vault = SecretManagerVault()
