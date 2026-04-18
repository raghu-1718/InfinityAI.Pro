"""
Circuit Breaker - Trading halt mechanism with Supabase state persistence.
Replaces Firestore state storage with Supabase PostgreSQL.
"""
import logging
import os
from datetime import datetime, timezone
from src.safety_limits import MAX_DAILY_LOSS, MAX_CONSECUTIVE_LOSSES

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
                logger.info("✅ CircuitBreaker: Supabase client initialized")
            else:
                logger.warning("⚠️ SUPABASE_URL or key not set; circuit breaker will use in-memory state only")
        except Exception as e:
            logger.error(f"Failed to init Supabase for circuit breaker: {e}")
    return _db

class TradingHalted(Exception):
    pass

class CircuitBreaker:
    def __init__(self, uid: str = "system"):
        self.uid = uid
        self.consecutive_losses = 0
        self.session_pnl = 0.0
        self.is_tripped = False
        self.trip_reason = None
        self.last_updated = None

        # Load existing state if any
        self.load_state()

    def load_state(self):
        """Load state from Supabase"""
        try:
            db = get_db()
            if not db:
                return

            response = db.table("circuit_breaker_state").select("*").eq("user_id", self.uid).execute()

            if response.data and len(response.data) > 0:
                data = response.data[0]
                self.consecutive_losses = data.get("consecutive_losses", 0)
                self.session_pnl = data.get("session_pnl", 0.0)
                self.is_tripped = data.get("halted", False)
                self.trip_reason = data.get("halt_reason")
                self.last_updated = data.get("updated_at")
                logger.info(f"🔄 CircuitBreaker State Loaded: PL={self.session_pnl}, Losses={self.consecutive_losses}, Halted={self.is_tripped}")
        except Exception as e:
            logger.error(f"Failed to load CircuitBreaker state: {e}")

    def save_state(self):
        """Persist state to Supabase"""
        try:
            db = get_db()
            if not db:
                return

            db.table("circuit_breaker_state").upsert({
                "user_id": self.uid,
                "consecutive_losses": self.consecutive_losses,
                "session_pnl": self.session_pnl,
                "halted": self.is_tripped,
                "halt_reason": self.trip_reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save CircuitBreaker state: {e}")

    def check_session_freshness(self):
        """
        Safety Check: If the state is from a previous day, auto-reset.
        If it's from today, KEEP it (implements Daily Loss Limit persistence).
        """
        if not self.last_updated:
            return  # No prev state, fresh

        now = datetime.now(timezone.utc)

        last_dt = self.last_updated
        # Handle string timestamps from Supabase
        if isinstance(last_dt, str):
            try:
                last_dt = datetime.fromisoformat(last_dt.replace('Z', '+00:00'))
            except Exception:
                return

        if last_dt.date() < now.date():
            logger.info("📅 New Day Detected: Resetting Circuit Breaker State")
            self.reset()
        else:
            logger.info("📅 Same Day Session: Keeping accumulated PnL/Losses")

    def update_trade_result(self, pnl: float):
        """Update state with closed trade result"""
        self.session_pnl += pnl

        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0  # Reset on win

        # Check Triggers
        self.check_limits()

        # Persist (Critical)
        self.save_state()

    def check_limits(self):
        """Check all circuit breaker limits"""
        if self.session_pnl <= MAX_DAILY_LOSS:
            self.trip("MAX_DRAWDOWN_REACHED")
            return  # Trip saves state

        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            self.trip("CONSECUTIVE_LOSSES_LIMIT")

    def trip(self, reason: str):
        self.is_tripped = True
        self.trip_reason = reason
        self.save_state()  # Immediate persist
        logger.critical(f"🛑 CIRCUIT BREAKER TRIPPED: {reason} (PnL: {self.session_pnl}, Losses: {self.consecutive_losses})")
        raise TradingHalted(reason)

    def reset(self):
        self.consecutive_losses = 0
        self.session_pnl = 0.0
        self.is_tripped = False
        self.trip_reason = None
        self.save_state()
