"""
LSTM Deep Learning Model for Time-Series Price Forecasting
Predicts next 30 days of stock prices using historical OHLCV data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import os

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    from sklearn.preprocessing import MinMaxScaler
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    logging.warning("TensorFlow not available - LSTM model disabled")

logger = logging.getLogger(__name__)


class LSTMPriceForecaster:
    """
    LSTM model for stock price prediction.

    Architecture:
    - Input: 60-day historical OHLCV + technical indicators
    - LSTM Layer 1: 128 units, return sequences
    - Dropout: 0.2
    - LSTM Layer 2: 64 units
    - Dropout: 0.2
    - Dense Layer 1: 32 units, ReLU
    - Dense Layer 2: 16 units, ReLU
    - Output: 30-day price forecast

    Training:
    - Loss: MSE (Mean Squared Error)
    - Optimizer: Adam (lr=0.001)
    - Epochs: 100 (with early stopping)
    - Batch size: 32
    """

    def __init__(
        self,
        symbol: str,
        lookback_days: int = 60,
        forecast_days: int = 30,
        model_dir: str = "models/lstm"
    ):
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow required for LSTM model")

        self.symbol = symbol
        self.lookback_days = lookback_days
        self.forecast_days = forecast_days
        self.model_dir = model_dir
        self.model: Optional[keras.Model] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))

        # Ensure model directory exists
        os.makedirs(self.model_dir, exist_ok=True)

    def _build_model(self, n_features: int) -> keras.Model:
        """Build LSTM architecture"""
        model = models.Sequential([
            # LSTM Layer 1
            layers.LSTM(
                128,
                return_sequences=True,
                input_shape=(self.lookback_days, n_features)
            ),
            layers.Dropout(0.2),

            # LSTM Layer 2
            layers.LSTM(64, return_sequences=False),
            layers.Dropout(0.2),

            # Dense layers
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu'),

            # Output layer (forecast_days prices)
            layers.Dense(self.forecast_days)
        ])

        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mape']
        )

        return model

    def _prepare_sequences(
        self,
        data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training.

        Args:
            data: DataFrame with OHLCV + technical indicators

        Returns:
            X: Input sequences (samples, lookback_days, features)
            y: Target sequences (samples, forecast_days)
        """
        # Extract features
        feature_cols = [col for col in data.columns if col != 'date']
        features = data[feature_cols].values

        # Scale features
        features_scaled = self.feature_scaler.fit_transform(features)

        # Scale target (close price)
        target = data['close'].values.reshape(-1, 1)
        target_scaled = self.scaler.fit_transform(target)

        X, y = [], []

        # Create sequences
        for i in range(self.lookback_days, len(data) - self.forecast_days):
            # Input: lookback_days of features
            X.append(features_scaled[i - self.lookback_days:i])

            # Target: next forecast_days of close prices
            y.append(target_scaled[i:i + self.forecast_days].flatten())

        return np.array(X), np.array(y)

    def train(
        self,
        historical_data: pd.DataFrame,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32,
        early_stop_patience: int = 10
    ) -> Dict[str, Any]:
        """
        Train LSTM model on historical data.

        Args:
            historical_data: DataFrame with columns:
                - date, open, high, low, close, volume
                - technical indicators (RSI, MACD, ATR, etc.)
            validation_split: Train/validation split ratio
            epochs: Maximum training epochs
            batch_size: Batch size for training
            early_stop_patience: Early stopping patience

        Returns:
            Training history and metrics
        """
        logger.info(f"Training LSTM for {self.symbol} with {len(historical_data)} samples")

        # Prepare sequences
        X, y = self._prepare_sequences(historical_data)

        logger.info(f"Prepared {len(X)} sequences: X={X.shape}, y={y.shape}")

        # Build model
        n_features = X.shape[2]
        self.model = self._build_model(n_features)

        logger.info(f"Model architecture:\n{self.model.summary()}")

        # Callbacks
        early_stopping = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=early_stop_patience,
            restore_best_weights=True,
            verbose=1
        )

        model_checkpoint = callbacks.ModelCheckpoint(
            os.path.join(self.model_dir, f"{self.symbol}_best.h5"),
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )

        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.00001,
            verbose=1
        )

        # Train model
        history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping, model_checkpoint, reduce_lr],
            verbose=1
        )

        # Save final model
        self.save_model()

        # Return training metrics
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

    def predict(
        self,
        recent_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate 30-day price forecast.

        Args:
            recent_data: Most recent lookback_days of data

        Returns:
            Forecast with dates, prices, and confidence intervals
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        if len(recent_data) < self.lookback_days:
            raise ValueError(f"Need at least {self.lookback_days} days of data")

        # Prepare input sequence
        feature_cols = [col for col in recent_data.columns if col != 'date']
        features = recent_data[feature_cols].tail(self.lookback_days).values

        # Scale features
        features_scaled = self.feature_scaler.transform(features)

        # Reshape for prediction
        X = features_scaled.reshape(1, self.lookback_days, len(feature_cols))

        # Predict
        y_pred_scaled = self.model.predict(X, verbose=0)

        # Inverse transform to get actual prices
        y_pred = self.scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()

        # Generate forecast dates
        last_date = pd.to_datetime(recent_data['date'].iloc[-1])
        forecast_dates = [
            (last_date + timedelta(days=i+1)).strftime("%Y-%m-%d")
            for i in range(self.forecast_days)
        ]

        # Create forecast output
        forecast = []
        for date, price in zip(forecast_dates, y_pred):
            forecast.append({
                "date": date,
                "predicted_close": round(float(price), 2)
            })

        # Calculate statistics
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
            "generated_at": datetime.now().isoformat()
        }

    def save_model(self):
        """Save model and scalers"""
        model_path = os.path.join(self.model_dir, f"{self.symbol}.h5")
        scaler_path = os.path.join(self.model_dir, f"{self.symbol}_scalers.json")

        # Save Keras model
        if self.model:
            self.model.save(model_path)
            logger.info(f"Saved model to {model_path}")

        # Save scalers (parameters only)
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

        logger.info(f"Saved scalers to {scaler_path}")

    def load_model(self) -> bool:
        """Load model and scalers"""
        model_path = os.path.join(self.model_dir, f"{self.symbol}.h5")
        scaler_path = os.path.join(self.model_dir, f"{self.symbol}_scalers.json")

        if not os.path.exists(model_path):
            logger.warning(f"Model not found: {model_path}")
            return False

        # Load Keras model
        self.model = keras.models.load_model(model_path)
        logger.info(f"Loaded model from {model_path}")

        # Load scalers
        if os.path.exists(scaler_path):
            with open(scaler_path, 'r') as f:
                scalers = json.load(f)

            # Restore scaler parameters
            if scalers["target_scaler"]["min"]:
                self.scaler.min_ = np.array(scalers["target_scaler"]["min"])
                self.scaler.scale_ = np.array(scalers["target_scaler"]["scale"])
                self.scaler.data_min_ = np.array(scalers["target_scaler"]["data_min"])
                self.scaler.data_max_ = np.array(scalers["target_scaler"]["data_max"])

            if scalers["feature_scaler"]["min"]:
                self.feature_scaler.min_ = np.array(scalers["feature_scaler"]["min"])
                self.feature_scaler.scale_ = np.array(scalers["feature_scaler"]["scale"])
                self.feature_scaler.data_min_ = np.array(scalers["feature_scaler"]["data_min"])
                self.feature_scaler.data_max_ = np.array(scalers["feature_scaler"]["data_max"])

            logger.info(f"Loaded scalers from {scaler_path}")

        return True


# Convenience function
def get_lstm_forecast(
    symbol: str,
    recent_data: pd.DataFrame,
    model_dir: str = "models/lstm"
) -> Dict[str, Any]:
    """
    Quick helper to get LSTM forecast for a symbol.

    Example:
        >>> forecast = get_lstm_forecast("NIFTY", recent_data_df)
        >>> print(forecast["predicted_price_30d"])
    """
    forecaster = LSTMPriceForecaster(symbol, model_dir=model_dir)

    if not forecaster.load_model():
        return {
            "error": "Model not trained",
            "symbol": symbol
        }

    return forecaster.predict(recent_data)
