import numpy as np
import pandas as pd
import logging
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from statsmodels.tsa.arima.model import ARIMA

# Optional Prophet
try:
    from prophet import Prophet
except (ImportError, ModuleNotFoundError):
    Prophet = None

logger = logging.getLogger("model_zoo")


class ModelZoo:
    """
    Lightweight regression-focused model container.

    PURPOSE:
    - Short-horizon price estimation
    - Real-time usage
    - No disk I/O
    - No classification
    """

    def __init__(self):
        self.models = {
            "rf_price": RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                random_state=42,
                n_jobs=-1
            ),
            "xgb_price": XGBRegressor(
                n_estimators=400,
                max_depth=6,
                eta=0.05,
                subsample=0.9,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=2
            ),
            "lgb_price": LGBMRegressor(
                n_estimators=400,
                learning_rate=0.05,
                max_depth=-1,
                num_leaves=48,
                subsample=0.9,
                colsample_bytree=0.8,
                random_state=42
            ),
        }

        self.fitted: dict[str, bool] = {}
        self.last_trained: dict[str, datetime] = {}
        self.metrics: dict[str, dict] = {}

        self.arima_cache: dict[str, Any] = {}
        self.prophet_cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Tabular regression
    # ------------------------------------------------------------------
    def train_tabular(self, X: np.ndarray, y: np.ndarray):
        if X.size == 0 or y.size == 0:
            raise ValueError("Training data is empty")

        for name, model in self.models.items():
            try:
                model.fit(X, y)
                self.fitted[name] = True
                self.last_trained[name] = datetime.utcnow()

                preds = model.predict(X)
                rmse = float(np.sqrt(np.mean((preds - y) ** 2)))
                self.metrics[name] = {"rmse": round(rmse, 4)}

            except Exception as e:
                logger.warning(f"Training failed for {name}: {e}")

    def predict_tabular(self, features: np.ndarray) -> dict[str, float]:
        if features is None or features.size == 0:
            return {}

        preds: dict[str, float] = {}
        for name, model in self.models.items():
            if self.fitted.get(name):
                try:
                    preds[name] = float(model.predict(features)[0])
                except Exception as e:
                    logger.warning(f"{name} prediction failed: {e}")

        return preds

    # ------------------------------------------------------------------
    # Time-series models (optional)
    # ------------------------------------------------------------------
    def train_arima(self, symbol: str, close_series: pd.Series):
        try:
            model = ARIMA(close_series, order=(2, 1, 2))
            self.arima_cache[symbol] = model.fit()
        except Exception as e:
            logger.warning(f"ARIMA fit failed for {symbol}: {e}")

    def predict_arima(self, symbol: str) -> float | None:
        res = self.arima_cache.get(symbol)
        if not res:
            return None
        try:
            return float(res.get_forecast(steps=1).predicted_mean.iloc[0])
        except Exception as e:
            logger.warning(f"ARIMA forecast failed {symbol}: {e}")
            return None

    def train_prophet(self, symbol: str, df: pd.DataFrame):
        if Prophet is None:
            return
        try:
            p = Prophet(
                seasonality_mode="multiplicative",
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True
            )
            ds = pd.DataFrame({
                "ds": df.index.tz_localize(None),
                "y": df["Close"].values
            })
            p.fit(ds)
            self.prophet_cache[symbol] = p
        except Exception as e:
            logger.warning(f"Prophet fit failed for {symbol}: {e}")

    def predict_prophet(self, symbol: str) -> float | None:
        p = self.prophet_cache.get(symbol)
        if not p:
            return None
        try:
            future = pd.DataFrame({"ds": [datetime.utcnow()]})
            return float(p.predict(future)["yhat"].iloc[0])
        except Exception as e:
            logger.warning(f"Prophet predict failed {symbol}: {e}")
            return None
