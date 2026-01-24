
import asyncio
import httpx
import json

ENGINE_C_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"
USER_ID = "1101302170"

async def check_creds():
    print(f"🔍 Checking Credentials for {USER_ID}...")
    async with httpx.AsyncClient() as client:
        try:
            # 1. Check Credentials Endpoint
            url = f"{ENGINE_C_URL}/api/dhan/credentials/{USER_ID}"
            print(f"   GET {url}")
            resp = await client.get(url)
            print(f"   Status: {resp.status_code}")
            try:
                data = resp.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response Text: {resp.text}")

            # 2. Check System Status (Authentication Check)
            url_status = f"{ENGINE_C_URL}/api/system/status"
            headers = {"X-User-ID": USER_ID}
            print(f"\n   GET {url_status} (Header: X-User-ID={USER_ID})")
            resp_status = await client.get(url_status, headers=headers)
            print(f"   Status: {resp_status.status_code}")
            print(f"   Response: {resp_status.text}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_creds())
