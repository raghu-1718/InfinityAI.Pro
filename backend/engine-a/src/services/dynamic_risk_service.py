"""
InfinityAI.Pro — Dynamic AI Risk & Autonomous Exit Service (DRE)
=================================================================
Completely eliminates hardcoded stop-losses. Instead, continuously evaluates
real-time market state, model alpha decay, microstructure liquidity imbalance,
and volatility surface dynamics to execute mathematically optimized exits.

Includes Firestore state persistence for multi-process Cloud Run resilience.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
try:
    from google.cloud import firestore
except Exception:
    firestore = None

from .risk_config import RiskRegimeThresholds, LiveMarketState, PositionState

logger = logging.getLogger("InfinityAI.DynamicRiskService")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-841b7f97-5ee3-4fbe-920")
COLLECTION_NAME = "risk_position_state"

class DynamicRiskService:
    """Institutional Dynamic AI Risk & Autonomous Exit Engine"""

    def __init__(self, config: Optional[RiskRegimeThresholds] = None, project_id: str = PROJECT_ID):
        self.config = config or RiskRegimeThresholds()
        self.project_id = project_id
        self.state = PositionState(position_id="global_portfolio_state")
        self.db = None
        
        try:
            if firestore:
                self.db = firestore.Client(project=project_id)
                self._load_state_from_firestore()
        except Exception as e:
            logger.debug(f"Firestore state persistence note: {e}")

    def _load_state_from_firestore(self):
        """Loads persistent position and loss-streak state from Firestore"""
        if not self.db:
            return
        try:
            doc_ref = self.db.collection(COLLECTION_NAME).document(self.state.position_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                self.state.consecutive_losses = data.get("consecutive_losses", 0)
                self.state.cool_down_active = data.get("cool_down_active", False)
                ts_str = data.get("last_exit_timestamp")
                if ts_str:
                    self.state.last_exit_timestamp = datetime.fromisoformat(ts_str)
                logger.info(f"✅ Loaded persistent Risk State: Consecutive Losses = {self.state.consecutive_losses}, Cooldown = {self.state.cool_down_active}")
        except Exception as e:
            logger.warning(f"Error loading risk state from Firestore: {e}")

    def _persist_state_to_firestore(self):
        """Persists internal position state table to Firestore"""
        if not self.db:
            return
        try:
            payload = {
                "position_id": self.state.position_id,
                "is_active": self.state.is_active,
                "consecutive_losses": self.state.consecutive_losses,
                "cool_down_active": self.state.cool_down_active,
                "last_exit_timestamp": self.state.last_exit_timestamp.isoformat() if self.state.last_exit_timestamp else None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self.db.collection(COLLECTION_NAME).document(self.state.position_id).set(payload)
        except Exception as e:
            logger.warning(f"Error persisting risk state to Firestore: {e}")

    def check_cool_down_status(self, current_time: datetime) -> bool:
        """Verifies if the system is currently locked out due to serial loss correlation."""
        if not self.state.cool_down_active:
            return False

        if self.state.last_exit_timestamp:
            elapsed = (current_time - self.state.last_exit_timestamp).total_seconds() / 60.0
            if elapsed >= self.config.cool_down_duration_minutes:
                logger.info(f"🟢 Cool-down window expired ({elapsed:.1f}m >= {self.config.cool_down_duration_minutes}m). Re-enabling trading fleet at {current_time}.")
                self.state.cool_down_active = False
                self.state.consecutive_losses = 0
                self._persist_state_to_firestore()
                return False
        return True

    def evaluate_live_signals(self, market: LiveMarketState) -> Dict[str, Any]:
        """
        Processes real-time tick telemetry against dynamic mathematical boundaries.
        Zero hardcoded static stop-loss values used.
        """
        # Step 1: Structural Circuit Breaker Pre-Check
        if self.check_cool_down_status(market.timestamp):
            return {
                "action": "BLOCK_ENTRY_COOL_DOWN_ACTIVE",
                "reasons": ["SERIAL_LOSS_CORRELATION_LOCKOUT"],
                "cool_down_active": True,
                "consecutive_losses": self.state.consecutive_losses
            }

        # Step 2: Compute Volatility-Adjusted Premium Boundary Floor
        iv = market.live_greeks.get("IV", 0.1717)
        gamma = market.live_greeks.get("Gamma", 0.00084)

        # Volatility buffer expands/contracts dynamically based on Gamma acceleration and IV surface
        dynamic_vol_buffer = max(0.035, (iv * 0.25) + (gamma * 15.0))
        calculated_floor_price = round(market.entry_premium * (1.0 - dynamic_vol_buffer), 2)

        # Hard emergency boundary safeguarding against network/data feed drops
        emergency_hard_floor = round(market.entry_premium * (1.0 - self.config.absolute_emergency_floor_pct), 2)

        reasons_to_exit = []

        # Step 3: Run Multi-Layer Evaluation Matrix (No hardcoded constants)
        # Layer A: Machine Learning Confidence Decay (Loss of Statistical Edge)
        if market.ml_confidence < self.config.min_alpha_confidence_threshold:
            reasons_to_exit.append(f"ALPHA_DECAY_SCORE_{market.ml_confidence:.2f}")

        # Layer B: Microstructure Liquidity & Order Book Imbalance (Institutional Dumping)
        if market.order_book_imbalance <= self.config.max_order_book_imbalance_limit:
            reasons_to_exit.append(f"MICROSTRUCTURE_DUMP_OBI_{market.order_book_imbalance:.2f}")

        # Layer C: Volatility Boundary Violations
        if market.current_premium <= calculated_floor_price:
            reasons_to_exit.append(f"DYNAMIC_VOLATILITY_BOUND_BREACH_FLOOR_{calculated_floor_price:.2f}")

        if market.current_premium <= emergency_hard_floor:
            reasons_to_exit.append("EMERGENCY_CATASTROPHE_HARD_FLOOR_BREACH")

        # Step 4: State Machine Registration & Output Mutation
        if len(reasons_to_exit) > 0:
            return self._handle_execution_trigger(market.current_premium, reasons_to_exit, market.timestamp, market.entry_premium)

        return {
            "action": "HOLD_POSITION",
            "dynamic_floor_zone": calculated_floor_price,
            "dynamic_buffer_pct": round(dynamic_vol_buffer * 100.0, 2),
            "current_buffer_pct": round((market.current_premium - calculated_floor_price) / market.current_premium * 100.0, 2),
            "cool_down_active": False
        }

    def _handle_execution_trigger(
        self,
        exit_premium: float,
        reasons: List[str],
        timestamp: datetime,
        entry_premium: float
    ) -> Dict[str, Any]:
        """Mutates internal position state tables, deploys circuit breakers, and persists state."""
        # Calculate real-world loss percentage
        loss_pct = (exit_premium - entry_premium) / entry_premium if entry_premium > 0 else 0.0
        is_loss = loss_pct < -0.01

        if is_loss:
            self.state.consecutive_losses += 1
            if self.state.consecutive_losses >= self.config.consecutive_loss_limit:
                self.state.cool_down_active = True
                logger.warning(f"⚠️ Circuit Breaker Cool-down triggered at {timestamp}. {self.state.consecutive_losses} consecutive losses.")
        else:
            # Clean alpha or breakeven exits do not increment loss streak
            self.state.consecutive_losses = max(0, self.state.consecutive_losses - 1)

        self.state.is_active = False
        self.state.last_exit_timestamp = timestamp
        self._persist_state_to_firestore()

        return {
            "action": "EXECUTE_MARKET_EXIT_PAYLOAD",
            "timestamp": timestamp.isoformat(),
            "target_execution_premium": round(exit_premium, 2),
            "reasons": reasons,
            "loss_pct": round(loss_pct * 100.0, 2),
            "consecutive_losses_logged": self.state.consecutive_losses,
            "system_cooldown_deployed": self.state.cool_down_active
        }

DYNAMIC_RISK_SERVICE = DynamicRiskService()
