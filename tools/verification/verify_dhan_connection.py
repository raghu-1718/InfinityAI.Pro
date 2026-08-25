
import requests
import json
import sys

ENGINE_C_URL = "https://engine-c-228557716858.asia-south1.run.app"
USER_ID = "B79BqvTlaTZltC8uGO3jLxJBBt93"

def verify_connection():
    print(f"Testing Connectivity to DhanHQ via Engine C...")
    print(f"Target: {ENGINE_C_URL}/api/dhan/funds?user_id={USER_ID}")
    
    try:
        response = requests.get(
            f"{ENGINE_C_URL}/api/dhan/funds",
            params={"user_id": USER_ID},
            timeout=15
        )
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print("\n[OK] CONNECTION SUCCESSFUL!")
                print(f"Raw Response Keys: {list(data.keys())}")
                print(f"Raw Data: {data.get('data')}")
                print("-" * 30)
                summary = data.get("summary", {})
                print(f"Available Balance: {summary.get('available_balance')}")
                print(f"Utilized Margin:   {summary.get('utilized_margin')}")
                print("-" * 30)
                return True
            else:
                print("\n[ERROR] API Error:")
                print(json.dumps(data, indent=2))
                return False
        else:
            print(f"\n[ERROR] HTTP Request Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n[EXCEPTION] Exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_connection()
    sys.exit(0 if success else 1)
