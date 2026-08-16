import requests
import json

BASE_URL = "https://engine-c-313407263327.asia-south1.run.app"

def test_renew():
    print("Testing /api/dhan/renew-token...")
    res = requests.post(f"{BASE_URL}/api/dhan/renew-token", timeout=25)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:300]}")

if __name__ == "__main__":
    test_renew()
