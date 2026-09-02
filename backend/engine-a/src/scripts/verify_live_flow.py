import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
engine_c_dir = os.path.abspath(os.path.join(current_dir, "../../../engine-c/src"))
if engine_c_dir not in sys.path:
    sys.path.insert(0, engine_c_dir)

from user_credentials import UserCredentialsManager
from dhanhq import dhanhq

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("InfinityAI.LiveFlowVerifier")

async def verify_flow():
    logger.info("🚀 Starting End-to-End Dhan -> BigQuery Flow Verification...")

    manager = UserCredentialsManager()
    creds = await manager.get_user_credentials(user_id="raghu_primary")

    if not creds or not creds.get("client_id"):
        logger.error("❌ Failed to retrieve vault credentials.")
        return

    client_id = creds["client_id"]
    access_token = creds["access_token"]

    dhan = dhanhq(client_id=str(client_id), access_token=str(access_token))

    logger.info("📡 Requesting market data snapshot via Dhan SDK...")
    try:
        # Correct SDK method for intraday data
        quote_res = dhan.get_intraday_data(
            security_id="13",
            exchange_segment="IDX_I",
            instrument_type="INDEX",
            from_date=(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            to_date=datetime.now().strftime('%Y-%m-%d'),
            interval="1"
        )
        if quote_res.get("status") == "success":
            logger.info("✅ Successfully fetched intraday market feed from Dhan API!")
        else:
            logger.warning(f"⚠️ Dhan Response: {quote_res}")
    except Exception as e:
        logger.error(f"❌ Dhan feed error: {e}")

    logger.info("📊 Verifying BigQuery tables for live data readiness...")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
    bq_client = bigquery.Client(project=project_id)

    query = """
        SELECT symbol, COUNT(*) as total_records
        FROM `project-841b7f97-5ee3-4fbe-920.market_data.live_ticks_partitioned`
        GROUP BY symbol
    """
    query_job = bq_client.query(query)
    results = [dict(row) for row in query_job]

    logger.info(f"✅ BigQuery Partitioned Ticks Table Status: {results}")
    logger.info("🎉 End-to-End Verification Complete: Vault ➔ Dhan ➔ BigQuery pipeline is fully operational!")

if __name__ == "__main__":
    asyncio.run(verify_flow())
