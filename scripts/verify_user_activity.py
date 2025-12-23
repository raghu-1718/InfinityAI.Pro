
from google.cloud import firestore
import logging
from datetime import datetime, timedelta
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def fetch_user_activity(user_id=None, limit=50):
    try:
        db = firestore.Client()
        print(f"\nSearching Activity Logs (Limit: {limit})...\n")
        
        # Base query
        query = db.collection('activity_logs').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        
        # Filter by user if provided (Client-side filtering might be needed if composite index missing)
        # But 'activity_logs' usually has 'user_id' field.
        
        docs = query.stream()
        
        activities = []
        for doc in docs:
            data = doc.to_dict()
            # Optional: Client-side filter if index issue
            if user_id and data.get('user_id') != user_id and data.get('user_id') != 'system':
                continue
                
            activities.append(data)

        if not activities:
            print("No activity logs found.")
            return

        print(f"{'TIMESTAMP':<25} | {'TYPE':<20} | {'DESCRIPTION'}")
        print("-" * 100)
        
        for act in activities:
            ts = act.get('timestamp')
            if isinstance(ts, datetime):
                # Apply timezone correction if needed, assuming UTC
                ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
            else:
                ts_str = str(ts)
                
            # Sanitize description for printing
            desc = act.get('description', 'N/A').encode('ascii', 'ignore').decode('ascii')
                
            print(f"{ts_str:<25} | {act.get('type', 'N/A'):<20} | {desc}")
            
            # Print metadata if configured/relevant (users want "complete activity")
            meta = act.get('metadata', {})
            if meta:
                print(f"   + Metadata: {meta}")
        
        print("\nActivity verification complete.\n")

    except Exception as e:
        logging.error(f"Failed to fetch logs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Fetch all recent logs to catch the user's "dashboard" actions
    fetch_user_activity(limit=20)
