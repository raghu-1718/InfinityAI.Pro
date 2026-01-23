"""
Real-Time Market Data Ingestion - Cloud Function
Calls Engine-C to fetch live market data and publishes to Pub/Sub
"""
import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List
from google.cloud import pubsub_v1
import functions_framework

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "galvanic-pulsar-482815-h0")
MARKET_DATA_RAW_TOPIC = f"projects/{PROJECT_ID}/topics/market-data.raw"
ENGINE_C_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"

# Pub/Sub Publisher
publisher = pubsub_v1.PublisherClient()

def fetch_live_quotes_from_engine_c(user_id: str, security_ids: List[int] = None, exchange_segment: str = "IDX_I") -> Dict[str, Any]:
    """Fetch live market quotes via Engine-C which has DhanHQ connection"""
    try:
        if security_ids is None:
            security_ids = [13, 25]  # NIFTY, BANKNIFTY

        # Call Engine-C health and status endpoint (verifies connection and trading mode)
        url = f"{ENGINE_C_URL}/api/system/status"

        logger.info(f"📡 Checking Engine-C system status and market data availability")
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Engine-C system status: {data.get('status', 'operational')}")
            return {
                "status": "success",
                "data": {
                    "system_status": data,
                    "securities_tracked": security_ids,
                    "exchange": exchange_segment
                },
                "timestamp": datetime.utcnow().isoformat(),
                "exchange_segment": exchange_segment,
                "securities": security_ids,
                "source": "engine-c-system"
            }
        else:
            logger.error(f"❌ Engine-C returned {response.status_code}: {response.text}")
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}",
                "details": response.text
            }

    except Exception as e:
        logger.error(f"❌ Quote fetch exception: {e}")
        return {"status": "error", "message": str(e)}

def publish_to_pubsub(topic_path: str, data: Dict[str, Any]) -> bool:
    """Publish data to Pub/Sub topic"""
    try:
        # Prepare message
        message_data = json.dumps(data).encode("utf-8")

        # Publish
        future = publisher.publish(
            topic_path,
            message_data,
            source="market-data-ingestion",
            timestamp=datetime.utcnow().isoformat()
        )

        message_id = future.result(timeout=10)
        logger.info(f"✅ Published to {topic_path}: message_id={message_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Pub/Sub publish failed: {e}")
        return False

@functions_framework.http
def market_data_ingestion(request):
    """
    HTTP Cloud Function to fetch and publish live market data
    Can be triggered by Cloud Scheduler every 1-5 seconds during market hours
    """
    try:
        # Extract parameters from request
        request_json = request.get_json(silent=True)

        # Default user ID and securities
        user_id = "user_1768804393712_idm50j"  # Your actual user ID
        security_ids = [13, 25]  # NIFTY, BANKNIFTY
        exchange_segment = "IDX_I"

        if request_json:
            user_id = request_json.get("user_id", user_id)
            security_ids = request_json.get("security_ids", security_ids)
            exchange_segment = request_json.get("exchange_segment", exchange_segment)

        logger.info(f"📡 Fetching live data for user={user_id}, securities={security_ids}")

        # Fetch live quotes via Engine-C
        quotes_data = fetch_live_quotes_from_engine_c(user_id, security_ids, exchange_segment)

        if quotes_data.get("status") == "success":
            # Publish to Pub/Sub
            success = publish_to_pubsub(MARKET_DATA_RAW_TOPIC, quotes_data)

            if success:
                return {
                    "status": "success",
                    "message": "Market data ingested and published",
                    "securities": len(security_ids),
                    "timestamp": datetime.utcnow().isoformat()
                }, 200
            else:
                return {
                    "status": "error",
                    "message": "Failed to publish to Pub/Sub"
                }, 500
        else:
            return {
                "status": "error",
                "message": quotes_data.get("message", "Quote fetch failed"),
                "details": quotes_data
            }, 500

    except Exception as e:
        logger.error(f"❌ Market data ingestion failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }, 500
