
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firestore
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'galvanic-pulsar-482815-h0',
    })

db = firestore.client()

TARGET_CLIENT_ID = "1101302170"
NEW_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NjgyMzUxMzUsImlhdCI6MTc2ODE0ODczNSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.YlMQEsP56qmF_lIANKz7lXuNEXgJGiCwsTzwJZmMB21AjVS4BrLcSQpXBbDhJze71rU_azCnTauEFslUkMhQQA"
NEW_API_KEY = "52f6af41" # Provided in prompt (though python lib usually uses client_id/token)
NEW_API_SECRET = "0db595ed-1d47-4a8d-80e5-289812f7e7f4" # Provided

def find_and_update_user():
    print(f"Searching for user with Client ID: {TARGET_CLIENT_ID}")
    
    # Strategy 1: Check 'user_credentials' collection (where profile mapping exists)
    # This collection often maps user_id -> client_id in fields
    # But filtering on fields requires an index. I'll scan (assuming low volume) or try direct lookup if schema allows.
    # Actually, usually 'user_credentials/{user_id}' contains {client_id: ...}
    
    users_ref = db.collection('user_credentials')
    docs = users_ref.stream()
    
    found_uid = None
    
    for doc in docs:
        data = doc.to_dict()
        if data.get('client_id') == TARGET_CLIENT_ID:
            found_uid = doc.id
            print(f"FOUND User ID: {found_uid}")
            break
            
    if not found_uid:
        print("User not found in 'user_credentials'. Checking 'users'...")
        # Fallback: Check 'users' collection
        users_ref = db.collection('users')
        docs = users_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            if data.get('dhanClientId') == TARGET_CLIENT_ID:
                found_uid = doc.id
                print(f"FOUND User ID in 'users': {found_uid}")
                break

    if found_uid:
        print(f"Updating credentials for User ID: {found_uid}...")
        
        creds_ref = db.collection('dhan_credentials').document(found_uid)
        
        # Update/Set the credentials
        creds_data = {
            "client_id": TARGET_CLIENT_ID,
            "access_token": NEW_ACCESS_TOKEN,
            "api_key": NEW_API_KEY, # Storing for completeness
            "api_secret": NEW_API_SECRET, # Storing for completeness
            "is_valid": True,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        creds_ref.set(creds_data, merge=True)
        print("✅ Credentials successfully updated in Firestore.")
        
        # Verify
        updated_doc = creds_ref.get()
        print(f"Verification: {updated_doc.to_dict().get('client_id') == TARGET_CLIENT_ID}")
        
    else:
        print("❌ Could not find a user associated with this Client ID. Cannot update credentials.")
        # Optional: prompt to create? But for now, just report.

if __name__ == "__main__":
    find_and_update_user()
