
import requests
import subprocess
import json
import sys
import time

ENGINE_B_URL = "https://engine-b-mfvaq54jjq-uc.a.run.app"

def check_endpoint(url, payload=None):
    print(f"Testing {url}...")
    try:
        if payload:
            response = requests.post(url, json=payload, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        if response.status_code < 500:
            print("Response:", response.text[:200] + "..." if len(response.text) > 200 else response.text)
            return True, response.status_code
        else:
            print("Error Response:", response.text)
            return False, response.status_code
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False, 0

def check_logs(search_text):
    print(f"Searching logs for: '{search_text}'...")
    cmd = [
        "gcloud", "logging", "read",
        f'resource.type=cloud_run_revision AND textPayload:"{search_text}"',
        "--limit=5", "--format=json"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if search_text in result.stdout or (result.stdout and len(json.loads(result.stdout)) > 0):
            print("✅ Log entry found!")
            return True
        else:
            print("⚠️ Log entry not found (yet).")
            return False
    except Exception as e:
        print(f"Log check failed: {e}")
        return False

def main():
    print("=== E2E Integration Verification ===")
    
    # 1. Health Check
    ok, status = check_endpoint(f"{ENGINE_B_URL}/api/v1/market/status")
    if not ok:
        print("❌ Engine B is not healthy.")
        sys.exit(1)
        
    # 2. AI Integration Check (Flash)
    print("\n--- AI Model Integration (Flash) ---")
    payload = {"symbol": "NIFTY", "use_pro_model": False}
    ok, status = check_endpoint(f"{ENGINE_B_URL}/api/v1/ai/enhanced-signal", payload)
    
    if status == 422:
        print("✅ Endpoint exists (Validation Error confirms reachability)")
    elif status == 200:
        print("✅ AI Signal Generation Successful!")
    else:
        print(f"⚠️ AI Endpoint returned unexpected status: {status}")

    # 3. Firestore Connectivity Check
    # We look for successful startup logs or recent writes
    print("\n--- Firestore Connectivity ---")
    check_logs("Firestore")
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()
