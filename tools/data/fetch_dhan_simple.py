import requests
import json
from datetime import datetime

ENGINE_C_URL = "https://engine-c-228557716858.us-central1.run.app"
CLIENT_ID = "1101302170"

def fetch(endpoint, params=None):
    try:
        r = requests.get(f"{ENGINE_C_URL}{endpoint}", params=params or {}, timeout=30)
        return {"ok": r.status_code == 200, "data": r.json() if r.status_code == 200 else {}, "err": r.text[:100] if r.status_code != 200 else None}
    except Exception as e:
        return {"ok": False, "data": {}, "err": str(e)}

print(f"DHAN ACCOUNT DATA - {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

# Account
print("\n[1/6] Account Overview...")
acc = fetch(f"/api/v1/user/{CLIENT_ID}/account")
if acc["ok"]:
    print(f"  Balance: Rs.{acc['data'].get('funds', {}).get('availableBalance', 0)}")
    print(f"  Holdings: {acc['data'].get('holdings_count', 0)}")
else:
    print(f"  ERROR: {acc['err']}")

# Funds
print("\n[2/6] Funds...")
funds = fetch(f"/api/dhan/funds", {"user_id": CLIENT_ID})
if funds["ok"]:
    print(f"  Available: Rs.{funds['data'].get('availableBalance', 0)}")
    print(f"  Utilized: Rs.{funds['data'].get('utilizedAmount', 0)}")
else:
    print(f"  ERROR: {funds['err']}")

# Holdings
print("\n[3/6] Holdings...")
h = fetch(f"/api/dhan/holdings", {"user_id": CLIENT_ID})
if h["ok"]:
    print(f"  Total: {len(h['data'].get('holdings', []))}")
else:
    print(f"  ERROR: {h['err']}")

# Positions
print("\n[4/6] Positions...")
p = fetch(f"/api/dhan/positions", {"user_id": CLIENT_ID})
if p["ok"]:
    print(f"  Open: {len(p['data'].get('positions', []))}")
else:
    print(f"  ERROR: {p['err']}")

# Orders
print("\n[5/6] Orders...")
o = fetch(f"/api/dhan/orders", {"user_id": CLIENT_ID})
if o["ok"]:
    print(f"  Total: {len(o['data'].get('orders', []))}")
else:
    print(f"  ERROR: {o['err']}")

# Trades
print("\n[6/6] Trades...")
t = fetch(f"/api/dhan/trades", {"user_id": CLIENT_ID})
if t["ok"]:
    print(f"  Total: {len(t['data'].get('trades', []))}")
else:
    print(f"  ERROR: {t['err']}")

print("\n" + "=" * 70)

# Save
with open("dhan_snapshot.json", "w") as f:
    json.dump({"timestamp": datetime.now().isoformat(), "account": acc, "funds": funds, "holdings": h, "positions": p, "orders": o, "trades": t}, f, indent=2)
    
print("Saved to: dhan_snapshot.json")
