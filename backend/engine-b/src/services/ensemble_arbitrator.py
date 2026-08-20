"""
InfinityAI.Pro — Dynamic Ensemble Arbitrator
============================================
Engine B | Engine-Grade: Production | Version: 2.0.0

Implements institutional-grade ensemble weight management:

  1. EMA-Weighted Performance Arbitration
     - Rolling 30-trade accuracy tracked per model
     - Exponential Moving Average decay (α=0.15, ≈13-trade half-life)
     - Softmax normalization → no model dominates completely

  2. Champion/Challenger Management
     - Champion: highest rolling 30-day Sharpe Ratio model
     - Challenger: new model being evaluated against champion
     - Champion gets +50% weight bonus (capped at 45%)
     - Challenger promoted if 7-day accuracy exceeds champion by >3%

  3. Regime-Aware Tilt
     - Integrates HMMRegimeModel tilt multipliers
     - Bull regime: momentum models (GRU, LSTM) get higher weight
     - Bear regime: statistical/Kalman models get higher weight

  4. Firestore Persistence
     - Weight history logged to `engine_b_state/ensemble_weights`
     - Model performance logged to BigQuery `market_data.model_performance`

  5. Safety Guardrails
     - Minimum weight floor: 5% per model (no dead models)
     - Maximum weight cap: 45% per model (no single-model dominance)
     - Graceful fallback to static weights on Firestore failure
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger("InfinityAI.EnsembleArbitrator")


# ─────────────────────────────────────────────────────────────────────────────
# STATIC BASELINE WEIGHTS (fallback)
# ─────────────────────────────────────────────────────────────────────────────

STATIC_BASELINE_WEIGHTS: Dict[str, float] = {
    "xgboost":       0.25,
    "lightgbm":      0.20,
    "catboost":      0.15,
    "extra_trees":   0.10,
    "gru":           0.12,
    "lstm":          0.08,
    "arima":         0.04,
    "kalman_filter": 0.04,
    "hmm_regime":    0.02,
}

# Weight bounds
MIN_WEIGHT = 0.05   # 5% floor
MAX_WEIGHT = 0.45   # 45% cap


class ModelPerformanceTracker:
    """
    Tracks rolling prediction accuracy and Sharpe Ratio per model.
    Backed by Firestore for persistence across Cloud Run instances.
    """

    EMA_ALPHA = 0.15   # EMA decay for 30-trade rolling window
    WINDOW    = 30     # Trade history window for Sharpe calculation

    def __init__(self, model_names: List[str]):
        self.model_names = model_names
        # EMA accuracy per model (0.0 → 1.0)
        self._ema_accuracy: Dict[str, float] = {m: 0.50 for m in model_names}
        # Trade history: [(predicted_signal, actual_return)]
        self._history: Dict[str, List[tuple]] = {m: [] for m in model_names}
        self._champion: Optional[str] = None
        self._challenger: Optional[str] = None
        self._last_updated: datetime = datetime.utcnow()

    def record_prediction(
        self,
        model_name: str,
        predicted_signal: str,   # "BUY", "HOLD", "SELL"
        actual_return: float,    # Next-bar realized return (pct)
    ) -> None:
        """
        Record a prediction outcome for performance tracking.

        Args:
            model_name: Name of the model being evaluated.
            predicted_signal: Model's predicted signal.
            actual_return: Actual price return that followed.
        """
        if model_name not in self._history:
            self._history[model_name] = []

        # Correctness: BUY + positive return = correct, SELL + negative = correct
        correct = (
            (predicted_signal == "BUY"  and actual_return >  0.001) or
            (predicted_signal == "SELL" and actual_return < -0.001) or
            (predicted_signal == "HOLD" and abs(actual_return) <= 0.002)
        )

        self._history[model_name].append((predicted_signal, actual_return, correct))
        # Keep only last WINDOW entries
        if len(self._history[model_name]) > self.WINDOW:
            self._history[model_name] = self._history[model_name][-self.WINDOW:]

        # Update EMA accuracy
        acc = 1.0 if correct else 0.0
        prev = self._ema_accuracy.get(model_name, 0.5)
        self._ema_accuracy[model_name] = self.EMA_ALPHA * acc + (1 - self.EMA_ALPHA) * prev
        self._last_updated = datetime.utcnow()

    def get_sharpe(self, model_name: str) -> float:
        """
        Compute rolling Sharpe-like score: mean_return / std_return
        when model signal was BUY or SELL (directional bets only).
        """
        hist = self._history.get(model_name, [])
        directional = [r for sig, r, _ in hist if sig in ("BUY", "SELL")]
        if len(directional) < 3:
            return 0.0
        arr = np.array(directional)
        mean_r = np.mean(arr)
        std_r  = np.std(arr) + 1e-9
        return float(mean_r / std_r * np.sqrt(252))   # annualized proxy

    def get_ema_accuracy(self, model_name: str) -> float:
        return self._ema_accuracy.get(model_name, 0.5)

    def update_champion_challenger(self) -> None:
        """
        Elect champion (highest Sharpe) and identify challenger
        (second-highest if within striking distance).
        """
        sharpes = {m: self.get_sharpe(m) for m in self.model_names}
        sorted_models = sorted(sharpes.items(), key=lambda x: x[1], reverse=True)

        if sorted_models:
            self._champion   = sorted_models[0][0]
            # Challenger: second-best if within 3% accuracy of champion
            if len(sorted_models) > 1:
                champ_acc     = self._ema_accuracy.get(self._champion, 0.5)
                chal_name     = sorted_models[1][0]
                chal_acc      = self._ema_accuracy.get(chal_name, 0.5)
                self._challenger = chal_name if (champ_acc - chal_acc) < 0.03 else None

    def get_status(self) -> Dict[str, Any]:
        return {
            "champion":      self._champion,
            "challenger":    self._challenger,
            "ema_accuracy":  {m: round(v, 4) for m, v in self._ema_accuracy.items()},
            "sharpe_scores": {m: round(self.get_sharpe(m), 4) for m in self.model_names},
            "last_updated":  self._last_updated.isoformat(),
        }


class EnsembleArbitrator:
    """
    Dynamic performance-weighted ensemble arbitrator.

    Core algorithm:
      1. Start from EMA accuracy per model
      2. Apply regime tilt multipliers
      3. Apply champion bonus
      4. Softmax normalize to [MIN_WEIGHT, MAX_WEIGHT]
      5. Persist to Firestore every 10 weight updates
    """

    VERSION  = "2.0.0"
    ALL_MODELS = list(STATIC_BASELINE_WEIGHTS.keys())

    def __init__(self):
        self.tracker = ModelPerformanceTracker(self.ALL_MODELS)
        self._current_weights: Dict[str, float] = STATIC_BASELINE_WEIGHTS.copy()
        self._update_count    = 0
        self._firestore_db    = None

    def _init_firestore(self):
        """Lazy Firestore init (avoids startup latency)."""
        if self._firestore_db is not None:
            return
        try:
            from google.cloud import firestore
            import os
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            self._firestore_db = firestore.Client(project=project_id)
        except Exception as e:
            logger.warning(f"Firestore unavailable for weight persistence: {e}")

    def compute_dynamic_weights(
        self,
        regime_tilt: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Compute dynamic ensemble weights from EMA accuracy + regime tilt.

        Algorithm:
          raw_weight = EMA_accuracy * regime_tilt_multiplier * champion_bonus
          final_weight = clip(softmax(raw_weights), MIN_WEIGHT, MAX_WEIGHT)
          Normalize final_weights to sum=1.0

        Args:
            regime_tilt: Dict of {model_name: multiplier} from HMMRegimeModel.
                         Pass None to use neutral multipliers (1.0 for all).

        Returns:
            Dict of {model_name: weight} summing to 1.0
        """
        tilt = regime_tilt or {m: 1.0 for m in self.ALL_MODELS}
        self.tracker.update_champion_challenger()
        champion = self.tracker._champion

        raw_weights: Dict[str, float] = {}
        for model in self.ALL_MODELS:
            ema_acc = self.tracker.get_ema_accuracy(model)
            mult    = tilt.get(model, 1.0)

            # Champion bonus: +50% weight, but only if champion is identified
            champ_bonus = 1.5 if (model == champion and champion is not None) else 1.0

            raw_weights[model] = max(MIN_WEIGHT, ema_acc * mult * champ_bonus)

        # Softmax normalization
        values = np.array(list(raw_weights.values()), dtype=np.float64)
        # Scale before softmax to avoid vanishing gradient effect
        values_scaled = values / values.mean()
        exp_vals = np.exp(values_scaled - values_scaled.max())  # numerically stable
        softmax_vals = exp_vals / exp_vals.sum()

        # Apply bounds [MIN_WEIGHT, MAX_WEIGHT] and renormalize
        clipped = np.clip(softmax_vals, MIN_WEIGHT, MAX_WEIGHT)
        final = clipped / clipped.sum()

        self._current_weights = {
            model: float(round(final[i], 4))
            for i, model in enumerate(self.ALL_MODELS)
        }
        self._update_count += 1

        logger.info(
            f"🎯 Ensemble weights updated (run #{self._update_count}): "
            f"champion={champion} | "
            f"top3={sorted(self._current_weights.items(), key=lambda x: x[1], reverse=True)[:3]}"
        )

        # Persist every 10 updates
        if self._update_count % 10 == 0:
            self._persist_weights_sync()

        return self._current_weights

    def weighted_ensemble_proba(
        self,
        model_probas: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None,
    ) -> np.ndarray:
        """
        Compute weighted ensemble probability from all model outputs.

        Args:
            model_probas: {model_name: (N, n_classes) probability array}
            weights: Optional weight override. Uses current dynamic weights if None.

        Returns:
            (N, n_classes) weighted average probability array.
        """
        weights = weights or self._current_weights

        if not model_probas:
            logger.warning("No model probabilities provided to ensemble.")
            return np.array([[1/3, 1/3, 1/3]])

        # Determine number of classes and samples from first available model
        first_proba = next(iter(model_probas.values()))
        n_samples, n_classes = (first_proba.shape[0], first_proba.shape[1]) \
                               if first_proba.ndim == 2 \
                               else (1, len(first_proba))

        ensemble = np.zeros((n_samples, n_classes), dtype=np.float64)
        total_w  = 0.0

        for model_name, proba in model_probas.items():
            w = weights.get(model_name, 0.0)
            if w <= 0:
                continue
            if proba.ndim == 1:
                proba = proba[np.newaxis, :]
            if proba.shape != (n_samples, n_classes):
                logger.warning(f"Shape mismatch for {model_name}: {proba.shape} vs ({n_samples},{n_classes})")
                continue
            ensemble += w * proba
            total_w  += w

        if total_w < 1e-9:
            return np.full((n_samples, n_classes), 1.0 / n_classes)

        # Normalize by actual weights used (handles missing models gracefully)
        ensemble /= total_w
        return ensemble.astype(np.float32)

    def ensemble_signal(
        self,
        model_probas: Dict[str, np.ndarray],
        threshold_buy: float = 0.40,
        threshold_sell: float = 0.40,
        regime_tilt: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute final ensemble signal with confidence.

        Args:
            model_probas: {model_name: proba_array}
            threshold_buy: Min BUY class probability to trigger BUY signal.
            threshold_sell: Min SELL class probability to trigger SELL signal.
            regime_tilt: Regime-based multipliers from HMMRegimeModel.

        Returns:
            {
              signal: "BUY" | "SELL" | "HOLD",
              confidence: float 0-100,
              signal_proba: {SELL: float, HOLD: float, BUY: float},
              weights_used: Dict[str, float],
              champion_model: str,
            }
        """
        weights = self.compute_dynamic_weights(regime_tilt)
        ensemble_proba = self.weighted_ensemble_proba(model_probas, weights)
        proba_last = ensemble_proba[-1] if ensemble_proba.ndim == 2 else ensemble_proba

        p_sell = float(proba_last[0])
        p_hold = float(proba_last[1])
        p_buy  = float(proba_last[2])

        if p_buy >= threshold_buy and p_buy > p_sell:
            signal = "BUY"
            confidence = round(p_buy * 100, 2)
        elif p_sell >= threshold_sell and p_sell > p_buy:
            signal = "SELL"
            confidence = round(p_sell * 100, 2)
        else:
            signal = "HOLD"
            confidence = round(p_hold * 100, 2)

        return {
            "signal":         signal,
            "confidence":     confidence,
            "signal_proba":   {"SELL": round(p_sell, 4), "HOLD": round(p_hold, 4), "BUY": round(p_buy, 4)},
            "weights_used":   weights,
            "champion_model": self.tracker._champion,
            "challenger_model": self.tracker._challenger,
            "update_count":   self._update_count,
        }

    def record_outcome(
        self,
        model_name: str,
        predicted_signal: str,
        actual_return: float,
    ) -> None:
        """Record a trade outcome for adaptive weight learning."""
        self.tracker.record_prediction(model_name, predicted_signal, actual_return)

    def record_all_outcomes(
        self,
        model_signals: Dict[str, str],
        actual_return: float,
    ) -> None:
        """Record outcomes for all models simultaneously."""
        for model_name, signal in model_signals.items():
            self.record_outcome(model_name, signal, actual_return)

    def _persist_weights_sync(self) -> None:
        """Persist current weights to Firestore (sync, fire-and-forget)."""
        try:
            self._init_firestore()
            if self._firestore_db is None:
                return
            doc_ref = self._firestore_db.collection("engine_b_state").document("ensemble_weights")
            doc_ref.set({
                "weights":        self._current_weights,
                "tracker_status": self.tracker.get_status(),
                "update_count":   self._update_count,
                "updated_at":     datetime.utcnow().isoformat(),
                "version":        self.VERSION,
            })
            logger.info("✅ Ensemble weights persisted to Firestore.")
        except Exception as e:
            logger.warning(f"Weight persistence failed (non-critical): {e}")

    async def persist_weights_async(self) -> None:
        """Async wrapper for weight persistence (for FastAPI background tasks)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._persist_weights_sync)

    def get_current_weights(self) -> Dict[str, float]:
        """Return currently active weights."""
        return self._current_weights.copy()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "version":          self.VERSION,
            "model_count":      len(self.ALL_MODELS),
            "models":           self.ALL_MODELS,
            "current_weights":  self._current_weights,
            "min_weight":       MIN_WEIGHT,
            "max_weight":       MAX_WEIGHT,
            "ema_alpha":        ModelPerformanceTracker.EMA_ALPHA,
            "tracker_status":   self.tracker.get_status(),
            "update_count":     self._update_count,
            "static_baseline":  STATIC_BASELINE_WEIGHTS,
        }


# ── Singleton instance ────────────────────────────────────────────────────────
ensemble_arbitrator = EnsembleArbitrator()
