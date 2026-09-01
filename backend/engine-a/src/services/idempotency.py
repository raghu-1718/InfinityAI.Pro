"""
Pub/Sub Message Idempotency Manager
InfinityAI.Pro - Institutional Trading Platform

Ensures exactly-once processing semantics for Pub/Sub push webhooks
by storing and checking message IDs in Firestore `processed_message_ids`.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from google.cloud import firestore

logger = logging.getLogger("InfinityAI.IdempotencyManager")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "processed_message_ids"

class IdempotencyManager:
    """Manages deduplication of Pub/Sub push messages using Firestore"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        try:
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"✅ IdempotencyManager initialized for collection [{COLLECTION_NAME}]")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore client in IdempotencyManager: {e}")
            self.db = None

    def check_and_claim_message(self, message_id: str, handler_name: str, topic: Optional[str] = None) -> bool:
        """
        Atomically checks if a message_id has already been processed.
        If not processed, records the message_id and returns True (proceed).
        If already processed, returns False (skip duplicate).
        """
        if not message_id or not self.db:
            return True  # Fallback: proceed if no ID or no DB

        doc_ref = self.db.collection(COLLECTION_NAME).document(str(message_id))
        
        try:
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                logger.warning(
                    f"⚠️ SKIPPED_DUPLICATE_PUBSUB_MESSAGE: Message ID [{message_id}] was already processed "
                    f"by [{data.get('handler')}] at {data.get('processed_at_ist') or data.get('processed_at')}."
                )
                return False

            # Record message claiming
            now_utc = datetime.now(timezone.utc)
            ist_time = now_utc + timedelta(hours=5, minutes=30)
            expire_at = now_utc + timedelta(days=7)  # 7-day TTL

            payload = {
                "message_id": str(message_id),
                "handler": handler_name,
                "topic": topic,
                "processed_at": now_utc.isoformat(),
                "processed_at_ist": ist_time.strftime("%Y-%m-%d %H:%M:%S IST"),
                "expires_at": expire_at.isoformat()
            }
            doc_ref.set(payload)
            logger.info(f"🔒 Claimed Pub/Sub message ID [{message_id}] for handler [{handler_name}]")
            return True

        except Exception as e:
            logger.error(f"❌ Idempotency check error for message [{message_id}]: {e}")
            return True  # Avoid dropping messages on transient Firestore error

IDEMPOTENCY_MANAGER = IdempotencyManager()
