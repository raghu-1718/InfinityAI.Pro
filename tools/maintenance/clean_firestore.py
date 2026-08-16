
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as google_firestore

# Initialize
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        "projectId": "project-841b7f97-5ee3-4fbe-920",
    })

db = google_firestore.Client()

# Collections to clean
TARGET_COLLECTIONS = [
    'users',
    'dhan_credentials',
    'user_profiles',
    'user_sessions',
    'redemptions',
    'trading_settings',
    'user_credentials',
    'orders',
    'positions',
    'signals'
]

# Collections to PRESERVE
PRESERVE_COLLECTIONS = ['coupons']

def delete_collection(coll_ref, batch_size=50):
    docs = list(coll_ref.limit(batch_size).stream())
    deleted = 0

    while docs:
        for doc in docs:
            print(f"Deleting doc {doc.id} => {coll_ref.id}")
            doc.reference.delete()
            deleted += 1
        docs = list(coll_ref.limit(batch_size).stream())

    return deleted

def clean_firestore():
    print(f"\n--- STARTING FIRESTORE CLEANUP FOR PROJECT {db.project} ---")
    
    for col_name in TARGET_COLLECTIONS:
        print(f"\nScanning collection: {col_name}...")
        coll_ref = db.collection(col_name)
        deleted_count = delete_collection(coll_ref)
        if deleted_count > 0:
            print(f"[OK] Cleared {deleted_count} documents from '{col_name}'")
        else:
            print(f"[INFO] Collection '{col_name}' was already empty.")

    print("\n--- VERIFYING PRESERVED COLLECTIONS ---")
    for col_name in PRESERVE_COLLECTIONS:
        coll_ref = db.collection(col_name)
        docs = list(coll_ref.stream())
        print(f"Collection '{col_name}' has {len(docs)} documents (PRESERVED).")

    print("\nCLEANUP COMPLETE. System is ready for fresh onboarding.")

if __name__ == "__main__":
    confirm = input("Are you sure you want to DELETE ALL USER DATA? (Type 'yes' to confirm): ")
    if confirm == "yes":
        clean_firestore()
    else:
        print("Cleanup aborted.")
