
import requests
import subprocess
import json
import sys
import time
from datetime import datetime

# --- Configuration ---
ENGINES = {
    "A (Orchestrator)": "https://engine-a-mfvaq54jjq-uc.a.run.app",
    "B (Analysis)": "https://engine-b-429140669077.us-central1.run.app",
    "C (Execution)": "https://engine-c-429140669077.us-central1.run.app" 
}
# Updated Engine B URL based on recent deployment logs.

APP_URL = "https://infinityai.pro"

REPORT_FILE = "live_verification_report.md"
report_content = [f"# Master Live Verification Report - {datetime.now()}"]

def log(msg):
    print(msg)
    report_content.append(msg)

def save_report():
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))
    print(f"\n📄 Report saved to {REPORT_FILE}")

print(f"=== MASTER LIVE VERIFICATION START: {datetime.now()} ===\n")

def run_cmd(args, description):
    log(f"\n### ⏳ {description}...")
    try:
        if sys.platform == "win32":
            args = " ".join(args)
            shell = True
        else:
            shell = False
            
        result = subprocess.run(args, capture_output=True, text=True, shell=shell)
        if result.returncode == 0:
            log(f"✅ PASS")
            output = result.stdout.strip()
            log(f"```\n{output}\n```")
            return output
        else:
            log(f"❌ FAIL: {result.stderr.strip()}")
            return None
    except Exception as e:
        log(f"❌ ERROR: {e}")
        return None

def check_endpoint(name, url, endpoint="/health", method="GET", payload=None):
    full_url = f"{url}{endpoint}"
    log(f"\n### 📡 Probing {name}: {method} {full_url}")
    try:
        start = time.time()
        if method == "GET":
            resp = requests.get(full_url, timeout=10, verify=False)
        else:
            resp = requests.post(full_url, json=payload, timeout=30, verify=False)
        duration = time.time() - start
        
        if resp.status_code < 400:
            log(f"   ✅ HTTP {resp.status_code} ({duration:.2f}s)")
            try:
                data = resp.json()
                log(f"   📄 Response: `{json.dumps(data, indent=2)[:500]}...`")
            except:
                log(f"   📄 Response: `{resp.text[:200]}`")
            return True
        else:
             log(f"   ❌ HTTP {resp.status_code} - {resp.text[:200]}")
             return False
    except Exception as e:
        log(f"   ❌ Connection Failed: {e}")
        return False

# --- Phase 1: Infrastructure ---
log("\n--- Phase 1: Infrastructure & Health ---")
for name, url in ENGINES.items():
    check_endpoint(name, url)

# --- Phase 2: AI & Signal Flow ---
log("\n--- Phase 2: AI & Real-Time Data Flow ---")
# 1. News Endpoint (New)
check_endpoint("Engine B (News)", ENGINES["B (Analysis)"], "/api/v1/news?limit=1", "GET")

# 2. AI Signal (Crude Oil)
payload = {
    "symbol": "CRUDEOIL",
    "timeframe": "INTRADAY",
    "user_analysis_type": "comprehensive",
    "use_pro_model": False,
    "market": "MCX",
    "current_price": 6000.0  # Dummy price to satisfy schema
}
check_endpoint("Engine B (AI Signal)", ENGINES["B (Analysis)"], "/api/v1/ai/enhanced-signal", "POST", payload)

# --- Phase 3: Cloud Forensics (Logs) ---
log("\n--- Phase 3: Cloud Forensics (Live Logs) ---")
# Simplified query to avoid Windows quoting hell
# We just want recent Cloud Run logs.
# Using --freshness to limit time instead of timestamp filter.

logs = run_cmd(
    ["gcloud", "logging", "read", 'resource.type="cloud_run_revision"', "--limit=5", "--freshness=5m", "--format=table(timestamp,resource.labels.service_name,textPayload,httpRequest.status)"], 
    "Scanning Cloud Run Logs (Last 5 mins)"
)
if not logs:
    log("   (No logs found yet - propagation delay is normal)")

# --- Phase 4: Firebase & Secrets ---
log("\n--- Phase 4: Configuration & Secrets ---")
run_cmd(["gcloud", "secrets", "list", "--format=table(name,createTime)"], "Verifying Secret Manager Inventory")

log("\n--- Phase 5: Firestore Index Check ---")
indexes = run_cmd(["gcloud", "firestore", "indexes", "composite", "list"], "Verifying Firestore Indexes")
if indexes is not None:
    log("✅ Firestore CLI Access Verified")
else:
    log("❌ Firestore Check Failed")

log("\n=== VERIFICATION COMPLETE ===")
save_report()
