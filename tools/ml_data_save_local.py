"""
Save ML data locally for upload via gcloud CLI
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import ta
import os

SYMBOLS = {
    'NIFTY': '^NSEI',
    'BANKNIFTY': '^NSEBANK',
    'FINNIFTY': 'NIFTY_FIN_SERVICE.NS',
    'SENSEX': '^BSESN',
    'GOLD': 'GC=F',
    'CRUDEOIL': 'CL=F'
}

def calculate_technical_indicators(df):
    """Calculate comprehensive technical indicators"""
    # Trend Indicators
    df['sma_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['sma_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['sma_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    df['ema_12'] = ta.trend.ema_indicator(df['Close'], window=12)
    df['ema_26'] = ta.trend.ema_indicator(df['Close'], window=26)
    
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    # RSI
    df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['bb_high'] = bollinger.bollinger_hband()
    df['bb_mid'] = bollinger.bollinger_mavg()
    df['bb_low'] = bollinger.bollinger_lband()
    df['bb_width'] = bollinger.bollinger_wband()
    
    # ATR
    df['atr'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
    
    # Stochastic
    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    
    # Volume indicators
    df['volume_sma'] = df['Volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['Volume'] / df['volume_sma']
    
    # Price changes
    df['returns'] = df['Close'].pct_change()
    df['log_returns'] = pd.Series(df['Close']).apply(lambda x: x).pct_change()
    
    # Volatility
    df['volatility_20'] = df['returns'].rolling(window=20).std()
    
    return df

# Create output directory
os.makedirs('ml_data_local', exist_ok=True)

print("Collecting and processing ML training data...")
print("=" * 60)

for symbol_name, yf_symbol in SYMBOLS.items():
    print(f"\nProcessing {symbol_name}...")
    
    # Fetch data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)
    
    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(start=start_date, end=end_date, interval='1d')
    
    if df.empty:
        print(f"  [SKIP] No data")
        continue
    
    print(f"  Retrieved {len(df)} days")
    
    # Calculate indicators
    df = calculate_technical_indicators(df)
    df = df.dropna()
    
    print(f"  Processed {len(df)} valid rows")
    
    # Add metadata
    df['symbol'] = symbol_name
    df['timestamp'] = df.index
    
    # Save locally
    filename = f'ml_data_local/{symbol_name}_3y_daily.csv'
    df.to_csv(filename, index=False)
    print(f"  [OK] Saved: {filename}")

print("\n" + "=" * 60)
print("Data collection complete!")
print("Files saved in: ml_data_local/")
print("\nTo upload to GCS, run:")
print("gcloud storage cp ml_data_local/*.csv gs://galvanic-pulsar-482815-h0-ml-models/training_data/")
