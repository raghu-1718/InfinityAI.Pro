#!/usr/bin/env python3
"""
DhanHQ Sandbox Environment Verification Script
Tests API connectivity with provided sandbox credentials.
"""
import requests
import json
import sys
from datetime import datetime

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Sandbox Credentials
SANDBOX_BASE_URL = "https://sandbox.dhan.co/v2"
SANDBOX_CLIENT_ID = "2508215064"
SANDBOX_ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"

# Prepare headers
HEADERS = {
    "access-token": SANDBOX_ACCESS_TOKEN,
    "client-id": SANDBOX_CLIENT_ID,
    "Content-Type": "application/json"
}

def test_endpoint(name, endpoint, method="GET", payload=None):
    """Test a Dhan API endpoint"""
    url = f"{SANDBOX_BASE_URL}{endpoint}"
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"Endpoint: {endpoint}")
    print(f"Method: {method}")
    print(f"{'='*80}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS")
            print(f"Response Preview:")
            print(json.dumps(data, indent=2)[:500])  # Preview first 500 chars
            return {"success": True, "data": data}
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text[:300]}")
            return {"success": False, "status": response.status_code, "error": response.text}
    
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    print("="*80)
    print("DHANHQ SANDBOX API VERIFICATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {SANDBOX_BASE_URL}")
    print(f"Client ID: {SANDBOX_CLIENT_ID}")
    print("="*80)
    
    results = {}
    
    # Test 1: Fund Limit
    results['fund_limit'] = test_endpoint(
        "Fund Limit",
        "/fundlimit"
    )
    
    # Test 2: Holdings
    results['holdings'] = test_endpoint(
        "Holdings",
        "/holdings"
    )
    
    # Test 3: Positions
    results['positions'] = test_endpoint(
        "Positions",
        "/positions"
    )
    
    # Test 4: Orders
    results['orders'] = test_endpoint(
        "Order History",
        "/orders"
    )
    
    # Test 5: Trades
    results['trades'] = test_endpoint(
        "Trade History",
        "/trades"
    )
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results.values() if r.get("success"))
    total_count = len(results)
    
    print(f"\nTests Passed: {success_count}/{total_count}")
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"  {test_name:20s} : {status}")
    
    # Save detailed results
    output_file = "sandbox_verification_results.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "sandbox_url": SANDBOX_BASE_URL,
            "client_id": SANDBOX_CLIENT_ID,
            "results": results,
            "summary": {
                "total_tests": total_count,
                "passed": success_count,
                "failed": total_count - success_count
            }
        }, f, indent=2)
    
    print(f"\n✅ Detailed results saved to: {output_file}")
    print("="*80)
    
    # Exit with appropriate code
    sys.exit(0 if success_count == total_count else 1)

if __name__ == "__main__":
    main()
