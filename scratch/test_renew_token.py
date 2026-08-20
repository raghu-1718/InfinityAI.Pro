import os
import sys
import json
import requests
from google.cloud import firestore

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def log(msg):
    try:
        print(msg, flush=True)
    except Exception:
        print(msg.encode('ascii', errors='replace').decode('ascii'), flush=True)

def main():
    log("="*70)
    log("[TEST] TESTING DHAN TOKEN RENEWAL (ENGINE C & DHAN API)")
    log("="*70)

    # 1. Trigger Engine C Token Renewal Endpoint
    engine_c_url = "https://engine-c-313407263327.asia-south1.run.app/api/dhan/renew-token?user_id=raghu_primary"
    log(f"\n1. Calling Engine C endpoint: {engine_c_url}")
    try:
        r = requests.post(engine_c_url, timeout=15)
        log(f"   - HTTP Status: {r.status_code}")
        log(f"   - Response: {r.text}")
    except Exception as e:
        log(f"❌ Engine C call error: {e}")

    # 2. Try Direct DhanHQ RenewToken API
    log("\n2. Trying Direct DhanHQ RenewToken API call...")
    db = firestore.Client(project="project-841b7f97-5ee3-4fbe-920")
    doc = db.collection("user_credentials").document("raghu_primary").get()
    if doc.exists:
        data = doc.to_dict()
        client_id = data.get("dhan_client_id") or data.get("client_id")
        access_token = data.get("dhan_access_token") or data.get("access_token")
        
        headers = {
            "dhanClientId": str(client_id),
            "access-token": str(access_token)
        }
        
        # Test GET /RenewToken
        try:
            dhan_resp = requests.get("https://api.dhan.co/v2/RenewToken", headers=headers, timeout=10)
            log(f"   - Dhan GET /RenewToken: HTTP {dhan_resp.status_code}")
            log(f"   - Body: {dhan_resp.text}")
        except Exception as e:
            log(f"❌ Direct Dhan GET error: {e}")

        # Test POST /RenewToken
        try:
            dhan_resp_post = requests.post("https://api.dhan.co/v2/RenewToken", headers=headers, timeout=10)
            log(f"   - Dhan POST /RenewToken: HTTP {dhan_resp_post.status_code}")
            log(f"   - Body: {dhan_resp_post.text}")
        except Exception as e:
            log(f"❌ Direct Dhan POST error: {e}")

    log("\n" + "="*70)
    log("[TEST] COMPLETED")
    log("="*70)

if __name__ == "__main__":
    main()
