import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
engine_c_dir = os.path.abspath(os.path.join(current_dir, "../../../engine-c/src"))
if engine_c_dir not in sys.path:
    sys.path.insert(0, engine_c_dir)

from user_credentials import UserCredentialsManager
from dhanhq import dhanhq

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("InfinityAI.VaultVerifier")

async def main():
    logger.info("🔐 Initializing InfinityAI UserCredentialsManager vault...")
    manager = UserCredentialsManager()

    # Await the async method
    creds = await manager.get_user_credentials(user_id="raghu_primary")

    if not creds or not creds.get("client_id") or not creds.get("access_token"):
        logger.error("❌ Failed to retrieve or decrypt credentials from Firestore vault.")
        sys.exit(1)

    client_id = creds["client_id"]
    access_token = creds["access_token"]

    logger.info(f"🔑 Successfully decrypted vault credentials for Client ID: {client_id}")

    try:
        dhan = dhanhq(client_id=str(client_id), access_token=str(access_token))
        fund_response = dhan.get_fund_limits()

        if fund_response.get("status") == "success" or "availabelBalance" in str(fund_response):
            balance = fund_response.get("data", {}).get("availabelBalance", fund_response.get("availabelBalance", "N/A"))
            logger.info("🎉 DhanHQ API Connected Successfully via Vault Encryption!")
            logger.info(f"💰 Available Trading Balance: ₹{balance}")
        else:
            logger.error(f"❌ Dhan API Error: {fund_response}")

    except Exception as e:
        logger.error(f"❌ Dhan Authentication Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
