
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json

# Init Firestore
if not firebase_admin._apps:
    app = firebase_admin.initialize_app()
db = firestore.client()

code = "INFINITYDAD"
print(f"Checking Coupon: {code}")

doc_ref = db.collection('coupons').document(code) # Plain Text ID
doc = doc_ref.get()

if doc.exists:
    print("✅ Coupon Found in Firestore!")
    data = doc.to_dict()
    print(f"Active: {data.get('is_active')}")
    print(f"Uses: {data.get('current_uses')}/{data.get('max_uses')}")
    print(f"Assigned: {data.get('assigned_email')}")
else:
    print("❌ Coupon NOT FOUND in Firestore.")

print("\n--- Live Endpoint Check ---")
url = "https://infinityai.pro/api/auth/coupon/verify"
payload = {
    "coupon_code": code,
    "google_user_id": "test_verification_script",
    "google_email": "test@infinityai.pro"
}

print(f"POST {url}")
try:
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    print(f"Status: {resp.status_code}")
    print("Response:")
    print(resp.text)
except Exception as e:
    print(f"Request failed: {e}")
