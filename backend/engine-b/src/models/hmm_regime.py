"""
InfinityAI.Pro — HMM Market Regime Detector
===========================================
Engine B | Engine-Grade: Production | Version: 1.0.0

Detects market regime using Hidden Markov Model (hmmlearn):
  State 0 → Bear / Volatile  (high vol, negative drift)
  State 1 → Sideways / Chop  (low vol, near-zero drift)
  State 2 → Bull / Trending  (low vol, positive drift)

Regime state is used as a meta-signal to:
  - Tilt ensemble weights (bull regime → more weight on momentum models)
  - Gate long/short signals (bear regime blocks BUY signals below threshold)
  - Pass to Gemini macro prompt as market context
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("InfinityAI.HMMRegime")

# Optional: hmmlearn
try:
    from hmmlearn import hmm
    HAS_HMM = True
except ImportError:
    HAS_HMM = False
    logger.warning("⚠️ hmmlearn not installed. HMMRegimeModel will use rule-based fallback.")


class HMMRegimeModel:
    """
    3-state Gaussian HMM for market regime detection.

    States are relabeled post-fit by drift sign + volatility rank:
      - Lowest vol + positive drift  → State 2 (Bull)
      - Medium characteristics       → State 1 (Sideways)
      - Highest vol or negative drift → State 0 (Bear)

    Usage:
        model = HMMRegimeModel(n_states=3)
        model.fit(close_series)
        regime = model.predict(close_series)
        current_regime = model.current_regime(close_series)
    """

    VERSION = "1.0.0"
    REGIME_LABELS = {0: "BEAR", 1: "SIDEWAYS", 2: "BULL"}

    def __init__(self, n_states: int = 3, n_iter: int = 200, random_state: int = 42):
        self.n_states = n_states
        self.n_iter = n_iter
        self.random_state = random_state
        self._model: Optional[Any] = None
        self._state_map: Dict[int, int] = {}  # raw HMM state → normalized state
        self._trained = False
        self._trained_at: Optional[datetime] = None
        self._train_length: int = 0

    def _compute_obs(self, close: pd.Series) -> np.ndarray:
        """
        Compute observation matrix for HMM:
          [log_return, rolling_volatility_5d]
        """
        log_ret = np.log(close / close.shift(1)).fillna(0)
        vol_5   = log_ret.rolling(5).std().fillna(0)
        obs = np.column_stack([log_ret.values, vol_5.values])
        return obs.astype(np.float64)

    def _relabel_states(self, close: pd.Series, raw_states: np.ndarray) -> Dict[int, int]:
        """
        Map raw HMM states (arbitrary) to canonical (0=Bear, 1=Sideways, 2=Bull)
        by ranking states on mean daily return.
        """
        log_ret = np.log(close / close.shift(1)).fillna(0).values
        state_means = {}
        for s in range(self.n_states):
            mask = raw_states == s
            state_means[s] = float(np.mean(log_ret[mask])) if mask.any() else 0.0

        # Sort by mean return ascending: lowest = Bear, middle = Sideways, highest = Bull
        sorted_states = sorted(state_means.keys(), key=lambda s: state_means[s])
        mapping = {raw: canonical for canonical, raw in enumerate(sorted_states)}
        return mapping

    def fit(self, close: pd.Series) -> "HMMRegimeModel":
        """
        Fit the HMM model on a price series.

        Args:
            close: pd.Series of daily close prices (min 60 bars recommended).

        Returns:
            self (for chaining)
        """
        if not HAS_HMM:
            logger.warning("hmmlearn not available — using rule-based regime fallback.")
            self._trained = False
            return self

        if len(close) < 30:
            logger.warning(f"Insufficient data for HMM fit: {len(close)} rows (need ≥30).")
            return self

        try:
            obs = self._compute_obs(close)
            model = hmm.GaussianHMM(
                n_components=self.n_states,
                covariance_type="full",
                n_iter=self.n_iter,
                random_state=self.random_state,
                verbose=False,
            )
            model.fit(obs)
            raw_states = model.predict(obs)
            self._model = model
            self._state_map = self._relabel_states(close, raw_states)
            self._trained = True
            self._trained_at = datetime.utcnow()
            self._train_length = len(close)
            logger.info(
                f"✅ HMM fit complete: {self.n_states} states on {len(close)} bars. "
                f"State map: {self._state_map}"
            )
        except Exception as e:
            logger.error(f"❌ HMM fit failed: {e}", exc_info=True)
            self._trained = False

        return self

    def predict(self, close: pd.Series) -> pd.Series:
        """
        Predict regime for each bar in the series.

        Returns:
            pd.Series of regime codes {0=Bear, 1=Sideways, 2=Bull}
            Falls back to rule-based ADX/return regime if HMM not trained.
        """
        if not self._trained or self._model is None:
            return self._rule_based_regime(close)

        try:
            obs = self._compute_obs(close)
            raw_states = self._model.predict(obs)
            mapped = np.array([self._state_map.get(int(s), 1) for s in raw_states])
            return pd.Series(mapped, index=close.index, name="hmm_regime")
        except Exception as e:
            logger.warning(f"HMM predict failed: {e}; using rule-based fallback.")
            return self._rule_based_regime(close)

    def _rule_based_regime(self, close: pd.Series) -> pd.Series:
        """
        Rule-based regime when HMM is unavailable.
        Uses 20-day return + 10-day realized vol to classify regime.
        """
        log_ret = np.log(close / close.shift(1)).fillna(0)
        ret_20  = close.pct_change(20, fill_method=None).fillna(0)
        rv_10   = log_ret.rolling(10).std().fillna(0)
        rv_med  = rv_10.median()

        regime = pd.Series(1, index=close.index, dtype=int)  # default: Sideways
        regime.loc[(ret_20 > 0.02) & (rv_10 < rv_med * 1.5)]  = 2  # Bull
        regime.loc[(ret_20 < -0.02) | (rv_10 > rv_med * 2.0)] = 0  # Bear
        return regime.rename("hmm_regime")

    def current_regime(self, close: pd.Series) -> Dict[str, Any]:
        """
        Return current (latest bar) regime with label and confidence.

        Returns:
            dict: {regime_code, regime_label, state_probabilities, trained_at}
        """
        regime_series = self.predict(close)
        current_code  = int(regime_series.iloc[-1])
        label         = self.REGIME_LABELS.get(current_code, "UNKNOWN")

        state_probs = {}
        if self._trained and self._model is not None:
            try:
                obs = self._compute_obs(close)
                _, posteriors = self._model.score_samples(obs)
                last_posteriors = posteriors[-1]
                # Remap to canonical state labels
                for raw_s, prob in enumerate(last_posteriors):
                    canonical = self._state_map.get(raw_s, raw_s)
                    state_probs[self.REGIME_LABELS.get(canonical, str(canonical))] = round(float(prob), 4)
            except Exception:
                pass

        return {
            "regime_code":        current_code,
            "regime_label":       label,
            "state_probabilities": state_probs,
            "trained_at":         self._trained_at.isoformat() if self._trained_at else None,
            "train_length":       self._train_length,
            "hmm_available":      HAS_HMM and self._trained,
        }

    def get_regime_tilt(self, close: pd.Series) -> Dict[str, float]:
        """
        Compute model weight tilt multipliers based on current regime.
        Used by EnsembleArbitrator to adjust base weights.

        Returns:
            Dict of {model_name: multiplier} where multiplier ∈ [0.5, 1.5]
        """
        regime_info = self.current_regime(close)
        regime = regime_info["regime_code"]

        if regime == 2:  # Bull / Trending
            return {
                "xgboost":       1.3,
                "lightgbm":      1.3,
                "catboost":      1.2,
                "extra_trees":   1.0,
                "gru":           1.4,   # momentum favours deep models in bull
                "lstm":          1.2,
                "arima":         0.8,   # statistical weaker in strong trends
                "hmm_regime":    1.0,
                "kalman_filter": 0.9,
            }
        elif regime == 0:  # Bear / Volatile
            return {
                "xgboost":       1.2,
                "lightgbm":      1.1,
                "catboost":      1.1,
                "extra_trees":   1.3,   # bagging more robust in noise
                "gru":           0.8,
                "lstm":          0.8,
                "arima":         1.2,   # statistical baseline more reliable
                "hmm_regime":    0.9,
                "kalman_filter": 1.3,   # Kalman handles mean-reversion
            }
        else:  # Sideways
            return {
                "xgboost":       1.0,
                "lightgbm":      1.0,
                "catboost":      1.0,
                "extra_trees":   1.0,
                "gru":           1.0,
                "lstm":          1.0,
                "arima":         1.1,
                "hmm_regime":    1.0,
                "kalman_filter": 1.1,
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        return {
            "model_type":    "HiddenMarkovModel",
            "n_states":      self.n_states,
            "version":       self.VERSION,
            "trained":       self._trained,
            "trained_at":    self._trained_at.isoformat() if self._trained_at else None,
            "train_length":  self._train_length,
            "hmm_available": HAS_HMM,
            "state_labels":  self.REGIME_LABELS,
            "state_map":     self._state_map,
        }


# ── Singleton instance ────────────────────────────────────────────────────────
hmm_regime_model = HMMRegimeModel(n_states=3)
