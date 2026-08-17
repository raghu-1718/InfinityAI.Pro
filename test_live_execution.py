import requests
import time
import os

ENDPOINT_URL = "http://35.200.135.175:8000/analyze-options"

def run_test():
    payload = {"ticker": "NIFTY50"}
    print(f"Sending request to {ENDPOINT_URL} ... ", end="", flush=True)
    try:
        start = time.perf_counter()
        response = requests.post(ENDPOINT_URL, json=payload, timeout=30)
        latency = round((time.perf_counter() - start) * 1000)
        
        if response.status_code == 200:
            print(f"✅ PASS ({latency} ms)")
            print("Response:", response.json())
        else:
            print(f"❌ FAIL (HTTP {response.status_code})")
            print("Details:", response.text)
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    run_test()
