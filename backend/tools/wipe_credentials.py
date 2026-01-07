import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase (Implicit Auth)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def wipe_collection(collection_name):
    logger.info(f"Scanning collection: {collection_name}")
    docs = db.collection(collection_name).stream()
    count = 0
    for doc in docs:
        logger.info(f"Deleting doc: {doc.id}")
        doc.reference.delete()
        count += 1
    logger.info(f"Deleted {count} documents from {collection_name}")

if __name__ == "__main__":
    print("WARNING: This will wipe credential data.")
    # Wipe both potential collection names just in case
    wipe_collection("user_credentials")
    wipe_collection("dhan_credentials")
    print("✅ Firestore cleanup complete.")
