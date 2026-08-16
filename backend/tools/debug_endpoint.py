
import requests
import json
import logging
import os
import time

# Create a custom logger
logger = logging.getLogger("debugger")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

ENGINE_C_URL = "https://engine-c-mfvaq54jjq-uc.a.run.app"
TEST_USER_ID = "debug_user_123"
TEST_CLIENT_ID = "1101302170" # Use a plausible ID
# Fake credentials (will fail verification, but should save if validation allows)
TEST_PAYLOAD = {
    "user_id": TEST_USER_ID,
    "client_id": TEST_CLIENT_ID,
    "api_key": "debug_key",
    "api_secret": "debug_secret",
    "access_token": "debug_token"
}

def test_save_endpoint():
    print("\n--- TEST: Call Endpoint Directly ---")
    url = f"{ENGINE_C_URL}/api/dhan/credentials"
    try:
        print(f"POST {url}")
        resp = requests.post(url, json=TEST_PAYLOAD)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        return data.get("success")
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def check_secret_manager():
    print("\n--- TEST: Check Secret Manager ---")
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or "gen-lang-client-0779271931"
    
    secret_name = f"projects/{project_id}/secrets/user-creds-{TEST_USER_ID}"
    try:
        client.get_secret(request={"name": secret_name})
        print("✅ Secret EXISTS in SM.")
        
        # Cleanup
        print("Cleaning up secret...")
        client.delete_secret(request={"name": secret_name})
        print("Secret deleted.")
        return True
    except Exception as e:
        print(f"❌ Secret NOT FOUND in SM: {e}")
        return False

def check_firestore():
    print("\n--- TEST: Check Google Cloud Firestore ---")
    try:
        from google.cloud import firestore
        import os
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
        db = firestore.Client(project=project_id)
        doc = db.collection("users").document(TEST_USER_ID).get()
        if doc.exists:
            print("✅ User Profile Exists in Firestore")
            return True
        else:
            print("❌ User Profile NOT FOUND in Firestore")
            return False
    except Exception as e:
        print(f"❌ Firestore check failed: {e}")
        return False

if __name__ == "__main__":
    success = test_save_endpoint()
    time.sleep(2)
    check_firestore()
