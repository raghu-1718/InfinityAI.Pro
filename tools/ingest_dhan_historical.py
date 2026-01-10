#!/usr/bin/env python3
"""
InfinityAI.Pro - Dhan Historical Data Ingestion Script
Fetches OHLCV data from Dhan API for backtesting across multiple symbols, timeframes, and date ranges
Stores data in Google Cloud Storage for later analysis

Usage:
    python tools/ingest_dhan_historical.py \
        --symbols NIFTY BANKNIFTY FINNIFTY \
        --intervals daily hourly 15min \
        --periods 6m 1y 3y \
        --bucket gs://infinityai-backtesting-data \
        --credentials-user-id 1101302170 (or provide DHAN_ACCESS_TOKEN/DHAN_CLIENT_ID)
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import csv
from dataclasses import dataclass, field, asdict

import aiohttp
import pandas as pd
from google.cloud import storage
from google.cloud import firestore

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class IngestConfig:
    """Configuration for data ingestion"""
    symbols: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "GOLD", "CRUDEOIL"])
    intervals: List[str] = field(default_factory=lambda: ["1d", "1h", "15m"])  # daily, hourly, 15-min
    periods: Dict[str, int] = field(default_factory=lambda: {"6m": 180, "1y": 365, "3y": 1095})  # days
    gcs_bucket: str = "infinityai-backtesting-data"
    dhan_access_token: Optional[str] = None
    dhan_client_id: Optional[str] = None
    credentials_user_id: Optional[str] = None
    max_concurrent: int = 5
    batch_size: int = 500  # candles per request


class DhanHistoricalClient:
    """Async client for fetching historical data from Dhan API"""
    
    BASE_URL = "https://api.dhan.co"
    
    # Symbol to Dhan Security ID mapping (NSE Equity)
    SYMBOL_MAP = {
        "NIFTY": "1333061140000000",  # NIFTY 50
        "BANKNIFTY": "1333061219000000",  # BANK NIFTY
        "FINNIFTY": "1333061221000000",  # FIN NIFTY
        "SENSEX": "1333060073000000",  # BSE SENSEX
        "GOLD": "1333062001000000",  # GOLD SPOT
        "CRUDEOIL": "1333061919000000",  # CRUDE OIL
    }
    
    # Interval mapping (Dhan API format)
    INTERVAL_MAP = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "1d": 1440,
    }
    
    def __init__(self, access_token: str, client_id: str, max_concurrent: int = 5):
        self.access_token = access_token
        self.client_id = client_id
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, endpoint: str, params: Dict) -> Dict:
        """Make async request to Dhan API with rate limiting"""
        async with self.semaphore:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Client-ID": self.client_id,
                "User-Agent": "InfinityAI-Backtester/1.0",
            }
            
            try:
                # Try v2 endpoint first, then fall back to v1
                for api_version in ["v2", "v1"]:
                    async with self.session.get(
                        f"{self.BASE_URL}/{api_version}/{endpoint}",
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 404 and api_version == "v2":
                            logger.debug(f"v2 endpoint not available, trying v1...")
                            continue
                        elif resp.status == 429:
                            logger.warning(f"Rate limited. Waiting 5s before retry...")
                            await asyncio.sleep(5)
                            return await self._request(endpoint, params)
                        else:
                            logger.error(f"API error {resp.status} on {api_version}: {await resp.text()}")
                
                return {}
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {endpoint}")
                return {}
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return {}
    
    async def get_historical_candles(
        self,
        symbol: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict]:
        """
        Fetch historical candles from Dhan API
        
        Args:
            symbol: Trading symbol (NIFTY, BANKNIFTY, etc.)
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 1d)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        
        Returns:
            List of OHLCV candles
        """
        if symbol not in self.SYMBOL_MAP:
            logger.error(f"Unknown symbol: {symbol}")
            return []
        
        if interval not in self.INTERVAL_MAP:
            logger.error(f"Unknown interval: {interval}")
            return []
        
        security_id = self.SYMBOL_MAP[symbol]
        interval_minutes = self.INTERVAL_MAP[interval]
        
        params = {
            "securityId": security_id,
            "interval": interval_minutes,
            "fromDate": from_date,
            "toDate": to_date,
            "pageNumber": 0,
        }
        
        all_candles = []
        page = 0
        
        while True:
            params["pageNumber"] = page
            
            logger.info(f"Fetching {symbol} {interval} page {page} ({from_date} to {to_date})...")
            
            response = await self._request("historical", params)
            
            if not response or "data" not in response:
                logger.warning(f"No data returned for {symbol} {interval} page {page}")
                break
            
            candles = response.get("data", {}).get("candles", [])
            
            if not candles:
                logger.info(f"No more candles for {symbol} {interval}")
                break
            
            all_candles.extend(candles)
            logger.info(f"  → Fetched {len(candles)} candles (total: {len(all_candles)})")
            
            # Check if more pages available
            if len(candles) < 500:  # Last page
                break
            
            page += 1
            await asyncio.sleep(0.5)  # Rate limiting
        
        return all_candles
    
    async def fetch_all(
        self,
        config: IngestConfig
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Fetch all symbol/interval/period combinations
        
        Returns: {symbol: {interval: {period: DataFrame}}}
        """
        results = {}
        today = datetime.now().date()
        
        for symbol in config.symbols:
            results[symbol] = {}
            
            for interval in config.intervals:
                results[symbol][interval] = {}
                
                for period_name, days in config.periods.items():
                    to_date = today.isoformat()
                    from_date = (today - timedelta(days=days)).isoformat()
                    
                    candles = await self.get_historical_candles(
                        symbol=symbol,
                        interval=interval,
                        from_date=from_date,
                        to_date=to_date,
                    )
                    
                    if candles:
                        # Convert to DataFrame
                        df = pd.DataFrame(candles)
                        
                        # Rename columns: Dhan API uses: timestamp, open, high, low, close, volume, openInterest
                        df.rename(columns={
                            "timestamp": "datetime",
                            "open": "open",
                            "high": "high",
                            "low": "low",
                            "close": "close",
                            "volume": "volume",
                            "openInterest": "oi",
                        }, inplace=True)
                        
                        # Ensure datetime is parsed
                        if "datetime" in df.columns:
                            df["datetime"] = pd.to_datetime(df["datetime"])
                            df.set_index("datetime", inplace=True)
                        
                        # Sort by datetime
                        df.sort_index(inplace=True)
                        
                        results[symbol][interval][period_name] = df
                        logger.info(f"✅ {symbol} {interval} {period_name}: {len(df)} candles")
                    else:
                        logger.warning(f"❌ {symbol} {interval} {period_name}: No data")
                    
                    await asyncio.sleep(1)  # Rate limiting between requests
        
        return results


class CloudStorageManager:
    """Manage data upload to Google Cloud Storage"""
    
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
    
    def upload_dataframe(
        self,
        df: pd.DataFrame,
        symbol: str,
        interval: str,
        period: str
    ) -> str:
        """Upload DataFrame to GCS as CSV"""
        
        # Create path: gs://bucket/data/SYMBOL/INTERVAL/PERIOD.csv
        path = f"data/{symbol}/{interval}/{period}.csv"
        blob = self.bucket.blob(path)
        
        # Convert to CSV in memory
        csv_data = df.to_csv()
        
        # Upload with gzip compression
        blob.upload_from_string(
            csv_data,
            content_type="text/csv",
        )
        
        gcs_uri = f"gs://{self.bucket.name}/{path}"
        logger.info(f"✅ Uploaded to {gcs_uri}")
        return gcs_uri
    
    def upload_metadata(self, metadata: Dict) -> str:
        """Upload ingestion metadata to GCS"""
        
        path = f"metadata/{datetime.now().isoformat().replace(':', '-')}_ingest.json"
        blob = self.bucket.blob(path)
        
        blob.upload_from_string(
            json.dumps(metadata, indent=2, default=str),
            content_type="application/json",
        )
        
        gcs_uri = f"gs://{self.bucket.name}/{path}"
        logger.info(f"✅ Metadata uploaded to {gcs_uri}")
        return gcs_uri


async def load_credentials_from_firestore(user_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Load Dhan credentials from Firestore (user_credentials collection)"""
    
    try:
        db = firestore.Client()
        doc = db.collection("user_credentials").document(user_id).get()
        
        if doc.exists:
            data = doc.to_dict()
            access_token = data.get("access_token")
            client_id = data.get("client_id")
            
            if access_token and client_id:
                logger.info(f"✅ Loaded credentials from Firestore for user {user_id}")
                return access_token, client_id
    except Exception as e:
        logger.warning(f"Could not load credentials from Firestore: {e}")
    
    return None, None


async def main():
    """Main ingestion workflow"""
    
    parser = argparse.ArgumentParser(
        description="Fetch historical data from Dhan API for backtesting"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "GOLD", "CRUDEOIL"],
        help="Symbols to fetch"
    )
    parser.add_argument(
        "--intervals",
        nargs="+",
        default=["1d", "1h", "15m"],
        help="Time intervals (1d, 1h, 15m, 30m, 5m, 1m)"
    )
    parser.add_argument(
        "--periods",
        nargs="+",
        default=["6m", "1y", "3y"],
        help="Date ranges (6m, 1y, 3y, etc.)"
    )
    parser.add_argument(
        "--bucket",
        default="infinityai-backtesting-data",
        help="GCS bucket for data storage"
    )
    parser.add_argument(
        "--credentials-user-id",
        help="Load Dhan credentials from Firestore for this user ID"
    )
    parser.add_argument(
        "--access-token",
        default=os.getenv("DHAN_ACCESS_TOKEN"),
        help="Dhan access token (or set DHAN_ACCESS_TOKEN env var)"
    )
    parser.add_argument(
        "--client-id",
        default=os.getenv("DHAN_CLIENT_ID"),
        help="Dhan client ID (or set DHAN_CLIENT_ID env var)"
    )
    
    args = parser.parse_args()
    
    # Load credentials
    access_token = args.access_token
    client_id = args.client_id
    
    if args.credentials_user_id:
        logger.info(f"Loading credentials from Firestore for user {args.credentials_user_id}...")
        access_token, client_id = await load_credentials_from_firestore(args.credentials_user_id)
    
    if not access_token or not client_id:
        logger.error("❌ Dhan credentials not provided. Use --access-token/--client-id or --credentials-user-id")
        sys.exit(1)
    
    # Build config
    periods = {}
    period_map = {"6m": 180, "1y": 365, "3y": 1095}
    for period in args.periods:
        if period in period_map:
            periods[period] = period_map[period]
    
    config = IngestConfig(
        symbols=args.symbols,
        intervals=args.intervals,
        periods=periods,
        gcs_bucket=args.bucket,
        dhan_access_token=access_token,
        dhan_client_id=client_id,
    )
    
    logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║          DHAN HISTORICAL DATA INGESTION                        ║
╚════════════════════════════════════════════════════════════════╝

Configuration:
  Symbols:    {', '.join(config.symbols)}
  Intervals:  {', '.join(config.intervals)}
  Periods:    {', '.join(config.periods.keys())}
  GCS Bucket: gs://{config.gcs_bucket}
  
Estimated Requests: {len(config.symbols) * len(config.intervals) * len(config.periods)}
Rate Limit: {config.max_concurrent} concurrent requests
    """)
    
    # Fetch data
    start_time = datetime.now()
    
    async with DhanHistoricalClient(access_token, client_id, config.max_concurrent) as client:
        results = await client.fetch_all(config)
    
    # Upload to GCS
    logger.info("\n📤 Uploading to Cloud Storage...")
    gcs_manager = CloudStorageManager(config.gcs_bucket)
    
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "symbols": config.symbols,
        "intervals": config.intervals,
        "periods": config.periods,
        "files_uploaded": 0,
        "total_candles": 0,
        "files": {}
    }
    
    for symbol in results:
        for interval in results[symbol]:
            for period, df in results[symbol][interval].items():
                if not df.empty:
                    gcs_uri = gcs_manager.upload_dataframe(df, symbol, interval, period)
                    
                    metadata["files_uploaded"] += 1
                    metadata["total_candles"] += len(df)
                    metadata["files"][f"{symbol}/{interval}/{period}"] = {
                        "uri": gcs_uri,
                        "rows": len(df),
                        "columns": list(df.columns),
                    }
    
    # Upload metadata
    metadata_uri = gcs_manager.upload_metadata(metadata)
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║                    INGESTION COMPLETE                          ║
╚════════════════════════════════════════════════════════════════╝

Summary:
  ✅ Files Uploaded: {metadata['files_uploaded']}
  ✅ Total Candles: {metadata['total_candles']:,}
  ✅ Duration: {elapsed:.1f}s
  ✅ Metadata: {metadata_uri}
  
Next Steps:
  1. Use backtester.py to load data from gs://{config.gcs_bucket}
  2. Run Engine-B signal generation on historical data
  3. Apply Engine-A risk calculations
  4. Execute backtests with Engine-C
  5. Generate performance reports
    """)


if __name__ == "__main__":
    asyncio.run(main())
