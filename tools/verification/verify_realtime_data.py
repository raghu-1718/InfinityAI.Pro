import requests
import json
import datetime
import traceback

ENGINE_C_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"
USER_ID = "B79BqvTlaTZltC8uGO3jLxJBBt93"

def get_next_thursday():
    today = datetime.date.today()
    # Thursday is 3 (Mon=0)
    days_ahead = 3 - today.weekday()
    if days_ahead <= 0:
         days_ahead += 7
    next_thursday = today + datetime.timedelta(days=days_ahead)
    return next_thursday.strftime("%Y-%m-%d")

def verify_market_data():
    print(f"Verifying Real-Time Option Chain Data Analysis on {ENGINE_C_URL}...")
    expiry = get_next_thursday()
    print(f"Target Expiry: {expiry}")

    # 1. Fetch Option Chain (NIFTY)
    # 13 = NIFTY 50, IDX_I = NSE Indices
    chain_url = f"{ENGINE_C_URL}/api/dhan/market/options/chain"
    params = {
        "under_security_id": 13,
        "under_exchange_segment": "IDX_I",
        "expiry": expiry,
        "user_id": USER_ID
    }
    
    print(f"\n[1] Fetching NIFTY Option Chain...")
    try:
        res = requests.get(chain_url, params=params, timeout=20)
        print(f"Response Code: {res.status_code}")
        
        if res.status_code != 200:
             print(f"[FAILED] Fetch Chain: {res.status_code}")
             print(f"Response: {res.text[:500]}")
             return

        try:
            data = res.json()
            print(f"Data: {json.dumps(data)[:200]}...") # Print start of data
        except:
            print(f"FAILED TO PARSE JSON. RAW: {res.text[:500]}")
            return
            
        print(f"Data Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        
        chain = data.get('data', [])
        
        if not chain:
            print("[WARNING] Option Chain is empty. Market closed or invalid expiry?")
            return

        print(f"Chain Type: {type(chain)}")
        if isinstance(chain, dict):
             # If dict, try to convert values to list
             chain = list(chain.values())
        
        if isinstance(chain, str):
             print(f"[ERROR] Chain data is a string: {chain}")
             return

        # 2. Extract Spot Price (Underlying)
        if hasattr(chain, '__getitem__') and len(chain) > 0:
             first_row = chain[0]
        else:
             print(f"Chain not indexable or empty: {chain}")
             return
        spot_price = first_row.get('underlying_price') or first_row.get('last_price') or first_row.get('ltp')
        if not spot_price:
            print("[FAILED] Could not determine Spot Price from chain data")
            print(f"Example Row: {first_row}")
            return
            
        print(f"[SUCCESS] NIFTY Spot Price: {spot_price}")
        
        # 3. Find ATM Strike
        # Simple logic: closest to spot
        # Filter for valid strikes first
        valid_chain = [x for x in chain if (x.get('strike_price') or x.get('strike'))]
        if not valid_chain:
             print("No valid strikes found")
             return

        atm_strike_row = min(valid_chain, key=lambda x: abs((x.get('strike_price') or x.get('strike')) - spot_price))
        atm_strike = atm_strike_row.get('strike_price') or atm_strike_row.get('strike')
        
        print(f"ATM Strike: {atm_strike}")
        
        # 4. Get Premiums (LTP)
        call_ltp = atm_strike_row.get('call_ltp') or atm_strike_row.get('call_close') or 0
        put_ltp = atm_strike_row.get('put_ltp') or atm_strike_row.get('put_close') or 0
        
        print(f"ATM Call LTP: {call_ltp}")
        print(f"ATM Put LTP: {put_ltp}")
        
        if call_ltp == 0 and put_ltp == 0:
             print("[WARNING] Zero premiums found.")
        
        # 5. Run Strategy Analysis (Long Straddle)
        print("\n[2] Analyzing Strategy with REAL Market Data...")
        payload = {
            "strategy_name": "Long Straddle",
            "spot_price": spot_price,
            "params": {
                "strike": atm_strike,
                "call_premium": call_ltp,
                "put_premium": put_ltp,
                "quantity": 50 # 1 Lot
            }
        }
        
        analyze_url = f"{ENGINE_C_URL}/api/dhan/options/strategies/analyze"
        res_analysis = requests.post(analyze_url, json=payload, timeout=20)
        
        if res_analysis.status_code == 200:
            result = res_analysis.json()
            print("[SUCCESS] Strategy Analysis Result:")
            print(json.dumps(result['summary'], indent=2))
        else:
            print(f"[FAILED] Analysis: {res_analysis.status_code} {res_analysis.text}")

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    verify_market_data()
