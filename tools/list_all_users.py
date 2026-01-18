"""List all users in Firestore to see what user IDs exist."""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
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
print("ALL USERS IN FIRESTORE")
print("=" * 80)

users_ref = db.collection('users')
users = list(users_ref.stream())

print(f"\n Found {len(users)} user(s) in Firestore:\n")

for user in users:
    user_data = user.to_dict()
    print(f"User ID (Firebase UID): {user.id}")
    print(f"   Created: {user_data.get('createdAt', 'N/A')}")
    print(f"   Email: {user_data.get('email', 'N/A')}")
    
    if 'dhanCredentials' in user_data:
        dhan_creds = user_data['dhanCredentials']
        print(f"   [DhanHQ] Client ID: {dhan_creds.get('clientId', 'N/A')}")
        print(f"   [DhanHQ] Last Updated: {dhan_creds.get('lastUpdated', 'N/A')}")
        if 'encryptedAccessToken' in dhan_creds:
            print(f"   [DhanHQ] Access Token: Present ({len(dhan_creds['encryptedAccessToken'])} chars)")
    
    if 'tradingEnabled' in user_data:
        print(f"   Trading Enabled: {user_data.get('tradingEnabled', False)}")
        print(f"   Last Trading Action: {user_data.get('lastTradingAction', 'N/A')}")
    
    print("-" * 80)

print("\n" + "=" * 80)
