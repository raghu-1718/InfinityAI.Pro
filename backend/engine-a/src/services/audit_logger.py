from google.cloud import firestore
from datetime import datetime
import os
import logging
import uuid
import json

logger = logging.getLogger(__name__)

# Initialize DB (Singleton-ish)
_db = None

def get_db():
    global _db
    if _db is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "infinity-ai-pro-dev")
        _db = firestore.Client(project=project_id)
    return _db

class AuditLogger:
    """
    Structured Audit Logger for Trading Safety Events.
    Writes to Firestore 'trade_audit' collection.
    Immutable, persistent, replayable.
    """
    
    def __init__(self):
        self.collection = "trade_audit"

    def log_event(self, uid: str, event: str, details: dict, severity: str = "INFO"):
        """
        Log a critical trading event.
        Fire & Forget (safe).
        """
        try:
            db = get_db()
            doc_data = {
                "uid": uid,
                "event": event,
                "details": details,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": details.get("trace_id") or str(uuid.uuid4()),
                "source": "engine-a"
            }
            
            db.collection(self.collection).add(doc_data)
            logger.info(f"📝 AUDIT LOG: {event} | {json.dumps(details)}")
            
        except Exception as e:
            logger.error(f"❌ AUDIT LOG FAILED: {event} - {e}")

    # Specific Shortcuts
    def log_session_start(self, uid: str, config: dict):
        self.log_event(uid, "SESSION_START", {"config": config}, "INFO")

    def log_session_stop(self, uid: str, reason: str = "MANUAL"):
        self.log_event(uid, "SESSION_STOP", {"reason": reason}, "INFO")
    
    def log_trade_approved(self, uid: str, symbol: str, qty: int, value: float, risk_score: dict):
        self.log_event(uid, "TRADE_APPROVED", {
            "symbol": symbol, "quantity": qty, "value": value, "risk": risk_score
        }, "INFO")

    def log_trade_rejected(self, uid: str, symbol: str, reason: str, details: dict):
        self.log_event(uid, "TRADE_REJECTED", {
            "symbol": symbol, "reason": reason, "details": details
        }, "WARNING")
    
    def log_kill_switch(self, uid: str, reason: str, pnl: float):
        self.log_event(uid, "KILL_SWITCH_TRIGGERED", {
            "reason": reason, "pnl": pnl
        }, "CRITICAL")
