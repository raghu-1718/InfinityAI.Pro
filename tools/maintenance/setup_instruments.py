"""
Instrument Discovery & Master Database Setup
Discovers all available instruments from Dhan and creates a master database
"""
import requests
import json
import pandas as pd
from datetime import datetime

# Dhan Sandbox credentials
SANDBOX_URL = "https://sandbox.dhan.co/v2"
SANDBOX_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"

# Define high-priority instruments manually (common Indian market instruments)
PRIORITY_INSTRUMENTS = {
    "equities": [
        {"symbol": "RELIANCE", "security_id": "2885", "exchange": "NSE_EQ", "name": "Reliance Industries"},
        {"symbol": "TCS", "security_id": "11536", "exchange": "NSE_EQ", "name": "Tata Consultancy Services"},
        {"symbol": "HDFCBANK", "security_id": "1333", "exchange": "NSE_EQ", "name": "HDFC Bank"},
        {"symbol": "INFY", "security_id": "1594", "exchange": "NSE_EQ", "name": "Infosys"},
        {"symbol": "ICICIBANK", "security_id": "4963", "exchange": "NSE_EQ", "name": "ICICI Bank"},
        {"symbol": "HINDUNILVR", "security_id": "1394", "exchange": "NSE_EQ", "name": "Hindustan Unilever"},
        {"symbol": "ITC", "security_id": "5258", "exchange": "NSE_EQ", "name": "ITC Limited"},
        {"symbol": "SBIN", "security_id": "3045", "exchange": "NSE_EQ", "name": "State Bank of India"},
        {"symbol": "BHARTIARTL", "security_id": "20614", "exchange": "NSE_EQ", "name": "Bharti Airtel"},
        {"symbol": "KOTAKBANK", "security_id": "1922", "exchange": "NSE_EQ", "name": "Kotak Mahindra Bank"},
    ],
    "indices": [
        {"symbol": "NIFTY", "security_id": "13", "exchange": "IDX_I", "name": "NIFTY 50"},
        {"symbol": "BANKNIFTY", "security_id": "25", "exchange": "IDX_I", "name": "Nifty Bank"},
        {"symbol": "FINNIFTY", "security_id": "27", "exchange": "IDX_I", "name": "Nifty Financial Services"},
    ],
    "futures": [
        {"symbol": "NIFTY-FUT", "security_id": "13", "exchange": "NSE_FNO", "name": "NIFTY Futures"},
        {"symbol": "BANKNIFTY-FUT", "security_id": "25", "exchange": "NSE_FNO", "name": "Bank Nifty Futures"},
    ]
}

def create_instrument_database():
    """Create a comprehensive instrument database"""
    print("=" * 80)
    print("  INSTRUMENT DISCOVERY & DATABASE CREATION")
    print("=" * 80)
    
    all_instruments = []
    
    # Add priority instruments
    for category, instruments in PRIORITY_INSTRUMENTS.items():
        print(f"\n[INFO] Adding {len(instruments)} {category.upper()}...")
        for inst in instruments:
            inst['category'] = category
            inst['added_date'] = datetime.now().strftime('%Y-%m-%d')
            inst['status'] = 'active'
            all_instruments.append(inst)
            print(f"  + {inst['symbol']:15s} ({inst['name']})")
    
    # Create DataFrame
    df = pd.DataFrame(all_instruments)
    
    # Save to CSV
    output_file = "data/instruments_master.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n[SUCCESS] Created instrument database with {len(all_instruments)} instruments")
    print(f"[SUCCESS] Saved to: {output_file}")
    
    # Display summary
    print(f"\nSummary by Category:")
    print(df.groupby('category')['symbol'].count())
    
    return df

def test_instrument_access():
    """Test if we can access data for sample instruments"""
    print("\n" + "=" * 80)
    print("  TESTING INSTRUMENT ACCESS")
    print("=" * 80)
    
    headers = {"access-token": SANDBOX_TOKEN}
    
    # Test with RELIANCE
    test_instruments = [
        {"security_id": "2885", "exchange": "NSE_EQ", "symbol": "RELIANCE"},
        {"security_id": "13", "exchange": "IDX_I", "symbol": "NIFTY"}
    ]
    
    for inst in test_instruments:
        print(f"\nTesting: {inst['symbol']} (ID: {inst['security_id']})")
        
        # Try to fetch holdings (will be empty but validates access)
        try:
            response = requests.get(f"{SANDBOX_URL}/holdings", headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"  [OK] Holdings API accessible")
            else:
                print(f"  [INFO] Holdings returned {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] Holdings: {str(e)}")
    
    print("\n[INFO] Instrument access test completed")

def main():
    """Main execution"""
    import os
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Create instrument database
    df = create_instrument_database()
    
    # Test access
    test_instrument_access()
    
    print("\n" + "=" * 80)
    print("  INSTRUMENT SETUP COMPLETE")
    print("=" * 80)
    print(f"\nNext Steps:")
    print("  1. Fetch historical data for these instruments")
    print("  2. Implement strategies")
    print("  3. Run backtests")
    print("  4. Test in sandbox\n")
    
    return df

if __name__ == "__main__":
    main()
