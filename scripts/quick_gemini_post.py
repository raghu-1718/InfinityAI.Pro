import requests, sys, json
BASE=sys.argv[1] if len(sys.argv)>1 else 'https://infinityai-engine-b-26140490557.us-central1.run.app'
url=f"{BASE}/api/gemini/analyze"
payload={"prompt":"Quick test analysis for NIFTY"}
print("POST", url)
try:
    r=requests.post(url, json=payload, timeout=60)
    print("status:", r.status_code)
    if r.headers.get('content-type','').startswith('application/json'):
        print("json keys:", list(r.json().keys()))
    else:
        print("text:", r.text[:200])
except Exception as e:
    print("ERROR:", e)
