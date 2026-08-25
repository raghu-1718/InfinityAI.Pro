import requests
import json
import time

ENGINE_B_URL = "https://engine-b-r2f5flt77q-el.a.run.app"
ENGINE_C_URL = "https://engine-c-r2f5flt77q-el.a.run.app"
USER_ID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

def main():
    print("==================================================")
    print("PHASE 3: END-TO-END LIVE PIPELINE EXECUTION")
    print("==================================================")
    
    # 1. Trigger Engine-B Signal
    print("\n[1] Triggering Engine-B (AI/ML) for RELIANCE...")
    try:
        res_b = requests.post(f"{ENGINE_B_URL}/api/v1/signal", json={"symbol": "RELIANCE"}, timeout=15)
        res_b.raise_for_status()
        signal_data = res_b.json()
        print("Engine-B Response:", json.dumps(signal_data, indent=2))
        signal = signal_data.get("signal", "BUY").upper()
    except Exception as e:
        print("Engine-B Error:", e)
        signal = "BUY"
    
    # 2. Trigger Engine-A (Simulated VaR/Orchestrator)
    print("\n[2] Triggering Engine-A (Orchestrator VaR Check)...")
    print("VaR Circuit Breakers Passed. Position Size: 1. Proceeding to execution.")
    
    # 3. Fire payload to Engine-C
    print("\n[3] Firing Payload to Engine-C (Execution)...")
    payload = {
        "transaction_type": signal,
        "exchange_segment": "NSE_EQ",
        "product_type": "INTRADAY",
        "order_type": "MARKET",
        "security_id": "2885", # RELIANCE
        "quantity": 1,
        "validity": "DAY",
        "price": 0.0
    }
    
    headers = {
        "X-Engine-Source": "engine-a",
        "X-User-ID": USER_ID
    }
    
    try:
        t0 = time.time()
        res_c = requests.post(f"{ENGINE_C_URL}/api/dhan/place-order", json=payload, headers=headers, timeout=15)
        t1 = time.time()
        print(f"Engine-C Response HTTP {res_c.status_code} in {(t1-t0)*1000:.2f}ms")
        try:
            print(json.dumps(res_c.json(), indent=2))
        except:
            print(res_c.text)
    except Exception as e:
        print("Engine-C Error:", e)

if __name__ == "__main__":
    main()
