#!/usr/bin/env python3
"""Test available Dhan credentials and endpoints"""

from google.cloud import firestore
import os
import sys

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ["GOOGLE_CLOUD_PROJECT"] = "galvanic-pulsar-482815-h0"

try:
    db = firestore.Client()

    print("=" * 70)
    print("DHAN_CREDENTIALS COLLECTION (Frontend - Encrypted):")
    print("=" * 70)

    docs = list(db.collection("dhan_credentials").stream())

    if docs:
        found_users = []
        for doc in docs:
            data = doc.to_dict()
            user_id = data.get("user_id", doc.id)
            found_users.append(user_id)
            print(f"\nFound credential doc: {doc.id}")
            print(f"  User ID: {user_id}")
            print(f"  Status: {data.get('connection_status', 'unknown')}")
            print(f"  Is Active: {data.get('is_active', False)}")
            print(f"  Created: {data.get('created_at', 'N/A')}")

        print(f"\n\nTest Users Available: {len(found_users)}")
        for uid in found_users:
            print(f"  - {uid}")
    else:
        print("No credentials found in dhan_credentials collection")

    # Check user_credentials backend store
    print("\n" + "=" * 70)
    print("USER_CREDENTIALS COLLECTION (Backend - Engine C):")
    print("=" * 70)

    user_docs = list(db.collection("user_credentials").stream())

    if user_docs:
        print(f"Found {len(user_docs)} backend credential docs:")
        for doc in user_docs:
            print(f"  - {doc.id}")
    else:
        print("No backend credentials found (expected - they are created on-demand)")

    # Try to get numeric client_id mapping
    print("\n" + "=" * 70)
    print("CHECKING NUMERIC CLIENT_ID (1101302170):")
    print("=" * 70)

    user_doc = db.collection("user_credentials").document("1101302170").get()
    if user_doc.exists:
        print("Found user_credentials/1101302170")
    else:
        print("user_credentials/1101302170 not found (will be created on first API call)")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
