from google.cloud import firestore
from dhanhq import dhanhq
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = firestore.Client()

def verify_and_fix():
    logger.info("Starting verification repair...")
    docs = db.collection('dhan_credentials').stream()
    
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        logger.info(f"Processing Doc ID: {doc_id}")
        
        creds = data.get('credentials', {})
        client_id = creds.get('client_id')
        access_token = creds.get('access_token')
        
        if not client_id or not access_token:
            logger.warning(f"  -> Missing credentials for {doc_id}")
            continue
            
        try:
            logger.info(f"  -> Verifying Client ID: {client_id}")
            dhan = dhanhq(client_id, access_token)
            funds = dhan.get_fund_limits()
            
            if funds:
                logger.info("  -> Verification SUCCESS! Funds data received.")
                
                # Test Holdings
                try:
                    logger.info("  -> Testing Holdings access...")
                    holdings = dhan.get_holdings()
                    # logger.info(f"  -> Holdings Result: {holdings}") # Noisy
                    if isinstance(holdings, dict) and holdings.get('status') == 'failure':
                         logger.warning(f"  -> Holdings FAILED: {holdings.get('remarks')}")
                    else:
                         logger.info("  -> Holdings SUCCESS.")
                except Exception as he:
                    logger.warning(f"  -> Holdings Exception: {he}")
                
                 # Test Market Data
                try:
                    logger.info("  -> Testing Market Data access (TCS)...")
                    quote = dhan.ohlc_data({'NSE_EQ': [11536]})
                    logger.info(f"  -> Quote Result: {quote}")
                    if isinstance(quote, dict) and quote.get('status') == 'failure':
                         logger.warning(f"  -> Market Data FAILED: {quote.get('remarks')}")
                except Exception as qe:
                    logger.warning(f"  -> Market Data Exception: {qe}")
                
                # Fix status
                updates = {
                    "connection_status": "connected",
                    "isConnected": True,
                    "verified": True
                }
                db.collection('dhan_credentials').document(doc_id).update(updates)
                
                # Also update users collection
                db.collection('users').document(doc_id).set({
                    "dhanConnected": True,
                    "dhanClientId": client_id
                }, merge=True)
                
                logger.info("  -> Database updated with correct status.")
            else:
                logger.warning("  -> Verification FAILED (No funds data returned).")
                
        except Exception as e:
            logger.error(f"  -> Verification Error: {e}")

if __name__ == "__main__":
    verify_and_fix()
