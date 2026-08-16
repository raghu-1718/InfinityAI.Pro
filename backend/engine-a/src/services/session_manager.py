"""
Session Manager - Distributed session locking via Google Cloud Firestore.
"""
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Initialize Google Cloud Firestore (Singleton)
_db = None

def get_db():
    global _db
    if _db is None:
        try:
            from google.cloud import firestore
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            _db = firestore.Client(project=project_id)
            logger.info("✅ SessionManager: Google Cloud Firestore client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not init Firestore for sessions (using in-memory fallback): {e}")
    return _db

# In-memory fallback for local/testing
_memory_sessions = {}

class SessionExistsError(Exception):
    pass

def acquire_session_lock(uid: str):
    """
    Acquire a distributed lock for the trading session.
    Uses Google Cloud Firestore to prevent race conditions.
    """
    db = get_db()

    if db:
        try:
            doc_ref = db.collection("trading_sessions").document(uid)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                if data.get("active") is True:
                    raise SessionExistsError(
                        f"Session already active for user {uid} (Started: {data.get('started_at')})"
                    )

            # Set Lock via Firestore
            doc_ref.set({
                "user_id": uid,
                "active": True,
                "started_at": datetime.utcnow().isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat()
            }, merge=True)

        except SessionExistsError:
            raise
        except Exception as e:
            logger.error(f"Session lock acquisition failed: {e}")
            raise
    else:
        # In-memory fallback
        if uid in _memory_sessions and _memory_sessions[uid].get("active"):
            raise SessionExistsError(f"Session already active for user {uid}")
        _memory_sessions[uid] = {
            "active": True,
            "started_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat()
        }

    logger.info(f"🔒 Session Lock Acquired: {uid}")

def release_session_lock(uid: str):
    """
    Release the session lock.
    Idempotent: Can be called multiple times safely.
    """
    db = get_db()

    if db:
        try:
            db.collection("trading_sessions").document(uid).update({
                "active": False,
                "stopped_at": datetime.utcnow().isoformat()
            })
            logger.info(f"🔓 Session Lock Released: {uid}")
        except Exception as e:
            logger.warning(f"Session lock release warning: {e}")
    else:
        if uid in _memory_sessions:
            _memory_sessions[uid]["active"] = False
        logger.info(f"🔓 Session Lock Released (in-memory): {uid}")

def check_session_active(uid: str) -> bool:
    db = get_db()

    if db:
        try:
            doc = db.collection("trading_sessions").document(uid).get()
            if doc.exists:
                return doc.to_dict().get("active", False) is True
        except Exception as e:
            logger.error(f"Session check failed: {e}")
        return False
    else:
        return _memory_sessions.get(uid, {}).get("active", False)

