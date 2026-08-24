"""
Test Batch Signals Endpoint on Engine B
"""
import urllib.request
import json

url = "http://127.0.0.1:8080/api/v1/signals/batch"
payload = json.dumps({"symbols": ["NIFTY", "BANKNIFTY"], "user_id": "raghu_primary"}).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print("=== ENGINE B BATCH SIGNAL GENERATION SUCCESS ===")
    print("Total Signals Generated:", len(res.get("signals", [])))
    for s in res.get("signals", []):
        sym = s.get("symbol")
        sig = s.get("signal")
        conf = s.get("confidence")
        score = s.get("score")
        price = s.get("price")
        print(f"  • {sym} -> Signal: {sig} | Confidence: {conf}% | Score: {score} | Price: ₹{price}")
