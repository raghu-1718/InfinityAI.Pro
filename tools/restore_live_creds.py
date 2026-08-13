import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'engine-c'))
from src.user_credentials import UserCredentialsManager

async def restore():
    mgr = UserCredentialsManager()

    # Restore for local-user-123
    r1 = await mgr.save_user_credentials(
        user_id="local-user-123",
        client_id="1101302170",
        access_token="test_token_placeholder",
        api_key="24880b7b",
        api_secret=""
    )
    await mgr.update_connection_status("local-user-123", "connected", {"dhanClientId": "1101302170"})

    # Restore for znyNtT2lW3MKHqFrVA6E0A2Iv3N2
    r2 = await mgr.save_user_credentials(
        user_id="znyNtT2lW3MKHqFrVA6E0A2Iv3N2",
        client_id="1101302170",
        access_token="test_token_placeholder",
        api_key="24880b7b",
        api_secret=""
    )
    await mgr.update_connection_status("znyNtT2lW3MKHqFrVA6E0A2Iv3N2", "connected", {"dhanClientId": "1101302170"})

    print("✅ Successfully restored credentials into Firestore:", r1, r2)

if __name__ == "__main__":
    asyncio.run(restore())
