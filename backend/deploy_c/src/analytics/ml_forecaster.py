import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from ..core.utils import setup_logger

log = setup_logger("Forecaster")

class MLForecaster:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)

    def train(self, df: pd.DataFrame):
        X = df[["open", "high", "low", "volume"]]
        y = df["close"]
        self.model.fit(X, y)
        log.info("📈 ML Model trained successfully.")

    def predict_next(self, features):
        pred = self.model.predict([features])[0]
        log.info(f"Predicted Next Price: {pred}")
        return float(pred)
