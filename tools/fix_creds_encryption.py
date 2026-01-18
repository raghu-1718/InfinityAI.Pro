
import os
import logging
from google.cloud import firestore
from google.cloud import secretmanager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = "galvanic-pulsar-482815-h0"
USER_ID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
CREDENTIALS = {
    "client_id": "1101302170",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NjgyMzUxMzUsImlhdCI6MTc2ODE0ODczNSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.YlMQEsP56qmF_lIANKz7lXuNEXgJGiCwsTzwJZmMB21AjVS4BrLcSQpXBbDhJze71rU_azCnTauEFslUkMhQQA",
    "api_key": "52f6af41",
    "api_secret": "0db595ed-1d47-4a8d-80e5-289812f7e7f4"
}

def get_secret_key():
    """Fetch the encryption key from Secret Manager"""
    # HARDCODED RECOVERY KEY (Captured via gcloud CLI)
    secret_data = "e0c704892c203b54433157ba33dc77395066498a442e3434674753086b99"
    # Backend logic: if len != 64, it uses encode(), NOT fromhex()
    # secret_data is 60 chars.
    key_bytes = secret_data.encode() 
    
    # Replicate main.py logic: Ensure key is 32 bytes (via padding with b'0' aka 0x30)
    if len(key_bytes) != 32:
         print(f"Warning: Key length {len(key_bytes)} != 32. Padding/Truncating to 32 bytes.")
         key_bytes = (key_bytes + b'0'*32)[:32]
    
    return key_bytes


def encrypt_data(data, key):
    """Encrypt data using AES-GCM with the provided key"""
    if not data:
        return None
    nonce = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
    return f"{nonce.hex()}:{encryptor.tag.hex()}:{ciphertext.hex()}"

def update_firestore(key):
    """Update Firestore with correctly encrypted credentials"""
    db = firestore.Client(project=PROJECT_ID)
    
    # Encrypt fields
    encrypted_creds = {
        "client_id": CREDENTIALS["client_id"], # Plaintext
        "access_token": encrypt_data(CREDENTIALS["access_token"], key),
        "api_key": encrypt_data(CREDENTIALS["api_key"], key),
        "api_secret": encrypt_data(CREDENTIALS["api_secret"], key)
    }

    doc_data = {
        "user_id": USER_ID,
        "credentials": {
            "client_id": CREDENTIALS["client_id"],
            "access_token": encrypted_creds["access_token"],
            "api_key": encrypted_creds["api_key"],
            "api_secret": encrypted_creds["api_secret"]
        },
        # Flat format for frontend compatibility (encrypted)
        "clientId": encrypt_data(CREDENTIALS["client_id"], key), 
        "accessToken": encrypted_creds["access_token"],
        "apiKey": encrypted_creds["api_key"],
        "apiSecret": encrypted_creds["api_secret"],
        
        "is_active": True,
        "connection_status": "connected",
        "updated_at": firestore.SERVER_TIMESTAMP
    }

    print(f"Updating credentials for {USER_ID}...")
    db.collection("dhan_credentials").document(USER_ID).set(doc_data, merge=True)
    print("✅ Credentials updated successfully!")

if __name__ == "__main__":
    print("Fetching key...")
    real_key = get_secret_key()
    print(f"Key fetched (len={len(real_key)})")
    
    update_firestore(real_key)
