import requests
import json
import sys
import os

# Engine C URL
ENGINE_C_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"

def test_strategy_analysis():
    print(f"Testing Option Strategy Analysis at {ENGINE_C_URL}...")
    
    endpoint = f"{ENGINE_C_URL}/api/dhan/options/strategies/analyze"
    
    # Test Case 1: Long Straddle (Simple)
    payload_1 = {
        "strategy_name": "Long Straddle",
        "spot_price": 24000,
        "params": {
            "strike": 24000,
            "call_premium": 150,
            "put_premium": 140,
            "quantity": 50
        }
    }
    
    print(f"\n[Test 1] Sending payload: {json.dumps(payload_1, indent=2)}")
    try:
        response = requests.post(endpoint, json=payload_1, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Analysis Received:")
            print(json.dumps(data['summary'], indent=2))
            print(f"Payoff Chart Points: {len(data['payoff_chart'])}")
        else:
            print(f"[FAILED] Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

    # Test Case 2: Bear Put Spread
    payload_2 = {
        "strategy_name": "Bear Put Spread",
        "spot_price": 24000,
        "params": {
            "buy_strike": 24000,
            "sell_strike": 23800,
            "buy_premium": 140,
            "sell_premium": 80,
            "quantity": 50
        }
    }
    
    print(f"\n[Test 2] Sending payload: {json.dumps(payload_2, indent=2)}")
    try:
        response = requests.post(endpoint, json=payload_2, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Analysis Received:")
            print(json.dumps(data['summary'], indent=2))
        else:
            print(f"[FAILED] Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

    # Test Case 3: Iron Condor (Complex Params)
    # Frontend sends: put_long_strike, put_short_strike etc.
    payload_3 = {
        "strategy_name": "Iron Condor",
        "spot_price": 24000,
        "params": {
            "put_long_strike": 23500,
            "put_short_strike": 23700,
            "call_short_strike": 24300,
            "call_long_strike": 24500,
            "put_long_premium": 20,
            "put_short_premium": 45,
            "call_short_premium": 50,
            "call_long_premium": 25,
            "quantity": 50
        }
    }
    print(f"\n[Test 3] Sending payload: {json.dumps(payload_3, indent=2)}")
    try:
        response = requests.post(endpoint, json=payload_3, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Analysis Received:")
            print(json.dumps(data['summary'], indent=2))
        else:
            print(f"[FAILED] Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    test_strategy_analysis()
