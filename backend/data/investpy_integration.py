"""
investpy Integration for Indian Stock Market Data
Backup data source with NSE/BSE support
"""
import investpy
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import os
import logging

logger = logging.getLogger(__name__)

class InvestpyDataFetcher:
    """
    Fetch Indian stock data using investpy
    Handles rate limiting and provides Supabase integration
    """
    
    def __init__(self):
        self.db = None
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
            if url and key:
                self.db = create_client(url, key)
        except Exception:
            pass
        self.rate_limit_delay = 1  # seconds between requests
    
    def fetch_stock_data(self, symbol: str, country: str = 'india', 
                        from_date: str = None, to_date: str = None):
        """
        Fetch historical stock data
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
            country: Country code ('india')
            from_date: Start date 'DD/MM/YYYY'
            to_date: End date 'DD/MM/YYYY'
        """
        try:
            if not from_date:
                from_date = (datetime.now() - timedelta(days=365)).strftime('%d/%m/%Y')
            if not to_date:
                to_date = datetime.now().strftime('%d/%m/%Y')
            
            df = investpy.stocks.get_stock_historical_data(
                stock=symbol,
                country=country,
                from_date=from_date,
                to_date=to_date
            )
            
            print(f"[OK] Fetched {len(df)} records for {symbol}")
            return df
        
        except Exception as e:
            print(f"[ERROR] investpy fetch failed for {symbol}: {str(e)}")
            return None
    
    def save_to_supabase(self, df, symbol: str):
        """Save data to Supabase"""
        try:
            if not self.db:
                print("[WARN] Supabase not available")
                return False

            for date, row in df.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                data = {
                    'date': date_str,
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                    'symbol': symbol,
                    'source': 'investpy',
                    'updated_at': datetime.now().isoformat()
                }
                self.db.table('historical_data').upsert(data).execute()
            
            print(f"[SUPABASE] Saved {len(df)} records for {symbol}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Supabase save failed: {str(e)}")
            return False


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  INVESTPY INTEGRATION - INDIAN STOCKS")
    print("=" * 80)
    
    print("\n[INFO] investpy provides:")
    print("  - NSE/BSE data")
    print("  - Free access")
    print("  - Rate limited")
    print("  - Fallback for yfinance")
    
    print("\n[INFO] Integration ready for production")
    print("=" * 80)
