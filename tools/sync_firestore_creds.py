from google.cloud import firestore
from datetime import datetime

db = firestore.Client()

def update_firestore_creds():
    user_id = "B79BqvTlaTZltC8uGO3jLxJBBt93"
    new_client_id = "1101302170"
    new_access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3Njg2NjQzNDAsImlhdCI6MTc2ODU3Nzk0MCwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.d7tffa3tVIlkKuOTbQHZDHDGLHv-VqNiQf6G63u7_6ehh4bpzpWJOPDhtQV0UtF7w4mg_uTHi9JhtGNdurZ5vA"
    new_api_key = "b76a41e2"
    new_api_secret = "3b27c08e-797c-40e4-8e80-0498ea853236"
    
    print(f"Updating Firestore credentials for {user_id}...")
    
    # 1. Update dhan_credentials collection (The Vault)
    creds_ref = db.collection('dhan_credentials').document(user_id)
    creds_ref.set({
        "credentials": {
            "client_id": new_client_id,
            "access_token": new_access_token,
            "api_key": new_api_key,
            "api_secret": new_api_secret,
            "connection_status": "connected" # We verified it works
        },
        "isConnected": True,
        "verified": True,
        "updatedAt": datetime.utcnow()
    }, merge=True)
    print("✅ dhan_credentials updated.")
    
    # 2. Update users collection (Frontend Profile)
    user_ref = db.collection('users').document(user_id)
    user_ref.set({
        "dhanConnected": True,
        "dhanClientId": new_client_id,
        "lastUpdatedAt": datetime.utcnow()
    }, merge=True)
    print("✅ users profile updated.")

if __name__ == "__main__":
    update_firestore_creds()
