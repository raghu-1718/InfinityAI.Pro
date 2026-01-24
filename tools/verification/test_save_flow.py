
import asyncio
import httpx
import json

ENGINE_C_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"
USER_ID = "B79BqvTlaTZltC8uGO3jLxJBBt93"

async def test_save():
    print(f"💾 Testing Save Credentials for {USER_ID}...")
    async with httpx.AsyncClient() as client:
        # 1. Save Dummy Credentials
        url = f"{ENGINE_C_URL}/api/dhan/credentials"
        payload = {
            "user_id": USER_ID,
            "client_id": "1000000000",
            "access_token": "dummy_token_for_verification_only",
            "api_key": "dummy_key",
            "api_secret": "dummy_secret"
        }
        print(f"   POST {url}")
        resp = await client.post(url, json=payload)
        print(f"   Status: {resp.status_code}")
        try:
            print(f"   Response: {resp.json()}")
        except:
            print(f"   Response Text: {resp.text}")

        # 2. Check if it persisted
        url_check = f"{ENGINE_C_URL}/api/dhan/credentials/{USER_ID}"
        print(f"\n   GET {url_check}")
        resp_check = await client.get(url_check)
        if resp_check.status_code == 200:
             data = resp_check.json()
             if data.get("credentials") and data.get("credentials").get("client_id") == "1000000000":
                 print("   ✅ Credentials Successfully Saved and Retrieved!")
             else:
                 print("   ❌ Save verification failed!")
        
        # 3. Cleanup
        print(f"\n   DELETE {url_check}")
        await client.delete(url_check)

if __name__ == "__main__":
    asyncio.run(test_save())
