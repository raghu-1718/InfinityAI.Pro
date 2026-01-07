
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Use default credentials (should work in Cloud Shell/local if authenticated)
if not firebase_admin._apps:
    app = firebase_admin.initialize_app()

db = firestore.client()

print("--- Checking Coupons Collection ---")
try:
    coupons = db.collection('coupons').get()
    if not coupons:
        print("No coupons found in 'coupons' collection.")
    else:
        for c in coupons:
            data = c.to_dict()
            print(f"ID: {c.id}")
            print(f"  Code Display: {data.get('code_display')}")
            print(f"  Active: {data.get('is_active')}")
            print(f"  Expires: {data.get('expires_at')}")
            print(f"  Features: {data.get('features')}")
except Exception as e:
    print(f"Error reading coupons: {e}")

print("\n--- Checking Coupon Sessions ---")
try:
    sessions = db.collection('coupon_sessions').limit(5).get()
    for s in sessions:
        print(f"Session {s.id}: {s.to_dict().get('user_id')}")
except Exception as e:
    print(f"Error reading sessions: {e}")
