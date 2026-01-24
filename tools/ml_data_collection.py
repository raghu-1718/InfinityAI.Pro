"""
ML Data Collection Pipeline for InfinityAI.Pro
Fetches historical data for NIFTY, BANKNIFTY, FINNIFTY, SENSEX, GOLD, CRUDEOIL
Calculates technical indicators and stores in GCS
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import storage
import json
import ta  # Technical Analysis library

# Symbol mappings
SYMBOLS = {
    'NIFTY': '^NSEI',
    'BANKNIFTY': '^NSEBANK',
    'FINNIFTY': 'NIFTY_FIN_SERVICE.NS',
    'SENSEX': '^BSESN',
    'GOLD': 'GC=F',
    'CRUDEOIL': 'CL=F'
}

GCS_BUCKET = 'galvanic-pulsar-482815-h0-ml-models'
PROJECT_ID = 'galvanic-pulsar-482815-h0'

def calculate_technical_indicators(df):
    """Calculate comprehensive technical indicators"""
    print("  Calculating technical indicators...")
    
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
    
    # ATR (Average True Range)
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
    df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # Volatility
    df['volatility_20'] = df['returns'].rolling(window=20).std()
    
    return df

def fetch_and_process_symbol(symbol_name, yf_symbol, years=3):
    """Fetch data for a single symbol and calculate indicators"""
    print(f"\nProcessing {symbol_name}...")
    
    try:
        # Fetch data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        print(f"  Fetching data from {start_date.date()} to {end_date.date()}...")
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if df.empty:
            print(f"  ERROR: No data retrieved for {symbol_name}")
            return None
        
        print(f"  Retrieved {len(df)} days of data")
        
        # Calculate indicators
        df = calculate_technical_indicators(df)
        
        # Drop NaN values
        df = df.dropna()
        
        print(f"  After processing: {len(df)} valid rows")
        
        # Add metadata
        df['symbol'] = symbol_name
        df['timestamp'] = df.index
        
        return df
        
    except Exception as e:
        print(f"  ERROR processing {symbol_name}: {e}")
        return None

def upload_to_gcs(df, symbol_name, bucket_name):
    """Upload processed data to GCS"""
    print(f"  Uploading to GCS...")
    
    try:
        # Explicitly set project
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        
        # Save as CSV
        csv_filename = f"training_data/{symbol_name}_3y_daily.csv"
        blob = bucket.blob(csv_filename)
        csv_data = df.to_csv(index=False)
        blob.upload_from_string(csv_data, content_type='text/csv')
        print(f"  Uploaded: gs://{bucket_name}/{csv_filename}")
        
        # Save metadata
        metadata = {
            'symbol': symbol_name,
            'rows': len(df),
            'start_date': str(df['timestamp'].min()),
            'end_date': str(df['timestamp'].max()),
            'features': list(df.columns),
            'generated_at': datetime.now().isoformat()
        }
        
        meta_filename = f"training_data/{symbol_name}_metadata.json"
        blob = bucket.blob(meta_filename)
        blob.upload_from_string(json.dumps(metadata, indent=2), content_type='application/json')
        
        return True
        
    except Exception as e:
        print(f"  ERROR uploading to GCS: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 80)
    print("ML Data Collection Pipeline - InfinityAI.Pro")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Target bucket: gs://{GCS_BUCKET}")
    print()
    
    results = {}
    
    for symbol_name, yf_symbol in SYMBOLS.items():
        df = fetch_and_process_symbol(symbol_name, yf_symbol, years=3)
        
        if df is not None:
            success = upload_to_gcs(df, symbol_name, GCS_BUCKET)
            results[symbol_name] = {
                'status': 'success' if success else 'upload_failed',
                'rows': len(df),
                'features': len(df.columns)
            }
        else:
            results[symbol_name] = {
                'status': 'fetch_failed',
                'rows': 0,
                'features': 0
            }
    
    # Summary
    print()
    print("=" * 80)
    print("DATA COLLECTION SUMMARY")
    print("=" * 80)
    for symbol, result in results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_icon} {symbol}: {result['status']} ({result['rows']} rows, {result['features']} features)")
    
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    print()
    print(f"Success Rate: {successful}/{len(SYMBOLS)} symbols ({successful/len(SYMBOLS)*100:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
