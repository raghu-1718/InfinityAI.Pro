import asyncio
import logging
import os
import uuid
import httpx
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from src.services.risk_manager import RiskManager
from src.services.circuit_breaker import CircuitBreaker, TradingHalted
from src.services.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# Constants - Can be provided by Cloud Run deployment, optional for startup
def _get_env(var: str, default: str = None) -> str:
    return os.environ.get(var, default)

ENGINE_B_URL = _get_env("ENGINE_B_URL", "http://engine-b:8080")
ENGINE_C_URL = _get_env("ENGINE_C_URL", "http://engine-c:8080")

# Data Freshness Enforcement (Phase-5 Security Fix)
MAX_SIGNAL_AGE = timedelta(minutes=5)  # Reject signals older than 5 minutes

class AutonomousTrader:
    """
    Centralized Authority for Autonomous Trading.
    Located in Engine A (Orchestrator).
    Responsible for:
    1. Fetching Signals (from Engine B)
    2. Risk Validation (Engine A Authority)
    3. Trade Approval/Rejection
    4. Execution Command (to Engine C)
    """

    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.circuit_breaker = CircuitBreaker("system") # Default until session start
        self.audit_logger = AuditLogger()       # Phase 5.7
        self.is_active = False
        self.task = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.config = {
            "min_confidence": 0.75,
            "poll_interval": 10,  # seconds
            "max_risk_per_trade": 0.02, # 2%
            "capital": 100000.0, # Virtual capital for sizing
            "stop_loss_pct": 0.02,
            "risk_mode": "conservative",
            "asset_class": "equities",
            "user_id": None
        }
        self.current_session_exposure = 0.0 # Phase 5.3
        logger.info("✅ AutonomousTrader initialized in Engine A")

    def configure_session(self, config: Dict[str, Any]):
        """
        Configure the trading session with immutable parameters.
        Must be called before starting the loop.
        """
        logger.info(f"⚙️ Configuring AutonomousTrader Session: {config}")
        # Merge config, overriding defaults
        self.config.update(config)

        # Initialize Circuit Breaker for this User (Phase 5 - Persistence)
        uid = self.config.get("user_id", "system")
        self.circuit_breaker = CircuitBreaker(uid)
        self.circuit_breaker.check_session_freshness() # Reset only if new day

        # Reset Exposure (Session Specific, not persisted across crash?)
        # User said "loss counters reset", checking Hard Capital logic.
        # Hard Capital is per session. If we crash and resume, we probably should
        # ideally load this too, but for now we'll reset exposure as it's an intra-session safety
        # and not a PnL guard.
        self.current_session_exposure = 0.0

        # Adjust risk params based on mode
        mode = self.config.get("risk_mode", "conservative")
        if mode == "aggressive":
            self.config["max_risk_per_trade"] = 0.05
            self.config["stop_loss_pct"] = 0.05
            self.config["min_confidence"] = 0.60
        elif mode == "moderate":
            self.config["max_risk_per_trade"] = 0.03
            self.config["stop_loss_pct"] = 0.03
            self.config["min_confidence"] = 0.70
        else: # conservative
            self.config["max_risk_per_trade"] = 0.015
            self.config["stop_loss_pct"] = 0.015
            self.config["min_confidence"] = 0.80

        logger.info(f"✅ Session Configured: {self.config}")


    def validate_signal_freshness(self, signal: Dict[str, Any]) -> bool:
        """
        Validate signal timestamp is not stale.
        Phase-5 Security Fix: Explicit data freshness enforcement.
        Returns: True if signal is fresh, False if stale (> MAX_SIGNAL_AGE)
        """
        timestamp_str = signal.get("timestamp")
        uid = self.config.get("user_id", "system")
        symbol = signal.get("symbol", "UNKNOWN")

        if not timestamp_str:
            logger.warning(f"⚠️ Signal missing timestamp - REJECTED (symbol: {symbol})")
            return False

        try:
            # Parse signal timestamp (assuming ISO format from Engine B)
            if isinstance(timestamp_str, str):
                signal_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                signal_timestamp = timestamp_str

            # Ensure UTC timezone
            if signal_timestamp.tzinfo is None:
                signal_timestamp = signal_timestamp.replace(tzinfo=timezone.utc)

            # Calculate age
            now = datetime.now(timezone.utc)
            age = now - signal_timestamp

            if age > MAX_SIGNAL_AGE:
                logger.warning(
                    f"❌ STALE SIGNAL REJECTED: {symbol} - "
                    f"Age: {age.total_seconds():.1f}s (max: {MAX_SIGNAL_AGE.total_seconds()}s)"
                )
                self.audit_logger.log_trade_rejected(uid, symbol, "STALE_SIGNAL", {"age_seconds": age.total_seconds()})
                return False

            logger.debug(f"✅ Signal freshness OK: {symbol} (age: {age.total_seconds():.1f}s)")
            return True

        except Exception as e:
            logger.error(f"❌ Timestamp parse error for {symbol}: {e} - REJECTED")
            return False


    async def start(self):
        """Start the autonomous trading loop"""
        if self.is_active:
            logger.warning("AutonomousTrader already running")
            return

        # re-initialize client if necessary
        if self.http_client is None or self.http_client.is_closed:
            self.http_client = httpx.AsyncClient(timeout=30.0)

        self.is_active = True
        self.task = asyncio.create_task(self._trading_loop())
        logger.info("🚀 AutonomousTrader Loop Started")

    async def stop(self):
        """Stop the autonomous trading loop"""
        import traceback
        logger.info(f"🛑 Stopping AutonomousTrader... Caller:\n{''.join(traceback.format_stack())}")
        self.is_active = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        await self.http_client.aclose()
        logger.info("✅ AutonomousTrader Stopped")

    def get_status(self):
        """Get the current status of the trader"""
        return {
            "is_active": self.is_active,
            "user_id": self.config.get("user_id"),
            "config": self.config
        }

    async def force_start(self):
        """Manually force start the trader"""
        if self.is_active:
            return False, "Already active"
        await self.start()
        return True, "Started"

    async def _trading_loop(self):
        """Main loop: Signal -> Risk -> Execution"""
        uid = self.config.get("user_id", "system")

        while self.is_active:
            try:
                # ---------------------------------------------------------
                # CIRCUIT BREAKER CHECK (PHASE 5.4)
                # ---------------------------------------------------------
                if self.circuit_breaker.is_tripped:
                    reason = self.circuit_breaker.trip_reason
                    logger.critical(f"🛑 TRADING HALTED: {reason}")
                    self.audit_logger.log_kill_switch(uid, reason, self.circuit_breaker.session_pnl)
                    await self.stop()
                    break

                # Generate Trace ID for this cycle
                trace_id = str(uuid.uuid4())

                # 1. Fetch Signals from Engine B
                signals = await self._fetch_signals(trace_id)

                for signal in signals:
                    if not self.is_active: break

                    # 2. Process & Risk Check
                    await self._process_signal(signal, trace_id)

                await asyncio.sleep(self.config["poll_interval"])

            except Exception as e:
                logger.error(f"Error in AutonomousTrader loop: {e}")
                await asyncio.sleep(10) # Backoff on error

    async def _fetch_signals(self, trace_id: Optional[str] = None) -> List[Dict]:
        """Call Engine B to get AI Signals"""
        try:
            # Select symbols based on Asset Class configuration
            asset_class = self.config.get("asset_class", "equities")

            if asset_class == "commodities":
                symbols = ["CRUDEOIL", "GOLD", "SILVER", "NATURALGAS", "COPPER"]
            elif asset_class == "fno":
                symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
            elif asset_class == "multi_asset":
                # Unified selection across classes
                symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "CRUDEOIL", "GOLD"]
                logger.info(f"🌐 Multi-Asset Session: Monitoring {len(symbols)} instruments across segments")
            else: # equities
                symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "ITC", "LT", "AXISBANK", "WIPRO"]

            # Using the batch signal endpoint verified in Engine B
            url = f"{ENGINE_B_URL}/api/v1/signals/batch"

            # Using configured user_id (fixed bug #4)
            uid = self.config.get("user_id", "active_trader")

            payload = {
                "symbols": symbols,
                "fast": True,
                "user_id": uid
            }

            logger.info(f"📡 Fetching signals from Engine B for user {uid}...")

            headers = {"X-Trace-ID": trace_id} if trace_id else {}
            resp = await self.http_client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"✅ Engine B Response: {str(data)[:200]}...") # Log first 200 chars
                if isinstance(data, str):
                    import json
                    try:
                        data = json.loads(data)
                    except Exception as e:
                        logger.error(f"Double decode failed: {e}")
                        return []

                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "signals" in data:
                    return data["signals"]
                elif isinstance(data, dict) and "data" in data:
                    return data["data"]
                elif isinstance(data, dict):
                     # Maybe a single signal wrapped?
                     return [data]

                return []
            else:
                logger.warning(f"Engine B Signal Fetch Failed: {resp.status_code} - {resp.text}")
                return []
        except Exception as e:
            logger.error(f"Signal API Error: {e}")
            return []

    async def _process_signal(self, signal: Dict, trace_id: Optional[str] = None):
        """Authorize and Execute a potential trade"""
        symbol = signal.get("symbol")
        confidence = signal.get("confidence", 0)
        signal_type = signal.get("signal", "HOLD") # BUY/SELL
        uid = self.config.get("user_id", "system")

        if signal_type == "HOLD":
            return

        logger.info(f"🔎 Analyzing Signal: {signal_type} {symbol} ({confidence:.1%})")

        # ---------------------------------------------------------
        # FRESHNESS GATE (PHASE-5 SECURITY FIX)
        # ---------------------------------------------------------
        if not self.validate_signal_freshness(signal):
            return

        # ---------------------------------------------------------
        # RISK GATE (MANDATORY)
        # ---------------------------------------------------------
        # Calculate Position Size
        pos_size_res = self.risk_manager.optimize_position_size(
            capital=self.config["capital"],
            risk_per_trade=self.config["max_risk_per_trade"],
            stop_loss_pct=self.config["stop_loss_pct"]
        )
        current_price = signal.get("current_price") or 1000
        safe_quantity = int(pos_size_res.get("optimal_position_size", 0) / current_price)
        if safe_quantity <= 0:
            logger.warning(f"❌ Trade Rejected: Position size 0 for {symbol}")
            self.audit_logger.log_trade_rejected(uid, symbol, "ZERO_POSITION_SIZE", {"current_price": current_price})
            return

        # Risk Score
        risk_res = self.risk_manager.score_risk(
            position_size=pos_size_res.get("risk_amount", 0),
            volatility=0.02, # Should come from signal/market data
            max_drawdown=0.05 # Should come from portfolio state
        )

        if risk_res.get("recommendation") != "PROCEED":
             logger.warning(f"❌ Trade Rejected by Risk Manager: {symbol} - {risk_res['risk_level']}")
             self.audit_logger.log_trade_rejected(uid, symbol, "RISK_MANAGER_REJECT", risk_res)
             return

        # ---------------------------------------------------------
        # HARD CAPITAL GUARD (PHASE 5.3) - CRITICAL
        # ---------------------------------------------------------
        order_value = safe_quantity * current_price
        try:
            self.risk_manager.validate_hard_capital_limit(
                order_value=order_value,
                current_session_exposure=self.current_session_exposure
            )
        except Exception as e:
            logger.error(f"🛑 HARD CAPITAL GUARD REJECTED: {e}")
            self.audit_logger.log_trade_rejected(uid, symbol, "HARD_CAPITAL_LIMIT", {"error": str(e), "value": order_value})
            return

        # ---------------------------------------------------------
        # EXECUTION AUTHORITY
        # ---------------------------------------------------------
        logger.info(f"✅ Trade APPROVED: {signal_type} {safe_quantity} {symbol} (₹{order_value:,.2f}). Sending to Execution Engine.")
        await self._execute_trade(symbol, signal_type, safe_quantity, signal, trace_id, order_value, risk_res)

    async def _execute_trade(self, symbol: str, side: str, qty: int, signal_data: Dict, trace_id: Optional[str] = None, order_value: float = 0.0, risk_res: dict = None):
        """Send explicit command to Engine C"""
        uid = self.config.get("user_id", "system")
        try:
            # Mapping schema to Engine C's OrderRequest
            sec_id = signal_data.get("security_id", "0")
            segment = signal_data.get("exchange_segment", "NSE_EQ")

            # Asset Class Override / Intelligent Segment Logic
            asset_class = self.config.get("asset_class", "equities")

            # Map symbol prefixes to segments if not provided by signal
            if segment == "NSE_EQ": # Default or generic
                if symbol in ["CRUDEOIL", "GOLD", "SILVER", "NATURALGAS", "COPPER"]:
                    segment = "MCX_COMM"
                elif symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
                    segment = "NSE_FNO" # Or just NSE_EQ if tracking index, but usually FNO for trading

            # Additional safety for commodity specific sessions
            if asset_class == "commodities" and segment == "NSE_EQ":
                 segment = "MCX_COMM"
            payload = {
                "transaction_type": side.upper(), # BUY/SELL
                "exchange_segment": segment,
                "product_type": "INTRADAY",
                "order_type": "MARKET",
                "validity": "DAY",
                "security_id": sec_id,
                "quantity": qty,
                "price": 0
            }

            url = f"{ENGINE_C_URL}/api/dhan/place-order"

            # Build headers safely - avoid None values
            headers = {
                "X-Trace-ID": trace_id if trace_id else str(uuid.uuid4()),
                "X-Engine-Source": "engine-a"
            }
            # Only add X-User-ID if uid is not None
            if uid is not None and uid != "system":
                headers["X-User-ID"] = str(uid)

            resp = await self.http_client.post(url, json=payload, headers=headers)

            if resp.status_code == 200:
                logger.info(f"🎉 Execution Success: {resp.json()}")

                # Update Session Exposure
                self.current_session_exposure += order_value

                # Log Success Audit
                self.audit_logger.log_trade_approved(uid, symbol, qty, order_value, risk_res)

            else:
                logger.error(f"❌ Execution Failed: {resp.text}")
                self.audit_logger.log_event(uid, "EXECUTION_ERROR", {"symbol": symbol, "error": resp.text}, "ERROR")

                # Log failed trade
                self.circuit_breaker.update_trade_result(-100) # Penalize failures potentially

        except Exception as e:
            logger.error(f"Execution API Error: {e}")
            self.audit_logger.log_event(uid, "EXECUTION_EXCEPTION", {"error": str(e)}, "ERROR")


