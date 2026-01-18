import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Initialize Firebase
if not firebase_admin._apps:
    try:
        app = firebase_admin.get_app()
    except ValueError:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': 'galvanic-pulsar-482815-h0',
        })

db = firestore.client()

SOURCE_UID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
TARGET_UID = "B79BqvTlaTZltC8uGO3jLxJBBt93"

def copy_credentials():
    print(f"Copying credentials from {SOURCE_UID} -> {TARGET_UID}")
    
    # 1. Get Source Credentials
    source_ref = db.collection('dhan_credentials').document(SOURCE_UID)
    source_doc = source_ref.get()
    
    if not source_doc.exists:
        print(f"Source document {SOURCE_UID} not found!")
        return
        
    data = source_doc.to_dict()
    print(f"Found source credentials (keys: {list(data.keys())})")
    
    # 2. Update User ID in data
    data['user_id'] = TARGET_UID
    if 'credentials' in data and 'user_id' in data['credentials']: # Check deeply nested
         # It seems from previous log, 'credentials' map didn't have user_id, but the top level did
         pass

    # 3. Write to Target
    target_ref = db.collection('dhan_credentials').document(TARGET_UID)
    target_ref.set(data)
    print(f"Copied credentials to {TARGET_UID}")
    
    # 4. Update User Document
    user_ref = db.collection('users').document(TARGET_UID)
    user_ref.set({
        'dhanConnected': True,
        'dhanClientId': data.get('credentials', {}).get('client_id', 'UNKNOWN'),
        'displayName': 'Test User (Auto-Created)',
        'email': 'test_user_B79B@example.com'
    }, merge=True)
    print(f"Updated user document {TARGET_UID} with dhanConnected=True")

if __name__ == "__main__":
    copy_credentials()
