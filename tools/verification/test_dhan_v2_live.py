"""
Comprehensive DhanHQ API v2 Live Verification Script
Tests all DhanHQ v2 endpoints against Engine C using stored live credentials.
"""
import sys
import os
import asyncio

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'engine-c'))
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def run_dhan_v2_verification():
    print("=" * 80)
    print("LIVE VERIFICATION OF DHANHQ API V2 INTEGRATION IN ENGINE C")
    print("=" * 80)

    test_user = "local-user-123"

    # Test 1: Get Stored Credentials
    print("\n1. Testing GET /api/user/credentials...")
    res = client.get(f"/api/user/credentials?user_id={test_user}")
    print(f"  - Status code: {res.status_code}")
    data = res.json()
    print(f"  - Configured: {data.get('configured')}, Client ID: {data.get('client_id')}, Verified: {data.get('is_verified')}")
    assert res.status_code == 200
    assert data.get("configured") is True
    print("  ✅ GET /api/user/credentials test PASSED")

    # Test 2: Live Fund Limits
    print("\n2. Testing Live DhanHQ Fund Limits (GET /api/dhan/funds)...")
    res = client.get(f"/api/dhan/funds?user_id={test_user}")
    print(f"  - Status code: {res.status_code}")
    data = res.json()
    print(f"  - Response: {data}")
    assert res.status_code == 200
    print("  ✅ Live Fund Limits test PASSED")

    # Test 3: Live Positions
    print("\n3. Testing Live DhanHQ Positions (GET /api/dhan/positions)...")
    res = client.get(f"/api/dhan/positions?user_id={test_user}")
    print(f"  - Status code: {res.status_code}")
    data = res.json()
    print(f"  - Response data length: {len(data.get('data', [])) if isinstance(data, dict) else 0}")
    assert res.status_code == 200
    print("  ✅ Live Positions test PASSED")

    # Test 4: Live Orders List
    print("\n4. Testing Live DhanHQ Orders (GET /api/dhan/orders)...")
    res = client.get(f"/api/dhan/orders?user_id={test_user}")
    print(f"  - Status code: {res.status_code}")
    data = res.json()
    print(f"  - Response data length: {len(data.get('data', [])) if isinstance(data, dict) else 0}")
    assert res.status_code == 200
    print("  ✅ Live Orders test PASSED")

    # Test 5: Forever Orders (GTT)
    print("\n5. Testing DhanHQ v2 Forever Orders (GET /api/dhan/v2/forever/orders)...")
    res = client.get(f"/api/dhan/v2/forever/orders?user_id={test_user}")
    print(f"  - Status code: {res.status_code}")
    data = res.json()
    print(f"  - Response: {data}")
    assert res.status_code == 200
    print("  ✅ Forever Orders test PASSED")

    # Test 6: Margin Calculator
    print("\n6. Testing DhanHQ v2 Margin Calculator (POST /api/dhan/v2/margin/calculator)...")
    margin_payload = {
        "user_id": test_user,
        "exchange_segment": "NSE_EQ",
        "transaction_type": "BUY",
        "quantity": 10,
        "product_type": "CNC",
        "security_id": "11536",
        "price": 2500.0
    }
    res = client.post("/api/dhan/v2/margin/calculator", json=margin_payload)
    print(f"  - Status code: {res.status_code}")
    print(f"  - Response: {res.json()}")
    assert res.status_code == 200
    print("  ✅ Margin Calculator test PASSED")

    # Test 7: Account Ledger
    print("\n7. Testing DhanHQ v2 Account Ledger (GET /api/dhan/v2/ledger)...")
    res = client.get(f"/api/dhan/v2/ledger?user_id={test_user}")
    print(f"  - Status code: {res.status_code}")
    print(f"  - Response: {res.json()}")
    assert res.status_code == 200
    print("  ✅ Account Ledger test PASSED")

    print("\n" + "=" * 80)
    print("ALL DHANHQ API V2 INTEGRATION TESTS PASSED SUCCESSFULLY 🎉")
    print("=" * 80)

if __name__ == "__main__":
    run_dhan_v2_verification()
