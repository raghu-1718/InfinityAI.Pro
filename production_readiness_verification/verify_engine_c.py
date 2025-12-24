
import asyncio
import os
import sys

# Add project root to path
# Handle hyphenated folder names
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend/engine-c/src')))
from providers.dhan_rest_async import DhanRESTAsync

class MockConnectionPool:
    async def get_session(self):
        import aiohttp
        return aiohttp.ClientSession()

async def verify_engine_c_signatures():
    print("Verifying Engine C Signatures...")
    client = DhanRESTAsync()
    
    # Check method existence
    methods = [
        "place_super_order", "place_forever_order", "place_slice_order",
        "convert_position", "generate_edis_form", "get_ip", "set_ip"
    ]
    
    for m in methods:
        if hasattr(client, m):
            print(f"✅ Method Found: {m}")
        else:
            print(f"❌ Method MISSING: {m}")
            
    print("Engine C Verification Complete")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_engine_c_signatures())
