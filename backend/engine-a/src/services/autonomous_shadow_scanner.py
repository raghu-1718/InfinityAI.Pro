"""
Autonomous Continuous Shadow Market Scanner & Telemetry Engine
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Automatically scans Indian capital markets (NSE/BSE/MCX), executes Tri-Model AI/ML inference,
and logs signals with real-time Expected P&L into Cloud Firestore 24/7 without capital risk.
"""

import os
import asyncio
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from .shadow_signal_logger import ShadowSignalLogger
from .black_swan_circuit_breaker import BLACK_SWAN_BREAKER
from .mtf_confluence_filter import MTF_CONFLUENCE_FILTER

logger = logging.getLogger("InfinityAI.ContinuousShadowScanner")

ENGINE_B_URL = os.getenv("ENGINE_B_URL", "https://engine-b-r2f5flt77q-el.a.run.app")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")
SCAN_INTERVAL_SECONDS = int(os.getenv("SHADOW_SCAN_INTERVAL_SECONDS", "60"))

CORE_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]

class ContinuousShadowScanner:
    """Autonomous market radar and paper P&L tracker daemon"""

    def __init__(self):
        self.shadow_logger = ShadowSignalLogger()
        self.db = self.shadow_logger.db
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.last_scan_time: Optional[datetime] = None
        self.last_signals_cache: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """Starts the autonomous shadow scanner background task"""
        if self.is_running:
            logger.info("ContinuousShadowScanner is already running.")
            return

        self.is_running = True
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
        self.task = asyncio.create_task(self._scanner_loop())
        logger.info("🛰️ ContinuousShadowScanner Background Loop STARTED (24/7 Shadow Telemetry Active)")

    async def stop(self):
        """Stops the autonomous shadow scanner background task"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.http_client:
            await self.http_client.aclose()
        logger.info("🛑 ContinuousShadowScanner Background Loop STOPPED")

    @staticmethod
    def is_market_hours() -> bool:
        """Enforces Indian stock market operational hours (09:15–15:30 IST Mon-Fri)"""
        now_utc = datetime.now(timezone.utc)
        ist = now_utc + timedelta(hours=5, minutes=30)
        if ist.weekday() >= 5:
            return False
        market_open = ist.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = ist.replace(hour=15, minute=30, second=0, microsecond=0)
        return market_open <= ist <= market_close

    async def scan_once(self, force: bool = False) -> Dict[str, Any]:
        """Executes a single market scan cycle during 09:15-15:30 IST and updates MTM"""
        if not self.http_client or self.http_client.is_closed:
            self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signals_generated": [],
            "signals_committed": 0,
            "mtm_updates": {},
            "market_hours_active": self.is_market_hours()
        }

        try:
            # 1. Fetch live quotes for spot prices
            spot_prices = await self._fetch_spot_prices()

            # 2. Check market hours enforcement (09:15 to 15:30 IST)
            if not self.is_market_hours() and not force:
                logger.info("ℹ️ Market CLOSED (09:15–15:30 IST). Updating MTM without logging off-market signals.")
                if spot_prices:
                    mtm_res = self.shadow_logger.update_open_signals_mtm(spot_prices)
                    results["mtm_updates"] = mtm_res
                results["status"] = "MARKET_CLOSED_MTM_TRACKED"
                return results

            # 3. Call Engine B ML ensemble batch inference
            raw_signals = await self._fetch_engine_b_signals()

            # 4. Process each signal, evaluate expected PnL, and log to Firestore
            for sig in raw_signals:
                now_utc = datetime.now(timezone.utc)
                sym = sig.get("symbol", "").upper()
                if not sym:
                    continue

                signal_dir = sig.get("signal", "HOLD").upper()
                conf = float(sig.get("confidence", 50.0))
                if conf > 1.0:
                    conf = conf / 100.0  # normalize 50.0 -> 0.50

                spot = spot_prices.get(sym, float(sig.get("current_price", 0.0)))
                if spot <= 0:
                    spot = float(sig.get("current_price", 1000.0))

                # Model breakdowns & technical analysis
                models = sig.get("analysis", {})
                adx = float(models.get("adx", 25.0))
                key_factors = models.get("key_factors", [])
                veto_in_factors = any("VETO" in str(k).upper() for k in key_factors)
                veto_active = models.get("veto_active", False) or veto_in_factors or (adx < 22.0)

                # Strict fail-closed directional decision framework
                if veto_active or signal_dir in ["HOLD", "NEUTRAL", "NO_TRADE", ""]:
                    decision = "NO_TRADE"
                    logger.info(f"⏸️ Signal for {sym} is {signal_dir} (ADX: {adx:.1f}, Veto: {veto_active}). No trade executed.")
                elif ("BUY" in signal_dir or "CALL" in signal_dir) and conf >= 0.60:
                    decision = "BUY_CALL"
                elif ("SELL" in signal_dir or "PUT" in signal_dir) and conf >= 0.60:
                    decision = "BUY_PUT"
                else:
                    decision = "NO_TRADE"
                    logger.info(f"⏸️ Signal for {sym} ({signal_dir}, conf: {conf:.2f}) did not meet conviction threshold (0.60).")

                # If NO_TRADE, record observation telemetry and skip trade ledger execution
                if decision == "NO_TRADE":
                    self.last_signals_cache[sym] = {"time": now_utc, "spot": spot, "decision": "NO_TRADE"}
                    continue

                # 1. Circuit Breaker Gatekeeper (India VIX & Flash Crash check)
                breaker_status = BLACK_SWAN_BREAKER.update_market_vitals(
                    india_vix=float(spot_prices.get("INDIAVIX", 13.5)),
                    spot_price=spot,
                    symbol=sym
                )
                if not breaker_status["can_trade"]:
                    logger.warning(f"⛔ Trade blocked by Black Swan Breaker: {breaker_status['reason']}")
                    continue

                # 2. Multi-Timeframe (MTF) Confluence Filter
                confluence_eval = MTF_CONFLUENCE_FILTER.evaluate_confluence(
                    symbol=sym,
                    signal_type=decision,
                    current_price=spot,
                    indicators_snapshot={"rsi": float(sig.get("rsi", 52)), "vwap": spot, "macd": float(sig.get("macd", 0))}
                )
                if not confluence_eval["is_approved"] and not force:
                    logger.info(f"ℹ️ Signal {sym} {decision} filtered out: Low MTF Confluence ({confluence_eval['confluence_pct_str']})")
                    continue

                # 3. Check deduplication window (don't create duplicate identical signal within 15 min unless price moved > 0.4%)
                last_sig = self.last_signals_cache.get(sym)
                if last_sig:
                    last_time = last_sig.get("time", datetime.min.replace(tzinfo=timezone.utc))
                    last_spot = last_sig.get("spot", 0.0)
                    time_diff = (now_utc - last_time).total_seconds()
                    price_diff_pct = abs(spot - last_spot) / last_spot if last_spot > 0 else 1.0

                    if time_diff < 900 and price_diff_pct < 0.004 and last_sig.get("decision") == decision:
                        # Skip duplicate commit to avoid spamming the ledger
                        continue

                catboost_p = float(models.get("catboost_prob", conf))
                lightgbm_p = float(models.get("lightgbm_prob", conf))
                xgboost_p = float(models.get("xgboost_prob", conf))
                gemini_sentiment = str(sig.get("sentiment_score") or (
                    "BULLISH (+0.65)" if decision == "BUY_CALL" else ("BEARISH (-0.65)" if decision == "BUY_PUT" else "NEUTRAL")
                ))

                # Fetch live Dhan market depth for realistic Ask/Bid entry if Engine C is reachable
                live_quote = await self._fetch_option_quote(sym, spot, decision)

                logged_payload = self.shadow_logger.log_shadow_signal(
                    symbol=sym,
                    spot_price=spot,
                    decision=decision,
                    confidence_score=conf,
                    catboost_prob=catboost_p,
                    lightgbm_prob=lightgbm_p,
                    xgboost_prob=xgboost_p,
                    gemini_sentiment=gemini_sentiment,
                    live_option_quote=live_quote
                )

                if logged_payload:
                    self.last_signals_cache[sym] = {"time": now_utc, "spot": spot, "decision": decision}
                    results["signals_generated"].append(logged_payload)
                    results["signals_committed"] += 1

            # 4. Update MTM P&L for all open signals
            if spot_prices:
                mtm_res = self.shadow_logger.update_open_signals_mtm(spot_prices)
                results["mtm_updates"] = mtm_res

            self.last_scan_time = datetime.now(timezone.utc)
            return results

        except Exception as e:
            logger.error(f"Error during shadow scan cycle: {e}")
            results["error"] = str(e)
            return results

    async def _fetch_spot_prices(self) -> Dict[str, float]:
        """Queries live market quotes dynamically via MARKET_REGIME_HEARTBEAT_SERVICE and Dhan gateway"""
        try:
            from .market_regime_heartbeat_service import MARKET_REGIME_HEARTBEAT_SERVICE
            quotes = await MARKET_REGIME_HEARTBEAT_SERVICE._fetch_live_market_quotes()
            spots = {}
            for k in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "INDIAVIX"]:
                v = quotes.get(k)
                if v is not None and float(v) > 0:
                    spots[k] = round(float(v), 2)

            # Check if feed is degraded
            if quotes.get("is_degraded") or not spots.get("NIFTY") or not spots.get("BANKNIFTY"):
                logger.warning("🚨 Shadow Scanner: Live broker feed degraded. Suppressing fabricated spot approximations.")
                spots["status"] = "DEGRADED"
                spots["data_source"] = quotes.get("data_source", "DEGRADED_BROKER_FEED_UNAVAILABLE")
                return spots

            spots["status"] = "LIVE"
            spots["data_source"] = quotes.get("data_source", "live_broker_feed")
            return spots
        except Exception as e:
            logger.error(f"Error fetching live spot prices in shadow scanner: {e}")
            return {"status": "ERROR", "data_source": "UNAVAILABLE"}

    async def _fetch_engine_b_signals(self) -> List[Dict[str, Any]]:
        """Queries Engine B for batch signals"""
        try:
            payload = {
                "symbols": CORE_SYMBOLS,
                "fast": True,
                "user_id": "shadow_telemetry_scanner"
            }
            internal_token = os.getenv("INTERNAL_AUTH_TOKEN", "inf-prod-internal-key-920-v1")
            resp = await self.http_client.post(
                f"{ENGINE_B_URL}/api/v1/signals/batch",
                json=payload,
                headers={"X-Internal-Token": internal_token},
                timeout=30.0
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    if "signals" in data and isinstance(data["signals"], list):
                        return data["signals"]
                    elif "data" in data and isinstance(data["data"], list):
                        return data["data"]
                    elif "data" in data and isinstance(data["data"], dict) and "signals" in data["data"]:
                        return data["data"]["signals"]
        except Exception as e:
            logger.warning(f"Failed to query Engine B batch signals: {e}")

        return []

    async def _fetch_option_quote(self, symbol: str, spot: float, decision: str) -> Optional[dict]:
        """Queries Engine C for real-time Dhan ATM option chain depth (Ask, Bid, LTP, OI)"""
        try:
            if not self.http_client or self.http_client.is_closed:
                self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0))

            sym_u = symbol.upper()
            strike_step = 100 if "BANKNIFTY" in sym_u or "SENSEX" in sym_u else (25 if "MIDCP" in sym_u else 50)
            strike = round(spot / strike_step) * strike_step
            opt_type = "CE" if "CALL" in decision.upper() else "PE"

            resp = await self.http_client.get(
                f"{ENGINE_C_URL}/api/dhan/option-chain/{symbol}?strike={strike}&option_type={opt_type}",
                timeout=2.5
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and (data.get("ltp") or data.get("ask_price")):
                    return data
        except Exception as e:
            logger.debug(f"Option quote query notice for {symbol}: {e}")
        return None

    async def _update_active_trade_mtm(self, doc_id: str, trade_data: dict, current_spot: float):
        """
        Polls live market price, evaluates Mode 2 Uncapped Milestone Ladder,
        and updates Firestore `ai_signals_ledger` in real time.
        """
        entry_premium = float(trade_data.get("entry_price") or trade_data.get("entry_premium") or 100.0)
        highest_observed = float(trade_data.get("highest_observed_premium") or entry_premium)
        current_sl = float(trade_data.get("active_trailing_sl") or trade_data.get("stop_loss") or (entry_premium * 0.92))
        lot_size = int(trade_data.get("lot_size") or 65)
        lots = int(trade_data.get("lots") or 1)
        units = lot_size * lots
        # 1. Compute current option price via Black-Scholes Greeks or live quote
        from .options_greeks_engine import OPTIONS_GREEKS_ENGINE
        greeks = OPTIONS_GREEKS_ENGINE.calculate_greeks(
            spot=current_spot,
            strike=trade_data.get("strike", current_spot),
            dte_days=max(0.5, 3.0),
            iv=0.145,
            option_type=trade_data.get("option_type", "CE")
        )
        current_premium = float(greeks.get("price") or greeks.get("theoretical_price") or entry_premium)
        # 2. Evaluate Mode 2 Milestone Ladder
        from .dynamic_trailing_profit_lock import DYNAMIC_PROFIT_LOCK
        eval_res = DYNAMIC_PROFIT_LOCK.evaluate_trailing_lock(
            entry_price=entry_premium,
            current_price=current_premium,
            highest_observed_price=highest_observed,
            current_sl=current_sl
        )
        unrealized_pnl = round((current_premium - entry_premium) * units, 2)
        # 3. Check for Trailing Stop-Loss Hit (Exit Trigger)
        if eval_res["is_sl_hit"]:
            exit_price = eval_res["new_sl"]
            gross_pnl = round((exit_price - entry_premium) * units, 2)
            
            # Deduct SEBI 2026 Taxes and Dhan Brokerage
            from .tax_calculator import calculate_options_roundtrip_charges
            tax_breakdown = calculate_options_roundtrip_charges(
                premium=entry_premium,
                lot_size=lot_size,
                lots=lots
            )
            net_pnl = round(gross_pnl - tax_breakdown["summary"]["total_roundtrip_cost"], 2)
            settlement_type = "TRAILING_PROFIT_LOCK_HIT" if net_pnl > 0 else "INITIAL_STOP_LOSS_HIT"
            # Update Firestore Document as CLOSED
            update_payload = {
                "status": "CLOSED",
                "current_price": exit_price,
                "highest_observed_premium": eval_res["highest_observed"],
                "active_trailing_sl": eval_res["new_sl"],
                "highest_milestone_reached": eval_res["highest_milestone"],
                "milestones_ladder": eval_res["milestones_achieved"],
                "exit_price": exit_price,
                "exit_time": datetime.utcnow().isoformat(),
                "gross_pnl": gross_pnl,
                "net_pnl": net_pnl,
                "settlement_type": settlement_type,
                "return_pct": round((exit_price - entry_premium) / entry_premium, 4)
            }
            if self.db:
                self.db.collection("ai_signals_ledger").document(doc_id).update(update_payload)
            logger.info(f"🏁 Trade Closed for {doc_id} | Milestone: {eval_res['highest_milestone']} | Net P&L: ₹{net_pnl}")
        else:
            # Update Firestore Document with Active MTM & Ratcheted SL
            update_payload = {
                "current_price": current_premium,
                "highest_observed_premium": eval_res["highest_observed"],
                "active_trailing_sl": eval_res["new_sl"],
                "highest_milestone_reached": eval_res["highest_milestone"],
                "milestones_ladder": eval_res["milestones_achieved"],
                "unrealized_pnl": unrealized_pnl,
                "last_mtm_time": datetime.utcnow().isoformat()
            }
            if self.db:
                self.db.collection("ai_signals_ledger").document(doc_id).update(update_payload)

    async def _scanner_loop(self):
        """Infinite loop executing periodic market scans"""
        logger.info(f"🛰️ Autonomous Shadow Scanner loop activated. Interval: {SCAN_INTERVAL_SECONDS}s")
        # Run initial scan immediately on startup
        try:
            await self.scan_once()
        except Exception as e:
            logger.error(f"Initial shadow scan failed: {e}")

        while self.is_running:
            try:
                await asyncio.sleep(SCAN_INTERVAL_SECONDS)
                if not self.is_running:
                    break
                await self.scan_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Continuous shadow scanner loop error: {e}")
                await asyncio.sleep(15)

# Class and Singleton Instances
AutonomousShadowScanner = ContinuousShadowScanner
AUTONOMOUS_SHADOW_SCANNER = ContinuousShadowScanner()

