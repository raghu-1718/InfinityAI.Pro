
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import os
from google.cloud import secretmanager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()
sm_client = secretmanager.SecretManagerServiceClient()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or "gen-lang-client-0779271931"

def debug_dhan_state():
    print(f"\n--- DEBUGGING DHAN STATE (Project: {project_id}) ---")
    
    # 1. List Users in Firestore
    print("\n[1] FIRESTORE 'users' COLLECTION:")
    users = db.collection("users").stream()
    user_count = 0
    for user in users:
        user_count += 1
        data = user.to_dict()
        uid = user.id
        print(f"  User: {uid}")
        print(f"    - dhanConnected: {data.get('dhanConnected')}")
        print(f"    - dhanClientId: {data.get('dhanClientId')}")
        print(f"    - lastUpdatedAt: {data.get('lastUpdatedAt')}")
        
        # Check matching dhan_credentials doc
        dc_ref = db.collection("dhan_credentials").document(uid)
        dc_doc = dc_ref.get()
        if dc_doc.exists:
             print(f"    - [dhan_credentials] Exists: {dc_doc.to_dict()}")
        else:
             print(f"    - [dhan_credentials] MISSING")
             
        # Check Secret Manager
        secret_name = f"user-creds-{uid}"
        full_name = f"projects/{project_id}/secrets/{secret_name}"
        try:
            sm_client.get_secret(request={"name": full_name})
            print(f"    - [SecretManager] Secret '{secret_name}' EXISTS")
            
            # List versions
            versions = sm_client.list_secret_versions(request={"parent": full_name})
            active_versions = [v.name.split('/')[-1] for v in versions if v.state.name == "ENABLED"]
            print(f"      Active Versions: {len(active_versions)} ({', '.join(active_versions)})")
            
        except Exception as e:
            if "NotFound" in str(e):
                print(f"    - [SecretManager] Secret '{secret_name}' NOT FOUND")
            else:
                print(f"    - [SecretManager] Error: {e}")

    if user_count == 0:
        print("  No users found in Firestore.")

    # 2. List all Secrets starting with user-creds-
    print("\n[2] ALL 'user-creds-*' SECRETS IN SECRET MANAGER:")
    try:
        secrets = sm_client.list_secrets(request={"parent": f"projects/{project_id}"})
        found_secrets = False
        for secret in secrets:
            s_name = secret.name.split('/')[-1]
            if s_name.startswith("user-creds-"):
                found_secrets = True
                print(f"  - {s_name}")
        if not found_secrets:
            print("  No 'user-creds-*' secrets found.")
    except Exception as e:
        print(f"  Error listing secrets: {e}")

if __name__ == "__main__":
    debug_dhan_state()
