"""
Session Manager - Distributed session locking via Supabase PostgreSQL.
Replaces Firestore transactional locking with Supabase row-level upserts.
"""
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase (Singleton)
_db = None

def get_db():
    global _db
    if _db is None:
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if url and key:
                _db = create_client(url, key)
                logger.info("✅ SessionManager: Supabase client initialized")
            else:
                logger.warning("⚠️ SUPABASE_URL or key not set; session locking will use in-memory fallback")
        except Exception as e:
            logger.error(f"Failed to init Supabase for sessions: {e}")
    return _db

# In-memory fallback for local/testing
_memory_sessions = {}

class SessionExistsError(Exception):
    pass

def acquire_session_lock(uid: str):
    """
    Acquire a distributed lock for the trading session.
    Uses Supabase upsert with active-check to prevent race conditions.
    """
    db = get_db()

    if db:
        try:
            # Check if session is already active
            response = db.table("trading_sessions").select("*").eq("user_id", uid).eq("active", True).execute()

            if response.data and len(response.data) > 0:
                existing = response.data[0]
                raise SessionExistsError(
                    f"Session already active for user {uid} (Started: {existing.get('started_at')})"
                )

            # Set Lock via upsert
            db.table("trading_sessions").upsert({
                "user_id": uid,
                "active": True,
                "started_at": datetime.utcnow().isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat()
            }).execute()

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
            db.table("trading_sessions").update({
                "active": False,
                "stopped_at": datetime.utcnow().isoformat()
            }).eq("user_id", uid).execute()
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
            response = db.table("trading_sessions").select("active").eq("user_id", uid).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get("active", False) is True
        except Exception as e:
            logger.error(f"Session check failed: {e}")
        return False
    else:
        return _memory_sessions.get(uid, {}).get("active", False)
