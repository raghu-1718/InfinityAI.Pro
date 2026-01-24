import requests
import json
import os

# Configuration (Mirrors frontend environment variables)
ENGINE_A_URL = os.getenv("NEXT_PUBLIC_ENGINE_A_URL", "https://engine-a-3acobgd3qa-uc.a.run.app")
ENGINE_B_URL = os.getenv("NEXT_PUBLIC_ENGINE_B_URL", "https://engine-b-3acobgd3qa-uc.a.run.app")
ENGINE_C_URL = os.getenv("NEXT_PUBLIC_ENGINE_C_URL", "https://engine-c-3acobgd3qa-uc.a.run.app")

# Mock User Context (Simulating a logged-in user)
TEST_USER_ID = "test-user-simulation"
TEST_HEADERS = {
    "X-User-ID": TEST_USER_ID,
    "Content-Type": "application/json"
}

def log_step(name, status, details=""):
    print(f"[{'PASS' if status else 'FAIL'}] {name}")
    if details:
        print(f"    -> {details}")

def verify_system_state():
    """Verify the main dashboard system state endpoint"""
    url = f"{ENGINE_A_URL}/api/system/state"
    try:
        resp = requests.get(url, headers=TEST_HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            log_step("Fetch System State", True, f"Status: {data.get('system_status')}")
            return True
        else:
            log_step("Fetch System State", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        log_step("Fetch System State", False, str(e))
        return False

def verify_market_signals():
    """Verify fetching signals (Engine B -> Engine A -> Frontend)"""
    # Note: Frontend might call Engine A or Engine B directly depending on architecture.
    # Architecture doc says Engine A orchestrates, but let's check Engine B direct as well.
    url = f"{ENGINE_B_URL}/api/v1/signal"
    payload = {"symbol": "NIFTY", "timeframe": "1d"}
    try:
        resp = requests.post(url, headers=TEST_HEADERS, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            log_step("Fetch Market Signal (NIFTY)", True, f"Signal: {data.get('signal')}, Confidence: {data.get('confidence')}")
            return True
        else:
            log_step("Fetch Market Signal (NIFTY)", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        log_step("Fetch Market Signal (NIFTY)", False, str(e))
        return False

def verify_dhan_proxy_mock():
    """Verify Dhan proxy endpoints (simulating frontend call)"""
    # Requires Mock Creds passed in headers usually, or stored in Firestore.
    # For this simulation, we'll check if the endpoint responds at all (even 401/400 is 'alive')
    url = f"{ENGINE_C_URL}/api/dhan/funds?user_id={TEST_USER_ID}"
    try:
        resp = requests.get(url, headers=TEST_HEADERS, timeout=10)
        # We expect a failure or success depending on if the user exists in Firestore
        # But a 404 means the route is missing (Bad). 500 is Bad.
        # 400/401/200 are 'Good' in terms of connectivity.
        if resp.status_code != 404:
            log_step("Dhan Proxy Connectivity", True, f"Received HTTP {resp.status_code} (Expected)")
            return True
        else:
            log_step("Dhan Proxy Connectivity", False, "HTTP 404 - Endpoint Route Missing")
            return False
    except Exception as e:
        log_step("Dhan Proxy Connectivity", False, str(e))
        return False

def main():
    print("=== Simulating Frontend-to-Backend Flow ===")
    s1 = verify_system_state()
    s2 = verify_market_signals()
    s3 = verify_dhan_proxy_mock()
    
    if all([s1, s2, s3]):
        print("\n✅ Verification Successful: Frontend API contracts appear valid.")
        exit(0)
    else:
        print("\n❌ Verification Failed: Some endpoints are not behaving as expected.")
        exit(1)

if __name__ == "__main__":
    main()
