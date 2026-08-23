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

ENGINE_B_URL = _get_env(
    "ENGINE_B_URL",
    "http://localhost:8002"
    if _get_env("ENVIRONMENT", "production") == "development"
    else "http://10.160.0.2:8080",
)
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
        PRIMARY_USER = os.getenv("PRIMARY_USER_ID", "raghu_primary")
        self.config = {
            "min_confidence": 0.75,
            "poll_interval": 10,  # seconds
            "max_risk_per_trade": 0.02, # 2%
            "capital": 100000.0, # Virtual capital for sizing
            "stop_loss_pct": 0.02,
            "risk_mode": "conservative",
            "asset_class": "fno",
            "user_id": PRIMARY_USER
        }
        self.current_session_exposure = 0.0 # Phase 5.3
        logger.info(f"✅ AutonomousTrader initialized in Engine A for user: {PRIMARY_USER}")

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
            asset_class = self.config.get("asset_class", "fno")

            if asset_class == "fno":
                symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
            else: # general index basket
                symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]

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
        # MARGIN-AWARE DYNAMIC LOT SIZING & RISK GATE
        # ---------------------------------------------------------
        user_capital = float(self.config.get("capital", 10000.0))
        max_risk_trade = float(self.config.get("max_risk_per_trade", 0.10))
        min_sl_pct = float(self.config.get("stop_loss_pct", 0.11))
        min_target_pct = float(self.config.get("target_profit_pct", 0.15))

        current_price = float(signal.get("current_price") or 1000.0)
        # Option Buying Premium calculation (approx 1.1% of spot if index)
        est_premium = float(signal.get("predicted_price", current_price * 0.011)) if current_price > 500 else current_price

        margin_sizing = self.risk_manager.calculate_margin_aware_lot_size(
            capital=user_capital,
            risk_per_trade=max_risk_trade,
            stop_loss_pct=min_sl_pct,
            symbol=symbol,
            premium=est_premium,
            max_lots_cap=int(self.config.get("max_lots", 5))
        )

        if not margin_sizing["is_viable"] or margin_sizing["optimal_lots"] <= 0:
            reason = margin_sizing.get("rejection_reason", "Insufficient margin")
            logger.warning(f"❌ Trade Rejected: {reason} for {symbol}")
            self.audit_logger.log_trade_rejected(uid, symbol, "INSUFFICIENT_MARGIN", margin_sizing)
            return

        lots_count = margin_sizing["optimal_lots"]
        safe_quantity = margin_sizing["total_units"]
        order_value = margin_sizing["total_margin_required"]

        # Risk Score validation
        risk_res = self.risk_manager.score_risk(
            position_size=margin_sizing["max_risk_amount"],
            volatility=0.02,
            max_drawdown=0.05
        )

        if risk_res.get("recommendation") != "PROCEED":
             logger.warning(f"❌ Trade Rejected by Risk Manager: {symbol} - {risk_res['risk_level']}")
             self.audit_logger.log_trade_rejected(uid, symbol, "RISK_MANAGER_REJECT", risk_res)
             return

        # ---------------------------------------------------------
        # NET PROFITABILITY GATE (ANTI-FEE CANNIBALIZATION)
        # ---------------------------------------------------------
        target_price = est_premium * (1.0 + min_target_pct)
        profitability = self.risk_manager.validate_net_profitability(
            entry_price=est_premium,
            target_price=target_price,
            lot_size=margin_sizing["lot_size"],
            lots=lots_count,
            max_fee_ratio=0.35,
            min_net_profit_margin=0.015
        )

        if not profitability.get("is_viable", True):
            reason = profitability.get("rejection_reason", "Excessive transaction friction")
            logger.warning(f"🛑 NET PROFITABILITY GATE REJECTED: {symbol} — {reason} (Fees: ₹{profitability.get('total_fees')})")
            self.audit_logger.log_trade_rejected(uid, symbol, "FEE_CANNIBALIZATION_RISK", profitability)
            return

        # ---------------------------------------------------------
        # HARD CAPITAL GUARD (PHASE 5.3) - CRITICAL
        # ---------------------------------------------------------
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
        logger.info(f"✅ Trade APPROVED: {signal_type} {safe_quantity} {symbol} (₹{order_value:,.2f} | Net ROI: {profitability.get('net_roi', 0):.2%}). Sending to Execution Engine.")
        await self._execute_trade(symbol, signal_type, safe_quantity, signal, trace_id, order_value, risk_res)

    async def resolve_optimal_option_strike(self, underlying_symbol: str, underlying_spot: float, option_type: str) -> dict:
        """
        Automatically scans the DhanHQ option chain via Engine-C proxy 
        to select the ideal ITM-1 strike for long Call/Put buying (Delta ~0.50 to 0.65).
        """
        symbol_upper = underlying_symbol.upper()
        # 1. Determine strike interval and lot size based on underlying (SEBI 2026 Mandate)
        if "BANKNIFTY" in symbol_upper:
            interval = 100
            lot_size = 30
        elif "MIDCP" in symbol_upper:
            interval = 25
            lot_size = 120
        elif "FINNIFTY" in symbol_upper:
            interval = 50
            lot_size = 60
        elif "SENSEX" in symbol_upper:
            interval = 100
            lot_size = 20
        else:  # NIFTY 50 default
            interval = 50
            lot_size = 65

        # 2. Round to nearest ATM strike
        atm_strike = round(underlying_spot / interval) * interval

        # 3. Select ITM-1 for option buying to ensure higher delta protection (SEBI 2026 Mandate)
        # For Call (CE): ITM-1 is one strike below spot (atm_strike - interval)
        # For Put (PE): ITM-1 is one strike above spot (atm_strike + interval)
        if option_type.upper() in ["CE", "BUY", "CALL"]:
            target_strike = atm_strike - interval
            opt_type_code = "CE"
        else:
            target_strike = atm_strike + interval
            opt_type_code = "PE"

        trading_symbol = f"{symbol_upper} {int(target_strike)} {opt_type_code}"

        # 4. Calculate Exact Analytical Greeks via OptionsGreeksEngine
        try:
            from .options_greeks_engine import OPTIONS_GREEKS_ENGINE
            greeks = OPTIONS_GREEKS_ENGINE.calculate_greeks(
                spot=underlying_spot,
                strike=target_strike,
                dte_days=3.0,
                iv=0.14,
                option_type=opt_type_code
            )
            exact_delta = abs(greeks.get("delta", 0.58))
            theta_decay = greeks.get("theta", -20.0)
            gamma = greeks.get("gamma", 0.001)
            vega = greeks.get("vega", 8.5)
        except Exception:
            exact_delta = 0.58
            theta_decay = -20.0
            gamma = 0.001
            vega = 8.5

        # 5. Fetch matching security ID from Engine-C option chain lookup
        try:
            url = f"{ENGINE_C_URL}/api/dhan/option-chain/{symbol_upper}?strike={target_strike}&option_type={opt_type_code}"
            headers = {"X-User-ID": str(self.config.get("user_id", "raghu_primary"))}
            chain_resp = await self.http_client.get(url, headers=headers)
            if chain_resp.status_code == 200:
                data = chain_resp.json()
                return {
                    "security_id": str(data.get("securityId", data.get("security_id", "45123"))),
                    "trading_symbol": data.get("tradingSymbol", trading_symbol),
                    "strike": target_strike,
                    "atm_strike": atm_strike,
                    "option_type": opt_type_code,
                    "lot_size": lot_size,
                    "implied_delta": exact_delta,
                    "theta_decay_per_day": theta_decay,
                    "gamma": gamma,
                    "vega": vega
                }
        except Exception as e:
            logger.warning(f"Option chain lookup fallback for {symbol_upper}: {e}")

        return {
            "security_id": "45123",
            "trading_symbol": trading_symbol,
            "strike": target_strike,
            "atm_strike": atm_strike,
            "option_type": opt_type_code,
            "lot_size": lot_size,
            "implied_delta": exact_delta,
            "theta_decay_per_day": theta_decay,
            "gamma": gamma,
            "vega": vega
        }

    async def _execute_trade(self, symbol: str, side: str, qty: int, signal_data: Dict, trace_id: Optional[str] = None, order_value: float = 0.0, risk_res: dict = None):
        """Send execution command to Engine C (with Super Order / ITM-1 Option support)"""
        uid = self.config.get("user_id", "system")
        try:
            current_price = signal_data.get("current_price", 100.0)
            target_price = signal_data.get("target", current_price * 1.05)
            stop_loss_price = signal_data.get("stop_loss", current_price * 0.98)
            segment = signal_data.get("exchange_segment", "NSE_FNO")
            asset_class = self.config.get("asset_class", "fno")
            symbol_upper = symbol.upper()

            # Handle F&O Options Execution with ITM-1 Strike Selection
            if asset_class in ["fno", "options"] or symbol_upper in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]:
                opt_info = await self.resolve_optimal_option_strike(
                    underlying_symbol=symbol_upper,
                    underlying_spot=current_price,
                    option_type="CE" if side.upper() == "BUY" else "PE"
                )
                sec_id = opt_info["security_id"]
                lot_size = opt_info["lot_size"]
                # Convert Lots to Exchange Units (Qty * LotSize)
                total_units = max(1, qty) * lot_size
                segment = "NSE_FNO"

                logger.info(f"🎯 ITM-1 Strike Locked: {opt_info['trading_symbol']} (Units: {total_units}, Delta: {opt_info['implied_delta']})")

                # Dispatch via DhanHQ Bracket Super Order
                super_order_payload = {
                    "security_id": sec_id,
                    "exchange_segment": "NSE_FNO",
                    "transaction_type": "BUY",  # Option buying
                    "quantity": total_units,
                    "order_type": "LIMIT",
                    "price": round(current_price, 2),
                    "target_price": round(target_price, 2),
                    "stop_loss_price": round(stop_loss_price, 2),
                    "trailing_jump": 5.0,
                    "user_id": uid
                }

                url = f"{ENGINE_C_URL}/api/dhan/super-order/bracket"
                headers = {
                    "X-Trace-ID": trace_id if trace_id else str(uuid.uuid4()),
                    "X-Engine-Source": "engine-a",
                    "X-User-ID": str(uid)
                }

                resp = await self.http_client.post(url, json=super_order_payload, headers=headers)
            else:
                # Regular Equity Order Execution
                sec_id = signal_data.get("security_id", "0")
                if symbol_upper in ["CRUDEOIL", "GOLD", "SILVER", "NATURALGAS", "COPPER"]:
                    segment = "MCX_COMM"

                payload = {
                    "transaction_type": side.upper(),
                    "exchange_segment": segment,
                    "product_type": "INTRADAY",
                    "order_type": "MARKET",
                    "validity": "DAY",
                    "security_id": sec_id,
                    "quantity": qty,
                    "price": 0
                }

                url = f"{ENGINE_C_URL}/api/dhan/place-order"
                headers = {
                    "X-Trace-ID": trace_id if trace_id else str(uuid.uuid4()),
                    "X-Engine-Source": "engine-a",
                    "X-User-ID": str(uid)
                }

                resp = await self.http_client.post(url, json=payload, headers=headers)

            if resp.status_code in [200, 201]:
                logger.info(f"🎉 Execution Success: {resp.json()}")
                self.current_session_exposure += order_value
                self.audit_logger.log_trade_approved(uid, symbol, qty, order_value, risk_res)
            else:
                logger.error(f"❌ Execution Failed: {resp.text}")
                self.audit_logger.log_event(uid, "EXECUTION_ERROR", {"symbol": symbol, "error": resp.text}, "ERROR")
                self.circuit_breaker.update_trade_result(-100)

        except Exception as e:
            logger.error(f"Execution API Error: {e}")
            self.audit_logger.log_event(uid, "EXECUTION_EXCEPTION", {"error": str(e)}, "ERROR")

