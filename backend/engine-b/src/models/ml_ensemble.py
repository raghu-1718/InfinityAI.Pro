"""
InfinityAI.Pro — Institutional Tri-Model MLOps Ensemble
=========================================================
Coordinating CatBoost, LightGBM, XGBoost, and Random Forest models
with Regime-Adaptive Mixture of Experts (MoE) weighting and ONNX acceleration.
"""

import os
import joblib
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

try:
    from .regime_adaptive_moe import RegimeAdaptiveMoE
    from .cpcv_evaluator import CombinatorialPurgedCV
except (ImportError, ValueError):
    from src.models.regime_adaptive_moe import RegimeAdaptiveMoE
    from src.models.cpcv_evaluator import CombinatorialPurgedCV

logger = logging.getLogger("InfinityAI.MLEnsemble")

class TriModelMLEnsemble:
    """Institutional Tri-Model Ensemble with Regime-Conditioned MoE"""

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = models_dir or os.getenv("MODELS_DIR", "/tmp/models")
        self.models: Dict[str, Any] = {}
        self.scaler = None
        self.is_loaded = False
        self.moe_router = RegimeAdaptiveMoE()

    def set_models(
        self,
        xgboost_model: Any,
        lightgbm_model: Any,
        catboost_model: Optional[Any] = None,
        random_forest_model: Optional[Any] = None,
        scaler: Optional[Any] = None
    ):
        """Injects model instances directly."""
        self.models = {
            "xgboost": xgboost_model,
            "lightgbm": lightgbm_model,
            "catboost": catboost_model,
            "random_forest": random_forest_model
        }
        self.scaler = scaler
        self.is_loaded = True

    def load_models_from_disk(self, directory: Optional[str] = None) -> bool:
        """Loads serialized model artifacts from disk."""
        path = directory or self.models_dir
        try:
            lgb_path = os.path.join(path, "lightgbm_model.pkl")
            rf_path = os.path.join(path, "random_forest_model.pkl")
            scaler_path = os.path.join(path, "scaler.pkl")
            xgb_path = os.path.join(path, "xgboost_model.json")
            cat_path = os.path.join(path, "catboost_model.cbm")

            if os.path.exists(lgb_path):
                self.models["lightgbm"] = joblib.load(lgb_path)
            if os.path.exists(rf_path):
                self.models["random_forest"] = joblib.load(rf_path)
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)

            if os.path.exists(xgb_path):
                import xgboost as xgb
                m = xgb.XGBClassifier()
                m.load_model(xgb_path)
                self.models["xgboost"] = m

            if os.path.exists(cat_path):
                try:
                    from catboost import CatBoostClassifier
                    cb = CatBoostClassifier()
                    cb.load_model(cat_path)
                    self.models["catboost"] = cb
                except ImportError:
                    pass

            self.is_loaded = any(v is not None for v in self.models.values())
            logger.info(f"Loaded ensemble models from {path}. Status: {self.is_loaded}")
            return self.is_loaded
        except Exception as e:
            logger.error(f"Error loading models from {path}: {e}")
            return False

    def predict_probabilities(
        self,
        X: np.ndarray,
        adx: float = 25.0,
        india_vix: float = 15.0
    ) -> Dict[str, Any]:
        """
        Executes regime-conditioned ensemble inference across available models.
        Returns blended multi-class probabilities [P(SELL), P(HOLD), P(BUY)].
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        X_scaled = self.scaler.transform(X) if self.scaler is not None else X

        # 1. Determine dynamic MoE weights conditioned on ADX and India VIX
        weights, regime = self.moe_router.determine_regime_weights(adx=adx, india_vix=india_vix)

        individual_probas = {}
        blended_proba = np.zeros((len(X), 3))
        active_weight_sum = 0.0

        for name, model in self.models.items():
            if model is None:
                continue
            w = weights.get(name, 0.0)
            try:
                proba = model.predict_proba(X_scaled)
                # Clip raw outputs to prevent extreme certainty distortion
                proba = np.clip(proba, 0.01, 0.99)
                proba = proba / proba.sum(axis=1, keepdims=True)
                individual_probas[name] = proba

                blended_proba += w * proba
                active_weight_sum += w
            except Exception as e:
                logger.warning(f"Model {name} inference notice: {e}")

        if active_weight_sum > 0:
            blended_proba /= active_weight_sum
        else:
            blended_proba = np.full((len(X), 3), 1.0 / 3.0)

        # Map to institutional decisions: 0=SELL (PUT), 1=HOLD, 2=BUY (CALL)
        top_decision_idx = int(np.argmax(blended_proba, axis=1)[0])
        decision_map = {0: "BUY_PUT", 1: "HOLD", 2: "BUY_CALL"}

        return {
            "decision": decision_map.get(top_decision_idx, "HOLD"),
            "probabilities": {
                "sell_put_prob": float(blended_proba[0, 0]),
                "hold_prob": float(blended_proba[0, 1]),
                "buy_call_prob": float(blended_proba[0, 2])
            },
            "confidence": float(np.max(blended_proba[0])),
            "market_regime": regime,
            "expert_weights": weights,
            "model_breakdown": {
                m: {
                    "sell_put_prob": float(p[0, 0]),
                    "hold_prob": float(p[0, 1]),
                    "buy_call_prob": float(p[0, 2])
                } for m, p in individual_probas.items()
            }
        }
