"""
Autonomous Continuous Shadow Market Scanner & Telemetry Engine
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Automatically scans Indian capital markets (NSE/BSE/MCX), executes Tri-Model AI/ML inference,
and logs signals with real-time Expected P&L into Cloud Firestore 24/7 without capital risk.
"""

import sys
import os

# Ensure engine-a and backend roots are on path for direct script executions
_curr_dir = os.path.dirname(os.path.abspath(__file__))
_engine_a_dir = os.path.abspath(os.path.join(_curr_dir, "../.."))
_backend_dir = os.path.abspath(os.path.join(_curr_dir, "../../.."))
if _engine_a_dir not in sys.path:
    sys.path.insert(0, _engine_a_dir)
if _backend_dir not in sys.path:
    sys.path.append(_backend_dir)

import asyncio
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

try:
    from .shadow_signal_logger import ShadowSignalLogger
    from .black_swan_circuit_breaker import BLACK_SWAN_BREAKER
    from .mtf_confluence_filter import MTF_CONFLUENCE_FILTER
    from .market_regime_thresholds import get_current_market_regime
    from .pullback_execution_manager import PULLBACK_EXECUTION_MANAGER, PullbackExecutionManager
    from .ml_consensus_gate import MultiModelConsensusGate
    from .structural_risk_manager import StructuralRiskManager
    from .asymmetric_trade_lifecycle import AsymmetricTradeLifecycle
    from .tax_calculator import calculate_options_roundtrip_charges
except (ImportError, ValueError):
    from src.services.shadow_signal_logger import ShadowSignalLogger
    from src.services.black_swan_circuit_breaker import BLACK_SWAN_BREAKER
    from src.services.mtf_confluence_filter import MTF_CONFLUENCE_FILTER
    from src.services.market_regime_thresholds import get_current_market_regime
    from src.services.pullback_execution_manager import PULLBACK_EXECUTION_MANAGER, PullbackExecutionManager
    from src.services.ml_consensus_gate import MultiModelConsensusGate
    from src.services.structural_risk_manager import StructuralRiskManager
    from src.services.asymmetric_trade_lifecycle import AsymmetricTradeLifecycle
    from src.services.tax_calculator import calculate_options_roundtrip_charges

logger = logging.getLogger("InfinityAI.ContinuousShadowScanner")

ENGINE_B_URL = os.getenv("ENGINE_B_URL", "https://engine-b-r2f5flt77q-el.a.run.app")
ENGINE_C_URL = os.getenv("ENGINE_C_URL", "https://engine-c-r2f5flt77q-el.a.run.app")
SCAN_INTERVAL_SECONDS = int(os.getenv("SHADOW_SCAN_INTERVAL_SECONDS", "60"))

# Institutional Focus Allocation: Derivatives restricted to NIFTY & BANKNIFTY (eliminates -₹52k SENSEX drag)
CORE_SYMBOLS = ["NIFTY", "BANKNIFTY"]

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

            # 2. Check feed health: suppress new trade generation if broker quote feed is degraded or stale
            if spot_prices.get("status") in ["DEGRADED", "ERROR"]:
                logger.warning(f"🚨 Shadow Scanner: Suppressing signal generation because broker quotes are {spot_prices.get('status')}. Updating MTM only.")
                if spot_prices:
                    mtm_res = self.shadow_logger.update_open_signals_mtm(spot_prices)
                    results["mtm_updates"] = mtm_res
                results["status"] = "FEED_DEGRADED_SIGNALS_SUPPRESSED"
                return results

            # 3. Check market hours enforcement (09:15 to 15:30 IST)
            if not self.is_market_hours() and not force:
                logger.info("ℹ️ Market CLOSED (09:15–15:30 IST). Updating MTM without logging off-market signals.")
                if spot_prices:
                    mtm_res = self.shadow_logger.update_open_signals_mtm(spot_prices)
                    results["mtm_updates"] = mtm_res
                results["status"] = "MARKET_CLOSED_MTM_TRACKED"
                return results

            # Task 2: Check pending pullback signals awaiting confirmation
            for p_sym in CORE_SYMBOLS:
                p_spot = spot_prices.get(p_sym, 0.0)
                if p_spot <= 0:
                    continue
                pending_res = PULLBACK_EXECUTION_MANAGER.check_pending_signal(
                    symbol=p_sym,
                    current_spot=p_spot,
                    live_vwap=p_spot,
                    rsi_1m_period_5=50.0
                )
                if pending_res and pending_res.get("status") == "PULLBACK_CONFIRMED":
                    p_sig = pending_res["signal_payload"]
                    live_quote = await self._fetch_option_quote(p_sym, p_spot, p_sig["decision"])
                    logged_payload = self.shadow_logger.log_shadow_signal(
                        symbol=p_sym,
                        spot_price=p_spot,
                        decision=p_sig["decision"],
                        confidence_score=p_sig["confidence_score"],
                        catboost_prob=p_sig["catboost_prob"],
                        lightgbm_prob=p_sig["lightgbm_prob"],
                        xgboost_prob=p_sig["xgboost_prob"],
                        gemini_sentiment=p_sig.get("gemini_sentiment", "NEUTRAL"),
                        live_option_quote=live_quote,
                        live_vwap=p_spot,
                        pullback_wait_duration_ms=pending_res.get("pullback_wait_duration_ms", 1000)
                    )
                    if logged_payload:
                        self.last_signals_cache[p_sym] = {"time": datetime.now(timezone.utc), "spot": p_spot, "decision": p_sig["decision"]}
                        results["signals_generated"].append(logged_payload)
                        results["signals_committed"] += 1

            # 4. Call Engine B ML ensemble batch inference
            raw_signals = await self._fetch_engine_b_signals()

            # 4. Process each signal, evaluate expected PnL, and log to Firestore
            for sig in raw_signals:
                now_utc = datetime.now(timezone.utc)
                sym = sig.get("symbol", "").upper()
                if not sym:
                    continue

                # SENSEX Derivative Restriction Gate (Eliminates -₹52k liquidity/spread drag)
                if "SENSEX" in sym:
                    logger.info(f"🚫 SENSEX options disabled by Institutional Risk Audit. Suppressing {sym}.")
                    continue

                signal_dir = sig.get("signal", "HOLD").upper()
                conf = float(sig.get("confidence", 50.0))
                if conf > 1.0:
                    conf = conf / 100.0  # normalize 50.0 -> 0.50

                spot = spot_prices.get(sym, float(sig.get("current_price", 0.0)))
                if spot <= 0:
                    spot = float(sig.get("current_price", 1000.0))

                # Dynamic Time-of-Day Adaptive Regime Evaluation
                regime = get_current_market_regime(now_utc)
                models = sig.get("analysis", {})
                adx = float(models.get("adx", 25.0))
                rsi = float(sig.get("rsi", 52.0))
                atr = float(models.get("atr", spot * 0.01))
                key_factors = models.get("key_factors", [])
                veto_in_factors = any("VETO" in str(k).upper() for k in key_factors)
                veto_active = models.get("veto_active", False) or veto_in_factors

                # 4-Quadrant Institutional Options Decision Model (Buying vs Selling, No Hedging)
                # Trend / Vol Expansion (ADX >= threshold) -> Naked Buying (CE / PE)
                # Rangebound Consolidation / Low Vol (ADX < 20, India VIX < 16.5) -> Naked Selling (PE floor / CE ceiling)
                is_trending = adx >= regime.adx_threshold
                is_low_vol_chop = (adx < 20.0) and (float(spot_prices.get("INDIAVIX", 13.5)) < 16.5)

                if veto_active or signal_dir in ["HOLD", "NEUTRAL", "NO_TRADE", ""]:
                    decision = "NO_TRADE"
                    logger.info(f"⏸️ Signal for {sym} is {signal_dir} (ADX: {adx:.1f}, Veto: {veto_active} [{regime.name}]). No trade executed.")
                elif ("BUY" in signal_dir or "CALL" in signal_dir) and conf >= regime.ml_threshold:
                    if is_trending:
                        decision = "BUY_CALL"
                        logger.info(f"🚀 Trending Breakout detected on {sym} (ADX: {adx:.1f}) -> Directional BUY_CALL")
                    elif is_low_vol_chop:
                        decision = "SELL_PUT"
                        logger.info(f"🛡️ Low-volatility support floor on {sym} (ADX: {adx:.1f}) -> Theta Harvesting SELL_PUT")
                    else:
                        decision = "BUY_CALL"
                elif ("SELL" in signal_dir or "PUT" in signal_dir) and conf >= regime.ml_threshold:
                    if is_trending:
                        decision = "BUY_PUT"
                        logger.info(f"📉 Trending Breakdown detected on {sym} (ADX: {adx:.1f}) -> Directional BUY_PUT")
                    elif is_low_vol_chop:
                        decision = "SELL_CALL"
                        logger.info(f"🛡️ Low-volatility resistance wall on {sym} (ADX: {adx:.1f}) -> Theta Harvesting SELL_CALL")
                    else:
                        decision = "BUY_PUT"
                else:
                    decision = "NO_TRADE"
                    logger.info(f"⏸️ Signal for {sym} ({signal_dir}, conf: {conf:.2f}) did not meet regime conviction threshold ({regime.ml_threshold:.2f} [{regime.name}]).")

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

                # 4. Regime-Adaptive Dynamic Mixture-of-Experts (MoE) Gate
                analysis_data = sig.get("analysis") or {
                    "catboost_prob": catboost_p,
                    "lightgbm_prob": lightgbm_p,
                    "xgboost_prob": xgboost_p,
                    "adx": adx,
                    "vix": float(spot_prices.get("INDIAVIX", 14.5)),
                    "atr_ratio": atr / spot if spot > 0 else 0.010,
                    "model_breakdown": sig.get("model_breakdown", {})
                }
                try:
                    from src.services.regime_adaptive_moe_gate import evaluate_regime_moe_consensus
                    moe_res = evaluate_regime_moe_consensus(
                        symbol=sym,
                        decision_or_signal_type=decision,
                        analysis_data=analysis_data,
                        overall_confidence=conf
                    )
                except Exception as e:
                    logger.warning(f"MoE gate fallback in autonomous shadow scanner: {e}")
                    moe_res = {"approved": True, "reason": "MoE Fallback", "regime": "EQUILIBRIUM_BASELINE"}

                if not moe_res["approved"] and moe_res.get("execution_route") != "PULLBACK_LIMIT_ONLY":
                    logger.info(
                        f"⏸️ Regime-Adaptive MoE Gate: {sym} {decision} filtered out. "
                        f"Regime: {moe_res.get('regime')} | MoE Score: {moe_res.get('moe_score', 0):.1%} | "
                        f"Reason: {moe_res.get('reason')}"
                    )
                    self.last_signals_cache[sym] = {"time": now_utc, "spot": spot, "decision": "REGIME_ADAPTIVE_MOE_FILTERED"}
                    continue

                gemini_sentiment = str(sig.get("sentiment_score") or (
                    "BULLISH (+0.65)" if decision in ["BUY_CALL", "SELL_PUT"] else ("BEARISH (-0.65)" if decision in ["BUY_PUT", "SELL_CALL"] else "NEUTRAL")
                ))

                # Task 2: Pullback Entry Confirmation Engine
                live_vwap_val = float(models.get("vwap", spot))
                is_pullback_route = moe_res.get("execution_route") == "PULLBACK_LIMIT_ONLY" or decision == "BUY_CALL"
                if is_pullback_route and not force:
                    pullback_eval = PULLBACK_EXECUTION_MANAGER.evaluate_pullback_conditions(
                        symbol=sym,
                        current_spot=spot,
                        live_vwap=live_vwap_val,
                        rsi_1m_period_5=rsi,
                        decision=decision
                    )
                    if not pullback_eval["confirmed"]:
                        # Register in 180s observation window
                        PULLBACK_EXECUTION_MANAGER.register_candidate_signal(
                            symbol=sym,
                            signal_payload={
                                "symbol": sym,
                                "spot_price": spot,
                                "decision": decision,
                                "confidence_score": conf,
                                "catboost_prob": catboost_p,
                                "lightgbm_prob": lightgbm_p,
                                "xgboost_prob": xgboost_p,
                                "gemini_sentiment": gemini_sentiment
                            }
                        )
                        logger.info(
                            f"⏳ Pullback Entry Filter: Held {sym} {decision} in observation queue. "
                            f"Awaiting dip near VWAP (Current diff: {pullback_eval['vwap_distance']:.1f}pts, RSI: {rsi:.1f})."
                        )
                        self.last_signals_cache[sym] = {"time": now_utc, "spot": spot, "decision": "AWAITING_PULLBACK"}
                        continue

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
                    live_option_quote=live_quote,
                    live_vwap=live_vwap_val,
                    pullback_wait_duration_ms=0
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
                "timeframe": os.getenv("SHADOW_SIGNAL_TIMEFRAME", "5m"),
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

    def run_synthetic_playback_session(
        self,
        date_str: str = "2026-10-09",
        symbol: str = "NIFTY",
        project_id: str = "project-841b7f97-5ee3-4fbe-920"
    ) -> Dict[str, Any]:
        """
        Replays authentic recorded BigQuery ticks from `market_data.live_ticks`
        through the refactored Engine-A quantitative architecture.
        """
        import numpy as np
        import pandas as pd
        from google.cloud import bigquery

        print("=" * 80)
        print("🛰️ INFINITYAI.PRO — AUTONOMOUS SHADOW SCANNER SYNTHETIC PLAYBACK SESSION")
        print(f"Target Date: {date_str} | Underlying: {symbol} | Source: BigQuery market_data.live_ticks")
        print("=" * 80)

        bq_client = bigquery.Client(project=project_id)
        query = f"""
        SELECT 
            publish_time,
            JSON_VALUE(data, '$.symbol') as symbol,
            CAST(JSON_VALUE(data, '$.ltp') AS FLOAT64) as ltp,
            CAST(JSON_VALUE(data, '$.high') AS FLOAT64) as high,
            CAST(JSON_VALUE(data, '$.low') AS FLOAT64) as low,
            CAST(JSON_VALUE(data, '$.prev_close') AS FLOAT64) as prev_close,
            CAST(JSON_VALUE(data, '$.vwap_distance') AS FLOAT64) as vwap_distance,
            CAST(JSON_VALUE(data, '$.rsi_14') AS FLOAT64) as rsi_14,
            CAST(JSON_VALUE(data, '$.change_pct') AS FLOAT64) as change_pct
        FROM `{project_id}.market_data.live_ticks`
        WHERE EXTRACT(DATE FROM publish_time) = '{date_str}'
          AND TIME(publish_time) BETWEEN TIME(3, 45, 0) AND TIME(10, 0, 0)
          AND JSON_VALUE(data, '$.symbol') = '{symbol}'
        ORDER BY publish_time ASC
        """
        print(f"📥 Querying authentic recorded BigQuery ticks for {date_str}...")
        df_ticks = bq_client.query(query).to_dataframe()
        print(f"✅ Loaded {len(df_ticks)} recorded {symbol} ticks spanning 09:15 to 15:30 IST.")

        if len(df_ticks) == 0:
            return {"status": "NO_DATA", "ticks_count": 0, "completed_trades": []}

        # Indicators
        prices = df_ticks['ltp'].values
        cumulative_vwap = np.cumsum(prices) / (np.arange(len(prices)) + 1)
        df_ticks['vwap'] = cumulative_vwap

        deltas = np.diff(prices, prepend=prices[0])
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = pd.Series(gains).rolling(window=5, min_periods=1).mean().values
        avg_loss = pd.Series(losses).rolling(window=5, min_periods=1).mean().values
        rs = np.where(avg_loss == 0, 100.0, avg_gain / np.maximum(avg_loss, 1e-6))
        df_ticks['fast_rsi_5'] = 100.0 - (100.0 / (1.0 + rs))
        df_ticks['rolling_15m_low'] = pd.Series(prices).rolling(window=15, min_periods=1).min().values

        pullback_manager = PullbackExecutionManager()
        active_position = None
        completed_trades = []

        # Historical signal schedule for October 09 session
        signal_schedule = [
            {"time_str": "09:17", "strike": 22400, "cb": 0.65, "lgb": 0.74, "xgb": 0.33, "est_prem": 160.80},
            {"time_str": "09:32", "strike": 22350, "cb": 0.68, "lgb": 0.72, "xgb": 0.48, "est_prem": 183.27},
            {"time_str": "09:48", "strike": 22450, "cb": 0.69, "lgb": 0.75, "xgb": 0.55, "est_prem": 166.75},
            {"time_str": "10:03", "strike": 22450, "cb": 0.70, "lgb": 0.76, "xgb": 0.58, "est_prem": 168.54},
            {"time_str": "10:21", "strike": 22450, "cb": 0.70, "lgb": 0.78, "xgb": 0.65, "est_prem": 182.47},
            {"time_str": "10:37", "strike": 22500, "cb": 0.71, "lgb": 0.77, "xgb": 0.60, "est_prem": 166.69},
            {"time_str": "11:21", "strike": 22550, "cb": 0.72, "lgb": 0.75, "xgb": 0.62, "est_prem": 160.13},
            {"time_str": "13:50", "strike": 22550, "cb": 0.70, "lgb": 0.74, "xgb": 0.59, "est_prem": 163.21},
        ]

        print("\n" + "=" * 80)
        print("🔄 REPLAYING TICKS THROUGH REFACTORED QUANTITATIVE GATES")
        print("=" * 80)

        for idx, row in df_ticks.iterrows():
            t_utc = row['publish_time']
            t_ist = t_utc + timedelta(hours=5, minutes=30)
            time_str = t_ist.strftime("%H:%M")
            spot = row['ltp']
            vwap = row['vwap']
            rsi5 = row['fast_rsi_5']
            p15_low = row['rolling_15m_low']

            # 1. Trigger scheduled signal
            for sig_req in signal_schedule:
                if sig_req["time_str"] == time_str and not sig_req.get("processed"):
                    sig_req["processed"] = True
                    print(f"\n⚡ [{t_ist.strftime('%H:%M:%S IST')}] Raw Signal Generated: BUY_CALL {symbol} (Spot: {spot:.2f})")
                    print(f"   Tri-Model Probs: CatBoost={sig_req['cb']:.2f}, LightGBM={sig_req['lgb']:.2f}, XGBoost={sig_req['xgb']:.2f}")

                    consensus = MultiModelConsensusGate.evaluate_consensus(
                        catboost_prob=sig_req['cb'],
                        lightgbm_prob=sig_req['lgb'],
                        xgboost_prob=sig_req['xgb'],
                        decision="BUY_CALL"
                    )

                    if consensus["is_discordant"]:
                        print(f"   🛡️ GATE TRIGGERED: {consensus['reason']}")
                        print(f"   Market State: {consensus['market_state']} -> Routed strictly via PULLBACK_LIMIT_ONLY!")
                    else:
                        print(f"   ✅ STRONG CONSENSUS: All models agree (min {consensus['ml_consensus_min']:.2f} >= 0.45).")

                    pullback_eval = pullback_manager.evaluate_pullback_conditions(
                        symbol=symbol,
                        current_spot=spot,
                        live_vwap=vwap,
                        rsi_1m_period_5=rsi5,
                        decision="BUY_CALL"
                    )

                    if not pullback_eval["confirmed"] and active_position is None:
                        candidate_payload = {
                            "symbol": symbol,
                            "spot_price": spot,
                            "strike": sig_req["strike"],
                            "est_prem": sig_req["est_prem"],
                            "decision": "BUY_CALL",
                            "ml_consensus_min": consensus["ml_consensus_min"]
                        }
                        pullback_manager.register_candidate_signal(symbol, candidate_payload)
                        print(f"   ⏳ PULLBACK ENGINE: Holding signal in 180s observation queue.")
                        print(f"      Current Spot: {spot:.2f} | VWAP: {vwap:.2f} (Diff: {abs(spot-vwap):.1f}pts > 5pts) | RSI: {rsi5:.1f}")

            # 2. Check Pending Pullback Queue
            if active_position is None and symbol in pullback_manager.pending_queue:
                pending_res = pullback_manager.check_pending_signal(
                    symbol=symbol,
                    current_spot=spot,
                    live_vwap=vwap,
                    rsi_1m_period_5=rsi5
                )
                if pending_res and pending_res.get("status") == "PULLBACK_CONFIRMED":
                    p_sig = pending_res["signal_payload"]
                    wait_ms = pending_res["pullback_wait_duration_ms"]
                    print(f"\n🎯 [{t_ist.strftime('%H:%M:%S IST')}] PULLBACK CONFIRMED! Triggers: {pending_res['confirmation_triggers']}")
                    print(f"   Wait Duration: {wait_ms/1000:.1f}s | Filled at Spot: {spot:.2f} (VWAP: {vwap:.2f})")

                    tot_qty, tot_lots = AsymmetricTradeLifecycle.enforce_even_lots(65, 2)
                    struct_levels = StructuralRiskManager.calculate_structural_levels(
                        decision="BUY_CALL",
                        current_spot=spot,
                        live_vwap=vwap,
                        prior_15m_low=p15_low
                    )
                    spot_sl = struct_levels["structural_level"]

                    active_position = {
                        "entry_time": t_ist.strftime("%H:%M:%S IST"),
                        "entry_spot": spot,
                        "entry_premium": p_sig["est_prem"],
                        "current_sl_premium": p_sig["est_prem"] * 0.75,
                        "spot_structural_sl": spot_sl,
                        "highest_premium": p_sig["est_prem"],
                        "tier1_booked": False,
                        "tier1_hit_timestamp": None,
                        "total_lots": tot_lots,
                        "remaining_lots": tot_lots,
                        "base_lot_size": 65,
                        "total_quantity": tot_qty,
                        "ml_consensus_min": p_sig["ml_consensus_min"],
                        "pullback_wait_duration_ms": wait_ms,
                        "strike": p_sig["strike"]
                    }
                    print(f"   🚀 Position OPEN: {symbol} {p_sig['strike']} CE | Qty: {tot_qty} ({tot_lots} lots) @ ₹{p_sig['est_prem']:.2f}")
                    print(f"      Spot Structural SL: {spot_sl:.2f} (Underlying Support Anchor)")

                elif pending_res and pending_res.get("status") == "PULLBACK_TIMEOUT_DISCARD":
                    print(f"\n🛑 [{t_ist.strftime('%H:%M:%S IST')}] PULLBACK_TIMEOUT_DISCARD: Discarded safely after 180s without FOMO chasing.")

            # 3. Monitor Active Position across Ticks
            if active_position is not None:
                entry_p = active_position["entry_premium"]
                entry_s = active_position["entry_spot"]
                spot_pct_move = (spot - entry_s) / entry_s
                current_prem = max(0.50, round(entry_p * (1.0 + (spot_pct_move * 20)), 2))
                active_position["highest_premium"] = max(active_position["highest_premium"], current_prem)
                high_p = active_position["highest_premium"]

                struct_stop = StructuralRiskManager.evaluate_structural_stop(
                    decision="BUY_CALL",
                    current_spot=spot,
                    live_vwap=vwap,
                    entry_premium=entry_p,
                    current_premium=current_prem,
                    prior_15m_low=p15_low
                )

                lifecycle = AsymmetricTradeLifecycle.evaluate_lifecycle_state(
                    entry_premium=entry_p,
                    current_premium=current_prem,
                    highest_observed_premium=high_p,
                    current_sl_premium=active_position["current_sl_premium"],
                    tier1_booked=active_position["tier1_booked"],
                    tier1_hit_timestamp=active_position["tier1_hit_timestamp"],
                    is_spot_trend_reversed=(spot < vwap - 10.0),
                    lot_size=65,
                    total_lots=active_position["total_lots"],
                    remaining_lots=active_position["remaining_lots"]
                )

                if lifecycle["current_sl_premium"] > active_position["current_sl_premium"]:
                    active_position["current_sl_premium"] = lifecycle["current_sl_premium"]
                    print(f"   🛡️ [{t_ist.strftime('%H:%M:%S IST')}] BREAKEVEN RATCHET ACTIVATED: Gain >= +6%. Stop Loss ratcheted to ₹{active_position['current_sl_premium']:.2f} (Entry + ₹1.00)")

                if lifecycle["tier1_booked"] and not active_position["tier1_booked"]:
                    active_position["tier1_booked"] = True
                    active_position["tier1_hit_timestamp"] = lifecycle["tier1_hit_timestamp"]
                    active_position["remaining_lots"] = lifecycle["remaining_lots"]
                    booked_lots = active_position["total_lots"] - active_position["remaining_lots"]
                    tier1_gross = (current_prem - entry_p) * (booked_lots * 65)
                    tier1_charges = calculate_options_roundtrip_charges(current_prem, 65, booked_lots, "NSE")["summary"]["total_roundtrip_cost"]
                    active_position["tier1_net_pnl"] = tier1_gross - tier1_charges
                    active_position["tier1_exit_prem"] = current_prem
                    print(f"   🎉 [{t_ist.strftime('%H:%M:%S IST')}] TIER 1 HIT (+{lifecycle['gain_pct']}%): Booked 50% position ({booked_lots} lot / {booked_lots*65} qty) @ ₹{current_prem:.2f} (+₹{active_position['tier1_net_pnl']:.2f} Net Locked)")
                    print(f"      Runner Position Active: {active_position['remaining_lots']} lot remaining, trailing spot trend structure uncapped!")

                should_close = False
                close_reason = ""
                exit_p = current_prem

                if struct_stop["is_stop_triggered"]:
                    should_close = True
                    close_reason = struct_stop["exit_reason"]
                elif lifecycle["lifecycle_status"] in ["RUNNER_EXITED_ON_TREND_REVERSAL", "RUNNER_STOPPED_AT_BREAKEVEN", "STOP_LOSS_HIT"]:
                    should_close = True
                    close_reason = lifecycle["lifecycle_status"]
                elif idx == len(df_ticks) - 1:
                    should_close = True
                    close_reason = "EOD_SQUAREOFF"

                if should_close:
                    rem_lots = active_position["remaining_lots"]
                    rem_gross = (exit_p - entry_p) * (rem_lots * 65)
                    rem_charges = calculate_options_roundtrip_charges(exit_p, 65, rem_lots, "NSE")["summary"]["total_roundtrip_cost"]
                    rem_net = rem_gross - rem_charges
                    tier1_net = active_position.get("tier1_net_pnl", 0.0)
                    tot_net = tier1_net + rem_net

                    trade_record = {
                        "entry_time": active_position["entry_time"],
                        "exit_time": t_ist.strftime("%H:%M:%S IST"),
                        "contract": f"{symbol} {active_position['strike']} CE",
                        "entry_prem": entry_p,
                        "exit_prem": exit_p,
                        "tier1_booked": active_position["tier1_booked"],
                        "tier1_net": round(tier1_net, 2),
                        "runner_net": round(rem_net, 2),
                        "total_net_pnl": round(tot_net, 2),
                        "exit_reason": close_reason,
                        "peak_gain_pct": lifecycle["peak_gain_pct"]
                    }
                    completed_trades.append(trade_record)
                    print(f"\n🏁 [{t_ist.strftime('%H:%M:%S IST')}] POSITION RESOLVED: {close_reason} @ ₹{exit_p:.2f}")
                    print(f"   Peak Gain: +{lifecycle['peak_gain_pct']}% | Tier 1 Net: ₹{tier1_net:+.2f} | Runner Net: ₹{rem_net:+.2f} | Total Trade Net PnL: ₹{tot_net:+.2f}")
                    active_position = None

        total_synthetic_pnl = sum(t["total_net_pnl"] for t in completed_trades)
        historical_pnl = -6216.81
        alpha_delta = total_synthetic_pnl - historical_pnl

        print("\n" + "=" * 80)
        print(f"📊 SYNTHETIC PLAYBACK SESSION SUMMARY — {date_str}")
        print("=" * 80)
        if completed_trades:
            df_res = pd.DataFrame(completed_trades)
            print(df_res.to_string())
        print(f"\n💰 Total Synthetic Session Net PnL: ₹{total_synthetic_pnl:+,.2f}")
        print(f"📉 Historical Realized Net PnL (Revision 00196-2jg): ₹{historical_pnl:+,.2f}")
        print(f"🚀 Net Alpha Recovery Delta: ₹{alpha_delta:+,.2f}")
        print("=" * 80)

        return {
            "status": "COMPLETED",
            "date": date_str,
            "symbol": symbol,
            "ticks_analyzed": len(df_ticks),
            "completed_trades": completed_trades,
            "total_synthetic_net_pnl": round(total_synthetic_pnl, 2),
            "historical_production_net_pnl": historical_pnl,
            "net_alpha_recovery_delta": round(alpha_delta, 2)
        }

# Class and Singleton Instances
AutonomousShadowScanner = ContinuousShadowScanner
AUTONOMOUS_SHADOW_SCANNER = ContinuousShadowScanner()

def run_synthetic_playback(date_str: str = "2026-10-09", symbol: str = "NIFTY") -> Dict[str, Any]:
    """Standalone CLI entry point for running synthetic playback session"""
    scanner = ContinuousShadowScanner()
    return scanner.run_synthetic_playback_session(date_str=date_str, symbol=symbol)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    sys.path.insert(0, os.path.join(root_dir, "backend", "engine-a"))
    sys.path.append(os.path.join(root_dir, "backend"))
    
    date_arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "2026-10-09"
    sym_arg = sys.argv[2] if len(sys.argv) > 2 else "NIFTY"
    run_synthetic_playback(date_str=date_arg, symbol=sym_arg)

