"""Check dhan_credentials collection directly."""
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firebase
try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'galvanic-pulsar-482815-h0',
    })

db = firestore.client()

print("=" * 80)
print("CHECKING DHAN_CREDENTIALS COLLECTION")
print("=" * 80)

user_id = "B79BqvTlaTZltC8uGO3jLxJBBt93"

# Check dhan_credentials collection
creds_ref = db.collection('dhan_credentials').document(user_id)
creds_doc = creds_ref.get()

if creds_doc.exists:
    creds_data = creds_doc.to_dict()
    print(f"\n[OK] Credentials found in dhan_credentials collection")
    print(f"\nDocument ID: {user_id}")
    
    # Show fields (but not encrypted values)
    print("\nFields present:")
    for key in creds_data.keys():
        if 'encrypted' in key.lower() or key in ['clientId', 'apiKey', 'apiSecret', 'accessToken']:
            print(f"  - {key}: [ENCRYPTED DATA PRESENT]")
        else:
            print(f"  - {key}: {creds_data[key]}")
    
    print(f"\nTotal fields: {len(creds_data)}")
else:
    print(f"\n[ERROR] No credentials found in dhan_credentials/{user_id}")

# Also check users collection
print("\n" + "=" * 80)
print("CHECKING USERS COLLECTION")
print("=" * 80)

user_ref = db.collection('users').document(user_id)
user_doc = user_ref.get()

if user_doc.exists:
    user_data = user_doc.to_dict()
    print(f"\n[OK] User document found")
    print(f"\ndhanConnected: {user_data.get('dhanConnected', False)}")
    
    if 'dhanCredentials' in user_data:
        print("\n[OK] dhanCredentials metadata found:")
        print(json.dumps(user_data['dhanCredentials'], indent=2, default=str))
    else:
        print("\n[MISSING] dhanCredentials metadata not in user document")
        print("\nThis is expected if you used the old version of the function.")
        print("Please re-store your credentials in the UI one more time.")

print("\n" + "=" * 80)
