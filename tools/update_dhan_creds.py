"""
Update Dhan Credentials Tool for InfinityAI.Pro
Updates user credentials in Firestore using environment variables.
"""
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
    firebase_admin.initialize_app(cred, {
        'projectId': project_id,
    })

db = firestore.client()

TARGET_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
NEW_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
NEW_API_KEY = os.getenv("DHAN_API_KEY", "")
NEW_API_SECRET = os.getenv("DHAN_API_SECRET", "")

def find_and_update_user():
    if not TARGET_CLIENT_ID or not NEW_ACCESS_TOKEN:
        print("⚠️ Environment variables DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN are required.")
        sys.exit(0)

    print(f"Searching for user with Client ID: {TARGET_CLIENT_ID}")
    
    users_ref = db.collection('user_credentials')
    docs = users_ref.stream()
    
    found_uid = None
    for doc in docs:
        data = doc.to_dict()
        if data.get('dhan_client_id') == TARGET_CLIENT_ID or data.get('client_id') == TARGET_CLIENT_ID:
            found_uid = doc.id
            print(f"FOUND User ID: {found_uid}")
            break

    if found_uid:
        print(f"Updating credentials for User ID: {found_uid}...")
        creds_ref = db.collection('user_credentials').document(found_uid)
        creds_data = {
            "dhan_client_id": TARGET_CLIENT_ID,
            "dhan_access_token": NEW_ACCESS_TOKEN,
            "api_key": NEW_API_KEY,
            "api_secret": NEW_API_SECRET,
            "is_valid": True,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        creds_ref.set(creds_data, merge=True)
        print("✅ Credentials successfully updated in Firestore.")
    else:
        print("❌ User ID not found.")

if __name__ == "__main__":
    find_and_update_user()
