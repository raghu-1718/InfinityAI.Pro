import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import logging
from google_integrations.reasoning_engine_client import ReasoningEngineClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyAgent")

async def main():
    logger.info("🚀 Starting Agent Connection Verification...")
    
    try:
        # Initialize Client
        client = ReasoningEngineClient()
        logger.info(f"✅ Client Initialized for Agent: {client.agent_id}")
        
        # Test Query
        test_query = "Hello, are you active?"
        logger.info(f"📤 Sending Query: '{test_query}'")
        
        response = await client.query(test_query)
        
        logger.info(f"📥 Received Response: {response}")
        
        if "error" in response:
            logger.error(f"❌ Verification Failed: {response['error']}")
        else:
            logger.info("✅ Verification SUCCESS!")
            
    except Exception as e:
        logger.error(f"❌ Verification Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
