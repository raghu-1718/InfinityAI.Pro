"""
InfinityAI.Pro - ML Model Manager Service
Handles model lifecycle: training, inference, versioning
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import joblib
import numpy as np
import pandas as pd

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import xgboost as xgb
import lightgbm as lgb

logger = logging.getLogger(__name__)

class MLModelManager:
    """
    Centralized ML model management
    Handles training, inference, persistence, and versioning
    """

    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        self.models = {}
        self.scalers = {}
        self.metadata = {}

        # Create model directory if not exists
        os.makedirs(model_dir, exist_ok=True)

        # Initialize default models
        self._initialize_models()

    def _initialize_models(self):
        """Initialize or load existing models"""
        logger.info("Initializing ML models...")

        # Try to load existing models
        for model_name in ['random_forest', 'xgboost', 'lightgbm']:
            model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
            if os.path.exists(model_path):
                try:
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"✅ Loaded model: {model_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load {model_name}: {e}")
                    self._create_default_model(model_name)
            else:
                self._create_default_model(model_name)

        # Initialize scaler
        scaler_path = os.path.join(self.model_dir, "scaler.joblib")
        if os.path.exists(scaler_path):
            self.scalers['standard'] = joblib.load(scaler_path)
        else:
            self.scalers['standard'] = StandardScaler()

    def _create_default_model(self, model_name: str):
        """Create default untrained model"""
        if model_name == 'random_forest':
            self.models[model_name] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif model_name == 'xgboost':
            self.models[model_name] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
        elif model_name == 'lightgbm':
            self.models[model_name] = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )

        logger.info(f"Created default model: {model_name}")

    def train_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Train specified models on provided data

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target labels (n_samples,)
            model_names: List of models to train (default: all)

        Returns:
            Dictionary with training results
        """
        if model_names is None:
            model_names = list(self.models.keys())

        results = {}

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        scaler = self.scalers['standard']
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train each model
        for model_name in model_names:
            if model_name not in self.models:
                logger.warning(f"Model {model_name} not found")
                continue

            try:
                logger.info(f"Training {model_name}...")
                model = self.models[model_name]

                # Train
                model.fit(X_train_scaled, y_train)

                # Evaluate
                train_score = model.score(X_train_scaled, y_train)
                test_score = model.score(X_test_scaled, y_test)

                results[model_name] = {
                    "train_accuracy": float(train_score),
                    "test_accuracy": float(test_score),
                    "trained_at": datetime.utcnow().isoformat()
                }

                # Save model
                self.save_model(model_name)

                logger.info(f"✅ {model_name} - Train: {train_score:.3f}, Test: {test_score:.3f}")

            except Exception as e:
                logger.error(f"❌ Training failed for {model_name}: {e}")
                results[model_name] = {"error": str(e)}

        # Save scaler
        self.save_scaler()

        return results

    def predict(
        self,
        X: np.ndarray,
        model_name: str = 'xgboost'
    ) -> np.ndarray:
        """
        Generate predictions using specified model

        Args:
            X: Feature matrix (n_samples, n_features)
            model_name: Model to use for prediction

        Returns:
            Predictions array
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model = self.models[model_name]
        scaler = self.scalers['standard']

        # Scale features
        X_scaled = scaler.transform(X)

        # Predict
        predictions = model.predict(X_scaled)

        return predictions

    def predict_proba(
        self,
        X: np.ndarray,
        model_name: str = 'xgboost'
    ) -> np.ndarray:
        """
        Generate prediction probabilities

        Args:
            X: Feature matrix (n_samples, n_features)
            model_name: Model to use for prediction

        Returns:
            Probability predictions array
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model = self.models[model_name]

        if not hasattr(model, 'predict_proba'):
            raise ValueError(f"Model {model_name} does not support probability predictions")

        scaler = self.scalers['standard']

        # Scale features
        X_scaled = scaler.transform(X)

        # Predict probabilities
        probas = model.predict_proba(X_scaled)

        return probas

    def ensemble_predict(
        self,
        X: np.ndarray,
        model_names: Optional[List[str]] = None,
        weights: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        Ensemble prediction using multiple models with weighted voting

        Args:
            X: Feature matrix
            model_names: Models to use (default: all)
            weights: Weights for each model (default: equal weights)

        Returns:
            Ensemble predictions
        """
        if model_names is None:
            model_names = ['random_forest', 'xgboost', 'lightgbm']

        if weights is None:
            weights = [1.0 / len(model_names)] * len(model_names)

        # Get predictions from each model
        predictions = []
        for model_name in model_names:
            try:
                pred = self.predict_proba(X, model_name)
                predictions.append(pred)
            except Exception as e:
                logger.warning(f"Skipping {model_name}: {e}")

        if not predictions:
            raise ValueError("No valid predictions from ensemble models")

        # Weighted average
        ensemble_proba = np.average(predictions, axis=0, weights=weights[:len(predictions)])

        # Convert to class predictions
        ensemble_pred = np.argmax(ensemble_proba, axis=1)

        return ensemble_pred

    def save_model(self, model_name: str):
        """Save model to disk"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
        joblib.dump(self.models[model_name], model_path)
        logger.info(f"💾 Saved model: {model_name}")

    def save_scaler(self):
        """Save scaler to disk"""
        scaler_path = os.path.join(self.model_dir, "scaler.joblib")
        joblib.dump(self.scalers['standard'], scaler_path)
        logger.info("💾 Saved scaler")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        info = {
            "models": {},
            "model_dir": self.model_dir
        }

        for name, model in self.models.items():
            info["models"][name] = {
                "type": type(model).__name__,
                "n_features": getattr(model, 'n_features_in_', 'unknown')
            }

        return info


# Global instance
model_manager = MLModelManager()
