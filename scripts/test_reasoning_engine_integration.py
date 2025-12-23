
import asyncio
import sys
import logging
import os

# Adjust Path to include engine-b src
sys.path.append("c:/workspace/InfinityAI.Pro/backend/engine-b/src")

from google_integrations.reasoning_engine_client import ReasoningEngineClient

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test.ReasoningEngine")

async def test_integration():
    print("\n🔬 Testing Vertex AI Reasoning Engine Integration...")
    client = ReasoningEngineClient()
    
    symbol = "GOOGL"
    print(f"👉 Asking agent to analyze: {symbol}")
    
    try:
        response = await client.analyze_stock(symbol)
        
        print("\n✅ Response Received:")
        print("--------------------------------------------------")
        print(response)
        print("--------------------------------------------------")
        
        if "error" in response:
            print("❌ Agent returned an error.")
            sys.exit(1)
        else:
            print("✅ Agent integrated successfully.")
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Add project root to path
    import os
    sys.path.append("c:/workspace/InfinityAI.Pro")
    
    asyncio.run(test_integration())
