import requests
import json
import sys

# Constants
ENGINE_C_URL = "https://engine-c-228557716858.asia-south1.run.app"
USER_ID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2" # Found in previous step

def check_endpoint(name, method, endpoint, params={}):
    url = f"{ENGINE_C_URL}{endpoint}"
    print(f"\n--- Checking {name} ---")
    print(f"URL: {url}")
    print(f"Params: {params}")
    try:
        if method == 'GET':
            res = requests.get(url, params=params, timeout=15)
        else:
            res = requests.post(url, json=params, timeout=15)
            
        print(f"Status: {res.status_code}")
        try:
            data = res.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        except:
            print(f"Raw Response: {res.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def verify_live_user_state():
    print(f"Diagnosing Live User ID: {USER_ID}")
    
    # 1. Check Health/Config (if exposed)
    check_endpoint("Engine C Health", "GET", "/health")
    
    # 2. Check User Credentials Status (Internal API)
    # Note: Engine C usually validates creds internally, let's see actual data fetches
    
    # 3. Check Funds
    funds = check_endpoint("Funds", "GET", "/api/dhan/funds", {"user_id": USER_ID})
    
    # 4. Check Holdings
    holdings = check_endpoint("Holdings", "GET", "/api/dhan/holdings", {"user_id": USER_ID})
    
    # 5. Check Positions
    positions = check_endpoint("Positions", "GET", "/api/dhan/positions", {"user_id": USER_ID})
    
    # 6. Check Option Chain (Real-Time Test)
    # NIFTY 50 = 13 (IDX_I)
    # Check for *incorrect data* (e.g. empty lists vs error messages)
    
if __name__ == "__main__":
    verify_live_user_state()
