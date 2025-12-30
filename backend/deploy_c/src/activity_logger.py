import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from google.cloud import firestore

logger = logging.getLogger(__name__)

class ActivityLogger:
    """
    Logs user activities and system events to Firestore 'activity_logs' collection.
    Used for user-facing activity feeds and system auditing.
    """

    def __init__(self, db_client: Optional[firestore.Client] = None):
        self.db = db_client or firestore.Client()
        self.collection = "activity_logs"
        logger.info("✅ ActivityLogger initialized")

    async def log_activity(
        self,
        user_id: str,
        activity_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        severity: str = "info"
    ) -> str:
        """
        Log an activity to Firestore.

        Args:
            user_id: The ID of the user associated with the activity.
            activity_type: Category (e.g., 'ORDER_PLACED', 'LOGIN', 'SYSTEM_EVENT').
            description: Human-readable description.
            metadata: Additional structured data (e.g., order details, error info).
            trace_id: Distributed trace ID for correlation.
            severity: 'info', 'warning', 'error', 'success'.

        Returns:
            The ID of the created log document.
        """
        try:
            timestamp = datetime.utcnow()
            doc_data = {
                "user_id": user_id,
                "type": activity_type,
                "description": description,
                "timestamp": timestamp,
                "metadata": metadata or {},
                "trace_id": trace_id or str(uuid.uuid4()),
                "severity": severity,
                "source": "engine-c"
            }

            # Use a time-sorted ID for easier querying if needed, or let Firestore auto-gen
            # Auto-gen is usually safer for hot-spotting prevention in high/write scenarios
            update_time, doc_ref = self.db.collection(self.collection).add(doc_data)
            
            logger.info(f"📝 Activity logged: {activity_type} for {user_id} (Trace: {trace_id})")
            return doc_ref.id

        except Exception as e:
            logger.error(f"❌ Failed to log activity: {e}")
            # We don't want logging failures to crash the main transaction
            return ""
