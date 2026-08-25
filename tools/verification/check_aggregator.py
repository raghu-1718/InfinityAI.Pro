
import requests
import json

ENGINE_C_URL = "https://engine-c-228557716858.asia-south1.run.app"
USER_ID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

def check(url):
    print(f"\nChecking: {url}")
    try:
        res = requests.get(url, timeout=15)
        print(f"Status: {res.status_code}")
        try:
            print(f"Data: {json.dumps(res.json(), indent=2)}")
        except:
            print(f"Text: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

check(f"{ENGINE_C_URL}/api/v1/user/{USER_ID}/account")
