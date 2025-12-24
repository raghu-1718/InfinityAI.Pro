import os
import sys
import pandas as pd
import requests
from datetime import datetime, timedelta
from io import StringIO
try:
    from dhanhq import dhanhq
except ImportError:
    print("Error: 'dhanhq' library not found. Please run 'pip install dhanhq'")
    sys.exit(1)

# Helper to find valid credentials
def get_credentials():
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    
    if not client_id or not access_token:
        print("Credentials not found in environment variables.")
        print("Please enter them below (they will not be saved, only used for this session):")
        client_id = input("Enter Client ID: ").strip()
        access_token = input("Enter Access Token: ").strip()
    
    return client_id, access_token

# Asset Configuration
ASSETS = {
    "CRUDEOIL": {
        "symbol_fragment": "CRUDEOIL", 
        "instrument_type": "FUTCOM", 
        "exchange_segment": "MCX_COMM",
        "is_index": False
    },
    "NIFTY": {
        "symbol_fragment": "NIFTY", 
        "instrument_type": "FUTIDX", 
        "exchange_segment": "NSE_FNO",
        "is_index": True
    },
    "BANKNIFTY": {
        "symbol_fragment": "BANKNIFTY", 
        "instrument_type": "FUTIDX", 
        "exchange_segment": "NSE_FNO",
        "is_index": True
    }
}

def get_security_id(dhan, symbol_key):
    config = ASSETS.get(symbol_key)
    if not config:
        print(f"Unknown asset: {symbol_key}")
        return None
        
    print(f"Fetching Scrip Master for {symbol_key} ({config['instrument_type']})...")
    
    # Fetch Scrip Master CSV (Use cached if possible in future, but fetching fresh for now)
    url = "https://images.dhan.co/api-data/api-scrip-master.csv"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch instrument list: {e}")
        return None

    # Parse CSV
    df = pd.read_csv(StringIO(response.text), low_memory=False)
    
    # Filter
    # 1. Exchange Segment check (Dhan CSV uses 'SEM_EXM_EXCH_ID'. MCX is usually 'MCX', NSE is 'NSE')
    # Actually simpler to filter by Instrument Type and Symbol Name first.
    
    # Filter
    # 1. Exchange Segment check (Dhan CSV uses 'SEM_EXM_EXCH_ID'. MCX is usually 'MCX', NSE is 'NSE')
    # actually simpler to filter by Instrument Type and Symbol Name first.
    
    # NIFTY collision fix: "NIFTY" is substring of "BANKNIFTY". 
    # Must use regex or strict start check.
    # Trading Symbol format: "NIFTY 25DEC 24000 CE" or "NIFTY-25DEC-FUT"
    # Usually starts with the Index Name.
    
    mask = (
        df['SEM_TRADING_SYMBOL'].str.contains(f"^{config['symbol_fragment']}", na=False, case=False, regex=True) & 
        (df['SEM_INSTRUMENT_NAME'] == config['instrument_type'])
    )
    
    subset = df[mask].copy()
    
    if subset.empty:
        print(f"No instruments found for {symbol_key} (Fragment: {config['symbol_fragment']}).")
        return None
        
    # Sort by Expiry
    if 'SEM_EXPIRY_DATE' in subset.columns:
        subset['expiry_dt'] = pd.to_datetime(subset['SEM_EXPIRY_DATE'], errors='coerce')
        current_time = datetime.now()
        active = subset[subset['expiry_dt'] > current_time].sort_values('expiry_dt')
        
        if active.empty:
            print(f"No future expiry contracts for {symbol_key}.")
            return None
            
        target = active.iloc[0] # Nearest expiry
    else:
        # Fallback if no expiry (e.g. Spot), but we asked for Futures
        target = subset.iloc[0]

    print(f"Found: {target['SEM_TRADING_SYMBOL']}")
    print(f"   Expiry: {target.get('SEM_EXPIRY_DATE', 'N/A')}")
    print(f"   ID: {target['SEM_SMST_SECURITY_ID']}")
    
    return str(target['SEM_SMST_SECURITY_ID']), target['SEM_TRADING_SYMBOL']

def fetch_data_for_asset(dhan, symbol_key):
    config = ASSETS[symbol_key]
    
    # 1. Get ID
    sec_info = get_security_id(dhan, symbol_key)
    if not sec_info:
        return None
    sec_id, symbol_name = sec_info
    
    # 2. Fetch
    print(f"Downloading Data for {symbol_name}...")
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=30)
    
    try:
        data = dhan.intraday_minute_data(
            security_id=sec_id,
            exchange_segment=config['exchange_segment'],
            instrument_type=config['instrument_type'],
            from_date=from_date.strftime('%Y-%m-%d'),
            to_date=to_date.strftime('%Y-%m-%d')
        )
    except Exception as e:
        print(f"API Error: {e}")
        return None

    # Process (Reuse logic)
    if not data or 'data' not in data:
        print("No data received.")
        return None
        
    raw = data['data']
    if not raw:
        print("Empty payload.")
        return None

    if 'timestamp' in raw:
        pass 
    elif 'start_Time' in raw:
        raw['timestamp'] = raw.pop('start_Time')
    else:
        # Dhan sometimes returns 'start_time' lowercase?
        # Or returns empty dict.
        print(f"Keys: {raw.keys()}")
        return None
        
    df = pd.DataFrame(raw)
    
    if 'timestamp' in df.columns:
        # Check if it's already datetime or int
        if pd.api.types.is_numeric_dtype(df['timestamp']):
             # If numbers are like 1326220200 (10 digits) -> seconds
             # If 1326220200000 (13 digits) -> ms
             # Dhan usually uses Dhan Time (Exchange time) or standard epoch.
             # Based on API docs snippet: "1326220200" -> Seconds.
             df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    
    # Ensure columns
    cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    if set(cols).issubset(df.columns):
        df = df[cols]
    else:
        print("Missing columns.")
        return None
        
    return df

def main():
    print("=== Dhan Multi-Asset Fetcher ===")
    
    client_id, access_token = get_credentials()
    if not client_id:
        return

    dhan = dhanhq(client_id, access_token)
    
    # Fetch all configured assets
    for key in ["CRUDEOIL", "NIFTY", "BANKNIFTY"]:
        print(f"\n--- Processing {key} ---")
        df = fetch_data_for_asset(dhan, key)
        
        if df is not None:
            filename = f"{key.lower()}_1min_real.csv"
            path = os.path.join("backtest", "data", filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            df.to_csv(path, index=False)
            print(f"Saved to {path} ({len(df)} rows)")
        else:
            print(f"Failed to fetch {key}")

if __name__ == "__main__":
    main()
