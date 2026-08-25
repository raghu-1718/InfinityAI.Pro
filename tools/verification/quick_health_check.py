import requests
import time

ENGINES = {
    "Engine A": "https://engine-a-228557716858.asia-south1.run.app/health",
    "Engine B": "https://engine-b-228557716858.asia-south1.run.app/health",
    "Engine C": "https://engine-c-228557716858.asia-south1.run.app/health"
}

print("Verifying Backend Health...")
for name, url in ENGINES.items():
    try:
        start = time.time()
        res = requests.get(url, timeout=10)
        dur = (time.time() - start) * 1000
        if res.status_code == 200:
            print(f"[PASS] {name}: {res.status_code} ({dur:.0f}ms)")
            print(f"       Response: {res.text}")
        else:
            print(f"[FAIL] {name}: {res.status_code} ({dur:.0f}ms)")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
