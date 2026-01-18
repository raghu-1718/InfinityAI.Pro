
import requests
import json

# URL from User Screenshot / Deployment
BASE_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"
USER_ID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
FALLBACK_ID = "1101302170"

def test_endpoint(uid, label):
    print(f"\n--- Testing for {label} ({uid}) ---")
    url = f"{BASE_URL}/api/dhan/funds"
    params = {"user_id": uid}
    
    try:
        print(f"GET {url} params={params}")
        resp = requests.get(url, params=params, timeout=15)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
            
            if data.get("status") == "success":
                funds = data.get("data", {})
                print(f"[OK] Extracted Balance: {funds.get('availabelBalance')} / {funds.get('availableBalance')}")
            else:
                print("[FAIL] API returned failure status")
                
        except json.JSONDecodeError:
            print("[FAIL] Response is not JSON:", resp.text[:200])
            
    except Exception as e:
        print(f"[ERROR] Request Failed: {e}")


def test_demat_endpoint(uid, label):
    print(f"\n--- Testing Demat for {label} ({uid}) ---")
    url = f"{BASE_URL}/api/user/demat"
    params = {"user_id": uid}
    
    try:
        print(f"GET {url} params={params}")
        resp = requests.get(url, params=params, timeout=15)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            # print("Response JSON:")
            # print(json.dumps(data, indent=2))
            
            funds = data.get("funds", {})
            print(f"[OK] Demat Balance: {funds.get('availabelBalance')} / {funds.get('availableBalance')}")
                
        except json.JSONDecodeError:
            print("[FAIL] Response is not JSON:", resp.text[:200])
            
    except Exception as e:
        print(f"[ERROR] Request Failed: {e}")


def test_account_endpoint(uid, label):
    print(f"\n--- Testing Aggregated Account for {label} ({uid}) ---")
    url = f"{BASE_URL}/api/v1/user/{uid}/account"
    
    try:
        print(f"GET {url}")
        resp = requests.get(url, timeout=15)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            funds = data.get("funds", {})
            print(f"[OK] Account Balance: Typo='{funds.get('availabelBalance')}' / Correct='{funds.get('availableBalance')}'")
                
        except json.JSONDecodeError:
            print("[FAIL] Response is not JSON:", resp.text[:200])
            
    except Exception as e:
        print(f"[ERROR] Request Failed: {e}")

if __name__ == "__main__":
    # Test with both IDs to be sure
    test_endpoint(USER_ID, "Firebase UID")
    test_account_endpoint(USER_ID, "Firebase UID")
    test_account_endpoint("1101302170", "Dhan Client ID")


