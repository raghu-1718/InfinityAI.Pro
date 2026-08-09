"""
Sync Firestore Credentials Tool for InfinityAI.Pro
Updates user credentials using Environment Variables or GCP Secret Manager.
"""
import os
import sys
from google.cloud import firestore
from datetime import datetime

def update_firestore_creds():
    user_id = os.getenv("USER_ID", "default_user")
    new_client_id = os.getenv("DHAN_CLIENT_ID")
    new_access_token = os.getenv("DHAN_ACCESS_TOKEN")
    new_api_key = os.getenv("DHAN_API_KEY", "")
    new_api_secret = os.getenv("DHAN_API_SECRET", "")
    
    if not new_client_id or not new_access_token:
        print("⚠️ Environment variables DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN required!")
        sys.exit(0)

    db = firestore.Client()
    print(f"Updating Firestore credentials for user: {user_id}...")
    
    # 1. Update user_credentials collection (The Vault)
    creds_ref = db.collection('user_credentials').document(user_id)
    creds_ref.set({
        "dhan_client_id": new_client_id,
        "dhan_access_token": new_access_token,
        "api_key": new_api_key,
        "api_secret": new_api_secret,
        "isConnected": True,
        "updated_at": datetime.utcnow().isoformat()
    }, merge=True)
    print("✅ user_credentials updated.")
    
    # 2. Update users collection (Frontend Profile)
    user_ref = db.collection('users').document(user_id)
    user_ref.set({
        "dhanConnected": True,
        "dhanClientId": new_client_id,
        "lastUpdatedAt": datetime.utcnow().isoformat()
    }, merge=True)
    print("✅ users profile updated.")

if __name__ == "__main__":
    update_firestore_creds()
