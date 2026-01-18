#!/usr/bin/env python3
"""Check credential freshness for user"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()
uid = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

print(f"Checking credentials for user: {uid}")

doc = db.collection("dhan_credentials").document(uid).get()
if doc.exists:
    data = doc.to_dict()
    updated_at = data.get("updated_at") or data.get("lastUpdatedAt")
    print(f"[OK] Credentials found.")
    print(f"  - Updated At: {updated_at}")
    print(f"  - Connection Status: {data.get('connection_status')}")
    print(f"  - Has API Key: {bool(data.get('apiKey') or (data.get('credentials', {}).get('api_key')))}")
    print(f"  - Has API Secret: {bool(data.get('apiSecret') or (data.get('credentials', {}).get('api_secret')))}")
else:
    print("[ERR] No credentials found.")
