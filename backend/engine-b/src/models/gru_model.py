"""
InfinityAI.Pro — GRU Sequence-to-Sequence Model
================================================
Engine B | Engine-Grade: Production | Version: 1.0.0

Gated Recurrent Unit (GRU) for short-term price direction classification.

Architecture:
  Input:   (batch, seq_len=30, n_features)  ← 30-bar lookback window
  GRU L1:  128 units, return_sequences=True, dropout=0.3
  GRU L2:  64 units, dropout=0.3
  Attention: Scaled dot-product over L1 outputs
  Dense:   32 → 16 → 3 (Softmax: SELL/HOLD/BUY)

Why GRU over LSTM:
  - ~30% fewer parameters → lower latency on Cloud Run
  - Comparable accuracy for short (30-bar) sequences
  - Faster training → suitable for nightly Vertex AI retraining

Fallback: If TensorFlow/Keras unavailable, returns uniform probability (0.33, 0.33, 0.33)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger("InfinityAI.GRUModel")

# Safe TensorFlow import
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks, regularizers
    HAS_TENSORFLOW = True
    logger.info(f"✅ TensorFlow {tf.__version__} available for GRU model.")
except ImportError:
    HAS_TENSORFLOW = False
    keras = None
    logger.warning("⚠️ TensorFlow not available — GRU model will use uniform fallback.")


class AttentionLayer(object if not HAS_TENSORFLOW else keras.layers.Layer):
    """
    Scaled dot-product attention over GRU output sequence.
    Learns which timesteps are most predictive.
    """

    def __init__(self, units: int = 64, **kwargs):
        if HAS_TENSORFLOW:
            super().__init__(**kwargs)
        self.units = units
        if HAS_TENSORFLOW:
            self.W = keras.layers.Dense(units)
            self.V = keras.layers.Dense(1)

    def call(self, features):
        """Bahdanau-style attention."""
        score  = tf.nn.tanh(self.W(features))         # (batch, seq, units)
        attn_w = tf.nn.softmax(self.V(score), axis=1) # (batch, seq, 1)
        context = attn_w * features                   # (batch, seq, features)
        context = tf.reduce_sum(context, axis=1)      # (batch, features)
        return context


class GRUSignalModel:
    """
    Production GRU classification model for 3-class signal prediction.
    Classes: 0=SELL, 1=HOLD, 2=BUY

    Usage:
        model = GRUSignalModel(symbol="NIFTY", seq_len=30)
        model.build(n_features=65)
        model.fit(X_sequences, y_labels)
        proba = model.predict_proba(X_seq)
    """

    VERSION = "1.0.0"
    SIGNAL_MAP = {0: "SELL", 1: "HOLD", 2: "BUY"}

    def __init__(
        self,
        symbol: str = "NIFTY",
        seq_len: int = 30,
        n_classes: int = 3,
        model_dir: str = "models_store/gru",
    ):
        self.symbol    = symbol
        self.seq_len   = seq_len
        self.n_classes = n_classes
        self.model_dir = model_dir
        self._model: Optional[Any] = None
        self._n_features: Optional[int] = None
        self._trained   = False
        self._trained_at: Optional[datetime] = None
        self._train_metrics: Dict[str, float] = {}
        self._history: Optional[Any] = None

    def build(self, n_features: int) -> Optional[Any]:
        """
        Build GRU architecture.

        Args:
            n_features: Number of input features per timestep.

        Returns:
            Compiled Keras model, or None if TF unavailable.
        """
        if not HAS_TENSORFLOW:
            logger.warning("TF not available — GRU build skipped.")
            return None

        self._n_features = n_features

        inp = keras.Input(shape=(self.seq_len, n_features), name="gru_input")

        # GRU Layer 1 — return sequences for attention
        x = layers.GRU(
            128,
            return_sequences=True,
            dropout=0.3,
            recurrent_dropout=0.1,
            kernel_regularizer=regularizers.l2(1e-4),
            name="gru_1",
        )(inp)
        x = layers.BatchNormalization()(x)

        # GRU Layer 2 — return sequences for attention
        x = layers.GRU(
            64,
            return_sequences=True,
            dropout=0.3,
            name="gru_2",
        )(x)

        # Scaled dot-product attention
        attn_score = layers.Dense(64, activation="tanh")(x)          # (batch, seq, 64)
        attn_w     = layers.Dense(1, activation="softmax")(attn_score) # (batch, seq, 1)
        context    = layers.Multiply()([x, attn_w])                   # weight GRU outputs
        x          = layers.Lambda(lambda t: tf.reduce_sum(t, axis=1))(context)

        # Classification head
        x   = layers.Dense(32, activation="relu", kernel_regularizer=regularizers.l2(1e-4))(x)
        x   = layers.Dropout(0.3)(x)
        x   = layers.Dense(16, activation="relu")(x)
        out = layers.Dense(self.n_classes, activation="softmax", name="signal_output")(x)

        model = keras.Model(inputs=inp, outputs=out, name=f"GRU_{self.symbol}")
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-3),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        self._model = model
        logger.info(
            f"✅ GRU model built: seq_len={self.seq_len}, "
            f"n_features={n_features}, params={model.count_params():,}"
        )
        return model

    @staticmethod
    def build_sequences(
        features_df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str = "target",
        seq_len: int = 30,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert flat feature DataFrame into (X, y) sequence arrays for GRU.

        Args:
            features_df: DataFrame with feature columns and target.
            feature_cols: Columns to use as input features.
            target_col: Label column name.
            seq_len: Lookback window size.

        Returns:
            X: (N, seq_len, n_features)
            y: (N,) integer class labels
        """
        avail_cols = [c for c in feature_cols if c in features_df.columns]
        vals = features_df[avail_cols].values.astype(np.float32)
        tgts = features_df[target_col].values.astype(np.int32) if target_col in features_df.columns else None

        X_list, y_list = [], []
        for i in range(seq_len, len(vals)):
            X_list.append(vals[i - seq_len: i])
            if tgts is not None:
                y_list.append(tgts[i])

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.int32) if y_list else np.array([])
        return X, y

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 64,
        class_weight: Optional[Dict[int, float]] = None,
    ) -> Dict[str, Any]:
        """
        Train the GRU model.

        Args:
            X_train: (N, seq_len, n_features)
            y_train: (N,) integer labels
            X_val, y_val: Optional validation set.
            epochs: Max training epochs.
            batch_size: Mini-batch size.
            class_weight: Optional class weights for imbalanced data.

        Returns:
            Training metrics dict.
        """
        if not HAS_TENSORFLOW or self._model is None:
            logger.warning("GRU fit skipped — TF unavailable or model not built.")
            return {"error": "TensorFlow not available"}

        # Auto-build if not yet built
        if self._model is None:
            self.build(X_train.shape[-1])

        cbs = [
            callbacks.EarlyStopping(
                monitor="val_loss" if X_val is not None else "loss",
                patience=10,
                restore_best_weights=True,
            ),
            callbacks.ReduceLROnPlateau(
                monitor="val_loss" if X_val is not None else "loss",
                factor=0.5,
                patience=5,
                min_lr=1e-6,
            ),
        ]

        validation_data = (X_val, y_val) if (X_val is not None and y_val is not None) else None

        hist = self._model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            class_weight=class_weight,
            callbacks=cbs,
            verbose=0,
        )
        self._history = hist
        self._trained = True
        self._trained_at = datetime.utcnow()

        # Extract final metrics
        final_epoch = len(hist.history["accuracy"]) - 1
        self._train_metrics = {
            "train_accuracy": float(hist.history["accuracy"][final_epoch]),
            "epochs_trained":  final_epoch + 1,
        }
        if validation_data is not None:
            self._train_metrics["val_accuracy"] = float(hist.history.get("val_accuracy", [0])[-1])

        logger.info(
            f"✅ GRU {self.symbol} training complete: "
            f"acc={self._train_metrics.get('train_accuracy', 0):.4f}, "
            f"epochs={self._train_metrics.get('epochs_trained', 0)}"
        )
        return self._train_metrics

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            X: (N, seq_len, n_features) or (seq_len, n_features) for single sample.

        Returns:
            (N, 3) probability array [P(SELL), P(HOLD), P(BUY)]
        """
        if not HAS_TENSORFLOW or not self._trained or self._model is None:
            # Uniform fallback
            n = X.shape[0] if X.ndim == 3 else 1
            return np.full((n, self.n_classes), 1.0 / self.n_classes)

        if X.ndim == 2:
            X = X[np.newaxis, ...]  # (1, seq, features)

        try:
            proba = self._model.predict(X, verbose=0)
            return proba.astype(np.float32)
        except Exception as e:
            logger.warning(f"GRU predict failed: {e}; returning uniform proba.")
            return np.full((X.shape[0], self.n_classes), 1.0 / self.n_classes)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels (argmax of probabilities)."""
        proba = self.predict_proba(X)
        return np.argmax(proba, axis=1)

    def save(self, path: Optional[str] = None) -> str:
        """Save model to HDF5 / SavedModel format."""
        if not HAS_TENSORFLOW or self._model is None:
            return ""
        import os
        save_path = path or os.path.join(self.model_dir, f"gru_{self.symbol}.h5")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        self._model.save(save_path)
        logger.info(f"✅ GRU model saved: {save_path}")
        return save_path

    def load(self, path: str) -> bool:
        """Load GRU model from disk."""
        if not HAS_TENSORFLOW:
            return False
        try:
            self._model  = keras.models.load_model(path)
            self._trained = True
            logger.info(f"✅ GRU model loaded from: {path}")
            return True
        except Exception as e:
            logger.error(f"GRU model load failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type":    "GRU_Seq2Seq_Attention",
            "version":       self.VERSION,
            "symbol":        self.symbol,
            "seq_len":       self.seq_len,
            "n_classes":     self.n_classes,
            "n_features":    self._n_features,
            "trained":       self._trained,
            "trained_at":    self._trained_at.isoformat() if self._trained_at else None,
            "tf_available":  HAS_TENSORFLOW,
            "train_metrics": self._train_metrics,
            "signal_map":    self.SIGNAL_MAP,
        }
