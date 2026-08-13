#!/usr/bin/env python3
"""
Integration Verification Suite for InfinityAI.Pro Cloud Run Engines
Verifies live health, system state, AI signals, and Dhan connectivity routes.
"""
import sys
import requests
import json
import time
from datetime import datetime

# Configure stdout encoding for Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Live Production URLs (asia-south1 Mumbai)
ENGINE_A_URL = "https://engine-a-313407263327.asia-south1.run.app"
ENGINE_B_URL = "https://engine-b-313407263327.asia-south1.run.app"
ENGINE_C_URL = "https://engine-c-313407263327.asia-south1.run.app"
HOSTING_URL = "https://project-841b7f97-5ee3-4fbe-920.web.app"

TEST_USER_ID = "sandbox_test_user_001"
HEADERS = {
    "X-User-ID": TEST_USER_ID,
    "Content-Type": "application/json"
}

def log(status: str, name: str, latency_ms: float, detail: str = ""):
    icon = "✅" if status == "PASS" else "❌"
    detail_str = f" | {detail}" if detail else ""
    print(f"[{status}] {icon} {name:<35} | {latency_ms:>7.2f}ms{detail_str}")

def test_engine_health():
    print("\n" + "=" * 80)
    print("1. HEALTH CHECKS ACROSS ENGINES")
    print("=" * 80)
    
    engines = [
        ("Engine A (Orchestration)", ENGINE_A_URL),
        ("Engine B (AI/ML Signals)", ENGINE_B_URL),
        ("Engine C (Options/Dhan)", ENGINE_C_URL),
    ]
    
    all_ok = True
    for name, base_url in engines:
        t0 = time.time()
        try:
            resp = requests.get(f"{base_url}/health", timeout=15)
            lat = (time.time() - t0) * 1000
            if resp.status_code == 200:
                data = resp.json()
                log("PASS", name, lat, f"status: {data.get('status')}, version: {data.get('version', 'N/A')}")
            else:
                log("FAIL", name, lat, f"HTTP {resp.status_code}")
                all_ok = False
        except Exception as e:
            lat = (time.time() - t0) * 1000
            log("FAIL", name, lat, f"Error: {e}")
            all_ok = False
            
    return all_ok

def test_system_state():
    print("\n" + "=" * 80)
    print("2. TESTING FASTAPI SYSTEM STATE ROUTE")
    print("=" * 80)
    
    # Correct FastAPI route for unified system state aggregator
    endpoint = "/api/system/state"
    url = f"{ENGINE_A_URL}{endpoint}"
    
    t0 = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        lat = (time.time() - t0) * 1000
        if resp.status_code == 200:
            data = resp.json()
            log("PASS", f"GET {endpoint}", lat, f"system_status: {data.get('system_status')}, vix: {data.get('current_vix')}")
            return True
        else:
            log("FAIL", f"GET {endpoint}", lat, f"HTTP {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        lat = (time.time() - t0) * 1000
        log("FAIL", f"GET {endpoint}", lat, f"Error: {e}")
        return False

def test_engine_b_signals():
    print("\n" + "=" * 80)
    print("3. TESTING ENGINE B AI SIGNALS (60s BREATHING ROOM)")
    print("=" * 80)
    
    endpoint = "/api/v1/signal"
    url = f"{ENGINE_B_URL}{endpoint}"
    payload = {"symbol": "NIFTY", "timeframe": "1d"}
    
    t0 = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=60)
        lat = (time.time() - t0) * 1000
        if resp.status_code == 200:
            data = resp.json()
            log("PASS", f"POST {endpoint} (NIFTY)", lat, f"signal: {data.get('signal')}, conf: {data.get('confidence')}")
            return True
        else:
            log("FAIL", f"POST {endpoint} (NIFTY)", lat, f"HTTP {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        lat = (time.time() - t0) * 1000
        log("FAIL", f"POST {endpoint} (NIFTY)", lat, f"Error: {e}")
        return False

def test_engine_c_credentials():
    print("\n" + "=" * 80)
    print("4. TESTING ENGINE C USER DHAN ROUTE")
    print("=" * 80)
    
    endpoint = f"/api/user/credentials?user_id={TEST_USER_ID}"
    url = f"{ENGINE_C_URL}{endpoint}"
    
    t0 = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        lat = (time.time() - t0) * 1000
        if resp.status_code == 200:
            data = resp.json()
            log("PASS", "GET /api/user/credentials", lat, f"configured: {data.get('configured')}")
            return True
        else:
            log("FAIL", "GET /api/user/credentials", lat, f"HTTP {resp.status_code}")
            return False
    except Exception as e:
        lat = (time.time() - t0) * 1000
        log("FAIL", "GET /api/user/credentials", lat, f"Error: {e}")
        return False

def test_hosting_integration():
    print("\n" + "=" * 80)
    print("5. TESTING FIREBASE HOSTING INTEGRATION")
    print("=" * 80)
    
    t0 = time.time()
    try:
        resp = requests.get(HOSTING_URL, timeout=15)
        lat = (time.time() - t0) * 1000
        if resp.status_code == 200:
            log("PASS", "Firebase Hosting Base", lat, f"HTTP 200 OK")
            return True
        else:
            log("FAIL", "Firebase Hosting Base", lat, f"HTTP {resp.status_code}")
            return False
    except Exception as e:
        lat = (time.time() - t0) * 1000
        log("FAIL", "Firebase Hosting Base", lat, f"Error: {e}")
        return False

def main():
    print("=" * 80)
    print(f"INFINITYAI.PRO ENGINE VERIFICATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("=" * 80)
    
    results = [
        test_engine_health(),
        test_system_state(),
        test_engine_b_signals(),
        test_engine_c_credentials(),
        test_hosting_integration()
    ]
    
    print("\n" + "=" * 80)
    if all(results):
        print("🎉 ALL ENGINE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    else:
        print(f"⚠️ {results.count(False)} out of {len(results)} tests failed.")
    print("=" * 80)

if __name__ == "__main__":
    main()
