import shap
import joblib
import numpy as np
import os
from lightgbm import LGBMRegressor

class ExplainabilityService:
    def __init__(self, model_path: str, scaler_path: str, features_path: str):
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        with open(features_path, "r") as f:
            import json
            self.features = json.load(f)
        self.explainer = shap.Explainer(self.model)

    def explain(self, X: np.ndarray):
        X_scaled = self.scaler.transform(X)
        shap_values = self.explainer(X_scaled)
        feature_importance = dict(zip(self.features, np.abs(shap_values.values[0])))
        return feature_importance
