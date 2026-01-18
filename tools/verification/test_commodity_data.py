"""Test commodity market data retrieval and trading hours validation."""
import sys
import os
import json
from datetime import datetime, time
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'engine-c'))

from dhanhq import dhanhq

# Load commodity configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'config', 'commodity_markets_config.json')

def load_commodity_config():
    """Load commodity configuration."""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def is_commodity_market_open():
    """Check if commodity markets are currently open."""
    now = datetime.now().time()
    # MCX trading hours: 9:00 AM to 11:30 PM
    market_open = time(9, 0)
    market_close = time(23, 30)
    
    is_open = market_open <= now <= market_close
    print(f"\nCurrent Time: {now.strftime('%H:%M:%S')}")
    print(f"MCX Market Hours: {market_open.strftime('%H:%M')} - {market_close.strftime('%H:%M')}")
    print(f"Market Status: {'OPEN' if is_open else 'CLOSED'}")
    
    return is_open

def test_commodity_config():
    """Test commodity configuration loading."""
    print("=" * 80)
    print("COMMODITY MARKETS CONFIGURATION TEST")
    print("=" * 80)
    
    config = load_commodity_config()
    
    print(f"\nCommodity Scanning Enabled: {config.get('enabled', False)}")
    print(f"Scan Interval: {config.get('scan_interval_minutes', 'N/A')} minutes")
    print(f"\nConfigured Commodities ({len(config['mcx_commodities'])}):")
    print("-" * 80)
    
    for commodity in config['mcx_commodities']:
        print(f"\n{commodity['display_name']} ({commodity['symbol']})")
        print(f"  Security ID: {commodity['security_id']}")
        print(f"  Exchange: {commodity['exchange_segment']}")
        print(f"  Trading Hours: {commodity['trading_hours']['start']} - {commodity['trading_hours']['end']}")
        print(f"  Lot Size: {commodity['lot_size']}")
        print(f"  Enabled: {commodity.get('enabled', True)}")
    
    print("\n" + "=" * 80)

async def test_commodity_data_fetch(user_id: str = None):
    """Test fetching commodity market data via DhanHQ API."""
    print("\n" + "=" * 80)
    print("COMMODITY MARKET DATA FETCH TEST")
    print("=" * 80)
    
    if not user_id:
        print("\n⚠️ No user_id provided. Skipping live data fetch.")
        print("To test live data, run: python test_commodity_data.py <firebase_user_id>")
        return
    
    try:
        # Import credentials manager
        from src.user_credentials import get_credentials_manager
        
        creds_manager = get_credentials_manager()
        creds = await creds_manager.get_user_credentials(user_id)
        
        if not creds:
            print(f"❌ No credentials found for user {user_id}")
            return
        
        credentials = creds.get("credentials", {})
        client_id = credentials.get("client_id")
        access_token = credentials.get("access_token")
        
        if not client_id or not access_token:
            print(f"❌ Incomplete credentials for user {user_id}")
            return
        
        print(f"\n✅ Credentials loaded for user {user_id}")
        print(f"Client ID: {client_id}")
        
        # Create DhanHQ client
        dhan = dhanhq(client_id, access_token)
        
        # Test fetching data for each commodity
        config = load_commodity_config()
        
        for commodity in config['mcx_commodities']:
            if not commodity.get('enabled', True):
                continue
            
            print(f"\n--- {commodity['display_name']} ---")
            print(f"Security ID: {commodity['security_id']}")
            
            try:
                # Fetch quote
                quote = dhan.get_quote(commodity['security_id'], commodity['exchange_segment'])
                
                if quote and 'data' in quote:
                    data = quote['data']
                    print(f"LTP: ₹{data.get('LTP', 'N/A')}")
                    print(f"Volume: {data.get('volume', 'N/A')}")
                    print(f"Open: ₹{data.get('open', 'N/A')}")
                    print(f"High: ₹{data.get('high', 'N/A')}")
                    print(f"Low: ₹{data.get('low', 'N/A')}")
                    print(f"Close: ₹{data.get('close', 'N/A')}")
                else:
                    print(f"⚠️ No data returned")
                    
            except Exception as e:
                print(f"❌ Error fetching data: {e}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error in commodity data fetch: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test configuration
    test_commodity_config()
    
    # Test market hours
    is_commodity_market_open()
    
    # Test live data fetch if user_id provided
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if user_id:
        asyncio.run(test_commodity_data_fetch(user_id))
    else:
        print("\nTip: To test live commodity data, run:")
        print("   python tools\\test_commodity_data.py <your_firebase_user_id>")
