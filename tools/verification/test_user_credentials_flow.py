"""
Verification Script for User Credentials & Dhan Connection Flow
"""
import sys
import os
import asyncio
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'engine-c'))

from src.user_credentials import get_credentials_manager

async def run_verification():
    print("=" * 80)
    print("VERIFYING USER CREDENTIALS & DHAN CONNECTION FLOW")
    print("=" * 80)

    manager = get_credentials_manager()
    test_user = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

    # Test 1: Resolve User ID for guest/default/unknown
    print("\n1. Testing User ID Resolution...")
    resolved_guest = await manager.resolve_user_id("guest")
    resolved_none = await manager.resolve_user_id(None)
    resolved_custom = await manager.resolve_user_id(test_user)

    print(f"  - 'guest' -> {resolved_guest}")
    print(f"  - None -> {resolved_none}")
    print(f"  - '{test_user}' -> {resolved_custom}")

    assert resolved_guest in [test_user, "local-user-123"], f"Expected valid resolved ID, got {resolved_guest}"
    assert resolved_none in [test_user, "local-user-123"], f"Expected valid resolved ID, got {resolved_none}"
    print("  ✅ User ID resolution test PASSED")

    # Test 2: Save Credentials
    print("\n2. Testing Credentials Save...")
    save_res = await manager.save_user_credentials(
        user_id="guest", # Should resolve to primary user
        client_id="1000000000",
        access_token="test_token_12345",
        api_key="test_key",
        api_secret="test_secret"
    )
    print(f"  - Save result: {save_res}")
    assert save_res.get("user_id") in [test_user, "local-user-123"], "Save failed to resolve user_id"
    print("  ✅ Credentials Save test PASSED")

    # Test 3: Get Credentials
    print("\n3. Testing Credentials Fetch...")
    creds = await manager.get_user_credentials("guest")
    print(f"  - Fetched Client ID: {creds.get('client_id') if creds else None}")
    assert creds is not None, "Failed to retrieve credentials"
    assert creds.get("client_id") == "1000000000", "Client ID mismatch"
    print("  ✅ Credentials Fetch test PASSED")

    # Test 4: Update Status
    print("\n4. Testing Connection Status Update...")
    status_updated = await manager.update_connection_status("guest", "connected")
    print(f"  - Status update result: {status_updated}")
    assert status_updated, "Status update failed"
    print("  ✅ Connection Status Update test PASSED")

    print("\n" + "=" * 80)
    print("ALL USER CREDENTIALS TESTS PASSED SUCCESSFULLY 🎉")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_verification())
