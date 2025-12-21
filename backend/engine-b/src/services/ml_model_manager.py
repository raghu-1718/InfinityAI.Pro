"""
InfinityAI.Pro - ML Model Manager Service

⚠️ ROLE CLARITY:
This module is intended for:
- Offline / batch training
- Research & experimentation
- Admin-triggered retraining
- Model persistence & versioning

It is NOT used in the real-time trading signal path.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

import xgboost as xgb
import lightgbm as lgb

logger = logging.getLogger("ml_model_manager")


class MLModelManager:
    """
    Centralized offline ML model manager.
    Handles training, inference, persistence, and metadata.
    """

    SUPPORTED_MODELS = ("random_forest", "xgboost", "lightgbm")

    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

        os.makedirs(self.model_dir, exist_ok=True)
        self._initialize_models()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _initialize_models(self):
        logger.info("🔄 Initializing MLModelManager...")

        for model_name in self.SUPPORTED_MODELS:
            path = os.path.join(self.model_dir, f"{model_name}.joblib")
            if os.path.exists(path):
                try:
                    self.models[model_name] = joblib.load(path)
                    logger.info(f"✅ Loaded model: {model_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed loading {model_name}: {e}")
                    self._create_default_model(model_name)
            else:
                self._create_default_model(model_name)

        scaler_path = os.path.join(self.model_dir, "scaler.joblib")
        self.scalers["standard"] = (
            joblib.load(scaler_path)
            if os.path.exists(scaler_path)
            else StandardScaler()
        )

    def _create_default_model(self, model_name: str):
        if model_name == "random_forest":
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif model_name == "xgboost":
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
        elif model_name == "lightgbm":
            model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unsupported model: {model_name}")

        self.models[model_name] = model
        self.metadata[model_name] = {"initialized_at": datetime.utcnow().isoformat()}
        logger.info(f"🆕 Created default model: {model_name}")

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:

        if X is None or y is None or len(X) == 0:
            raise ValueError("Empty training data")

        model_names = model_names or list(self.models.keys())
        results = {}

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        scaler = self.scalers["standard"]
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        for name in model_names:
            model = self.models.get(name)
            if not model:
                continue

            try:
                logger.info(f"🎓 Training {name}...")
                model.fit(X_train_scaled, y_train)

                train_acc = float(model.score(X_train_scaled, y_train))
                test_acc = float(model.score(X_test_scaled, y_test))

                self.metadata[name] = {
                    "trained_at": datetime.utcnow().isoformat(),
                    "train_accuracy": train_acc,
                    "test_accuracy": test_acc,
                    "samples": int(len(X))
                }

                self.save_model(name)
                results[name] = self.metadata[name]

            except Exception as e:
                logger.error(f"❌ Training failed for {name}: {e}")
                results[name] = {"error": str(e)}

        self.save_scaler()
        return results

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, X: np.ndarray, model_name: str = "xgboost") -> np.ndarray:
        self._validate_input(X, model_name)
        X_scaled = self.scalers["standard"].transform(X)
        return self.models[model_name].predict(X_scaled)

    def predict_proba(self, X: np.ndarray, model_name: str = "xgboost") -> np.ndarray:
        self._validate_input(X, model_name)

        model = self.models[model_name]
        if not hasattr(model, "predict_proba"):
            raise ValueError(f"{model_name} does not support predict_proba")

        X_scaled = self.scalers["standard"].transform(X)
        return model.predict_proba(X_scaled)

    def ensemble_predict(
        self,
        X: np.ndarray,
        model_names: Optional[List[str]] = None,
        weights: Optional[List[float]] = None
    ) -> np.ndarray:

        model_names = model_names or list(self.models.keys())
        weights = weights or [1.0] * len(model_names)

        if len(model_names) != len(weights):
            raise ValueError("Model names and weights length mismatch")

        weights = np.array(weights, dtype=float)
        weights = weights / weights.sum()  # normalize

        probas = []
        for name in model_names:
            try:
                probas.append(self.predict_proba(X, name))
            except Exception as e:
                logger.warning(f"Skipping {name}: {e}")

        if not probas:
            raise ValueError("No valid predictions in ensemble")

        ensemble = np.average(probas, axis=0, weights=weights[:len(probas)])
        return np.argmax(ensemble, axis=1)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_model(self, model_name: str):
        joblib.dump(self.models[model_name], os.path.join(self.model_dir, f"{model_name}.joblib"))

    def save_scaler(self):
        joblib.dump(self.scalers["standard"], os.path.join(self.model_dir, "scaler.joblib"))

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _validate_input(self, X: np.ndarray, model_name: str):
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        if X is None or X.size == 0:
            raise ValueError("Empty feature array")

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_dir": self.model_dir,
            "models": {
                name: {
                    "type": type(model).__name__,
                    "metadata": self.metadata.get(name, {})
                }
                for name, model in self.models.items()
            }
        }


# Singleton (offline usage only)
model_manager = MLModelManager()
