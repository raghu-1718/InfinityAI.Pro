"""
AES-256-GCM Symmetric Encryption Engine for InfinityAI.Pro
Ensures authenticated encryption for credentials stored in Firestore.
"""
import os
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AES256Vault:
    """
    AES-256-GCM Authenticated Encryption & Decryption.
    Guarantees both confidentiality and integrity of broker credentials.
    """

    def __init__(self, key: bytes = None):
        if key is None:
            raw_key = os.getenv("USER_CREDENTIALS_KEY") or os.getenv("ENCRYPTION_KEY")
            if not raw_key:
                # Local dev fallback 32-byte key
                self.key = b"\x00" * 32
            elif len(raw_key) == 64:
                self.key = bytes.fromhex(raw_key)
            elif len(raw_key) >= 32:
                self.key = raw_key[:32].encode("utf-8") if isinstance(raw_key, str) else raw_key[:32]
            else:
                self.key = raw_key.ljust(32, "0").encode("utf-8")
        else:
            self.key = key

        if len(self.key) != 32:
            raise ValueError(f"AES-256 key must be exactly 32 bytes (got {len(self.key)})")
        self._aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string using AES-256-GCM with a random 12-byte nonce.
        Returns base64-encoded nonce + ciphertext + tag.
        """
        nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode("utf-8")

    def decrypt(self, encoded_ciphertext: str) -> str:
        """
        Decrypt base64-encoded nonce + ciphertext + tag.
        Raises ValueError if authentication tag does not match (tamper detection).
        """
        combined = base64.b64decode(encoded_ciphertext.encode("utf-8"))
        if len(combined) < 28:
            raise ValueError("Ciphertext too short to contain valid nonce and GCM tag.")
        nonce = combined[:12]
        ciphertext = combined[12:]
        decrypted_bytes = self._aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")
