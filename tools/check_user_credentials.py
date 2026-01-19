#!/usr/bin/env python3
"""
Check user credentials in Firestore
"""
import os
os.environ['GOOGLE_CLOUD_PROJECT'] = 'galvanic-pulsar-482815-h0'

from google.cloud import firestore

db = firestore.Client(project='galvanic-pulsar-482815-h0')

user_id = "raghuyuvi10@gmail.com"

print(f"🔍 Checking credentials for: {user_id}\n")

# Check users collection
print("=" * 60)
print("1. Checking users/{user_id}...")
print("=" * 60)
try:
    user_doc = db.collection('users').document(user_id).get()
    if user_doc.exists:
        data = user_doc.to_dict()
        print(f"✅ Found user document")
        print(f"   dhanConnected: {data.get('dhanConnected', False)}")
        print(f"   dhanCredentials: {data.get('dhanCredentials', {})}")
    else:
        print(f"❌ No document found in users collection")
except Exception as e:
    print(f"❌ Error: {e}")

# Check dhan_credentials collection
print("\n" + "=" * 60)
print("2. Checking dhan_credentials/{user_id}...")
print("=" * 60)
try:
    creds_doc = db.collection('dhan_credentials').document(user_id).get()
    if creds_doc.exists:
        data = creds_doc.to_dict()
        print(f"✅ Found credentials document")
        print(f"   Keys: {list(data.keys())}")
        print(f"   Has clientId: {'clientId' in data or 'client_id' in data}")
        print(f"   Has accessToken: {'accessToken' in data or 'access_token' in data}")
        print(f"   userId: {data.get('userId', 'N/A')}")
    else:
        print(f"❌ No document found in dhan_credentials collection")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If credentials are in 'dhan_credentials' collection but Engine-C")
print("returns 'not configured', this indicates Engine-C is reading from")
print("a different location or the document structure doesn't match.")
