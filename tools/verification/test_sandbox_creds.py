#!/usr/bin/env python3
"""Test DhanHQ sandbox credentials by calling various API endpoints."""
import requests
import json
from datetime import datetime

# Sandbox credentials
CLIENT_ID = "2508215064"
ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"

# DhanHQ sandbox base URL - Different from production!
# Sandbox: https://sandbox.dhan.co/v2
# Production: https://api.dhan.co/v2
BASE_URL = "https://sandbox.dhan.co/v2"

# Common headers
HEADERS = {
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_api(endpoint, method="GET", payload=None):
    """Test a DhanHQ API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        print(f"\n[TEST] Endpoint: {method} {endpoint}")
        print(f"       Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"       [OK] SUCCESS")
            data = response.json()
            print(f"       Response: {json.dumps(data, indent=2)[:500]}...")
            return True, data
        else:
            print(f"       [FAIL] Failed with status {response.status_code}")
            print(f"       Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"       [ERROR] EXCEPTION: {str(e)}")
        return False, None

def main():
    """Run all sandbox API tests."""
    
    print_section("DHAN SANDBOX CREDENTIALS TEST")
    print(f"\nClient ID: {CLIENT_ID}")
    print(f"Token Expiry: Extracted from JWT would be Unix timestamp 1769022714")
    print(f"             = {datetime.fromtimestamp(1769022714).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Webhook URL: https://engine-c-3acobgd3qa-uc.a.run.app/api/dhan/postback")
    
    # Test 1: Holdings
    print_section("TEST 1: Get Holdings")
    success, data = test_api("/holdings")
    
    # Test 2: Positions
    print_section("TEST 2: Get Positions")
    success, data = test_api("/positions")
    
    # Test 3: Order Book
    print_section("TEST 3: Get Order Book")
    success, data = test_api("/orders")
    
    # Test 4: Fund Limits
    print_section("TEST 4: Get Fund Limits")
    success, data = test_api("/fundlimit")
    
    # Test 5: Trade Book
    print_section("TEST 5: Get Trade Book")
    success, data = test_api("/tradebook")
    
    # Test 6: Fetch KillSwitch Status
    print_section("TEST 6: Get KillSwitch Status")
    success, data = test_api("/killswitch")
    
    # Test 7: Market Quote (NIFTY 50)
    print_section("TEST 7: Get Market Quote (NIFTY 50)")
    quote_payload = {
        "NSE_EQ": ["1333"]  # NIFTY 50 security ID
    }
    success, data = test_api("/marketfeed/quotes", method="POST", payload=quote_payload)
    
    # Test 8: LTP Data (RELIANCE)
    print_section("TEST 8: Get LTP Data (RELIANCE)")
    ltp_payload = {
        "NSE_EQ": ["2885"]  # RELIANCE security ID
    }
    success, data = test_api("/marketfeed/ltp", method="POST", payload=ltp_payload)
    
    print_section("TEST SUMMARY")
    print("\n[OK] All sandbox credential tests completed.")
    print("\nNote: Sandbox environment may return mock/empty data.")
    print("Check status codes - 200 means authentication is working correctly.\n")

if __name__ == "__main__":
    main()
