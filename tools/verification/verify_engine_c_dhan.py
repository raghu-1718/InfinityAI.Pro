import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

# Configuration
ENGINE_C_URL = os.environ.get("ENGINE_C_URL", "https://engine-c-738553258162.asia-south1.run.app")
PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': PROJECT_ID,
            })
        print(f"✅ Firebase Admin initialized for project: {PROJECT_ID}")
        return firestore.client()
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        return None

def verify_user_dhan_status(db, user_id):
    """Check Firestore user document"""
    print(f"\n🔍 Checking Firestore for User: {user_id}")
    try:
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()

        if doc.exists:
            data = doc.to_dict()
            print(f"   📄 User Document Found:")
            print(f"      - Dhan Connected: {data.get('dhanConnected')}")
            print(f"      - Dhan Client ID: {data.get('dhanClientId')}")
            return data.get('dhanConnected')
        else:
            print("   ⚠️ User document does not exist!")
            return False

    except Exception as e:
        print(f"   ❌ Firestore check failed: {e}")
        return False

def check_stored_credentials(user_id):
    """Check if credentials exist in backend (Secret Manager) via API"""
    print(f"\n🔐 Checking Stored Credentials for User: {user_id}")
    try:
        response = requests.get(f"{ENGINE_C_URL}/api/dhan/credentials/{user_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("credentials"):
                creds = data["credentials"]
                print("   ✅ Credentials found in Secret Manager!")
                print(f"      - Client ID: {creds.get('client_id')}")
                print(f"      - Verified Status: {creds.get('is_verified')}")
                print(f"      - Last Updated: {creds.get('updated_at')}")
                return True
            else:
                print(f"   ⚠️ No credentials returned: {data.get('message')}")
                return False
        else:
             print(f"   ❌ API Error: {response.status_code} - {response.text}")
             return False
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def main():
    print("==================================================")
    print("   DHAN INTEGRATION VERIFICATION TOOL")
    print("==================================================")

    # Accept user id via CLI or VERIFY_USER_ID env; otherwise skip gracefully to keep smoke non-blocking.
    user_id = sys.argv[1] if len(sys.argv) >= 2 else os.environ.get("VERIFY_USER_ID")
    if not user_id:
        print("⚠️ No user id provided via args or VERIFY_USER_ID env; skipping Dhan verification smoke.")
        return

    db = init_firebase()
    if not db:
        return

    # 1. Check Firestore
    dhan_connected = verify_user_dhan_status(db, user_id)

    # 2. Check Backend Storage (Secret Manager)
    creds_found = check_stored_credentials(user_id)

    # 3. Summary
    print("\n📊 DIAGNOSIS SUMMARY")
    print("-" * 30)
    print(f"Firestore 'dhanConnected': {dhan_connected}")
    print(f"Secret Manager Credentials: {'FOUND' if creds_found else 'MISSING'}")

    if creds_found and not dhan_connected:
        print("\n🚨 INCONSISTENCY DETECTED!")
        print("   Credentials exist in backend but Firestore flag is False.")
        print("   This confirms the issue. The fix I deployed should resolve this for future connections.")
        print("   To fix this user manually, they simply need to click 'Verify Connection' or 'Save' again in the UI.")
    elif not creds_found and not dhan_connected:
        print("\n✅ System state is consistent (Not Connected).")
    elif creds_found and dhan_connected:
        print("\n✅ System state is consistent (Connected).")


if __name__ == "__main__":
    main()
