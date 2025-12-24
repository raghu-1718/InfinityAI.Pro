
import asyncio
import os
import sys

# Add project root to path
# Handle hyphenated folder names
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend/engine-b/src')))
from providers.dhan_data_async import DhanMarketDataClient

async def verify_engine_b_signatures():
    print("Verifying Engine B Signatures...")
    client = DhanMarketDataClient()
    
    # Check method existence
    methods = [
        "get_intraday_charts", "get_historical_charts", 
        "get_rolling_option_chain", "get_quote"
    ]
    
    for m in methods:
        if hasattr(client, m):
            print(f"✅ Method Found: {m}")
        else:
            print(f"❌ Method MISSING: {m}")
            
    print("Engine B Verification Complete")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_engine_b_signatures())
