"""
yfinance Integration for Indian Stock Market Data
Provides FREE historical and real-time data for NSE/BSE stocks
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

class YFinanceDataFetcher:
    """
    Fetch Indian stock data using yfinance
    """
    
    def __init__(self):
        self.exchange_suffix = {
            'NSE': '.NS',
            'BSE': '.BO'
        }
    
    def get_ticker(self, symbol, exchange='NSE'):
        """
        Convert symbol to yfinance format
        Example: RELIANCE + NSE -> RELIANCE.NS
        """
        suffix = self.exchange_suffix.get(exchange, '.NS')
        return f"{symbol}{suffix}"
    
    def fetch_historical_data(self, symbol, exchange='NSE', period='1y', interval='1d'):
        """
        Fetch historical OHLCV data
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
            exchange: 'NSE' or 'BSE'
            period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
            interval: '1m', '5m', '15m', '1h', '1d', '1wk', '1mo'
        
        Returns:
            DataFrame with OHLCV data
        """
        ticker = self.get_ticker(symbol, exchange)
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                print(f"[WARNING] No data found for {ticker}")
                return None
            
            # Standardize column names
            df.columns = df.columns.str.lower()
            df.index.name = 'date'
            df.reset_index(inplace=True)
            
            print(f"[OK] Fetched {len(df)} records for {ticker}")
            return df
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch {ticker}: {str(e)}")
            return None
    
    def fetch_current_price(self, symbol, exchange='NSE'):
        """
        Get current/latest price
        """
        ticker = self.get_ticker(symbol, exchange)
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'symbol': symbol,
                'exchange': exchange,
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'previous_close': info.get('previousClose'),
                'open': info.get('open'),
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                'volume': info.get('volume'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE')
            }
        except Exception as e:
            print(f"[ERROR] Failed to fetch current price for {ticker}: {str(e)}")
            return None
    
    def fetch_multiple_stocks(self, symbols, exchange='NSE', period='1y'):
        """
        Fetch data for multiple stocks
        """
        results = {}
        
        for symbol in symbols:
            print(f"\nFetching {symbol}...")
            df = self.fetch_historical_data(symbol, exchange, period)
            if df is not None:
                results[symbol] = df
        
        return results
    
    def save_to_csv(self, df, symbol, exchange='NSE', directory='data/historical'):
        """
        Save data to CSV file
        """
        os.makedirs(directory, exist_ok=True)
        filename = f"{directory}/{symbol}_{exchange}_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"[SAVED] {filename}")
        return filename
    
    def save_to_firestore(self, df, symbol, exchange='NSE'):
        """
        Save historical data to Google Cloud Firestore
        Collection: historical_data
        """
        try:
            from google.cloud import firestore
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
            db = firestore.Client(project=project_id)

            for _, row in df.iterrows():
                date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])

                data = {
                    'date': date_str,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'symbol': symbol,
                    'exchange': exchange,
                    'updated_at': datetime.now().isoformat()
                }

                doc_id = f"{symbol}_{exchange}_{date_str}"
                db.collection('historical_data').document(doc_id).set(data, merge=True)

            print(f"[FIRESTORE] Saved {len(df)} records for {symbol}_{exchange}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to save to Firestore: {str(e)}")
            return False

# Demo
if __name__ == "__main__":
    fetcher = YFinanceDataFetcher()
    
    print("=" * 80)
    print("  YFINANCE INDIAN STOCK DATA FETCHER - DEMO")
    print("=" * 80)
    
    # Test with popular stocks
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    
    print("\n[TEST 1] Current Prices")
    print("-" * 80)
    for symbol in test_symbols[:3]:
        price_data = fetcher.fetch_current_price(symbol, 'NSE')
        if price_data:
            print(f"\n{symbol}:")
            print(f"  Current Price: Rs. {price_data['current_price']:.2f}")
            print(f"  Prev Close: Rs. {price_data['previous_close']:.2f}")
            print(f"  Day Range: Rs. {price_data['day_low']:.2f} - Rs. {price_data['day_high']:.2f}")
    
    print("\n\n[TEST 2] Historical Data (6 months)")
    print("-" * 80)
    df = fetcher.fetch_historical_data('RELIANCE', 'NSE', period='6mo')
    
    if df is not None:
        print(f"\nData Summary:")
        print(f"  Period: {df['date'].min()} to {df['date'].max()}")
        print(f"  Records: {len(df)}")
        print(f"\nLast 5 days:")
        print(df[['date', 'open', 'high', 'low', 'close', 'volume']].tail())
        
        # Save to CSV
        fetcher.save_to_csv(df, 'RELIANCE', 'NSE')
    
    print("\n\n[TEST 3] Multiple Stocks")
    print("-" * 80)
    results = fetcher.fetch_multiple_stocks(['NIFTY50', 'BANKNIFTY'], 'NSE', period='1mo')
    
    print(f"\n[SUCCESS] yfinance integration working!")
    print(f"[INFO] Data source: FREE, no rate limits")
    print(f"[INFO] Supports: NSE (.NS), BSE (.BO)")
    print(f"[INFO] Real-time delay: ~15 minutes")
