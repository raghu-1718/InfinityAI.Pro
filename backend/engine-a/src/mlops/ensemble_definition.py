"""
InfinityAI.Pro — Shared Ensemble Model Definitions
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import ExtraTreesClassifier

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

class BaseEnsembleModel:
    """Base Tri-Model Ensemble for Algorithmic Trading"""
    def __init__(self, n_estimators: int = 120, max_depth: int = 4, learning_rate: float = 0.04):
        self.scaler = StandardScaler()
        self.models = {}
        self.weights = {}
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_scaled = self.scaler.fit_transform(np.asarray(X, dtype=np.float32))
        y_clean = np.asarray(y, dtype=np.int32)

        if HAS_XGB:
            clf_xgb = xgb.XGBClassifier(
                n_estimators=self.n_estimators, max_depth=self.max_depth,
                learning_rate=self.learning_rate, subsample=0.85, colsample_bytree=0.85,
                eval_metric="logloss", random_state=42
            )
            clf_xgb.fit(X_scaled, y_clean)
            self.models["xgboost"] = clf_xgb
            self.weights["xgboost"] = 0.35

        if HAS_LGBM:
            clf_lgb = lgb.LGBMClassifier(
                n_estimators=self.n_estimators, max_depth=self.max_depth,
                learning_rate=self.learning_rate, subsample=0.85, colsample_bytree=0.85,
                verbose=-1, random_state=42
            )
            clf_lgb.fit(X_scaled, y_clean)
            self.models["lightgbm"] = clf_lgb
            self.weights["lightgbm"] = 0.35

        if HAS_CATBOOST:
            clf_cb = CatBoostClassifier(
                iterations=self.n_estimators, depth=self.max_depth,
                learning_rate=self.learning_rate, verbose=0, random_seed=42
            )
            clf_cb.fit(X_scaled, y_clean)
            self.models["catboost"] = clf_cb
            self.weights["catboost"] = 0.30
        else:
            clf_et = ExtraTreesClassifier(n_estimators=self.n_estimators, max_depth=self.max_depth + 2, random_state=42)
            clf_et.fit(X_scaled, y_clean)
            self.models["extratrees"] = clf_et
            self.weights["extratrees"] = 0.30

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.transform(np.asarray(X, dtype=np.float32))
        ensemble_prob = np.zeros(len(X))
        total_w = sum(self.weights.values())

        for name, model in self.models.items():
            w = self.weights[name] / total_w
            prob = model.predict_proba(X_scaled)[:, 1]
            ensemble_prob += w * prob

        return ensemble_prob

    def predict(self, X: np.ndarray, threshold: float = 0.50) -> np.ndarray:
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)

class EquityEnsembleModel(BaseEnsembleModel):
    """Equity Specific Tri-Model Ensemble"""
    pass

class OptionsEnsembleModel(BaseEnsembleModel):
    """Options Specific Tri-Model Ensemble"""
    def __init__(self):
        super().__init__(n_estimators=100, max_depth=3, learning_rate=0.05)
