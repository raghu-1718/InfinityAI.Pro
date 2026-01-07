
import requests
import json

url = "https://infinityai.pro/api/auth/coupon/verify"
origin = "https://infinityai.pro"

def print_headers(resp, label):
    print(f"\n--- {label} ---")
    print(f"Status: {resp.status_code}")
    headers = dict(resp.headers)
    cors_headers = {k: v for k, v in headers.items() if "access-control" in k.lower()}
    print("CORS Headers:")
    print(json.dumps(cors_headers, indent=2))

print(f"Target: {url}")
print(f"Origin: {origin}")

try:
    # OPTIONS
    resp = requests.options(url, headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    })
    print_headers(resp, "OPTIONS")

    # POST
    resp = requests.post(url, json={
        "coupon_code": "DEBUG_TEST",
        "google_user_id": "debug_uid"
    }, headers={
        "Origin": origin,
        "Content-Type": "application/json"
    })
    print_headers(resp, "POST")
    print("\nBody Preview:")
    print(resp.text[:200])

except Exception as e:
    print(f"Request Failed: {e}")
