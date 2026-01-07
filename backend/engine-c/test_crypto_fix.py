import os
import sys
import logging
from unittest.mock import MagicMock

# Mock Firestore BEFORE importing the module that uses it
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.firestore"] = MagicMock()
sys.modules["google.cloud.secretmanager"] = MagicMock()

# Now import valid classes
from src.user_credentials import UserCredentialsManager, get_encryption_key

# Mock Environment
os.environ["ENCRYPTION_KEY"] = "758c6bfc504fbffce67090816617dbfb6556770c3e5105fe40b7f69a37d4f5ee"

# Inputs from Node.js generation
IV_HEX = "dd346af1964175317be93845"
TAG_HEX = "773cf0a0456d8183fc47566c68c7b21a"
CIPHER_HEX = "acc41650f17632f4c69bc741"

# Constructed format
ENCRYPTED_STRING = f"{IV_HEX}:{TAG_HEX}:{CIPHER_HEX}"
EXPECTED_PLAINTEXT = "TopSecret123"

def test_decryption():
    print(f"Testing decryption of: {ENCRYPTED_STRING}")
    
    manager = UserCredentialsManager()
    print(f"DEBUG: Manager Key: {manager.encryption_key.hex()}")
    
    try:
        decrypted = manager._decrypt(ENCRYPTED_STRING)
        print(f"Decrypted: {decrypted}")
        
        if decrypted == EXPECTED_PLAINTEXT:
            print("SUCCESS: Decryption matched plaintext.")
        else:
            print(f"FAILURE: Mismatch. Got {decrypted}")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")

def test_encryption_cycle():
    print("\nTesting full encryption cycle (Python -> Python)...")
    manager = UserCredentialsManager()
    original = "PythonMessage"
    try:
        encrypted = manager._encrypt(original)
        print(f"Encrypted (Py): {encrypted}")
        # Inspect format
        parts = encrypted.split(':')
        print(f"Py-Generated Parts: IVLen={len(parts[0])}, TagLen={len(parts[1])}, CipherLen={len(parts[2])}")
        
        decrypted = manager._decrypt(encrypted)
        
        if decrypted == original:
            print("SUCCESS: Cycle complete.")
        else:
            print(f"FAILURE: Cycle mismatch. Got {decrypted}")
    except Exception as e:
        print(f"EXCEPTION Cycle: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_decryption()
    test_encryption_cycle()
