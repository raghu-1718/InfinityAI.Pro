import requests
import json
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

ENGINE_C_URL = "https://engine-c-313407263327.asia-south1.run.app"

def test_endpoints():
    endpoints = [
        ("/api/dhan/funds", "Funds (Zero Query Param)"),
        ("/api/dhan/positions", "Positions (Zero Query Param)"),
        ("/api/dhan/holdings", "Holdings (Zero Query Param)"),
        ("/api/dhan/orders", "Orders (Zero Query Param)"),
        ("/api/dhan/trades", "Trades (Zero Query Param)"),
        ("/api/dhan/market/quotes?security_ids=1333,11536&exchange_segment=NSE_EQ", "Live Market Quotes (TCS & Reliance)"),
        ("/api/user/demat", "Demat Summary (Zero Query Param)"),
        ("/api/user/credentials", "Credentials Status (Zero Query Param)"),
        ("/api/user/credentials/verify", "Credentials Verification (Zero Query Param)"),
    ]

    print("=" * 70)
    print("[TEST] INFINITYAI.PRO SINGLE-TENANT LIVE TELEMETRY VERIFICATION")
    print(f"Target: {ENGINE_C_URL}")
    print("=" * 70)

    all_passed = True
    for route, name in endpoints:
        url = f"{ENGINE_C_URL}{route}"
        try:
            resp = requests.get(url, timeout=20)
            status = resp.status_code
            if status == 200:
                data = resp.json()
                print(f"[PASS 200 OK] {name}")
                print(f"   Response: {json.dumps(data)[:140]}...")
            else:
                print(f"[FAIL {status}] {name}")
                print(f"   Response: {resp.text[:150]}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            all_passed = False
        
        # Respect DhanHQ API rate limits (1 request/sec max)
        time.sleep(1.5)

    print("=" * 70)
    if all_passed:
        print("[SUCCESS] ALL SINGLE-TENANT DEMAT & TELEMETRY ENDPOINTS VERIFIED 100% OPERATIONAL!")
    else:
        print("[WARNING] Some endpoints failed. Check logs above.")
    print("=" * 70)

if __name__ == "__main__":
    test_endpoints()
