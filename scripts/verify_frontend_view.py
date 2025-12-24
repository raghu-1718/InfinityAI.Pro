
import requests
import json
import time
import subprocess
import sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
FRONTEND_URL = "https://infinityai.pro"
ENGINE_B_URL = "https://engine-b-429140669077.us-central1.run.app" 
PROJECT_ID = "gen-lang-client-0779271931"
REGION = "us-central1"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def check_url(url, description):
    log(f"Testing {description}: {url}")
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            log(f"✅ PASS: {url} returned 200 OK")
            return True
        else:
            log(f"❌ FAIL: {url} returned {resp.status_code}")
            return False
    except Exception as e:
        log(f"❌ ERROR: Could not connect to {url}: {e}")
        return False

def verify_cloud_function(func_name, project_id):
    log(f"Verifying Cloud Function: {func_name}")
    # Using gcloud to describe status
    cmd = ["gcloud", "functions", "describe", func_name, "--project", project_id, "--region", "us-central1", "--gen2", "--format=json"]
    if sys.platform == "win32":
        cmd_str = " ".join(cmd)
        result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        state = data.get("state", "UNKNOWN")
        url = data.get("serviceConfig", {}).get("uri", "N/A")
        log(f"✅ Function '{func_name}' is {state} at {url}")
        return url
    else:
        log(f"❌ Failed to describe function {func_name}: {result.stderr[:200]}")
        return None

def get_id_token():
    try:
        if sys.platform == "win32":
            cmd = "gcloud auth print-identity-token"
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        else:
            result = subprocess.run(["gcloud", "auth", "print-identity-token"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        log(f"⚠️ Failed to get ID token: {e}")
        return ""

def verify_engine_b_signal():
    url = f"{ENGINE_B_URL}/api/v1/signal" 
    # Checking the new enhanced logic or at least basic connectivity
    payload = {
        "symbol": "RELIANCE",
        "use_gemini": True,
        "_metadata": {"timeframe": "1d", "type": "technical"}
    }
    log(f"Testing Engine B Signal Generation: {url}")
    token = get_id_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            signal = data.get("signal", "UNKNOWN")
            conf = data.get("confidence", 0)
            log(f"✅ Engine B Response: Signal={signal}, Confidence={conf}")
            return True
        else:
            log(f"❌ Engine B returned {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        log(f"❌ Engine B Connection Error: {e}")
        return False

def check_firestore_logs():
    log("Checking Firestore for recent activity logs...")
    # This assumes gcloud is auth'd
    cmd = 'gcloud firestore query --collection-ids=activity_logs --limit=1 --order-by="-timestamp"'
    # Note: query support in gcloud alpha might be limited or require specific syntax. 
    # Fallback to listing indexes or basic collection verification if query fails.
    
    # Better approach: check if collection exists via documents list
    cmd = ["gcloud", "firestore", "documents", "list", "gs://gen-lang-client-0779271931.appspot.com/activity_logs", "--limit=1"] # Incorrect URI format for firestore
    # Correct gcloud firestore documents list uses resource paths.
    # Resource path: projects/gen-lang-client-0779271931/databases/(default)/documents/activity_logs
    
    resource_path = f"projects/{PROJECT_ID}/databases/(default)/documents/activity_logs"
    cmd = ["gcloud", "firestore", "documents", "list", resource_path, "--limit=1"]
    
    if sys.platform == "win32":
        result = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        log("✅ Firestore 'activity_logs' collection is accessible.")
        # log(f"Latest Log: {result.stdout.strip()}")
    else:
        log(f"⚠️ Could not list Firestore documents (permissions/syntax?): {result.stderr[:100]}")


def main():
    print("=== FRONTEND & E2E VERIFICATION START ===")
    
    # 1. Frontend Hosting
    check_url(FRONTEND_URL, "Frontend Public URL")
    
    # 2. Key Cloud Functions
    # getBatchAiSignals is critical for the Live Watchlist
    verify_cloud_function("getBatchAiSignals", PROJECT_ID)
    verify_cloud_function("startTrading", PROJECT_ID) # Backend trigger
    
    # 3. Engine B Direct Check (Simulating what Functions do)
    verify_engine_b_signal()
    
    # 4. Data Consistency (Firestore)
    check_firestore_logs()
    
    print("=== VERIFICATION END ===")

if __name__ == "__main__":
    main()
