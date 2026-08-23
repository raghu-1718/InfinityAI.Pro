"""
InfinityAI.Pro — Institutional ML Model Manager (v3.0)
=======================================================
Engine B | Engine-Grade: Production | Version: 3.0.0

PURPOSE:
  - Loads all 9 trained model artifacts from GCS Model Vault
  - Routes prediction requests to the correct model
  - Coordinates with EnsembleArbitrator for dynamic weighting
  - Provides ensemble inference API for main.py signal endpoints
  - Integrates DQN agent in dual mode:
      A. Position Sizing Adjuster: scales lot size by DQN Q-value confidence
      B. Primary Signal: DQN generates autonomous BUY/HOLD/SELL (when enabled)

NOTE: This is the PRODUCTION inference path — NOT for offline training.
      For training, use: training/train_ensemble.py
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
import joblib

logger = logging.getLogger("InfinityAI.MLModelManager")


# ─────────────────────────────────────────────────────────────────────────────
# MODEL REGISTRY — GCS paths per model per symbol
# ─────────────────────────────────────────────────────────────────────────────

GCS_BUCKET   = "infinity-ai-models-vault"
GCS_PREFIX   = "{symbol}/latest"

MODEL_FILE_MAP = {
    "xgboost":       "{symbol}/latest/xgboost_{symbol}.json",
    "lightgbm":      "{symbol}/latest/lightgbm_{symbol}.pkl",
    "catboost":      "{symbol}/latest/catboost_{symbol}.cbm",
    "extra_trees":   "{symbol}/latest/extra_trees_{symbol}.pkl",
    "scaler":        "{symbol}/latest/scaler.pkl",
    "feature_cols":  "{symbol}/latest/feature_cols_{symbol}.json",
    "gru":           "{symbol}/latest/gru_{symbol}.h5",    # optional TF
    "lstm":          "{symbol}/latest/lstm_{symbol}.h5",   # optional TF
}


class MLModelManager:
    """
    Centralized production ML model manager for Engine B.

    Loads:
      - 4 tabular classifiers (XGBoost, LightGBM, CatBoost, ExtraTrees)
      - 3 statistical/regime models (ARIMA, HMM, Kalman) — loaded on demand
      - 2 deep learning models (GRU, LSTM) — optional TF
      - DQN Agent in dual mode

    Prediction flow:
      1. prepare_features(df) → feature array
      2. predict_all(X) → Dict[model_name, proba_array]
      3. ensemble_arbitrator.ensemble_signal(probas) → final signal
      4. dqn_position_adjuster(signal, state) → adjusted lot size
    """

    VERSION = "3.0.0"

    def __init__(self, model_dir: Optional[str] = None, symbol: str = "NIFTY"):
        if model_dir:
            self.model_dir = model_dir
        else:
            candidates = [
                "/opt/infinityai/engine-b/models_store",
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models_store")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models_store")),
                os.path.abspath("./models_store"),
                "/app/models",
            ]
            self.model_dir = next((c for c in candidates if os.path.exists(c)), candidates[0])

        self.symbol    = symbol
        self.models: Dict[str, Any] = {}
        self.scaler: Optional[Any]  = None
        self.feature_cols: List[str] = []
        self.metadata: Dict[str, Dict] = {}
        self._dqn_agent    = None
        self._dqn_mode     = "position_sizing"   # "position_sizing" | "primary_signal" | "both"
        self._loaded_at: Optional[datetime] = None
        os.makedirs(self.model_dir, exist_ok=True)
        # Eager load initial symbol
        self.load_models(symbol)

    # ── Model Loading ─────────────────────────────────────────────────────

    def load_models(self, symbol: Optional[str] = None) -> Dict[str, bool]:
        """
        Load all model artifacts from local model_dir.
        Falls back to GCS download if local files missing.

        Returns:
            Dict {model_name: loaded_successfully}
        """
        symbol = symbol or self.symbol
        status: Dict[str, bool] = {}

        # ── Scaler (required) ──────────────────────────────────────────────
        scaler_path = os.path.join(self.model_dir, f"scaler_{symbol}.pkl")
        if not os.path.exists(scaler_path):
            scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        if os.path.exists(scaler_path):
            try:
                self.scaler = joblib.load(scaler_path)
                status["scaler"] = True
                logger.info(f"✅ Scaler loaded from {scaler_path}")
            except Exception as e:
                logger.error(f"Scaler load failed: {e}")
                status["scaler"] = False
        else:
            logger.warning("⚠️ Scaler file not found — using identity transform.")
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            status["scaler"] = False

        # ── Feature columns ────────────────────────────────────────────────
        import json
        feat_path = os.path.join(self.model_dir, f"feature_cols_{symbol}.json")
        if os.path.exists(feat_path):
            with open(feat_path) as f:
                self.feature_cols = json.load(f)
            logger.info(f"✅ Feature cols loaded: {len(self.feature_cols)} features")

        # ── XGBoost ───────────────────────────────────────────────────────
        xgb_path = os.path.join(self.model_dir, f"xgboost_{symbol}.json")
        if not os.path.exists(xgb_path):
            xgb_path = os.path.join(self.model_dir, "xgboost_model.json")
        status["xgboost"] = self._load_xgboost(xgb_path)

        # ── LightGBM ──────────────────────────────────────────────────────
        for lgb_name in [f"lightgbm_{symbol}.pkl", "lightgbm_model.pkl"]:
            lgb_path = os.path.join(self.model_dir, lgb_name)
            if os.path.exists(lgb_path):
                status["lightgbm"] = self._load_joblib("lightgbm", lgb_path)
                break

        # ── CatBoost ──────────────────────────────────────────────────────
        for cat_name in [f"catboost_{symbol}.cbm", "catboost_model.cbm"]:
            cat_path = os.path.join(self.model_dir, cat_name)
            if os.path.exists(cat_path):
                status["catboost"] = self._load_catboost(cat_path)
                break

        # ── ExtraTrees ────────────────────────────────────────────────────
        for et_name in [f"extra_trees_{symbol}.pkl", "extra_trees_model.pkl"]:
            et_path = os.path.join(self.model_dir, et_name)
            if os.path.exists(et_path):
                status["extra_trees"] = self._load_joblib("extra_trees", et_path)
                break

        # ── GRU (optional TF) ─────────────────────────────────────────────
        gru_path = os.path.join(self.model_dir, f"gru_{symbol}.h5")
        if os.path.exists(gru_path):
            status["gru"] = self._load_keras("gru", gru_path)

        # ── LSTM (optional TF) ────────────────────────────────────────────
        lstm_path = os.path.join(self.model_dir, f"lstm_{symbol}.h5")
        if os.path.exists(lstm_path):
            status["lstm"] = self._load_keras("lstm", lstm_path)

        # ── HMM Regime (lazy-initialize) ──────────────────────────────────
        try:
            from models.hmm_regime import HMMRegimeModel
            self.models["hmm_regime"] = HMMRegimeModel(n_states=3)
            status["hmm_regime"] = True
        except Exception as e:
            logger.warning(f"HMM load: {e}")
            status["hmm_regime"] = False

        # ── Kalman Filter (lazy-initialize) ───────────────────────────────
        try:
            from models.kalman_filter import KalmanTrendFilter
            self.models["kalman_filter"] = KalmanTrendFilter()
            status["kalman_filter"] = True
        except Exception as e:
            logger.warning(f"Kalman load: {e}")
            status["kalman_filter"] = False

        # ── DQN Agent ─────────────────────────────────────────────────────
        self._load_dqn(symbol)

        self._loaded_at = datetime.utcnow()
        loaded = sum(1 for v in status.values() if v)
        logger.info(
            f"✅ MLModelManager: {loaded}/{len(status)} models loaded "
            f"for {symbol} at {self._loaded_at.isoformat()}"
        )
        return status

    def _load_xgboost(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        try:
            import xgboost as xgb_lib
            model = xgb_lib.XGBClassifier()
            model.load_model(path)
            self.models["xgboost"] = model
            logger.info(f"✅ XGBoost loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"XGBoost load failed: {e}")
            return False

    def _load_joblib(self, name: str, path: str) -> bool:
        try:
            self.models[name] = joblib.load(path)
            logger.info(f"✅ {name} loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"{name} load failed: {e}")
            return False

    def _load_catboost(self, path: str) -> bool:
        try:
            from catboost import CatBoostClassifier
            model = CatBoostClassifier()
            model.load_model(path)
            self.models["catboost"] = model
            logger.info(f"✅ CatBoost loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"CatBoost load failed: {e}")
            return False

    def _load_keras(self, name: str, path: str) -> bool:
        try:
            import tensorflow as tf
            self.models[name] = tf.keras.models.load_model(path)
            logger.info(f"✅ {name} (Keras) loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"{name} Keras load failed: {e}")
            return False

    def _load_dqn(self, symbol: str) -> None:
        """Load DQN agent from models_store."""
        try:
            from models.dqn_agent import DQNTradingAgent
            dqn_path = os.path.join(self.model_dir, f"dqn_{symbol}.pkl")
            if os.path.exists(dqn_path):
                self._dqn_agent = joblib.load(dqn_path)
                logger.info(f"✅ DQN agent loaded from {dqn_path}")
            else:
                # Create fresh agent (will use random policy until trained)
                self._dqn_agent = DQNTradingAgent(state_size=65, action_size=3)
                logger.info("🆕 DQN agent created (untrained — will refine in signal generation)")
        except Exception as e:
            logger.warning(f"DQN agent load: {e}")

    # ── Inference ─────────────────────────────────────────────────────────

    def predict_all_proba(
        self,
        X: np.ndarray,
        close_series=None,
        symbol: Optional[str] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Run all loaded models and return probability arrays.

        Args:
            X: (N, n_features) feature array (already scaled by caller OR auto-scaled here)
            close_series: pd.Series for HMM/Kalman models
            symbol: Target symbol to ensure correct models are loaded

        Returns:
            Dict {model_name: (N, 3) probability array}
        """
        if symbol and (symbol != self.symbol or not any(self.models.get(k) for k in ["xgboost", "lightgbm", "catboost", "extra_trees"])):
            self.load_models(symbol)

        # Auto-scale if scaler is fitted
        try:
            X_scaled = self.scaler.transform(X)
        except Exception:
            X_scaled = X

        probas: Dict[str, np.ndarray] = {}

        # Tabular classifiers
        for name in ["xgboost", "lightgbm", "catboost", "extra_trees"]:
            model = self.models.get(name)
            if model is None:
                continue
            try:
                # Handle feature dimension mismatch (e.g. 18 vs 20)
                n_feats = getattr(model, 'n_features_', getattr(model, 'n_features_in_', X_scaled.shape[1]))
                if X_scaled.shape[1] > n_feats:
                    X_input = X_scaled[:, :n_feats]
                elif X_scaled.shape[1] < n_feats:
                    X_input = np.pad(X_scaled, ((0, 0), (0, n_feats - X_scaled.shape[1])), mode='constant')
                else:
                    X_input = X_scaled
                proba = model.predict_proba(X_input)
                if proba.shape[1] == 3:
                    probas[name] = proba.astype(np.float32)
            except Exception as e:
                logger.warning(f"predict_proba failed for {name}: {e}")

        # Sequence models (GRU/LSTM) — single sample from last X rows
        for name in ["gru", "lstm"]:
            model = self.models.get(name)
            if model is None:
                continue
            try:
                seq_len = 30 if name == "gru" else 60
                if len(X_scaled) >= seq_len:
                    seq_input = X_scaled[-seq_len:][np.newaxis, ...]   # (1, seq_len, n_features)
                    proba = model.predict(seq_input, verbose=0)         # (1, 3)
                    # Broadcast to match N samples
                    probas[name] = np.tile(proba, (len(X_scaled), 1)).astype(np.float32)
            except Exception as e:
                logger.warning(f"Sequence model {name} failed: {e}")

        # Regime/statistical models — produce directional probability
        if close_series is not None:
            probas.update(self._predict_regime_models(close_series, len(X_scaled)))

        return probas

    def _predict_regime_models(
        self,
        close_series,
        n_samples: int,
    ) -> Dict[str, np.ndarray]:
        """Convert regime/trend models to probability arrays."""
        probas: Dict[str, np.ndarray] = {}

        # HMM — current regime maps to directional probability
        hmm_model = self.models.get("hmm_regime")
        if hmm_model is not None:
            try:
                regime_result = hmm_model.current_regime(close_series)
                regime_code   = regime_result.get("regime_code", 1)
                # Map regime to proba: Bear→SELL, Sideways→HOLD, Bull→BUY
                proba = np.zeros((n_samples, 3), dtype=np.float32)
                if regime_code == 0:   # Bear → favor SELL
                    proba[:] = [0.55, 0.30, 0.15]
                elif regime_code == 2: # Bull → favor BUY
                    proba[:] = [0.15, 0.30, 0.55]
                else:                  # Sideways → HOLD
                    proba[:] = [0.20, 0.60, 0.20]
                probas["hmm_regime"] = proba
            except Exception as e:
                logger.warning(f"HMM predict failed: {e}")

        # Kalman — velocity direction → directional probability
        kalman_model = self.models.get("kalman_filter")
        if kalman_model is not None:
            try:
                next_pred = kalman_model.predict_next(close_series)
                vel       = next_pred.get("predicted_velocity", 0.0)
                proba     = np.zeros((n_samples, 3), dtype=np.float32)
                if vel > 0:
                    strength = min(abs(vel) / close_series.iloc[-1] * 1000, 1.0)
                    proba[:] = [0.15, 0.35, 0.50 + strength * 0.15]
                elif vel < 0:
                    strength = min(abs(vel) / close_series.iloc[-1] * 1000, 1.0)
                    proba[:] = [0.50 + strength * 0.15, 0.35, 0.15]
                else:
                    proba[:] = [0.20, 0.60, 0.20]
                # Re-normalize
                proba = proba / proba.sum(axis=1, keepdims=True)
                probas["kalman_filter"] = proba
            except Exception as e:
                logger.warning(f"Kalman predict failed: {e}")

        return probas

    # ── DQN Integration (Dual Mode) ────────────────────────────────────────

    def get_dqn_position_sizing(
        self,
        state: np.ndarray,
        base_lots: int = 1,
    ) -> Dict[str, Any]:
        """
        Mode A: DQN as position sizing adjuster.
        Uses DQN Q-values to scale lot size:
          - High BUY Q-value confidence → 1.5x lots
          - Low confidence or HOLD → 0.5x lots
          - SELL signal → 0x (do not trade)
        """
        if self._dqn_agent is None:
            return {"adjusted_lots": base_lots, "dqn_mode": "disabled", "q_values": None}

        try:
            q_values  = self._dqn_agent.get_q_values(state)
            max_q     = float(q_values.max())
            best_action = int(q_values.argmax())

            # Confidence: normalized Q-value spread
            q_spread  = float(q_values.max() - q_values.min())
            confidence = min(1.0, q_spread / (abs(max_q) + 1e-9))

            # Scale lots by confidence
            if best_action == 2:  # BUY
                multiplier = 1.0 + confidence * 0.5  # 1.0x to 1.5x
            elif best_action == 0:  # SELL (short signal)
                multiplier = 1.0 + confidence * 0.3
            else:  # HOLD — reduce exposure
                multiplier = 0.5

            adjusted_lots = max(1, round(base_lots * multiplier))
            return {
                "adjusted_lots":  adjusted_lots,
                "multiplier":     round(multiplier, 3),
                "dqn_action":     {0: "SELL", 1: "HOLD", 2: "BUY"}.get(best_action, "HOLD"),
                "dqn_confidence": round(confidence, 4),
                "q_values":       {k: round(float(v), 4) for k, v in zip(["SELL", "HOLD", "BUY"], q_values)},
                "dqn_mode":       "position_sizing",
            }
        except Exception as e:
            logger.warning(f"DQN position sizing error: {e}")
            return {"adjusted_lots": base_lots, "dqn_mode": "error"}

    def get_dqn_primary_signal(self, state: np.ndarray) -> Dict[str, Any]:
        """
        Mode B: DQN as primary autonomous trading signal.
        Returns direct BUY/HOLD/SELL based on DQN policy (greedy).
        """
        if self._dqn_agent is None:
            return {"signal": "HOLD", "dqn_mode": "disabled"}

        try:
            action    = int(self._dqn_agent.act(state, training=False))
            q_values  = self._dqn_agent.get_q_values(state)
            confidence = float(q_values[action] / (np.abs(q_values).mean() + 1e-9))
            return {
                "signal":         {0: "SELL", 1: "HOLD", 2: "BUY"}.get(action, "HOLD"),
                "confidence":     round(min(100.0, max(50.0, 50.0 + confidence * 25)), 2),
                "q_values":       {k: round(float(v), 4) for k, v in zip(["SELL", "HOLD", "BUY"], q_values)},
                "dqn_mode":       "primary_signal",
            }
        except Exception as e:
            logger.warning(f"DQN primary signal error: {e}")
            return {"signal": "HOLD", "dqn_mode": "error"}

    def get_combined_dqn_signal(self, state: np.ndarray, base_lots: int = 1) -> Dict[str, Any]:
        """
        Mode C (BOTH): Combines primary signal + position sizing in one call.
        Returns both DQN primary signal AND adjusted lot sizing.
        """
        primary = self.get_dqn_primary_signal(state)
        sizing  = self.get_dqn_position_sizing(state, base_lots)
        return {
            "dqn_primary_signal": primary.get("signal", "HOLD"),
            "dqn_confidence":     primary.get("confidence", 50.0),
            "dqn_adjusted_lots":  sizing.get("adjusted_lots", base_lots),
            "dqn_lot_multiplier": sizing.get("multiplier", 1.0),
            "q_values":           primary.get("q_values", {}),
            "dqn_mode":           "both",
        }

    # ── Utilities ─────────────────────────────────────────────────────────

    def reload_from_gcs(self, symbol: str) -> bool:
        """Download latest model artifacts from GCS and reload."""
        try:
            from google.cloud import storage as gcs_lib
            client = gcs_lib.Client()
            bucket = client.bucket(GCS_BUCKET)
            prefix = f"{symbol}/latest/"

            blobs = list(bucket.list_blobs(prefix=prefix))
            if not blobs:
                logger.warning(f"No artifacts found in gs://{GCS_BUCKET}/{prefix}")
                return False

            for blob in blobs:
                local_path = os.path.join(self.model_dir, os.path.basename(blob.name))
                blob.download_to_filename(local_path)
                logger.info(f"📥 Downloaded: gs://{GCS_BUCKET}/{blob.name} → {local_path}")

            self.load_models(symbol)
            return True
        except Exception as e:
            logger.error(f"GCS reload failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "version":         self.VERSION,
            "symbol":          self.symbol,
            "model_dir":       self.model_dir,
            "loaded_at":       self._loaded_at.isoformat() if self._loaded_at else None,
            "loaded_models":   list(self.models.keys()),
            "feature_count":   len(self.feature_cols),
            "scaler_fitted":   (self.scaler is not None and hasattr(self.scaler, "mean_")),
            "dqn_mode":        self._dqn_mode,
            "dqn_available":   self._dqn_agent is not None,
            "gcs_bucket":      GCS_BUCKET,
        }


# ── Singleton instance ────────────────────────────────────────────────────────
model_manager = MLModelManager()
