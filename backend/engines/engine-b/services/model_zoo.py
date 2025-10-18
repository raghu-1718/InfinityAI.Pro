import numpy as np, pandas as pd, logging
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from statsmodels.tsa.arima.model import ARIMA

# Prophet is optional - gracefully handle if not installed
try:
    from prophet import Prophet
except (ImportError, ModuleNotFoundError):
    Prophet = None

logger = logging.getLogger("model_zoo")

class ModelZoo:
    def __init__(self):
        self.models = {}
        self.fitted = {}
        self.last_trained = {}
        self.metrics = {}
        self.models["rf_price"]  = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
        self.models["xgb_price"] = XGBRegressor(n_estimators=400, max_depth=6, eta=0.05, subsample=0.9, colsample_bytree=0.8, random_state=42, n_jobs=2)
        self.models["lgb_price"] = LGBMRegressor(n_estimators=400, learning_rate=0.05, max_depth=-1, num_leaves=48, subsample=0.9, colsample_bytree=0.8, random_state=42)
        self.arima_cache: dict[str, ARIMA] = {}
        self.prophet_cache: dict = {}  # Type depends on Prophet availability

    def train_tabular(self, X: np.ndarray, y: np.ndarray):
        for name in ["rf_price","xgb_price","lgb_price"]:
            self.models[name].fit(X, y)
            self.fitted[name] = True
            self.last_trained[name] = datetime.utcnow()
            self.metrics[name] = {"rmse": float(np.sqrt(np.mean((self.models[name].predict(X) - y)**2)))}

    def predict_tabular(self, features: np.ndarray) -> dict:
        preds = {}
        for name in ["rf_price","xgb_price","lgb_price"]:
            if self.fitted.get(name):
                preds[name] = float(self.models[name].predict(features)[0])
        return preds

    def train_arima(self, symbol: str, close_series: pd.Series):
        try:
            model = ARIMA(close_series, order=(2,1,2))
            res = model.fit()
            self.arima_cache[symbol] = res
        except Exception as e:
            logger.warning(f"ARIMA fit failed for {symbol}: {e}")

    def predict_arima(self, symbol: str) -> float | None:
        res = self.arima_cache.get(symbol)
        if not res: return None
        try:
            fc = res.get_forecast(steps=1).predicted_mean.iloc[0]
            return float(fc)
        except Exception as e:
            logger.warning(f"ARIMA forecast failed {symbol}: {e}")
            return None

    def train_prophet(self, symbol: str, df: pd.DataFrame):
        try:
            p = Prophet(seasonality_mode="multiplicative", daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
            ds = pd.DataFrame({"ds": df.index.tz_localize(None), "y": df["Close"].values})
            p.fit(ds)
            self.prophet_cache[symbol] = p
        except Exception as e:
            logger.warning(f"Prophet fit failed for {symbol}: {e}")

    def predict_prophet(self, symbol: str) -> float | None:
        p = self.prophet_cache.get(symbol)
        if not p: return None
        try:
            import pandas as pd
            future = pd.DataFrame({"ds":[datetime.utcnow()]})
            yhat = p.predict(future)["yhat"].iloc[0]
            return float(yhat)
        except Exception as e:
            logger.warning(f"Prophet predict failed {symbol}: {e}")
            return None
