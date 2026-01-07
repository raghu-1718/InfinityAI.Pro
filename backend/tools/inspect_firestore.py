import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def inspect_credentials():
    logger.info("Scanning 'dhan_credentials'...")
    docs = db.collection("dhan_credentials").stream()
    found = False
    for doc in docs:
        found = True
        data = doc.to_dict()
        logger.info(f"User: {doc.id}")
        # Print keys to verify structure, not values (security)
        logger.info(f"Fields: {list(data.keys())}")
        
        # Check IV length safely
        if 'accessToken' in data:
            try:
                parts = data['accessToken'].split(':')
                iv_hex = parts[0]
                logger.info(f"Access Token IV Length (Hex): {len(iv_hex)} chars ({len(iv_hex)//2} bytes)")
                if len(iv_hex) == 24:
                    logger.info("✅ IV Length Correct (12 bytes)")
                else:
                    logger.error(f"❌ IV Length Incorrect! Expected 24 chars, got {len(iv_hex)}")
            except Exception as e:
                logger.error(f"❌ Malformed Token: {e}")

    if not found:
        logger.warning("⚠️ No credentials found in Firestore.")

if __name__ == "__main__":
    inspect_credentials()
