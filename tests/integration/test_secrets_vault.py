"""
Integration Tests for Secrets Vault & Pre-Commit Scanner
"""
import pytest
from pathlib import Path
from vault.mock_vault import MockSecretManagerClient
from vault.secret_manager import SecretManagerVault
from vault.crypto_vault import AES256Vault
from vault.precommit.check_secrets import scan_file, SECRET_PATTERNS


def test_mock_vault_retrieval_in_ci():
    """Verify secret retrieval works via MockSecretManagerClient in CI environments."""
    mock_client = MockSecretManagerClient({
        "DHAN_CLIENT_ID": "1101302170",
        "DHAN_ACCESS_TOKEN": "mock-token-xyz-9876",
        "GEMINI_API_KEY": "AIzaSyMockKeyForGeminiApiIntegration"
    })
    vault = SecretManagerVault(project_id="test-project", client=mock_client)

    # 1. Retrieve secrets
    client_id = vault.get_secret("DHAN_CLIENT_ID")
    access_token = vault.get_secret("DHAN_ACCESS_TOKEN")
    gemini_key = vault.get_secret("GEMINI_API_KEY")

    assert client_id == "1101302170"
    assert access_token == "mock-token-xyz-9876"
    assert gemini_key == "AIzaSyMockKeyForGeminiApiIntegration"

    # 2. Verify cache hit on second retrieval
    cached_val = vault.get_secret("DHAN_CLIENT_ID")
    assert cached_val == "1101302170"


def test_aes_256_gcm_vault_encrypt_decrypt_roundtrip():
    """Verify AES-256-GCM encryption, decryption, and tamper detection."""
    test_key = b"0123456789abcdef0123456789abcdef"
    vault = AES256Vault(key=test_key)

    plaintext = '{"client_id": "1101302170", "pin": "9876", "totp": "123456"}'
    ciphertext = vault.encrypt(plaintext)

    assert isinstance(ciphertext, str)
    assert ciphertext != plaintext

    # Decrypt and verify equality
    decrypted = vault.decrypt(ciphertext)
    assert decrypted == plaintext

    # Tamper test: Altering ciphertext must raise error due to GCM authentication tag
    tampered_ciphertext = ciphertext[:-4] + "AAAA"
    with pytest.raises(Exception):
        vault.decrypt(tampered_ciphertext)


def test_precommit_scanner_detects_prohibited_patterns(tmp_path: Path):
    """Verify pre-commit scanner detects synthetic credentials and private keys."""
    dirty_file = tmp_path / "leaked_credentials.py"
    dirty_file.write_text("""
# Hardcoded API key leak simulation
DHAN_API_SECRET = "abcdef1234567890abcdef1234"
""")
    findings = scan_file(dirty_file)
    assert len(findings) == 1
    assert "Hardcoded DhanHQ Credential" in findings[0][1]


def test_precommit_scanner_ignores_placeholders(tmp_path: Path):
    """Verify scanner does not flag placeholder templates."""
    clean_file = tmp_path / ".env.template"
    clean_file.write_text("""
DHAN_CLIENT_ID=your-dhan-client-id
DHAN_API_SECRET=your-dhan-api-secret
""")
    findings = scan_file(clean_file)
    assert len(findings) == 0
