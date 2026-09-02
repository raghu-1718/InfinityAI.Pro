import os
import sys
import logging
from dotenv import load_dotenv
from google.cloud import firestore
from dhanhq import dhanhq

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("InfinityAI.DhanVerifier")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
user_id = os.getenv("USER_ID", "znyNtT2lW3MKHqFrVA6E0A2Iv3N2")

logger.info(f"🔥 Connecting to Firebase Firestore for user: {user_id}...")

client_id = None
access_token = None

try:
    # Initialize Firestore client using project GCP credentials
    db = firestore.Client(project=project_id)

    # Check standard user credentials path in Firestore
    doc_ref = db.collection("users").document(user_id).collection("credentials").document("dhan")
    doc = doc_ref.get()

    if not doc.exists:
        # Fallback to checking the user document directly
        doc = doc_ref = db.collection("users").document(user_id).get()

    if doc.exists:
        data = doc.to_dict()
        logger.info(f"📄 Firestore Document Fields Found: {list(data.keys())}")

        # Map your Firestore fields
        client_id = data.get("dhanClientId") or data.get("client_id") or os.getenv("DHAN_CLIENT_ID")
        access_token = data.get("dhanAccessToken") or data.get("access_token") or data.get("token")
    else:
        logger.warning("⚠️ User document not found in Firestore, falling back to .env")

except Exception as e:
    logger.error(f"❌ Firestore retrieval error: {e}")

# Fallback to environment variables if needed
if not client_id:
    client_id = os.getenv("DHAN_CLIENT_ID")
if not access_token:
    access_token = os.getenv("DHAN_ACCESS_TOKEN")

if not client_id or not access_token:
    logger.error("❌ Could not resolve Client ID or Access Token.")
    sys.exit(1)

logger.info(f"🔑 Testing Dhan connection for Client ID: {str(client_id)[:4]}****")

try:
    dhan = dhanhq(client_id=str(client_id), access_token=str(access_token))
    fund_response = dhan.get_fund_limits()

    if fund_response.get("status") == "success" or "availabelBalance" in str(fund_response):
        balance = fund_response.get("data", {}).get("availabelBalance", fund_response.get("availabelBalance", "N/A"))
        logger.info("🎉 DhanHQ API Connected Successfully via Firebase Credentials!")
        logger.info(f"💰 Available Trading Balance: ₹{balance}")
    else:
        logger.error(f"❌ Dhan API Error: {fund_response}")

except Exception as e:
    logger.error(f"❌ Dhan Authentication Failed: {e}")
