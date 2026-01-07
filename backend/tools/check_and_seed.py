
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib

# Init Firestore
if not firebase_admin._apps:
    app = firebase_admin.initialize_app()
db = firestore.client()

code = "INFAI-FAM-DAD"
code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
print(f"Checking Coupon: {code} ({code_hash})")

doc_ref = db.collection('coupons').document(code_hash)
doc = doc_ref.get()

if doc.exists:
    print("✅ Coupon Found!")
    print(f"Active: {doc.to_dict().get('is_active')}")
    print(f"Current Uses: {doc.to_dict().get('current_uses')}")
else:
    print("❌ Coupon NOT FOUND.")
    # Try creating it if missing (recovery)
    print("Attempting to seed...")
    try:
        data = {
            "code_hash": code_hash,
            "code_display": "INFA****DAD",
            "is_active": True,
            "max_uses": 100,
            "current_uses": 0,
            "features": ["dashboard", "trading"]
        }
        doc_ref.set(data)
        print("✅ Seeded INFAI-FAM-DAD")
    except Exception as e:
        print(f"Seeding failed: {e}")
