#!/usr/bin/env python3
"""Clean stale Firestore data for fresh test"""
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Your Firebase UID
uid = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

print("Cleaning stale data...")

# Delete holdings
holdings_ref = db.collection("holdings").document(uid)
items_ref = holdings_ref.collection("items")
for doc in items_ref.stream():
    doc.reference.delete()
    print(f"  Deleted holding: {doc.id}")

holdings_ref.delete()
print("  Deleted holdings document")

# Delete trading sessions
sessions = db.collection("trading_sessions").where("userId", "==", uid).stream()
for session in sessions:
    session.reference.delete()
    print(f"  Deleted session: {session.id}")

print("\nCleanup complete! Refresh the page.")
