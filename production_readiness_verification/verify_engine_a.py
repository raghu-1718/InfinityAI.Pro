
import asyncio
import os
import sys

# Add project root to path
# Handle hyphenated folder names
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend/engine-a/src')))
from providers.dhan import DhanProvider

async def verify_engine_a_signatures():
    print("Verifying Engine A Signatures...")
    client = DhanProvider()
    
    # Check method existence
    methods = [
        "get_kill_switch_status", "set_kill_switch", 
        "calculate_margin", "get_ledger"
    ]
    
    for m in methods:
        if hasattr(client, m):
            print(f"✅ Method Found: {m}")
        else:
            print(f"❌ Method MISSING: {m}")
            
    print("Engine A Verification Complete")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_engine_a_signatures())
