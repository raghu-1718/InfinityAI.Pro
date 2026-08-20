"""
InfinityAI.Pro — Kalman Filter Trend Model
==========================================
Engine B | Engine-Grade: Production | Version: 1.0.0

Implements a Kalman Filter for:
  1. Real-time price trend estimation (denoised price)
  2. Dynamic beta estimation (market sensitivity)
  3. Mean-reversion signal (price vs Kalman trend = z-score)
  4. Velocity (price momentum) estimation

Key advantages over simple MAs:
  - Optimal online estimator (minimum variance)
  - Adapts to non-stationary market dynamics
  - No fixed window size → reacts immediately to regime changes
  - Produces uncertainty bounds (Kalman gain)

Two models:
  A. KalmanTrendFilter  — single-asset denoised price + velocity
  B. KalmanRegressionFilter — rolling dynamic pair regression (for spread/beta)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("InfinityAI.KalmanFilter")


class KalmanTrendFilter:
    """
    Constant-velocity Kalman Filter for price trend extraction.

    State vector: [price, velocity]
    Observation: [close_price]

    Tuning:
      - process_noise (Q): Higher Q → faster adaptation, more noise
      - observation_noise (R): Higher R → smoother output, slower adaptation
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        process_noise: float = 1e-4,
        observation_noise: float = 1e-2,
        initial_state_cov: float = 1.0,
    ):
        self.Q = process_noise       # Process noise covariance
        self.R = observation_noise   # Observation noise covariance

        # State transition matrix (constant velocity model)
        self.F = np.array([[1.0, 1.0],   # price_t = price_{t-1} + velocity_{t-1}
                           [0.0, 1.0]])  # velocity_t = velocity_{t-1}

        # Observation matrix (we observe price only)
        self.H = np.array([[1.0, 0.0]])

        # Initial state covariance
        self.P0 = np.eye(2) * initial_state_cov

        self._states: Optional[np.ndarray] = None
        self._gains: Optional[np.ndarray] = None
        self._trained = False
        self._trained_at: Optional[datetime] = None

    def _run_filter(self, observations: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Run forward Kalman filter pass.

        Args:
            observations: 1D array of close prices.

        Returns:
            states (N, 2): [filtered_price, velocity] per timestep.
            gains  (N, 2): Kalman gain per timestep.
        """
        n = len(observations)
        states = np.zeros((n, 2))
        gains  = np.zeros((n, 2))

        # Initialize state from first observation
        x = np.array([observations[0], 0.0])
        P = self.P0.copy()

        # Process noise covariance matrix
        Q = np.array([[self.Q, 0.0],
                      [0.0,    self.Q]])

        for t in range(n):
            # ── Predict ──────────────────────────────────────────────────
            x_pred = self.F @ x
            P_pred = self.F @ P @ self.F.T + Q

            # ── Update ───────────────────────────────────────────────────
            y = observations[t] - (self.H @ x_pred)[0]            # innovation
            S = (self.H @ P_pred @ self.H.T)[0, 0] + self.R       # innovation covariance
            K = (P_pred @ self.H.T) / S                            # Kalman gain (2,)

            x = x_pred + K.flatten() * y
            P = (np.eye(2) - K @ self.H) @ P_pred

            states[t] = x
            gains[t]  = K.flatten()

        return states, gains

    def fit_predict(self, close: pd.Series) -> pd.DataFrame:
        """
        Fit and predict Kalman trend on a price series.

        Returns:
            DataFrame with columns:
              - kalman_price:    Denoised (filtered) price
              - kalman_velocity: Price velocity (momentum)
              - kalman_zscore:   Deviation of raw price from Kalman trend (normalized)
              - kalman_gain:     Current Kalman gain (adaptivity)
        """
        obs = close.fillna(method="ffill").values.astype(np.float64)
        states, gains = self._run_filter(obs)

        kalman_price    = states[:, 0]
        kalman_velocity = states[:, 1]
        residuals       = obs - kalman_price

        # Z-score of residuals using rolling std
        roll_std = pd.Series(residuals).rolling(20).std().fillna(1.0).values
        kalman_zscore = residuals / (roll_std + 1e-9)

        result = pd.DataFrame({
            "kalman_price":    kalman_price,
            "kalman_velocity": kalman_velocity,
            "kalman_zscore":   kalman_zscore,
            "kalman_gain":     gains[:, 0],   # price component gain
        }, index=close.index)

        self._states = states
        self._gains  = gains
        self._trained = True
        self._trained_at = datetime.utcnow()

        logger.info(f"✅ KalmanTrendFilter: Filtered {len(close)} bars.")
        return result

    def get_features(self, close: pd.Series) -> Dict[str, pd.Series]:
        """Convenience wrapper — returns dict of feature series for FeatureEngineer."""
        df = self.fit_predict(close)
        return {
            "kalman_price":    df["kalman_price"],
            "kalman_velocity": df["kalman_velocity"],
            "kalman_zscore":   df["kalman_zscore"],
            "kalman_gain":     df["kalman_gain"],
        }

    def predict_next(self, close: pd.Series) -> Dict[str, float]:
        """
        One-step ahead prediction for the next bar.

        Returns:
            {predicted_price, predicted_velocity, uncertainty}
        """
        df = self.fit_predict(close)
        last_state = self._states[-1]
        x_pred = self.F @ last_state

        return {
            "predicted_price":    float(x_pred[0]),
            "predicted_velocity": float(x_pred[1]),
            "current_zscore":     float(df["kalman_zscore"].iloc[-1]),
            "kalman_gain":        float(df["kalman_gain"].iloc[-1]),
            "signal":             "BUY" if x_pred[1] > 0 else ("SELL" if x_pred[1] < 0 else "HOLD"),
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type":       "KalmanTrendFilter",
            "version":          self.VERSION,
            "process_noise":    self.Q,
            "observation_noise": self.R,
            "trained":          self._trained,
            "trained_at":       self._trained_at.isoformat() if self._trained_at else None,
            "state_dim":        2,
            "obs_dim":          1,
            "features_produced": ["kalman_price", "kalman_velocity", "kalman_zscore", "kalman_gain"],
        }


class KalmanRegressionFilter:
    """
    Kalman Filter for dynamic linear regression (rolling beta estimation).

    Models:  y_t = alpha_t + beta_t * x_t + epsilon_t
    Where:   alpha, beta evolve as random walks.

    Primary use: Dynamic hedge ratio, spread trading, cross-asset beta.
    """

    def __init__(self, delta: float = 1e-4, ve: float = 1e-3):
        """
        Args:
            delta: State covariance growth per step (process noise).
                   Higher → faster beta adaptation.
            ve:    Observation noise variance.
        """
        self.delta = delta
        self.ve    = ve
        self._theta = None   # [alpha, beta]
        self._P     = None   # State covariance

    def fit_predict(self, y: pd.Series, x: pd.Series) -> pd.DataFrame:
        """
        Compute rolling dynamic alpha and beta using Kalman filter.

        Args:
            y: Dependent variable (e.g., BANKNIFTY returns)
            x: Independent variable (e.g., NIFTY returns)

        Returns:
            DataFrame: {alpha, beta, spread, hedge_ratio}
        """
        n = min(len(y), len(x))
        y_vals = y.values[:n].astype(np.float64)
        x_vals = x.values[:n].astype(np.float64)

        # Initialize
        theta = np.zeros(2)          # [alpha, beta]
        P = self.delta / (1 - self.delta) * np.eye(2)

        Q = self.delta / (1 - self.delta) * np.eye(2)  # process noise

        alphas = np.zeros(n)
        betas  = np.zeros(n)
        spreads= np.zeros(n)

        for t in range(n):
            x_t = np.array([1.0, x_vals[t]])

            # Predict
            P_pred = P + Q

            # Update
            yhat    = x_t @ theta
            innov   = y_vals[t] - yhat
            S       = x_t @ P_pred @ x_t.T + self.ve
            K       = P_pred @ x_t.T / S
            theta   = theta + K * innov
            P       = (np.eye(2) - np.outer(K, x_t)) @ P_pred

            alphas[t]  = theta[0]
            betas[t]   = theta[1]
            spreads[t] = innov

        idx = y.index[:n]
        spread_series = pd.Series(spreads, index=idx)
        spread_std    = spread_series.rolling(20).std()
        spread_zscore = spread_series / (spread_std + 1e-9)

        return pd.DataFrame({
            "kalman_alpha":        alphas,
            "kalman_beta":         betas,
            "kalman_spread":       spreads,
            "kalman_spread_zscore": spread_zscore.values,
        }, index=idx)


# ── Singleton instances ───────────────────────────────────────────────────────
kalman_trend    = KalmanTrendFilter(process_noise=1e-4, observation_noise=1e-2)
kalman_regression = KalmanRegressionFilter(delta=1e-4, ve=1e-3)
