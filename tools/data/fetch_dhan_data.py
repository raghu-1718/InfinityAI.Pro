# encoding: utf-8
import requests
import json
from datetime import datetime
import sys

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

ENGINE_C_URL = "https://engine-c-313407263327.asia-south1.run.app"
USER_ID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
CLIENT_ID = "1101302170"

def fetch_endpoint(endpoint, params=None):
    url = f"{ENGINE_C_URL}{endpoint}"
    try:
        response = requests.get(url, params=params or {}, timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "status": response.status_code, "error": response.text[:200]}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 80)
print(f"DHAN ACCOUNT DATA FETCH - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 1. Account Overview
print("\n[1/7] Fetching Account Overview...")
account = fetch_endpoint(f"/api/v1/user/{CLIENT_ID}/account")
if account["success"]:
    data = account["data"]
    print(f"  [OK] Balance: Rs.{data.get('funds', {}).get('availableBalance', 0)}")
    print(f"  [OK] Holdings: {data.get('holdings_count', 0)}")
    print(f"  [OK] Positions: {len(data.get('positions', []))}")
else:
    print(f"  [ERR] Failed: {account.get('error', 'Unknown')}")

# 2. Funds
print("\n[2/7] Fetching Detailed Funds...")
funds = fetch_endpoint(f"/api/dhan/funds", {"user_id": CLIENT_ID})
if funds["success"]:
    f = funds["data"]
    print(f"  [OK] SOD Limit: Rs.{f.get('sodLimit', 0)}")
    print(f"  [OK] Available Balance: Rs.{f.get('availableBalance', 0)}")
    print(f"  [OK] Utilized Amount: Rs.{f.get('utilizedAmount', 0)}")
    print(f"  [OK] Collateral: Rs.{f.get('collateral', 0)}")
else:
    print(f"  [ERR] Failed: {funds.get('error', 'Unknown')}")

# 3. Holdings
print("\n[3/7] Fetching Holdings...")
holdings = fetch_endpoint(f"/api/dhan/holdings", {"user_id": CLIENT_ID})
if holdings["success"]:
    h_list = holdings["data"].get("holdings", [])
    print(f"  [OK] Total Holdings: {len(h_list)}")
    print(f"DEBUG: type(h_list)={type(h_list)}")
    print(f"DEBUG: holdings['data']={holdings['data']}")
    # Assume it's a dict, maybe the data is the dict itself, or under another key?
    # Based on the error, h_list is a dict.
    # Let's try to find the list.
    actual_list = []
    if isinstance(h_list, list):
        actual_list = h_list
    elif isinstance(h_list, dict):
        # Try to find a list value in the dict
        for k, v in h_list.items():
            if isinstance(v, list):
                actual_list = v
                break
    
    for h in actual_list[:5]:
        print(f"    - {h.get('tradingSymbol')}: {h.get('totalQty')} @ Rs.{h.get('avgCostPrice')}")
else:
    print(f"  [ERR] Failed: {holdings.get('error', 'Unknown')}")

# 4. Positions
print("\n[4/7] Fetching Open Positions...")
positions = fetch_endpoint(f"/api/dhan/positions", {"user_id": CLIENT_ID})
if positions["success"]:
    p_list = positions["data"].get("positions", [])
    for p in p_list[:5]:
        print(f"    - {p.get('tradingSymbol')}: {p.get('positionType')}")
else:
    print(f"  [ERR] Failed: {positions.get('error', 'Unknown')}")

# 5. Orders
print("\n[5/7] Fetching Order History...")
orders = fetch_endpoint(f"/api/dhan/orders", {"user_id": CLIENT_ID})
if orders["success"]:
    o_list = orders["data"].get("orders", [])
    print(f"  [OK] Total Orders: {len(o_list)}")
else:
    print(f"  [ERR] Failed: {orders.get('error', 'Unknown')}")

# 6. Trades
print("\n[6/7] Fetching Trade History...")
trades = fetch_endpoint(f"/api/dhan/trades", {"user_id": CLIENT_ID})
if trades["success"]:
    t_list = trades["data"].get("trades", [])
    print(f"  [OK] Total Trades: {len(t_list)}")
else:
    print(f"  [ERR] Failed: {trades.get('error', 'Unknown')}")

# 7. Credentials
print("\n[7/7] Fetching Credential Status...")
creds = fetch_endpoint(f"/api/user/credentials", {"user_id": CLIENT_ID})
if creds["success"]:
    print(f"  [OK] Configured: {creds['data'].get('configured', False)}")
    print(f"  [OK] Verified: {creds['data'].get('is_verified', False)}")
    print(f"  [OK] Client ID: {creds['data'].get('client_id', 'N/A')}")
else:
    print(f"  [ERR] Failed: {creds.get('error', 'Unknown')}")

print("\n" + "=" * 80)
print("DATA FETCH COMPLETE")
print("=" * 80)

# Save JSON
with open("dhan_account_snapshot.json", "w", encoding='utf-8') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "account_overview": account,
        "funds": funds,
        "holdings": holdings,
        "positions": positions,
        "orders": orders,
        "trades": trades,
        "credentials": creds
    }, f, indent=2)

print(f"\nDetailed data saved to: dhan_account_snapshot.json")
