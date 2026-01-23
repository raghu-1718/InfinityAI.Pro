
import firebase_admin
from firebase_admin import credentials, firestore
import json
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_firestore_credentials(user_id="B79BqvTlaTZltC8uGO3jLxJBBt93"):
    """
    Fetch and display Firestore credentials for verification.
    Note: Real credentials are encrypted.
    """
    try:
        # Initialize Firebase (if not already)
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': 'galvanic-pulsar-482815-h0',
            })
        
        db = firestore.client()
        
        print(f"\n--- Checking Firestore Credentials for User: {user_id} ---")
        
        doc_ref = db.collection('dhan_credentials').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            print("✅ Document Exists!")
            print(f"ID: {doc.id}")
            print(f"Created At: {data.get('created_at')}")
            print(f"Updated At: {data.get('updated_at')}")
            print(f"Is Active: {data.get('is_active')}")
            print(f"Connection Status: {data.get('connection_status')}")
            
            # Check for fields (without printing sensitive encrypted values fully)
            creds = data.get('credentials', {})
            print("\nCredentials Fields Present:")
            print(f"  - Client ID: {'✅ Present' if creds.get('client_id') else '❌ Missing'}")
            print(f"  - Access Token: {'✅ Encrypted' if creds.get('access_token') else '❌ Missing'}")
            print(f"  - API Key: {'✅ Encrypted' if creds.get('api_key') else '❌ Missing'}")
            print(f"  - API Secret: {'✅ Encrypted' if creds.get('api_secret') else '❌ Missing'}")
            
            # Check for flat fields (Frontend compatibility)
            print("\nFrontend Compat Fields:")
            print(f"  - clientId: {'✅ Encrypted' if data.get('clientId') else '❌ Missing'}")
            print(f"  - accessToken: {'✅ Encrypted' if data.get('accessToken') else '❌ Missing'}")
            
        else:
            print("❌ Document NOT Found!")
            
    except Exception as e:
        print(f"❌ Error fetching Firestore data: {e}")

if __name__ == "__main__":
    check_firestore_credentials()
