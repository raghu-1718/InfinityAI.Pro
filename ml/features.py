"""
Feature Engineering for XGBoost Trading Model
Converts OHLCV data to ML-ready features using technical indicators
"""
import pandas as pd
import numpy as np

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    print("⚠️ TA-Lib not available - using fallback calculations")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build ML features from OHLCV data
    
    Args:
        df: DataFrame with columns: open, high, low, close, volume
    
    Returns:
        DataFrame with features and target column
    """
    df = df.copy()
    
    # Ensure required columns exist
    required = ['open', 'high', 'low', 'close', 'volume']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Technical Indicators
    if HAS_TALIB:
        df['rsi_14'] = talib.RSI(df['close'], timeperiod=14)
        df['ema_10'] = talib.EMA(df['close'], timeperiod=10)
        df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        df['macd'], df['macd_signal'], _ = talib.MACD(df['close'])
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'])
    else:
        # Fallback calculations (manual)
        df['rsi_14'] = _calculate_rsi(df['close'], 14)
        df['ema_10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['atr'] = _calculate_atr(df['high'], df['low'], df['close'], 14)
    
    # Price-based features
    df['return_1'] = df['close'].pct_change(1)
    df['return_5'] = df['close'].pct_change(5)
    df['return_10'] = df['close'].pct_change(10)
    
    # Volume features
    df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # Volatility
    df['volatility_20'] = df['return_1'].rolling(20).std()
    
    # Target: Next candle direction (1 = up, 0 = down)
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    # Drop rows with NaN values
    df.dropna(inplace=True)
    
    return df


def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Manual RSI calculation"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Manual ATR calculation"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


if __name__ == "__main__":
    # Test with sample data
    sample = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    result = build_features(sample)
    print(f"Features created: {len(result.columns)} columns")
    print(f"Rows after processing: {len(result)}")
    print(f"Target distribution: {result['target'].value_counts()}")
