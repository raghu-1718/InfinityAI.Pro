import requests
import json
import time

ENGINE_B_URL = "https://engine-b-228557716858.us-central1.run.app"
USER_ID = "B79BqvTlaTZltC8uGO3jLxJBBt93"

def trigger_batch_signals():
    url = f"{ENGINE_B_URL}/api/v1/signals/batch"
    
    payload = {
        "symbols": ["CRUDEOIL", "GOLD", "RELIANCE", "TCS", "NIFTY"],
        "user_id": USER_ID,
        "fast": True  # Use fast mode for quick verification
    }
    
    print(f"Triggering batch signal generation at {url}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=60)
        duration = time.time() - start_time
        
        print(f"\nResponse Code: {response.status_code}")
        print(f"Time Taken: {duration:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSuccess! Response:")
            print(f"  Total Signals Generated: {data.get('total', 0)}")
            print(f"  Signals Stored: {data.get('stored', 'Unknown')} (This is the key field!)")
            
            # Print first few signals
            signals = data.get('signals', [])
            if signals:
                print(f"\nFirst generated signal: {signals[0].get('symbol')} - {signals[0].get('signal')}")
        else:
            print(f"\nFailed: {response.text}")
            
    except Exception as e:
        print(f"\nError triggering signals: {e}")

if __name__ == "__main__":
    trigger_batch_signals()
