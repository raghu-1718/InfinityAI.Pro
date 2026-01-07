
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone

# Init Firestore
if not firebase_admin._apps:
    app = firebase_admin.initialize_app()
db = firestore.client()

def utcnow():
    return datetime.now(timezone.utc)

def reset_coupons():
    print("--- 🗑️  DELETING OLD COUPONS ---")
    coll = db.collection('coupons')
    docs = coll.stream()
    deleted = 0
    for doc in docs:
        print(f"Deleting {doc.id}")
        doc.reference.delete()
        deleted += 1
    print(f"Deleted {deleted} coupons.")

    print("\n--- 🌱 SEEDING NEW COUPONS ---")
    new_coupons = [
        "INFINITY1718", "INFINITY0506", 
        "INFINITYRAJ", "INFINITYMOM", "INFINITYDAD", 
        "INFINITYKAVI", "INFINITYHARSHA", "INIFINTYSAI", "INFINITYPRI"
    ]

    for code in new_coupons:
        # Plain text Key as requested
        doc_ref = coll.document(code) 
        data = {
            "code_id": code,
            "code_display": code,
            "description": "InfinityAI Family Access",
            "max_uses": 1, # Strict 1-user limit
            "current_uses": 0,
            "is_active": True,
            "expires_at": utcnow() + timedelta(days=3650),
            "created_at": utcnow(),
            "features": ["dashboard", "trading", "signals", "ai_analysis", "family_plan"],
            "assigned_email": None, # Open for first claimant
            "used_by": []
        }
        doc_ref.set(data)
        print(f"✅ Created {code}")

if __name__ == "__main__":
    reset_coupons()
