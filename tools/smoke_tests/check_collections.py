#!/usr/bin/env python3
"""
Simple smoke tests to inspect key Firestore collections used by InfinityAI.Pro

Usage:
  python check_collections.py

Requirements:
  pip install google-cloud-firestore
  set GOOGLE_APPLICATION_CREDENTIALS to a service account with Firestore access
"""
from google.cloud import firestore
import os

def print_doc(ref):
    doc = ref.get()
    if not doc.exists:
        print("  (no document)")
        return
    data = doc.to_dict()
    print("  id:", doc.id)
    for k,v in data.items():
        print(f"   - {k}: {str(v)[:200]}")

def main():
    print("Connecting to Firestore...")
    db = firestore.Client()

    collections = [
        ("dhan_credentials", "Per-user encrypted credentials (frontend)") ,
        ("user_credentials", "Engine-C backend credentials store"),
        ("holdings", "Holdings root collection - contains per-user docs and items subcollections"),
        ("trading_sessions", "Active/past trading sessions") ,
        ("generate", "Gemini/analysis documents"),
        ("activity_logs", "Audit/activity logs from engines")
    ]

    for coll,desc in collections:
        print(f"\nCollection: {coll} - {desc}")
        docs = db.collection(coll).limit(5).order_by("_", direction=firestore.Query.DESCENDING).stream()
        found = False
        for doc in docs:
            found = True
            print(f"- doc: {doc.id}")
            data = doc.to_dict()
            keys = list(data.keys())[:8]
            for k in keys:
                val = data.get(k)
                print(f"    {k}: {str(val)[:200]}")
        if not found:
            print("  (no documents or unable to list)" )

    # Special: show holdings items for first user if exists
    try:
        users = db.collection("holdings").limit(3).stream()
        for u in users:
            uid = u.id
            print(f"\nHoldings for user {uid} (items):")
            items = db.collection("holdings").document(uid).collection("items").limit(10).stream()
            for it in items:
                print(f" - {it.id}: {str(it.to_dict())[:200]}")
            break
    except Exception as e:
        print("Could not fetch holdings items:", e)

if __name__ == '__main__':
    main()
