
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase (Implicit Auth)
if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()

USER_ID = "B79BqvTlaTZltC8uGO3jLxJBBt93"
SANDBOX_CLIENT_ID = "2508215064"
SANDBOX_ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"

# Update 'dhan_credentials' collection
print(f"Updating credentials for {USER_ID}...")
creds_ref = db.collection("dhan_credentials").document(USER_ID)
creds_ref.set({
    "client_id": SANDBOX_CLIENT_ID,
    "access_token": SANDBOX_ACCESS_TOKEN,
    "status": "active",
    "mode": "sandbox",
    "updated_at": datetime.utcnow()
}, merge=True)

# Update 'users' main document metadata
print("Updating user metadata...")
user_ref = db.collection("users").document(USER_ID)
user_ref.set({
    "dhanClientId": SANDBOX_CLIENT_ID,
    "dhanConnected": True,
    "tradingMode": "sandbox"
}, merge=True)

print("✅ Sandbox credentials applied successfully!")
