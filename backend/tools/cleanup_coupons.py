"""
Cleanup script: Delete non-INFAI coupons from Firestore.
Retains only INFAI-FAM-* coupons for production use.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

# Init Firestore
if not firebase_admin._apps:
    app = firebase_admin.initialize_app()
db = firestore.client()

# Coupons to DELETE (all non-INFAI)
COUPONS_TO_DELETE = [
    "INFINITY0506",
    "INFINITY1718",
    "INFINITYDAD",
    "INFINITYHARSHA",
    "INFINITYKAVI",
    "INFINITYMOM",
    "INFINITYPRI",
    "INFINITYRAJ",
    "INIFINTYSAI",  # Typo version
]

# Coupons to KEEP (INFAI-FAM-*)
COUPONS_TO_KEEP = [
    "INFAI-FAM-0506",
    "INFAI-FAM-1718",
    "INFAI-FAM-CHOTU",
    "INFAI-FAM-DAD",
    "INFAI-FAM-HARSHA",
    "INFAI-FAM-KAVI",
    "INFAI-FAM-MOM",
    "INFAI-FAM-PRI",
    "INFAI-FAM-RAJ",
    "INFAI-FAM-SAI",
]

def cleanup():
    print("=" * 60)
    print("🗑️  COUPON CLEANUP: Removing non-INFAI coupons")
    print("=" * 60)
    
    print(f"\n📋 DELETING {len(COUPONS_TO_DELETE)} coupons:")
    for code in COUPONS_TO_DELETE:
        print(f"   - {code}")
    
    print(f"\n✅ KEEPING {len(COUPONS_TO_KEEP)} INFAI-FAM-* coupons")
    
    # Delete non-INFAI coupons
    deleted_count = 0
    for code in COUPONS_TO_DELETE:
        try:
            doc_ref = db.collection('coupons').document(code)
            doc_ref.delete()
            print(f"  ✓ Deleted {code}")
            deleted_count += 1
        except Exception as e:
            print(f"  ✗ Failed to delete {code}: {e}")
    
    print(f"\n✅ Deleted {deleted_count}/{len(COUPONS_TO_DELETE)} coupons.")
    
    # Verify KEEP coupons still exist
    print(f"\n🔍 Verifying {len(COUPONS_TO_KEEP)} INFAI-FAM-* coupons remain...")
    verified_count = 0
    for code in COUPONS_TO_KEEP:
        try:
            doc_ref = db.collection('coupons').document(code)
            doc = doc_ref.get()
            if doc.exists:
                print(f"  ✓ {code} exists")
                verified_count += 1
            else:
                print(f"  ✗ {code} NOT FOUND")
        except Exception as e:
            print(f"  ✗ Error checking {code}: {e}")
    
    print(f"\n✅ Verified {verified_count}/{len(COUPONS_TO_KEEP)} INFAI-FAM-* coupons.")
    
    # Final state
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"Total coupons deleted: {deleted_count}")
    print(f"Total INFAI coupons retained: {verified_count}")

if __name__ == "__main__":
    cleanup()
