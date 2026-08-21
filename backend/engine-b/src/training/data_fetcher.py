"""
Historical Market Data Fetcher
Fetches OHLCV data and calculates technical indicators for ML training
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    logging.warning("yfinance not available - using fallback data source")

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for ML features"""

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
    ) -> pd.DataFrame:
        """Moving Average Convergence Divergence"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return pd.DataFrame({
            'macd': macd,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        })

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2
    ) -> pd.DataFrame:
        """Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        return pd.DataFrame({
            'bb_middle': sma,
            'bb_upper': sma + (std * std_dev),
            'bb_lower': sma - (std * std_dev)
        })

    @staticmethod
    def calculate_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv


class MarketDataFetcher:
    """Fetch and prepare historical market data for ML training"""

    def __init__(self, symbol: str):
        self.symbol = symbol

    def fetch_historical_data(
        self,
        days: int = 730,  # 2 years default
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.

        Args:
            days: Number of historical days to fetch
            end_date: End date (defaults to today)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        if end_date is None:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching {days} days of data for {self.symbol} from {start_date.date()} to {end_date.date()}")

        # Use yfinance for NIFTY data
        if HAS_YFINANCE:
            return self._fetch_from_yfinance(start_date, end_date)
        else:
            raise ImportError("yfinance required for data fetching. Install: pip install yfinance")

    def _fetch_from_yfinance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch data from yfinance"""
        # Map symbol to yfinance ticker
        ticker_map = {
            'NIFTY': '^NSEI',
            'NIFTY50': '^NSEI',
            'BANKNIFTY': '^NSEBANK',
            'FINNIFTY': 'NIFTY_FIN_SERVICE.NS',
            'MIDCPNIFTY': '^NSEMDCP50',
            'SENSEX': '^BSESN',
            'BSESN': '^BSESN'
        }

        ticker = ticker_map.get(self.symbol, self.symbol)

        logger.info(f"Fetching from yfinance: {ticker}")

        # Download data
        data = yf.download(
            ticker,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False
        )

        if data.empty:
            raise ValueError(f"No data returned for {ticker}")

        # Flatten MultiIndex columns if present (yfinance can return MultiIndex)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # Prepare DataFrame - extract numpy arrays to avoid index alignment issues
        df = pd.DataFrame({
            'date': data.index.to_numpy(),
            'open': data['Open'].to_numpy(),
            'high': data['High'].to_numpy(),
            'low': data['Low'].to_numpy(),
            'close': data['Close'].to_numpy(),
            'volume': data['Volume'].to_numpy()
        })

        df.reset_index(drop=True, inplace=True)
        df['date'] = pd.to_datetime(df['date'])

        logger.info(f"Fetched {len(df)} rows")

        return df

    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators as ML features.

        Returns:
            DataFrame with additional columns for technical indicators
        """
        df = data.copy()

        logger.info("Calculating technical indicators...")

        # RSI
        df['rsi'] = TechnicalIndicators.calculate_rsi(df['close'])

        # MACD
        macd_df = TechnicalIndicators.calculate_macd(df['close'])
        df['macd'] = macd_df['macd'].values
        df['macd_signal'] = macd_df['macd_signal'].values
        df['macd_histogram'] = macd_df['macd_histogram'].values

        # Bollinger Bands
        bb_df = TechnicalIndicators.calculate_bollinger_bands(df['close'])
        df['bb_middle'] = bb_df['bb_middle'].values
        df['bb_upper'] = bb_df['bb_upper'].values
        df['bb_lower'] = bb_df['bb_lower'].values

        # ATR
        df['atr'] = TechnicalIndicators.calculate_atr(df['high'], df['low'], df['close'])

        # OBV
        df['obv'] = TechnicalIndicators.calculate_obv(df['close'], df['volume'])

        # Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()

        # Price momentum
        df['momentum_5'] = df['close'].pct_change(periods=5)
        df['momentum_10'] = df['close'].pct_change(periods=10)
        df['momentum_20'] = df['close'].pct_change(periods=20)

        # Volatility
        df['volatility_20'] = df['close'].rolling(window=20).std()

        # Volume features
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        # Drop NaN rows (from indicator calculations)
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)

        logger.info(f"Added {len(df.columns) - 6} technical indicators")
        logger.info(f"Final dataset: {len(df)} rows, {len(df.columns)} columns")

        return df

    def prepare_training_data(
        self,
        days: int = 730,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Complete pipeline: fetch data + add indicators.

        Args:
            days: Number of historical days
            end_date: End date

        Returns:
            DataFrame ready for ML training
        """
        # Fetch raw data
        raw_data = self.fetch_historical_data(days, end_date)

        # Add technical indicators
        training_data = self.add_technical_indicators(raw_data)

        # Validate
        if len(training_data) < 200:
            raise ValueError(f"Insufficient data: {len(training_data)} rows (need at least 200)")

        logger.info(f"Training data prepared: {len(training_data)} samples")

        return training_data


# Convenience function
def get_training_data(
    symbol: str,
    days: int = 730
) -> pd.DataFrame:
    """
    Quick helper to get training data.

    Example:
        >>> data = get_training_data("NIFTY", days=730)
        >>> print(data.columns)
        >>> print(len(data))
    """
    fetcher = MarketDataFetcher(symbol)
    return fetcher.prepare_training_data(days=days)
