
from google.cloud import firestore
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_activity_logs():
    try:
        db = firestore.Client()
        logging.info("Checking 'activity_logs' collection...")
        
        # Get recent logs
        logs_ref = db.collection('activity_logs').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5)
        docs = logs_ref.stream()
        
        count = 0
        for doc in docs:
            count += 1
            data = doc.to_dict()
            logging.info(f"✅ Found Log: {doc.id} - Type: {data.get('type')} - Trace: {data.get('trace_id')}")
            
        if count == 0:
            logging.warning("⚠️ No activity logs found.")
            sys.exit(1)
            
        logging.info("Activity Logging verification PASSED.")
        sys.exit(0)

    except Exception as e:
        logging.error(f"Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_activity_logs()
