"""
InfinityAI.Pro - Technical Analysis Feature Engineering
Generates ML features from market data for trading signal prediction
"""

import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    Advanced feature engineering for trading ML models
    Generates technical indicators and derived features
    """

    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=window).mean()

    @staticmethod
    def calculate_ema(prices: pd.Series, span: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """Moving Average Convergence Divergence"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        window: int = 20,
        num_std: float = 2.0
    ) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()

        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)

        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }

    @staticmethod
    def calculate_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """Average True Range (Volatility)"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    @staticmethod
    def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """Price Momentum"""
        return prices.diff(period)

    @staticmethod
    def calculate_rate_of_change(prices: pd.Series, period: int = 10) -> pd.Series:
        """Rate of Change (ROC)"""
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100

    @staticmethod
    def calculate_stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=3).mean()

        return {'%K': k, '%D': d}

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    def generate_all_features(
        self,
        df: pd.DataFrame,
        price_col: str = 'close',
        volume_col: Optional[str] = 'volume'
    ) -> pd.DataFrame:
        """
        Generate comprehensive feature set from OHLCV data

        Args:
            df: DataFrame with OHLCV data
            price_col: Column name for close price
            volume_col: Column name for volume (optional)

        Returns:
            DataFrame with all calculated features
        """
        features = df.copy()
        prices = df[price_col]

        try:
            # Moving Averages
            features['sma_5'] = self.calculate_sma(prices, 5)
            features['sma_10'] = self.calculate_sma(prices, 10)
            features['sma_20'] = self.calculate_sma(prices, 20)
            features['sma_50'] = self.calculate_sma(prices, 50)

            features['ema_5'] = self.calculate_ema(prices, 5)
            features['ema_10'] = self.calculate_ema(prices, 10)
            features['ema_20'] = self.calculate_ema(prices, 20)

            # RSI
            features['rsi_14'] = self.calculate_rsi(prices, 14)
            features['rsi_7'] = self.calculate_rsi(prices, 7)

            # MACD
            macd = self.calculate_macd(prices)
            features['macd'] = macd['macd']
            features['macd_signal'] = macd['signal']
            features['macd_histogram'] = macd['histogram']

            # Bollinger Bands
            bb = self.calculate_bollinger_bands(prices)
            features['bb_upper'] = bb['upper']
            features['bb_middle'] = bb['middle']
            features['bb_lower'] = bb['lower']
            features['bb_width'] = (bb['upper'] - bb['lower']) / bb['middle']
            features['bb_position'] = (prices - bb['lower']) / (bb['upper'] - bb['lower'])

            # Momentum
            features['momentum_10'] = self.calculate_momentum(prices, 10)
            features['momentum_20'] = self.calculate_momentum(prices, 20)

            # Rate of Change
            features['roc_10'] = self.calculate_rate_of_change(prices, 10)
            features['roc_20'] = self.calculate_rate_of_change(prices, 20)

            # Volatility
            if 'high' in df.columns and 'low' in df.columns:
                features['atr_14'] = self.calculate_atr(df['high'], df['low'], prices, 14)

                # Stochastic
                stoch = self.calculate_stochastic(df['high'], df['low'], prices)
                features['stoch_k'] = stoch['%K']
                features['stoch_d'] = stoch['%D']

            # Volume-based features
            if volume_col and volume_col in df.columns:
                features['obv'] = self.calculate_obv(prices, df[volume_col])
                features['volume_sma_20'] = df[volume_col].rolling(window=20).mean()
                features['volume_ratio'] = df[volume_col] / features['volume_sma_20']

            # Price patterns
            features['daily_return'] = prices.pct_change()
            features['log_return'] = np.log(prices / prices.shift(1))

            # Trend indicators
            features['trend_5_20'] = features['sma_5'] - features['sma_20']
            features['trend_10_50'] = features['sma_10'] - features['sma_50']

            # Drop NaN values
            features = features.fillna(method='bfill').fillna(0)

            logger.info(f"Generated {len(features.columns)} features")

        except Exception as e:
            logger.error(f"Feature generation error: {e}")
            raise

        return features

    def get_feature_columns(self) -> List[str]:
        """Return list of all feature column names"""
        return [
            'sma_5', 'sma_10', 'sma_20', 'sma_50',
            'ema_5', 'ema_10', 'ema_20',
            'rsi_14', 'rsi_7',
            'macd', 'macd_signal', 'macd_histogram',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
            'momentum_10', 'momentum_20',
            'roc_10', 'roc_20',
            'atr_14',
            'stoch_k', 'stoch_d',
            'obv', 'volume_sma_20', 'volume_ratio',
            'daily_return', 'log_return',
            'trend_5_20', 'trend_10_50'
        ]

    def select_top_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int = 10
    ) -> List[str]:
        """
        Select top N features using feature importance

        Args:
            X: Feature DataFrame
            y: Target variable
            n_features: Number of top features to select

        Returns:
            List of top feature names
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.feature_selection import SelectKBest, f_classif

        try:
            # Use Random Forest feature importance
            rf = RandomForestClassifier(n_estimators=50, random_state=42)
            rf.fit(X, y)

            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': rf.feature_importances_
            }).sort_values('importance', ascending=False)

            top_features = feature_importance.head(n_features)['feature'].tolist()

            logger.info(f"Selected top {n_features} features: {top_features}")

            return top_features

        except Exception as e:
            logger.error(f"Feature selection error: {e}")
            return list(X.columns[:n_features])


# Global instance
feature_engineer = FeatureEngineer()
