import firebase_admin
from firebase_admin import credentials, firestore
import json
import logging

logging.basicConfig(level=logging.INFO)

# Use Application Default Credentials
try:
    if not firebase_admin._apps:
        app = firebase_admin.initialize_app()
    db = firestore.client()
    logging.info("Firebase app initialized and Firestore client created.")
except Exception as e:
    logging.error(f"Failed to initialize Firebase: {e}")
    exit(1)

status_report = {
    "firestore_structure": {},
    "recent_signals": [],
    "recent_users": []
}

try:
    # Check 'market_data' collection
    logging.info("Checking 'market_data' collection...")
    market_docs = list(db.collection('market_data').limit(5).stream())
    status_report["firestore_structure"]["market_data"] = {
        "count": len(market_docs),
        "sample_ids": [d.id for d in market_docs]
    }
    
    # Check 'signals' collection
    logging.info("Checking 'signals' collection...")
    signal_docs = list(db.collection('signals').order_by('generated_at', direction=firestore.Query.DESCENDING).limit(5).stream())
    status_report["recent_signals"] = [d.to_dict() for d in signal_docs]
    
    # Check 'users' collection (limited fields for privacy)
    logging.info("Checking 'users' collection...")
    user_docs = list(db.collection('users').limit(5).stream())
    status_report["recent_users"] = [{"uid": d.id, "email": d.to_dict().get("email")} for d in user_docs]

    print(json.dumps(status_report, indent=2, default=str))

except Exception as e:
    logging.error(f"Error accessing Firestore: {e}")
    exit(1)
