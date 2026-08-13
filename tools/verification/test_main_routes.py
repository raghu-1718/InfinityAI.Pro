"""
Test Engine C FastAPI routes directly
"""
import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'engine-c'))

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def run_route_tests():
    print("=" * 80)
    print("TESTING ENGINE C API ROUTES FOR FRONTEND DHAN CONNECTION")
    print("=" * 80)

    # Test 1: GET /api/user/credentials
    print("\n1. Testing GET /api/user/credentials...")
    res = client.get("/api/user/credentials?user_id=guest")
    print(f"  - Status code: {res.status_code}")
    print(f"  - Response: {res.json()}")
    assert res.status_code == 200
    assert "configured" in res.json()
    print("  ✅ GET /api/user/credentials test PASSED")

    # Test 2: POST /api/user/credentials
    print("\n2. Testing POST /api/user/credentials...")
    payload = {
        "user_id": "guest",
        "client_id": "1100112233",
        "api_key": "key_abc",
        "api_secret": "sec_xyz",
        "access_token": "token_1234567890"
    }
    res = client.post("/api/user/credentials", json=payload)
    print(f"  - Status code: {res.status_code}")
    print(f"  - Response: {res.json()}")
    assert res.status_code == 200
    assert res.json().get("status") == "success"
    print("  ✅ POST /api/user/credentials test PASSED")

    # Test 3: GET /api/user/credentials/verify
    print("\n3. Testing GET /api/user/credentials/verify...")
    res = client.get("/api/user/credentials/verify?user_id=guest")
    print(f"  - Status code: {res.status_code}")
    print(f"  - Response: {res.json()}")
    assert res.status_code == 200
    assert "is_verified" in res.json()
    print("  ✅ GET /api/user/credentials/verify test PASSED")

    # Test 4: GET /auth/dhan/success HTML page
    print("\n4. Testing GET /auth/dhan/success landing page...")
    res = client.get("/auth/dhan/success")
    print(f"  - Status code: {res.status_code}")
    assert res.status_code == 200
    assert "Dhan Authentication Successful" in res.text
    print("  ✅ GET /auth/dhan/success test PASSED")

    # Test 5: DELETE /api/user/credentials
    print("\n5. Testing DELETE /api/user/credentials...")
    res = client.delete("/api/user/credentials?user_id=test_delete_only_user_999")
    print(f"  - Status code: {res.status_code}")
    print(f"  - Response: {res.json()}")
    assert res.status_code == 200
    assert res.json().get("status") == "success"
    print("  ✅ DELETE /api/user/credentials test PASSED")

    print("\n" + "=" * 80)
    print("ALL FASTAPI ROUTE TESTS PASSED SUCCESSFULLY 🎉")
    print("=" * 80)

if __name__ == "__main__":
    run_route_tests()
