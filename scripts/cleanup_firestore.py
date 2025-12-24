import firebase_admin
from firebase_admin import credentials, firestore
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_firestore():
    """Wipe all activity data for a fresh start"""
    try:
        # Initialize (assumes ADC or env var set)
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        
        db = firestore.client()
        
        # Collections to wipe
        collections_to_wipe = [
            'activity_logs',
            'trading_sessions',
            'signals',
            'orders',
            'background_trading_config'
        ]
        
        logger.info("🧹 Starting Firestore Cleanup...")
        
        for coll_name in collections_to_wipe:
            coll_ref = db.collection(coll_name)
            docs = list(coll_ref.limit(500).stream())
            
            if not docs:
                logger.info(f"✨ Collection '{coll_name}' is already empty.")
                continue
                
            deleted_count = 0
            batch = db.batch()
            
            for doc in docs:
                batch.delete(doc.reference)
                deleted_count += 1
                if deleted_count % 400 == 0:
                     batch.commit()
                     batch = db.batch()
            
            batch.commit()
            logger.info(f"🗑️ Deleted {deleted_count} docs from '{coll_name}'")

        # Special handling for User Activity (Subcollections)
        users = list(db.collection('users').stream())
        logger.info(f"👥 Checking {len(users)} users for activity cleanup...")
        
        for user in users:
            activity_ref = user.reference.collection('activity')
            activities = list(activity_ref.limit(500).stream())
            if activities:
                batch = db.batch()
                for doc in activities:
                    batch.delete(doc.reference)
                batch.commit()
                logger.info(f"  - Cleaned activity for user {user.id}")

        logger.info("🎉 Firestore Cleanup Complete! System is ready for fresh deployment.")

    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    cleanup_firestore()
