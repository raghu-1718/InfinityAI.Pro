"""
LSTM Deep Learning Model for Time-Series Price Forecasting
Predicts next 30 days of stock prices using historical OHLCV data
Optimized for Production & Multi-Engine Deployment
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import os

# Safe TensorFlow Import & Fallback
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    from sklearn.preprocessing import MinMaxScaler
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    keras = None
    logging.warning("⚠️ TensorFlow not available - LSTM model disabled")

logger = logging.getLogger(__name__)


class LSTMPriceForecaster:
    """
    Production-grade LSTM model for stock price prediction.

    Architecture:
    - Input: 60-day historical OHLCV + technical indicators
    - LSTM Layer 1: 128 units, return sequences + Dropout(0.2)
    - LSTM Layer 2: 64 units + Dropout(0.2)
    - Dense Layers: 32 -> 16 units (ReLU)
    - Output: 30-day price forecast
    """

    def __init__(
        self,
        symbol: str,
        lookback_days: int = 60,
        forecast_days: int = 30,
        model_dir: str = "models/lstm"
    ):
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow required for LSTM model execution.")

        self.symbol = symbol
        self.lookback_days = lookback_days
        self.forecast_days = forecast_days
        self.model_dir = model_dir
        self.model: Optional[Any] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))

        # Ensure model directory exists
        os.makedirs(self.model_dir, exist_ok=True)

    def _build_model(self, n_features: int) -> Any:
        """Build optimized LSTM architecture"""
        model = models.Sequential([
            layers.LSTM(128, return_sequences=True, input_shape=(self.lookback_days, n_features)),
            layers.Dropout(0.2),
            layers.LSTM(64, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu'),
            layers.Dense(self.forecast_days)
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mape']
        )
        return model

    def _prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare vectorized sequences for LSTM training."""
        feature_cols = [col for col in data.columns if col != 'date']
        features = data[feature_cols].values
        target = data['close'].values.reshape(-1, 1)

        # Scale features and target
        features_scaled = self.feature_scaler.fit_transform(features)
        target_scaled = self.scaler.fit_transform(target)

        total_samples = len(data) - self.lookback_days - self.forecast_days + 1
        if total_samples <= 0:
            raise ValueError(f"Insufficient data: need > {self.lookback_days + self.forecast_days} rows.")

        X = np.empty((total_samples, self.lookback_days, features.shape[1]))
        y = np.empty((total_samples, self.forecast_days))

        for i in range(total_samples):
            start_idx = i
            end_idx = i + self.lookback_days
            X[i] = features_scaled[start_idx:end_idx]
            y[i] = target_scaled[end_idx:end_idx + self.forecast_days].flatten()

        return X, y

    def train(
        self,
        historical_data: pd.DataFrame,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32,
        early_stop_patience: int = 10
    ) -> Dict[str, Any]:
        """Train LSTM model on historical data with early stopping."""
        logger.info(f"🚀 Training LSTM for {self.symbol} with {len(historical_data)} samples")

        X, y = self._prepare_sequences(historical_data)
        logger.info(f"✅ Prepared sequences: X={X.shape}, y={y.shape}")

        self.model = self._build_model(X.shape[2])

        callbacks_list = [
            callbacks.EarlyStopping(monitor='val_loss', patience=early_stop_patience, restore_best_weights=True, verbose=1),
            callbacks.ModelCheckpoint(os.path.join(self.model_dir, f"{self.symbol}_best.keras"), monitor='val_loss', save_best_only=True, verbose=1),
            callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-5, verbose=1)
        ]

        history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list,
            verbose=1
        )

        self.save_model()

        return {
            "symbol": self.symbol,
            "epochs_trained": len(history.history['loss']),
            "final_loss": float(history.history['loss'][-1]),
            "final_val_loss": float(history.history['val_loss'][-1]),
            "final_mae": float(history.history['mae'][-1]),
            "final_val_mae": float(history.history['val_mae'][-1]),
            "best_epoch": int(np.argmin(history.history['val_loss'])) + 1,
            "training_samples": len(X),
            "lookback_days": self.lookback_days,
            "forecast_days": self.forecast_days
        }

    def predict(self, recent_data: pd.DataFrame) -> Dict[str, Any]:
        """Generate 30-day price forecast."""
        if self.model is None:
            raise ValueError("Model not trained or loaded.")

        if len(recent_data) < self.lookback_days:
            raise ValueError(f"Need at least {self.lookback_days} days of data.")

        feature_cols = [col for col in recent_data.columns if col != 'date']
        features = recent_data[feature_cols].tail(self.lookback_days).values

        features_scaled = self.feature_scaler.transform(features)
        X = features_scaled.reshape(1, self.lookback_days, len(feature_cols))

        y_pred_scaled = self.model.predict(X, verbose=0)
        y_pred = self.scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()

        last_date = pd.to_datetime(recent_data['date'].iloc[-1])
        forecast_dates = [(last_date + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(self.forecast_days)]

        forecast = [{"date": d, "predicted_close": round(float(p), 2)} for d, p in zip(forecast_dates, y_pred)]

        current_price = float(recent_data['close'].iloc[-1])
        predicted_price_30d = float(y_pred[-1])
        price_change = predicted_price_30d - current_price
        price_change_pct = (price_change / current_price) * 100

        return {
            "symbol": self.symbol,
            "current_price": round(current_price, 2),
            "predicted_price_30d": round(predicted_price_30d, 2),
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "forecast": forecast,
            "lookback_days": self.lookback_days,
            "forecast_days": self.forecast_days,
            "generated_at": datetime.now(datetime.UTC).isoformat()
        }

    def save_model(self):
        """Save model and scaler configurations."""
        model_path = os.path.join(self.model_dir, f"{self.symbol}.keras")
        scaler_path = os.path.join(self.model_dir, f"{self.symbol}_scalers.json")

        if self.model:
            self.model.save(model_path)
            logger.info(f"💾 Saved Keras model to {model_path}")

        scalers = {
            "target_scaler": {
                "min": self.scaler.min_.tolist() if hasattr(self.scaler, 'min_') else None,
                "scale": self.scaler.scale_.tolist() if hasattr(self.scaler, 'scale_') else None,
                "data_min": self.scaler.data_min_.tolist() if hasattr(self.scaler, 'data_min_') else None,
                "data_max": self.scaler.data_max_.tolist() if hasattr(self.scaler, 'data_max_') else None
            },
            "feature_scaler": {
                "min": self.feature_scaler.min_.tolist() if hasattr(self.feature_scaler, 'min_') else None,
                "scale": self.feature_scaler.scale_.tolist() if hasattr(self.feature_scaler, 'scale_') else None,
                "data_min": self.feature_scaler.data_min_.tolist() if hasattr(self.feature_scaler, 'data_min_') else None,
                "data_max": self.feature_scaler.data_max_.tolist() if hasattr(self.feature_scaler, 'data_max_') else None
            }
        }

        with open(scaler_path, 'w') as f:
            json.dump(scalers, f, indent=2)
        logger.info(f"💾 Saved scalers to {scaler_path}")

    def load_model(self) -> bool:
        """Load model weights and scaler parameters."""
        model_path = os.path.join(self.model_dir, f"{self.symbol}.keras")
        legacy_path = os.path.join(self.model_dir, f"{self.symbol}.h5")
        scaler_path = os.path.join(self.model_dir, f"{self.symbol}_scalers.json")

        target_path = model_path if os.path.exists(model_path) else legacy_path
        if not os.path.exists(target_path):
            logger.warning(f"⚠️ Model not found at {target_path}")
            return False

        self.model = keras.models.load_model(target_path)
        logger.info(f"📂 Loaded model from {target_path}")

        if os.path.exists(scaler_path):
            with open(scaler_path, 'r') as f:
                scalers = json.load(f)

            if scalers.get("target_scaler", {}).get("min"):
                self.scaler.min_ = np.array(scalers["target_scaler"]["min"])
                self.scaler.scale_ = np.array(scalers["target_scaler"]["scale"])
                self.scaler.data_min_ = np.array(scalers["target_scaler"]["data_min"])
                self.scaler.data_max_ = np.array(scalers["target_scaler"]["data_max"])

            if scalers.get("feature_scaler", {}).get("min"):
                self.feature_scaler.min_ = np.array(scalers["feature_scaler"]["min"])
                self.feature_scaler.scale_ = np.array(scalers["feature_scaler"]["scale"])
                self.feature_scaler.data_min_ = np.array(scalers["feature_scaler"]["data_min"])
                self.feature_scaler.data_max_ = np.array(scalers["feature_scaler"]["data_max"])

            logger.info(f"📂 Loaded scalers from {scaler_path}")

        return True


def get_lstm_forecast(symbol: str, recent_data: pd.DataFrame, model_dir: str = "models/lstm") -> Dict[str, Any]:
    """Helper utility for generating quick LSTM forecasts."""
    forecaster = LSTMPriceForecaster(symbol, model_dir=model_dir)
    if not forecaster.load_model():
        return {"error": "Model not trained or weights missing", "symbol": symbol}
    return forecaster.predict(recent_data)
