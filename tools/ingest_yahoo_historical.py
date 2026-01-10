#!/usr/bin/env python3
"""
Yahoo Finance Historical Data Ingestion
Fetches OHLCV data for Indian indices and commodities
Uploads to Google Cloud Storage
"""

import yfinance as yf
import pandas as pd
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from google.cloud import storage
from io import StringIO
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Yahoo Finance ticker mapping for Indian indices/commodities
SYMBOL_MAP = {
    'NIFTY': '^NSEI',           # NIFTY 50
    'BANKNIFTY': '^NSEBANK',    # Bank Nifty
    'FINNIFTY': '^CNXIT',       # Nifty Financial Services (Finnifty proxy)
    'SENSEX': '^BSESN',         # BSE Sensex
    'GOLD': 'GC=F',             # Gold Futures
    'CRUDEOIL': 'CL=F'          # WTI Crude Oil Futures
}

# Interval mapping (Yahoo Finance uses 1m, 5m, 15m, 30m, 1h, 1d)
INTERVAL_MAP = {
    '1m': '1m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h',
    '1d': '1d'
}

# Period mapping
PERIOD_MAP = {
    '6m': '6mo',
    '1y': '1y',
    '3y': '3y',
    '5y': '5y'
}


class YahooHistoricalClient:
    """Async client for fetching Yahoo Finance historical data"""
    
    def __init__(self, bucket_name: str = 'infinityai-backtesting-data'):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self.session_count = 0
        self.total_records = 0
        
    async def fetch_historical(
        self, 
        symbol: str, 
        interval: str = '1d', 
        period: str = '1y'
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data from Yahoo Finance
        
        Args:
            symbol: Symbol name (NIFTY, BANKNIFTY, etc.)
            interval: Time interval (1d, 1h, 15m, etc.)
            period: Period (6m, 1y, 3y, etc.)
            
        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        if symbol not in SYMBOL_MAP:
            logger.warning(f"❌ Symbol {symbol} not in SYMBOL_MAP")
            return None
            
        ticker = SYMBOL_MAP[symbol]
        yahoo_interval = INTERVAL_MAP.get(interval, '1d')
        yahoo_period = PERIOD_MAP.get(period, '1y')
        
        try:
            logger.info(f"Fetching {symbol} {interval} {period} ({yahoo_period}) from Yahoo Finance...")
            
            # Fetch data using yfinance
            data = yf.download(
                ticker,
                period=yahoo_period,
                interval=yahoo_interval,
                progress=False,
                prepost=False
            )
            
            if data.empty:
                logger.warning(f"❌ {symbol} {interval} {period}: No data returned")
                return None
            
            # Ensure we have required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_cols):
                logger.warning(f"❌ {symbol}: Missing required columns")
                return None
            
            # Rename columns to match expected format
            data = data[required_cols].copy()
            data.columns = ['open', 'high', 'low', 'close', 'volume']
            data['timestamp'] = data.index
            data = data.reset_index(drop=True)
            
            logger.info(f"✅ {symbol} {interval} {period}: {len(data)} candles fetched")
            self.total_records += len(data)
            return data
            
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol} {interval} {period}: {str(e)}")
            return None
    
    async def upload_to_gcs(
        self, 
        symbol: str, 
        interval: str, 
        period: str,
        data: pd.DataFrame
    ) -> bool:
        """
        Upload CSV to Google Cloud Storage
        
        Args:
            symbol: Symbol name
            interval: Time interval
            period: Period
            data: DataFrame to upload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create blob name: symbol/SYMBOL_INTERVAL_PERIOD.csv
            blob_name = f"{symbol}/{symbol}_{interval}_{period}.csv"
            blob = self.bucket.blob(blob_name)
            
            # Convert DataFrame to CSV
            csv_buffer = StringIO()
            data.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            # Upload to GCS
            blob.upload_from_string(
                csv_content,
                content_type='text/csv'
            )
            
            logger.info(f"✅ Uploaded {symbol}/{interval}/{period} to gs://{self.bucket_name}/{blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error uploading {symbol} {interval} {period}: {str(e)}")
            return False
    
    async def fetch_and_upload(
        self,
        symbol: str,
        interval: str,
        period: str
    ) -> Tuple[bool, Optional[pd.DataFrame]]:
        """
        Fetch historical data and upload to GCS
        
        Returns:
            (success: bool, data: DataFrame)
        """
        data = await self.fetch_historical(symbol, interval, period)
        
        if data is not None:
            success = await self.upload_to_gcs(symbol, interval, period, data)
            return success, data
        
        return False, None


async def fetch_all_data(
    symbols: List[str],
    intervals: List[str],
    periods: List[str],
    bucket: str = 'infinityai-backtesting-data'
) -> Dict[str, Tuple[bool, Optional[pd.DataFrame]]]:
    """
    Fetch all symbol-interval-period combinations
    
    Returns:
        Dictionary with results for each combination
    """
    client = YahooHistoricalClient(bucket_name=bucket)
    results = {}
    
    total_requests = len(symbols) * len(intervals) * len(periods)
    completed = 0
    
    logger.info(f"\n╔══════════════════════════════════════════════════════════╗")
    logger.info(f"║        YAHOO FINANCE HISTORICAL DATA INGESTION          ║")
    logger.info(f"╚══════════════════════════════════════════════════════════╝")
    logger.info(f"\nConfiguration:")
    logger.info(f"  Symbols:    {', '.join(symbols)}")
    logger.info(f"  Intervals:  {', '.join(intervals)}")
    logger.info(f"  Periods:    {', '.join(periods)}")
    logger.info(f"  GCS Bucket: gs://{bucket}")
    logger.info(f"  Total Requests: {total_requests}\n")
    
    # Fetch sequentially to avoid rate limiting
    for symbol in symbols:
        for interval in intervals:
            for period in periods:
                key = f"{symbol}_{interval}_{period}"
                success, data = await client.fetch_and_upload(symbol, interval, period)
                results[key] = (success, data)
                completed += 1
                
                status = "✅" if success else "❌"
                logger.info(f"[{completed}/{total_requests}] {status} {key}")
                
                # Small delay between requests
                await asyncio.sleep(0.5)
    
    # Print summary
    successful = sum(1 for s, _ in results.values() if s)
    logger.info(f"\n╔══════════════════════════════════════════════════════════╗")
    logger.info(f"║                    INGESTION COMPLETE                    ║")
    logger.info(f"╚══════════════════════════════════════════════════════════╝")
    logger.info(f"\nResults:")
    logger.info(f"  Total Requests: {total_requests}")
    logger.info(f"  Successful: {successful} ✅")
    logger.info(f"  Failed: {total_requests - successful} ❌")
    logger.info(f"  Total Records Ingested: {client.total_records:,}")
    logger.info(f"  Location: gs://{bucket}/")
    
    return results


async def get_current_market_status(symbols: List[str] = None) -> Dict[str, Dict]:
    """Get current market status for symbols"""
    if symbols is None:
        symbols = list(SYMBOL_MAP.keys())
    
    status = {}
    logger.info(f"\n╔══════════════════════════════════════════════════════════╗")
    logger.info(f"║          📊 CURRENT MARKET STATUS (Yahoo Finance)       ║")
    logger.info(f"╚══════════════════════════════════════════════════════════╝\n")
    
    for symbol in symbols:
        if symbol not in SYMBOL_MAP:
            continue
            
        try:
            ticker = SYMBOL_MAP[symbol]
            data = yf.Ticker(ticker)
            hist = data.history(period='5d')  # Get 5 days for trend
            
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                high = hist['High'].iloc[-1]
                low = hist['Low'].iloc[-1]
                
                change = current - open_price
                change_pct = (change / open_price * 100) if open_price > 0 else 0
                
                trend_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100) if hist['Close'].iloc[0] > 0 else 0
                
                status_emoji = "🟢 UP" if change >= 0 else "🔴 DOWN"
                
                status[symbol] = {
                    'price': float(current),
                    'change': float(change),
                    'change_pct': float(change_pct),
                    'high': float(high),
                    'low': float(low),
                    'open': float(open_price),
                    '5d_trend': float(trend_change)
                }
                
                logger.info(f"{symbol:12} │ Price: {current:10.2f} │ {status_emoji:8} {change:+7.2f} ({change_pct:+6.2f}%)")
                logger.info(f"{'':12} │ High: {high:10.2f} │ Low: {low:10.2f} │ 5D Trend: {trend_change:+6.2f}%")
                logger.info()
        except Exception as e:
            logger.warning(f"{symbol:12} │ ⚠️  Error: {str(e)[:40]}")
    
    return status


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Fetch historical data from Yahoo Finance')
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'GOLD', 'CRUDEOIL'],
        help='Symbols to fetch'
    )
    parser.add_argument(
        '--intervals',
        nargs='+',
        default=['1d', '1h', '15m'],
        help='Time intervals'
    )
    parser.add_argument(
        '--periods',
        nargs='+',
        default=['6m', '1y', '3y'],
        help='Periods to fetch'
    )
    parser.add_argument(
        '--bucket',
        default='infinityai-backtesting-data',
        help='GCS bucket name'
    )
    parser.add_argument(
        '--market-status-only',
        action='store_true',
        help='Only show market status, do not fetch data'
    )
    
    args = parser.parse_args()
    
    # Show market status
    await get_current_market_status(args.symbols)
    
    if args.market_status_only:
        logger.info("\n✅ Market status retrieved. Exiting.")
        return
    
    # Fetch and upload data
    results = await fetch_all_data(
        symbols=args.symbols,
        intervals=args.intervals,
        periods=args.periods,
        bucket=args.bucket
    )
    
    logger.info("\n✅ Data ingestion complete. Ready for backtesting!")


if __name__ == '__main__':
    asyncio.run(main())
