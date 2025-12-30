from google.cloud import firestore
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Initialize DB (Singleton-ish)
_db = None

def get_db():
    global _db
    if _db is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "infinity-ai-pro-dev")
        _db = firestore.Client(project=project_id)
    return _db

class SessionExistsError(Exception):
    pass

def acquire_session_lock(uid: str):
    """
    Acquire a distributed lock for the trading session.
    Atomic: Prevents race conditions.
    """
    db = get_db()
    ref = db.collection("trading_sessions").document(uid)

    @firestore.transactional
    def _txn(transaction):
        snap = ref.get(transaction=transaction)
        
        # Check if active is True
        if snap.exists:
            data = snap.to_dict()
            if data.get("active"):
                raise SessionExistsError(f"Session already active for user {uid} (Started: {data.get('started_at')})")

        # Set Lock
        transaction.set(ref, {
            "active": True,
            "user_id": uid,
            "started_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat()
        }, merge=True)

    transaction = db.transaction()
    _txn(transaction)
    logger.info(f"🔒 Session Lock Acquired: {uid}")

def release_session_lock(uid: str):
    """
    Release the session lock.
    Idempotent: Can be called multiple times.
    """
    db = get_db()
    ref = db.collection("trading_sessions").document(uid)
    
    try:
        ref.update({
            "active": False,
            "stopped_at": datetime.utcnow().isoformat()
        })
        logger.info(f"🔓 Session Lock Released: {uid}")
    except Exception as e:
        logger.warning(f"Session lock release warning (might be already deleted/updated): {e}")

def check_session_active(uid: str) -> bool:
    db = get_db()
    doc = db.collection("trading_sessions").document(uid).get()
    return doc.exists and doc.to_dict().get("active") is True
