"""
In-Memory Mock Secrets Vault for CI/CD and Unit Testing
Mimics the google.cloud.secretmanager.SecretManagerServiceClient API.
"""
from typing import Dict, Optional


class MockSecretPayload:
    def __init__(self, data: str):
        self._data = data.encode("utf-8")

    @property
    def data(self) -> bytes:
        return self._data


class MockSecretResponse:
    def __init__(self, data: str):
        self.payload = MockSecretPayload(data)


class MockSecretManagerClient:
    """
    Hermetic in-memory mock of GCP Secret Manager client.
    Used during CI/CD to prevent live GCP API calls and verify secret retrieval.
    """

    def __init__(self, initial_secrets: Optional[Dict[str, str]] = None):
        self._secrets: Dict[str, str] = initial_secrets or {
            "DHAN_CLIENT_ID": "1101302170",
            "DHAN_ACCESS_TOKEN": "mock-dhan-access-token-jwt-secure",
            "GEMINI_API_KEY": "mock-vertex-gemini-key-placeholder",
            "USER_CREDENTIALS_KEY": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        }

    def set_secret(self, secret_id: str, secret_value: str) -> None:
        self._secrets[secret_id] = secret_value

    def access_secret_version(self, request: dict) -> MockSecretResponse:
        """
        Mimics sm.access_secret_version(request={"name": "projects/.../secrets/{secret_id}/versions/latest"})
        """
        name = request.get("name", "")
        # Extract secret_id from name format
        parts = name.split("/")
        secret_id = None
        for i, p in enumerate(parts):
            if p == "secrets" and i + 1 < len(parts):
                secret_id = parts[i + 1]
                break

        if not secret_id or secret_id not in self._secrets:
            # Fallback: check if the exact string matches
            for k, v in self._secrets.items():
                if k in name:
                    return MockSecretResponse(v)
            raise KeyError(f"Secret '{secret_id or name}' not found in mock vault.")

        return MockSecretResponse(self._secrets[secret_id])
