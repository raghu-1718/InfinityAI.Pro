"""
Autonomous Shadow Signal Logger & Telemetry Vault
InfinityAI.Pro - Institutional Algorithmic Trading Platform
Automatically records all Tri-Model ML & Gemini signals into Cloud Firestore
without requiring manual trading execution or live capital risk.
"""

import os
import time
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

try:
    from .alert_dispatcher import ALERT_DISPATCHER
except Exception:
    try:
        from src.services.alert_dispatcher import ALERT_DISPATCHER
    except Exception:
        ALERT_DISPATCHER = None

try:
    from shared.tax_calculator import calculate_options_roundtrip_charges
except ImportError:
    try:
        from tax_calculator import calculate_options_roundtrip_charges
    except ImportError:
        def calculate_options_roundtrip_charges(*args, **kwargs):
            return {"grand_total_charges": 55.0}

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "ai_signals_ledger"

class ShadowSignalLogger:
    """Manages autonomous shadow signal logging and outcome resolution in Firestore"""

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        try:
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"✅ ShadowSignalLogger connected to Firestore [{self.project_id}]")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Firestore: {e}")
            self.db = None

    def log_shadow_signal(
        self,
        symbol: str,
        spot_price: float,
        decision: str,  # "BUY_CALL", "BUY_PUT", "NEUTRAL"
        confidence_score: float,
        catboost_prob: float,
        lightgbm_prob: float,
        xgboost_prob: float,
        gemini_sentiment: str = "NEUTRAL",
        lot_size: int = 65,
        risk_reward_ratio: str = "1:2.0",
        live_option_quote: Optional[Dict[str, Any]] = None,
        live_vwap: Optional[float] = None,
        prior_15m_low: Optional[float] = None,
        prior_15m_high: Optional[float] = None,
        pullback_wait_duration_ms: Optional[int] = 0,
        requested_lots: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Logs a generated trading signal into Firestore in SHADOW_OBSERVATION mode.
        Supports live market depth pricing (Ask-entry / Bid-exit) with liquidity and spread safeguards,
        spot-anchored structural stops, and asymmetric multi-tier profit trailing.
        """
        if not self.db:
            logger.warning("Firestore client not initialized. Skipping signal log.")
            return None

        # Strict filter: only execute on explicit directional decisions with sufficient confidence (>= 0.60)
        valid_trade_decisions = ["BUY_CALL", "BUY_PUT", "SELL_CALL", "SELL_PUT", "LONG_CALL", "LONG_PUT", "SHORT_CALL", "SHORT_PUT"]
        if decision not in valid_trade_decisions or confidence_score < 0.60:
            logger.info(f"Signal for {symbol} is {decision} (conf: {confidence_score:.3f}). Skipping trade ledger commit.")
            return None

        # SENSEX Derivative Restriction Gate (Eliminates -₹52k liquidity/spread drag)
        if "SENSEX" in symbol.upper():
            logger.warning(f"🚫 SENSEX derivatives disabled by Institutional Risk Audit. Skipping trade ledger commit for {symbol}.")
            return None

        # ── Task 1: Multi-Model Consensus & Discordance Gate ──────────────────
        try:
            from .ml_consensus_gate import MultiModelConsensusGate
            consensus_eval = MultiModelConsensusGate.evaluate_consensus(
                catboost_prob=catboost_prob,
                lightgbm_prob=lightgbm_prob,
                xgboost_prob=xgboost_prob,
                decision=decision
            )
        except Exception as e:
            logger.warning(f"Consensus gate evaluation fallback: {e}")
            consensus_eval = {
                "consensus_passed": True,
                "is_discordant": False,
                "market_state": "REGIME_TRENDING_CONSENSUS",
                "execution_route": "STANDARD_MARKET_ALLOWED",
                "ml_consensus_min": min(catboost_prob, lightgbm_prob, xgboost_prob),
                "reason": "Consensus Fallback"
            }

        ml_consensus_min = float(consensus_eval.get("ml_consensus_min", min(catboost_prob, lightgbm_prob, xgboost_prob)))

        # Veto immediate market orders if discordant and no pullback confirmation was provided
        if consensus_eval.get("is_discordant") and (not pullback_wait_duration_ms or pullback_wait_duration_ms <= 0):
            logger.warning(
                f"⚠️ Multi-Model Discordance Veto: min({ml_consensus_min:.3f}) < 0.40. "
                f"Flagged REGIME_CHOP_CONSOLIDATION. Immediate market order blocked; "
                f"routing strictly via Pullback Limit Engine."
            )
            return None

        # Regime-Adaptive Dynamic Mixture-of-Experts (MoE) Gate
        analysis_data = {
            "catboost_prob": catboost_prob,
            "lightgbm_prob": lightgbm_prob,
            "xgboost_prob": xgboost_prob,
            "overall_confidence": confidence_score
        }
        try:
            from .regime_adaptive_moe_gate import evaluate_regime_moe_consensus
            moe_res = evaluate_regime_moe_consensus(
                symbol=symbol,
                decision_or_signal_type=decision,
                analysis_data=analysis_data,
                overall_confidence=confidence_score
            )
        except Exception as e:
            logger.warning(f"MoE gate fallback in shadow logger: {e}")
            moe_res = {"approved": True, "reason": "MoE Fallback", "regime": "EQUILIBRIUM_BASELINE"}

        if not moe_res["approved"] and moe_res.get("execution_route") != "PULLBACK_LIMIT_ONLY":
            logger.info(
                f"⏸️ Signal for {symbol} rejected by Regime-Adaptive MoE Gate "
                f"(Regime: {moe_res.get('regime')}, Reason: {moe_res.get('reason')})."
            )
            return None

        now_utc = datetime.now(timezone.utc)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        timestamp_str = ist_time.strftime("%Y-%m-%d %H:%M:%S IST")
        signal_id = f"SIG_{ist_time.strftime('%Y%m%d_%H%M%S')}_{symbol}"

        # ── Task 4 Specification: Lot Size Determination & Even Multiples ─────
        sym_u = symbol.upper()
        if "BANKNIFTY" in sym_u:
            base_lot_size = 30
            strike_step = 100
        elif "BANKEX" in sym_u:
            base_lot_size = 30
            strike_step = 100
        elif "FINNIFTY" in sym_u:
            base_lot_size = 60
            strike_step = 50
        elif "MIDCP" in sym_u:
            base_lot_size = 120
            strike_step = 25
        elif "SENSEX" in sym_u:
            base_lot_size = 20
            strike_step = 100
        elif "NIFTY" in sym_u:
            base_lot_size = 65
            strike_step = 50
        else:
            base_lot_size = 65
            strike_step = 50

        from .asymmetric_trade_lifecycle import AsymmetricTradeLifecycle
        total_quantity, actual_lots = AsymmetricTradeLifecycle.enforce_even_lots(
            standard_lot_size=base_lot_size,
            requested_lots=requested_lots
        )
        actual_lot_size = total_quantity

        # Option Bracket Calculation
        is_sell = "SELL" in decision.upper() or "SHORT" in decision.upper()
        option_type = "CE" if "CALL" in decision.upper() else "PE"

        if is_sell:
            otm_offset = (2 * strike_step) if option_type == "CE" else (-2 * strike_step)
            strike = round((spot_price + otm_offset) / strike_step) * strike_step
        else:
            strike = round(spot_price / strike_step) * strike_step

        contract_name = f"{symbol} {int(strike)} {option_type} ({'SELL' if is_sell else 'BUY'})"

        # ── Realistic Pricing Model & Liquidity / Spread Filters (Checked First) ──
        pricing_source = "THEORETICAL_BLACK_SCHOLES"
        spread_pct = 0.0

        if live_option_quote and isinstance(live_option_quote, dict):
            ask_p = float(live_option_quote.get("ask_price", live_option_quote.get("ask", 0.0)))
            bid_p = float(live_option_quote.get("bid_price", live_option_quote.get("bid", 0.0)))
            ltp_p = float(live_option_quote.get("ltp", live_option_quote.get("last_price", 0.0)))
            oi = int(live_option_quote.get("open_interest", live_option_quote.get("oi", 50000)))
            vol = int(live_option_quote.get("volume", live_option_quote.get("vol", 10000)))

            # Liquidity Safeguard: Minimum OI & Volume
            if oi < 10000 or vol < 1000:
                logger.warning(f"⚠️ Liquidity filter failed for {contract_name} (OI: {oi}, Vol: {vol}) — Skipping trade.")
                return None

            # Spread Safeguard: Reject if Ask-Bid spread > 4% of LTP
            ref_p = max(ltp_p, ask_p, bid_p, 1.0)
            if ask_p > 0 and bid_p > 0:
                spread = ask_p - bid_p
                spread_pct = round((spread / ref_p) * 100.0, 2)
                if spread / ref_p > 0.04:
                    logger.warning(f"⚠️ Wide spread veto for {contract_name} ({spread_pct}% > 4%) — Skipping trade.")
                    return None
                # Realistic Entry: Taker buys at Ask, Taker sells at Bid
                est_premium = round(bid_p if is_sell else ask_p, 2)
                pricing_source = "LIVE_MARKET_DEPTH_BID" if is_sell else "LIVE_MARKET_DEPTH_ASK"
            elif ltp_p > 0:
                # Spread friction penalty: -1.0% for sell, +1.0% for buy
                est_premium = round(ltp_p * (0.99 if is_sell else 1.01), 2)
                pricing_source = "LIVE_LTP_SPREAD_ADJUSTED"
            else:
                est_premium = None
        else:
            est_premium = None

        # Deduplication Guard: Prevent duplicate positions for the same contract while one is OPEN
        try:
            open_signals = list(
                self.db.collection(COLLECTION_NAME)
                .where(filter=FieldFilter("symbol", "==", symbol))
                .where(filter=FieldFilter("outcome_status", "==", "OPEN"))
                .limit(10)
                .stream()
            )
            for open_sig in open_signals:
                open_data = open_sig.to_dict()
                bracket = open_data.get("trade_bracket", {})
                if bracket.get("strike") == strike and bracket.get("option_type") == option_type:
                    logger.info(f"⏸️ Duplicate signal suppressed: Already have OPEN position for {contract_name} (Existing Doc: {open_sig.id}).")
                    return None
        except Exception as e:
            logger.warning(f"Error checking open signals deduplication: {e}")

        # Fallback to Analytical Black-Scholes Option Pricing if Live Depth Unavailable
        if est_premium is None or est_premium <= 0:
            try:
                import math
                from scipy.stats import norm
                target_weekday = 3 if "SENSEX" in sym_u else 1
                today_weekday = ist_time.weekday()
                days_to_exp = (target_weekday - today_weekday) % 7
                if days_to_exp == 0:
                    hours_left = max(15.5 - (ist_time.hour + ist_time.minute / 60.0), 0.25)
                    dte_years = max(hours_left / (24.0 * 365.0), 1e-4)
                else:
                    dte_years = max(days_to_exp / 365.0, 1e-4)

                atm_iv = 0.172
                r = 0.065
                sigma = max(atm_iv, 0.01)

                d1 = (math.log(spot_price / strike) + (r + 0.5 * sigma ** 2) * dte_years) / (sigma * math.sqrt(dte_years))
                d2 = d1 - sigma * math.sqrt(dte_years)

                if option_type == "CE":
                    bs_price = spot_price * norm.cdf(d1) - strike * math.exp(-r * dte_years) * norm.cdf(d2)
                else:
                    bs_price = strike * math.exp(-r * dte_years) * norm.cdf(-d2) - spot_price * norm.cdf(-d1)

                friction_mult = 0.99 if is_sell else 1.01
                est_premium = max(round(float(bs_price) * friction_mult, 2), 5.0)
                pricing_source = "THEORETICAL_BS_SPREAD_ADJUSTED"
            except Exception:
                est_premium = round(spot_price * (0.0025 if is_sell else 0.004), 2)
                pricing_source = "ESTIMATED_RULE_OF_THUMB"

        # ── Task 3: Spot-Anchored Structural Stops Calculation ────────────────
        from .structural_risk_manager import StructuralRiskManager
        vwap_val = live_vwap if (live_vwap and live_vwap > 0) else spot_price
        struct_levels = StructuralRiskManager.calculate_structural_levels(
            decision=decision,
            current_spot=spot_price,
            live_vwap=vwap_val,
            prior_15m_low=prior_15m_low,
            prior_15m_high=prior_15m_high
        )
        spot_structural_sl = struct_levels["structural_level"]

        # Absolute Emergency Circuit Breaker: -25% option stop loss
        if is_sell:
            stop_loss_prem = round(est_premium * 1.25, 2)
            target_prem = round(est_premium * 0.55, 2)  # Decay target
            stop_loss_pct = 0.25
            target_pct = 0.45
        else:
            stop_loss_prem = round(est_premium * 0.75, 2)  # -25% emergency breaker
            target_prem = round(est_premium * 1.15, 2)     # Tier 1 +15% target
            stop_loss_pct = 0.25
            target_pct = 0.15

        # Statutory taxes & Dhan brokerage estimate (calculated on total lots)
        charges = calculate_options_roundtrip_charges(
            premium=est_premium,
            lot_size=base_lot_size,
            lots=actual_lots,
            exchange="NSE"
        )
        tax_cost = charges.get("grand_total_charges", 55.0 * actual_lots)

        # Expected P&L metrics based on system capability
        if is_sell:
            capital_required = 125000.0 * actual_lots
            expected_target_gross = round((est_premium - target_prem) * actual_lot_size, 2)
            expected_target_net = round(expected_target_gross - tax_cost, 2)
            max_loss_gross = round((est_premium - stop_loss_prem) * actual_lot_size, 2)
            max_loss_net = round(max_loss_gross - tax_cost, 2)
        else:
            capital_required = round(est_premium * actual_lot_size, 2)
            expected_target_gross = round((target_prem - est_premium) * actual_lot_size, 2)
            expected_target_net = round(expected_target_gross - tax_cost, 2)
            max_loss_gross = round((stop_loss_prem - est_premium) * actual_lot_size, 2)
            max_loss_net = round(max_loss_gross - tax_cost, 2)

        expected_roi_pct = round((expected_target_net / capital_required * 100), 2) if capital_required > 0 else 0.0

        expected_pnl_payload = {
            "expected_profit_target_gross": expected_target_gross,
            "expected_profit_target_net": expected_target_net,
            "expected_profit_target_pct": round(target_pct * 100, 1),
            "max_loss_stop_loss_gross": max_loss_gross,
            "max_loss_stop_loss_net": max_loss_net,
            "max_loss_stop_loss_pct": round(-stop_loss_pct * 100, 1),
            "system_capital_required": capital_required,
            "expected_roi_on_capital_pct": expected_roi_pct,
            "risk_reward_ratio": "1:2.0 (Asymmetric Trailing)",
            "system_capability_rating": "INSTITUTIONAL_TRI_MODEL_ENSEMBLE",
            "trade_action": "SELL" if is_sell else "BUY"
        }

        # Real-time Institutional FII/DII Flow Radar Multiplier
        try:
            from .fii_dii_flow_radar import FII_DII_FLOW_RADAR
            adj_conf, flow_data = FII_DII_FLOW_RADAR.apply_multiplier_to_confidence(confidence_score, decision)
            confidence_score = adj_conf
        except Exception:
            flow_data = {"regime": "BALANCED_EQUILIBRIUM", "institutional_multiplier": 1.0}

        payload = {
            "signal_id": signal_id,
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_ist": timestamp_str,
            "date": ist_time.strftime("%Y-%m-%d"),
            "month": ist_time.strftime("%Y-%m"),
            "symbol": symbol,
            "spot_price": spot_price,
            "live_vwap": vwap_val,
            "decision": decision,
            "confidence_score": round(confidence_score, 4),
            "ml_consensus_min": ml_consensus_min,
            "spot_structural_sl": spot_structural_sl,
            "pullback_wait_duration_ms": pullback_wait_duration_ms or 0,
            "tier1_hit_timestamp": None,
            "tier1_booked": False,
            "total_lots": actual_lots,
            "remaining_lots": actual_lots,
            "base_lot_size": base_lot_size,
            "current_sl_premium": stop_loss_prem,
            "model_breakdown": {
                "catboost_prob": round(catboost_prob, 4),
                "lightgbm_prob": round(lightgbm_prob, 4),
                "xgboost_prob": round(xgboost_prob, 4),
                "gemini_sentiment": gemini_sentiment,
                "institutional_flow": flow_data
            },
            "trade_bracket": {
                "contract": contract_name,
                "strike": strike,
                "option_type": option_type,
                "entry_premium": est_premium,
                "target_premium": target_prem,
                "target_percent": target_pct * 100,
                "stop_loss_premium": stop_loss_prem,
                "stop_loss_percent": stop_loss_pct * 100,
                "spot_structural_sl": spot_structural_sl,
                "trailing_stop_loss_active": True,
                "trailing_tiers": "Tier 1: +12-15% (50% Qty) | Breakeven Ratchet: +6% -> Entry+1.00 | Tier 2 Runner: Trail Spot Trend",
                "risk_reward": "1:2.0 (Asymmetric Trailing)",
                "lot_size": actual_lot_size,
                "total_lots": actual_lots,
                "pricing_source": pricing_source,
                "spread_pct": spread_pct
            },
            "expected_pnl": expected_pnl_payload,
            "highest_observed_premium": est_premium,
            "lowest_observed_premium": est_premium,
            "active_profit_tier": "BASE_STRUCTURAL_RISK",
            "current_mtm_gross_pnl": 0.0,
            "current_mtm_net_pnl": 0.0,
            "current_mtm_roi_pct": 0.0,
            "execution_mode": "SHADOW_OBSERVATION",
            "outcome_status": "OPEN",
            "estimated_tax_brokerage": tax_cost,
            "exit_premium": None,
            "gross_pnl": None,
            "net_pnl": None,
            "resolved_at": None
        }

        try:
            self.db.collection(COLLECTION_NAME).document(signal_id).set(payload)
            # Sync to active_positions collection for real-time risk supervision
            try:
                active_pos_payload = {
                    "signal_id": signal_id,
                    "symbol": symbol,
                    "decision": decision,
                    "contract": contract_name,
                    "entry_premium": est_premium,
                    "sl_premium": stop_loss_prem,
                    "spot_structural_sl": spot_structural_sl,
                    "ml_consensus_min": ml_consensus_min,
                    "pullback_wait_duration_ms": pullback_wait_duration_ms or 0,
                    "tier1_hit_timestamp": None,
                    "tier1_booked": False,
                    "total_lots": actual_lots,
                    "remaining_lots": actual_lots,
                    "status": "OPEN",
                    "created_at": timestamp_str,
                    "updated_at": timestamp_str
                }
                self.db.collection("active_positions").document(signal_id).set(active_pos_payload)
            except Exception as pos_err:
                logger.warning(f"Failed to record active_positions doc: {pos_err}")

            # Structured Cloud Logging with Institutional Telemetry
            logger.info(
                f"✅ Shadow Signal committed: [{signal_id}] -> {decision} on {symbol} (Lots: {actual_lots}, Spot SL: {spot_structural_sl})",
                extra={
                    "ml_consensus_min": ml_consensus_min,
                    "spot_structural_sl": spot_structural_sl,
                    "pullback_wait_duration_ms": pullback_wait_duration_ms or 0,
                    "tier1_hit_timestamp": None,
                    "signal_id": signal_id,
                    "symbol": symbol,
                    "decision": decision
                }
            )
            if ALERT_DISPATCHER:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(ALERT_DISPATCHER.dispatch_signal_alert(payload))
                except Exception:
                    pass
            return payload
        except Exception as e:
            logger.error(f"❌ Failed to write shadow signal to Firestore: {e}")
            return None

    def update_open_signals_mtm(self, current_spot_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Scans all OPEN shadow signals, recalculates live MTM PnL based on current spot prices,
        and triggers auto-resolution if targets or stops are hit.
        """
        if not self.db or not current_spot_prices:
            return {"updated": 0, "resolved": 0}

        try:
            open_docs = list(self.db.collection(COLLECTION_NAME).where(filter=FieldFilter("outcome_status", "==", "OPEN")).stream())
            updated_count = 0
            resolved_count = 0

            for doc in open_docs:
                data = doc.to_dict()
                sig_id = data.get("signal_id", doc.id)
                symbol = data.get("symbol", "").upper()
                current_spot = current_spot_prices.get(symbol)

                if not current_spot or current_spot <= 0:
                    continue

                res = self.resolve_signal_outcome(sig_id, current_spot)
                if res:
                    if res.get("outcome_status") != "OPEN":
                        resolved_count += 1
                    else:
                        updated_count += 1

            return {"updated": updated_count, "resolved": resolved_count}
        except Exception as e:
            logger.error(f"Error updating open signals MTM: {e}")
            return {"updated": 0, "resolved": 0, "error": str(e)}

    def resolve_signal_outcome(
        self,
        signal_id: str,
        current_spot: float,
        is_eod_squareoff: bool = False,
        current_option_premium: Optional[float] = None,
        live_vwap: Optional[float] = None,
        prior_15m_low: Optional[float] = None,
        prior_15m_high: Optional[float] = None,
        is_spot_trend_reversed: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates open signals using spot-anchored structural stops and the asymmetric multi-tier lifecycle:
          - Spot-Anchored Stops: Underlying index structure controls exits (not option premium noise).
          - Emergency Circuit Breaker: -25% option premium stop protects against extreme collapses.
          - Breakeven Shift (Dynamic Ratchet): Shifts sl_premium to entry + 1.00 at >= +6% gain.
          - Tier 1 Partial Booking: Books 50% position at +12% to +15% gain.
          - Tier 2 Runner: Trails spot trend structure with no static ceiling.
        """
        if not self.db:
            return None

        doc_ref = self.db.collection(COLLECTION_NAME).document(signal_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        if data.get("outcome_status") != "OPEN":
            return data  # Already resolved

        bracket = data.get("trade_bracket", {})
        entry_prem = bracket.get("entry_premium", 100.0)
        stop_prem = bracket.get("stop_loss_premium", 75.0)
        lot_size = bracket.get("lot_size", 65)
        decision = data.get("decision", "BUY_CALL")
        initial_spot = data.get("spot_price", current_spot)
        tax_cost = data.get("estimated_tax_brokerage", 55.0)
        is_sell = "SELL" in decision.upper() or "SHORT" in decision.upper()

        total_lots = data.get("total_lots", bracket.get("total_lots", 2))
        remaining_lots = data.get("remaining_lots", total_lots)
        base_lot_size = data.get("base_lot_size", 65)

        # ── Realistic Premium Calculation ──────────────────────────────────────
        if current_option_premium is not None and current_option_premium > 0:
            simulated_exit_prem = round(float(current_option_premium), 2)
        else:
            spot_pct_move = (current_spot - initial_spot) / initial_spot if initial_spot > 0 else 0.0
            if "CALL" in decision:
                simulated_exit_prem = entry_prem * (1.0 + (spot_pct_move * 20))
            else:
                simulated_exit_prem = entry_prem * (1.0 - (spot_pct_move * 20))
            simulated_exit_prem = max(0.50, simulated_exit_prem)

        highest_prev = data.get("highest_observed_premium", entry_prem)
        highest_now = max(highest_prev, simulated_exit_prem)
        lowest_prev = data.get("lowest_observed_premium", entry_prem)
        lowest_now = min(lowest_prev, simulated_exit_prem)
        peak_achieved_pct = round(((highest_now - entry_prem) / entry_prem) * 100, 2) if entry_prem > 0 else 0.0

        outcome_status = "OPEN"
        active_tier = data.get("active_profit_tier", "BASE_STRUCTURAL_RISK")
        effective_sl = data.get("current_sl_premium", stop_prem)

        now_utc = datetime.now(timezone.utc)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        timestamp_str = ist_time.strftime("%Y-%m-%d %H:%M:%S IST")

        # ── Task 3: Spot-Anchored Structural Stops Evaluation ──────────────────
        from .structural_risk_manager import StructuralRiskManager
        vwap_val = live_vwap or data.get("live_vwap") or initial_spot
        struct_stop_eval = StructuralRiskManager.evaluate_structural_stop(
            decision=decision,
            current_spot=current_spot,
            live_vwap=vwap_val,
            entry_premium=entry_prem,
            current_premium=simulated_exit_prem,
            prior_15m_low=prior_15m_low or data.get("prior_15m_low"),
            prior_15m_high=prior_15m_high or data.get("prior_15m_high")
        )
        spot_structural_sl = struct_stop_eval["spot_structural_sl"]

        if struct_stop_eval["is_stop_triggered"]:
            if struct_stop_eval["is_emergency_stop"]:
                outcome_status = "EMERGENCY_STOP_LOSS_HIT"
                active_tier = "EMERGENCY_PREMIUM_CIRCUIT_BREAKER_25PCT"
            else:
                outcome_status = "STOP_LOSS_HIT"
                active_tier = struct_stop_eval["exit_reason"]

        # ── Task 4: Asymmetric Multi-Tier Profit Trailing State Machine ─────────
        from .asymmetric_trade_lifecycle import AsymmetricTradeLifecycle
        tier1_booked = data.get("tier1_booked", False)
        tier1_hit_timestamp = data.get("tier1_hit_timestamp")

        lifecycle_eval = AsymmetricTradeLifecycle.evaluate_lifecycle_state(
            entry_premium=entry_prem,
            current_premium=simulated_exit_prem,
            highest_observed_premium=highest_now,
            current_sl_premium=effective_sl,
            tier1_booked=tier1_booked,
            tier1_hit_timestamp=tier1_hit_timestamp,
            is_spot_trend_reversed=is_spot_trend_reversed,
            lot_size=base_lot_size,
            total_lots=total_lots,
            remaining_lots=remaining_lots,
            is_sell=is_sell
        )

        effective_sl = lifecycle_eval["current_sl_premium"]
        new_tier1_booked = lifecycle_eval["tier1_booked"]
        new_tier1_timestamp = lifecycle_eval["tier1_hit_timestamp"]
        remaining_lots = lifecycle_eval["remaining_lots"]

        # Dynamic Breakeven Ratchet (+6% Gain): Update active_positions document field sl_premium
        if effective_sl > stop_prem:
            try:
                self.db.collection("active_positions").document(signal_id).update({
                    "sl_premium": effective_sl,
                    "active_tier": lifecycle_eval["active_tier_label"],
                    "updated_at": timestamp_str
                })
            except Exception as e:
                logger.debug(f"Failed to update active_positions sl_premium: {e}")

        # Update Tier 1 status if triggered
        if new_tier1_booked and not tier1_booked:
            tier1_booked = True
            tier1_hit_timestamp = new_tier1_timestamp
            active_tier = lifecycle_eval["active_tier_label"]
            try:
                self.db.collection("active_positions").document(signal_id).update({
                    "tier1_booked": True,
                    "tier1_hit_timestamp": tier1_hit_timestamp,
                    "remaining_lots": remaining_lots,
                    "updated_at": timestamp_str
                })
            except Exception as e:
                logger.debug(f"Failed to update active_positions tier1: {e}")

        # Check Lifecycle Status Exits
        if outcome_status == "OPEN":
            if lifecycle_eval["lifecycle_status"] == "RUNNER_EXITED_ON_TREND_REVERSAL":
                outcome_status = "RUNNER_TREND_REVERSAL_EXIT"
                active_tier = "TIER2_RUNNER_REVERSAL"
            elif lifecycle_eval["lifecycle_status"] == "RUNNER_STOPPED_AT_BREAKEVEN":
                outcome_status = "RUNNER_STOPPED_AT_BREAKEVEN"
                active_tier = "BREAKEVEN_RATCHET_EXIT"
            elif lifecycle_eval["lifecycle_status"] == "STOP_LOSS_HIT":
                outcome_status = "STOP_LOSS_HIT"
                active_tier = "BREAKEVEN_STOP_LOSS_HIT"

        # EOD Square-off
        if is_eod_squareoff and outcome_status == "OPEN":
            outcome_status = "EOD_SQUAREOFF"

        # Gross & Net PnL Calculation
        if is_sell:
            gross_pnl = (entry_prem - simulated_exit_prem) * lot_size
        else:
            gross_pnl = (simulated_exit_prem - entry_prem) * lot_size

        capital_required = 125000.0 * total_lots if is_sell else (entry_prem * lot_size)
        net_pnl = gross_pnl - tax_cost
        roi_pct = (net_pnl / capital_required * 100) if capital_required > 0 else 0.0

        if outcome_status != "OPEN":
            updates = {
                "outcome_status": outcome_status,
                "exit_premium": round(simulated_exit_prem, 2),
                "highest_observed_premium": round(highest_now, 2),
                "lowest_observed_premium": round(lowest_now, 2),
                "highest_target_achieved_pct": peak_achieved_pct,
                "active_profit_tier": active_tier,
                "current_sl_premium": round(effective_sl, 2),
                "spot_structural_sl": spot_structural_sl,
                "tier1_booked": tier1_booked,
                "tier1_hit_timestamp": tier1_hit_timestamp,
                "remaining_lots": remaining_lots,
                "gross_pnl": round(gross_pnl, 2),
                "net_pnl": round(net_pnl, 2),
                "roi_pct": round(roi_pct, 2),
                "resolved_at": timestamp_str
            }
            doc_ref.update(updates)
            try:
                self.db.collection("active_positions").document(signal_id).update({
                    "status": "CLOSED",
                    "outcome_status": outcome_status,
                    "resolved_at": timestamp_str
                })
            except Exception as e:
                logger.debug(f"Failed to close active_positions doc: {e}")

            # Structured Telemetry Logging for Resolution
            logger.info(
                f"🎯 Signal [{signal_id}] Resolved -> {outcome_status} ({active_tier}) | Peak: +{peak_achieved_pct}% | Net PnL: ₹{net_pnl:+.2f}",
                extra={
                    "ml_consensus_min": data.get("ml_consensus_min", 0.50),
                    "spot_structural_sl": spot_structural_sl,
                    "pullback_wait_duration_ms": data.get("pullback_wait_duration_ms", 0),
                    "tier1_hit_timestamp": tier1_hit_timestamp,
                    "signal_id": signal_id,
                    "outcome_status": outcome_status
                }
            )
            data.update(updates)
            if ALERT_DISPATCHER:
                try:
                    ALERT_DISPATCHER.dispatch_outcome_sync(data)
                except Exception as e:
                    logger.warning(f"Failed to dispatch outcome alert: {e}")
            return data
        else:
            # Update live Mark-to-Market (MTM)
            updates = {
                "current_mtm_spot": round(current_spot, 2),
                "current_mtm_premium": round(simulated_exit_prem, 2),
                "highest_observed_premium": round(highest_now, 2),
                "lowest_observed_premium": round(lowest_now, 2),
                "highest_target_achieved_pct": peak_achieved_pct,
                "current_sl_premium": round(effective_sl, 2),
                "effective_trailing_stop_loss": round(effective_sl, 2),
                "spot_structural_sl": spot_structural_sl,
                "tier1_booked": tier1_booked,
                "tier1_hit_timestamp": tier1_hit_timestamp,
                "remaining_lots": remaining_lots,
                "active_profit_tier": active_tier,
                "current_mtm_gross_pnl": round(gross_pnl, 2),
                "current_mtm_net_pnl": round(net_pnl, 2),
                "current_mtm_roi_pct": round(roi_pct, 2),
                "last_mtm_updated_at": timestamp_str
            }
            doc_ref.update(updates)
            data.update(updates)
            return data


def calculate_microstructure_slippage(
    raw_premium: float,
    obi: float,
    lot_size: int = 65
) -> float:
    """
    Computes real-world execution decay based on live order book imbalances (OBI 5-Depth).
    Ensures backtests and live shadow fills strictly reflect exchange liquidity.
    """
    if obi <= -0.70:
        slippage_penalty_pct = 0.015   # 1.5% slippage drop during institutional dumps
    elif -0.70 < obi <= -0.30:
        slippage_penalty_pct = 0.005   # 0.5% slippage drop during moderate ask pressure
    else:
        slippage_penalty_pct = 0.001   # 0.1% baseline structural bid-ask friction
        
    realized_execution_premium = raw_premium * (1.0 - slippage_penalty_pct)
    return round(realized_execution_premium, 2)

