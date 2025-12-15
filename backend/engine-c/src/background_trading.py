"""
Background Trading System for InfinityAI.Pro
Implements persistent trading that continues even when browser is closed.
Uses Firestore for state management and Cloud Scheduler for periodic execution.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class TradingState(Enum):
    """Trading session states"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class ActivityType(Enum):
    """Activity log types"""
    LOGIN = "login"
    LOGOUT = "logout"
    TRADING_START = "trading_start"
    TRADING_STOP = "trading_stop"
    TRADE_EXECUTED = "trade_executed"
    TRADE_FAILED = "trade_failed"
    SIGNAL_GENERATED = "signal_generated"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    FUNDS_CHECK = "funds_check"
    SETTINGS_CHANGED = "settings_changed"
    API_CALL = "api_call"
    ERROR = "error"
    SCHEDULER_RUN = "scheduler_run"


class BackgroundTradingManager:
    """
    Manages persistent background trading sessions.
    Trading continues even when browser is closed.
    """

    def __init__(self, firestore_db=None):
        self.db = firestore_db
        self.engine_b_url = "https://engine-b.infinityai.pro"
        self._initialized = False

    def initialize(self, firestore_db):
        """Initialize with Firestore database"""
        self.db = firestore_db
        self._initialized = True
        logger.info("✅ BackgroundTradingManager initialized with Firestore")

    @property
    def is_initialized(self) -> bool:
        return self._initialized and self.db is not None

    # =========================================================================
    # Trading Session Management
    # =========================================================================

    async def start_trading_session(
        self,
        user_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Start a persistent trading session for a user.
        Session continues in background via Cloud Scheduler.
        """
        if not self.is_initialized:
            return {"success": False, "error": "Trading manager not initialized"}

        try:
            session_data = {
                "user_id": user_id,
                "state": TradingState.ACTIVE.value,
                "config": {
                    "min_confidence": config.get("min_confidence", 0.7),
                    "max_risk_per_trade": config.get("max_risk_per_trade", 0.02),
                    "max_daily_trades": config.get("max_daily_trades", 10),
                    "trading_amount": config.get("trading_amount", 1000),
                    "instruments": config.get("instruments", ["equities"]),
                    "strategy": config.get("strategy", "ai-signals"),
                },
                "started_at": datetime.utcnow().isoformat(),
                "last_run": None,
                "trades_today": 0,
                "total_pnl_today": 0.0,
                "signals_processed": 0,
                "errors": [],
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store in Firestore
            doc_ref = self.db.collection("trading_sessions").document(user_id)
            doc_ref.set(session_data)

            # Log activity
            await self.log_activity(user_id, ActivityType.TRADING_START, {
                "config": session_data["config"],
                "message": "Background trading session started"
            })

            logger.info(f"✅ Started background trading for user {user_id}")

            return {
                "success": True,
                "session_id": user_id,
                "state": TradingState.ACTIVE.value,
                "config": session_data["config"],
                "message": "Trading session started. Will continue in background even if browser is closed."
            }

        except Exception as e:
            logger.error(f"Failed to start trading session: {e}")
            return {"success": False, "error": str(e)}

    async def stop_trading_session(self, user_id: str) -> Dict[str, Any]:
        """Stop a user's trading session"""
        if not self.is_initialized:
            return {"success": False, "error": "Trading manager not initialized"}

        try:
            doc_ref = self.db.collection("trading_sessions").document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                return {"success": False, "error": "No active trading session found"}

            session = doc.to_dict()

            doc_ref.update({
                "state": TradingState.STOPPED.value,
                "stopped_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })

            # Log activity
            await self.log_activity(user_id, ActivityType.TRADING_STOP, {
                "trades_executed": session.get("trades_today", 0),
                "total_pnl": session.get("total_pnl_today", 0),
                "message": "Background trading session stopped"
            })

            logger.info(f"🛑 Stopped background trading for user {user_id}")

            return {
                "success": True,
                "trades_executed": session.get("trades_today", 0),
                "total_pnl": session.get("total_pnl_today", 0),
                "message": "Trading session stopped"
            }

        except Exception as e:
            logger.error(f"Failed to stop trading session: {e}")
            return {"success": False, "error": str(e)}

    async def get_session_status(self, user_id: str) -> Dict[str, Any]:
        """Get current trading session status"""
        if not self.is_initialized:
            return {"active": False, "error": "Trading manager not initialized"}

        try:
            doc_ref = self.db.collection("trading_sessions").document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                return {"active": False, "message": "No trading session found"}

            session = doc.to_dict()

            return {
                "active": session.get("state") == TradingState.ACTIVE.value,
                "state": session.get("state"),
                "config": session.get("config", {}),
                "started_at": session.get("started_at"),
                "last_run": session.get("last_run"),
                "trades_today": session.get("trades_today", 0),
                "total_pnl_today": session.get("total_pnl_today", 0),
                "signals_processed": session.get("signals_processed", 0),
                "errors": session.get("errors", [])[-5:]  # Last 5 errors
            }

        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            return {"active": False, "error": str(e)}

    # =========================================================================
    # Scheduled Trading Execution (Called by Cloud Scheduler)
    # =========================================================================

    async def execute_trading_cycle(self, user_id: str) -> Dict[str, Any]:
        """
        Execute one trading cycle for a user.
        Called periodically by Cloud Scheduler.
        """
        if not self.is_initialized:
            return {"success": False, "error": "Trading manager not initialized"}

        try:
            # Get session
            doc_ref = self.db.collection("trading_sessions").document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                return {"success": False, "error": "No trading session found"}

            session = doc.to_dict()

            if session.get("state") != TradingState.ACTIVE.value:
                return {"success": False, "skipped": True, "reason": "Session not active"}

            config = session.get("config", {})
            trades_today = session.get("trades_today", 0)
            max_trades = config.get("max_daily_trades", 10)

            # Check daily trade limit
            if trades_today >= max_trades:
                return {"success": True, "skipped": True, "reason": "Daily trade limit reached"}

            # Log scheduler run
            await self.log_activity(user_id, ActivityType.SCHEDULER_RUN, {
                "cycle_number": trades_today + 1,
                "max_trades": max_trades
            })

            # Get AI signals from Engine B
            signals = await self._fetch_ai_signals(config)

            if not signals:
                doc_ref.update({
                    "last_run": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
                return {"success": True, "trades": 0, "message": "No actionable signals"}

            # Execute trades based on signals
            executed_trades = []
            total_pnl = session.get("total_pnl_today", 0)
            signals_processed = session.get("signals_processed", 0)

            for signal in signals[:3]:  # Max 3 trades per cycle
                if signal.get("confidence", 0) >= config.get("min_confidence", 0.7):
                    trade_result = await self._execute_trade(user_id, signal, config)
                    signals_processed += 1

                    if trade_result.get("success"):
                        executed_trades.append(trade_result)
                        trades_today += 1

                        # Log successful trade
                        await self.log_activity(user_id, ActivityType.TRADE_EXECUTED, {
                            "symbol": signal.get("symbol"),
                            "side": signal.get("signal"),
                            "confidence": signal.get("confidence"),
                            "order_id": trade_result.get("order_id")
                        })
                    else:
                        await self.log_activity(user_id, ActivityType.TRADE_FAILED, {
                            "symbol": signal.get("symbol"),
                            "error": trade_result.get("error")
                        })

            # Update session
            doc_ref.update({
                "last_run": datetime.utcnow().isoformat(),
                "trades_today": trades_today,
                "total_pnl_today": total_pnl,
                "signals_processed": signals_processed,
                "updated_at": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "trades_executed": len(executed_trades),
                "trades_today": trades_today,
                "signals_processed": signals_processed
            }

        except Exception as e:
            logger.error(f"Trading cycle error for {user_id}: {e}")
            await self.log_activity(user_id, ActivityType.ERROR, {"error": str(e)})
            return {"success": False, "error": str(e)}

    async def execute_all_active_sessions(self) -> Dict[str, Any]:
        """
        Execute trading cycle for ALL active sessions.
        Called by Cloud Scheduler every minute during market hours.
        """
        if not self.is_initialized:
            return {"success": False, "error": "Trading manager not initialized"}

        try:
            # Get all active sessions
            sessions_ref = self.db.collection("trading_sessions").where(
                "state", "==", TradingState.ACTIVE.value
            )
            sessions = sessions_ref.stream()

            results = []
            for session_doc in sessions:
                user_id = session_doc.id
                result = await self.execute_trading_cycle(user_id)
                results.append({
                    "user_id": user_id,
                    "result": result
                })

            return {
                "success": True,
                "sessions_processed": len(results),
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to execute all sessions: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Activity Logging System
    # =========================================================================

    async def log_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        details: Dict[str, Any] = None
    ) -> bool:
        """Log user activity to Firestore"""
        if not self.is_initialized:
            return False

        try:
            activity_data = {
                "user_id": user_id,
                "type": activity_type.value,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
                "date": datetime.utcnow().strftime("%Y-%m-%d")
            }

            # Add to activity log collection
            self.db.collection("activity_logs").add(activity_data)

            # Update daily summary
            await self._update_daily_summary(user_id, activity_type)

            return True

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return False

    async def _update_daily_summary(self, user_id: str, activity_type: ActivityType):
        """Update daily activity summary"""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            summary_ref = self.db.collection("daily_summaries").document(f"{user_id}_{today}")
            summary_doc = summary_ref.get()

            if summary_doc.exists:
                summary = summary_doc.to_dict()
                counts = summary.get("activity_counts", {})
                counts[activity_type.value] = counts.get(activity_type.value, 0) + 1
                summary_ref.update({
                    "activity_counts": counts,
                    "total_activities": summary.get("total_activities", 0) + 1,
                    "last_activity": datetime.utcnow().isoformat()
                })
            else:
                summary_ref.set({
                    "user_id": user_id,
                    "date": today,
                    "activity_counts": {activity_type.value: 1},
                    "total_activities": 1,
                    "first_activity": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat()
                })

        except Exception as e:
            logger.error(f"Failed to update daily summary: {e}")

    async def get_activity_log(
        self,
        user_id: str,
        date: str = None,
        activity_type: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get activity log for a user"""
        if not self.is_initialized:
            return []

        try:
            query = self.db.collection("activity_logs").where("user_id", "==", user_id)

            if date:
                query = query.where("date", "==", date)

            if activity_type:
                query = query.where("type", "==", activity_type)

            query = query.order_by("timestamp", direction="DESCENDING").limit(limit)

            activities = []
            for doc in query.stream():
                activities.append(doc.to_dict())

            return activities

        except Exception as e:
            logger.error(f"Failed to get activity log: {e}")
            return []

    async def get_daily_summary(self, user_id: str, date: str = None) -> Dict[str, Any]:
        """Get daily activity summary"""
        if not self.is_initialized:
            return {}

        try:
            if not date:
                date = datetime.utcnow().strftime("%Y-%m-%d")

            summary_ref = self.db.collection("daily_summaries").document(f"{user_id}_{date}")
            summary_doc = summary_ref.get()

            if summary_doc.exists:
                return summary_doc.to_dict()

            return {
                "user_id": user_id,
                "date": date,
                "activity_counts": {},
                "total_activities": 0,
                "message": "No activity recorded for this date"
            }

        except Exception as e:
            logger.error(f"Failed to get daily summary: {e}")
            return {}

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _fetch_ai_signals(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch AI trading signals from Engine B"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.engine_b_url}/api/v1/batch-signals",
                    json={
                        "instruments": config.get("instruments", ["equities"]),
                        "strategy": config.get("strategy", "ai-signals")
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("signals", [])

        except Exception as e:
            logger.error(f"Failed to fetch AI signals: {e}")

        return []

    async def _execute_trade(
        self,
        user_id: str,
        signal: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a trade based on signal"""
        try:
            # This would integrate with Dhan API
            # For now, return a placeholder
            return {
                "success": True,
                "order_id": f"ORD_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "symbol": signal.get("symbol"),
                "side": signal.get("signal"),
                "quantity": 1,
                "price": signal.get("current_price", 0)
            }

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
background_trading_manager = BackgroundTradingManager()


def get_background_trading_manager() -> BackgroundTradingManager:
    """Get the background trading manager instance"""
    return background_trading_manager
