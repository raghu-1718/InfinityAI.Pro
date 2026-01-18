#!/usr/bin/env python3
"""Check what credentials are stored in Firestore for the user"""
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

# User ID
uid = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

print(f"Checking credentials for user: {uid}\n")

# Check dhan_credentials collection
creds_ref = db.collection("dhan_credentials").document(uid)
creds_doc = creds_ref.get()

if creds_doc.exists:
    data = creds_doc.to_dict()
    print("[OK] Found in dhan_credentials:")
    print(f"  - Has client_id: {('clientId' in data) or ('client_id' in data)}")
    print(f"  - Has access_token: {('accessToken' in data) or ('access_token' in data)}")
    print(f"  - Has api_key: {('apiKey' in data) or ('api_key' in data)}")
    print(f"  - Has api_secret: {('apiSecret' in data) or ('api_secret' in data)}")
    print(f"\n  Fields: {list(data.keys())}")
else:
    print("[ERR] NOT found in dhan_credentials")

# Also check user_credentials collection (legacy)
user_creds_ref = db.collection("user_credentials").document(uid)
user_creds_doc = user_creds_ref.get()

if user_creds_doc.exists:
    data = user_creds_doc.to_dict()
    print("\n[OK] Found in user_credentials (legacy):")
    print(f"  Fields: {list(data.keys())}")
else:
    print("\n[ERR] NOT found in user_credentials")
