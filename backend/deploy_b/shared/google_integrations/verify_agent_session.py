import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import logging
from google_integrations.reasoning_engine_client import ReasoningEngineClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyAgentSession")

async def main():
    logger.info("🚀 Starting Agent Session Verification...")
    
    try:
        # Initialize Client
        client = ReasoningEngineClient()
        logger.info(f"✅ Client Initialized for Agent: {client.agent_id}")
        
        # Test create_session
        logger.info(f"____ Calling create_session() ____")
        
        response = await client.create_session()
        
        logger.info(f"📥 Received Response: {response}")
        
        if "error" in response:
            logger.error(f"❌ Verification Failed: {response['error']}")
            logger.error(f"Details: {response.get('details')}")
        else:
            logger.info("✅ Verification SUCCESS! (create_session worked)")
            
    except Exception as e:
        logger.error(f"❌ Verification Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
