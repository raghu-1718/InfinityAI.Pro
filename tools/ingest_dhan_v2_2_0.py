#!/usr/bin/env python3
"""
InfinityAI.Pro - Dhan v2.2.0 API Integration (Pre-release)
Updated to use new DhanContext authentication pattern and /charts/historical endpoint

Key Changes from v2.1.0:
  1. DhanContext-based authentication (secure context pattern)
  2. Direct imports: from dhanhq import MarketFeed, OrderUpdate, FullDepth
  3. Endpoints: /charts/historical (daily), /charts/intraday (minute)
  4. 200-level full market depth support
  5. Expired options data support
  6. Super Orders for risk management

Installation:
  pip install --pre dhanhq>=2.2.0

Usage:
  python tools/ingest_dhan_v2_2_0.py \
    --credentials-file .dhan_credentials_temp.json \
    --symbols NIFTY BANKNIFTY FINNIFTY SENSEX GOLD CRUDEOIL \
    --intervals 1d 1h 15m \
    --periods 6m 1y 3y \
    --bucket gs://infinityai-backtesting-data
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

import aiohttp
import pandas as pd
from google.cloud import storage

# Try importing dhanhq v2.2.0 - new pattern
try:
    from dhanhq import DhanContext, dhanhq
    DHAN_V2_2_0 = True
except ImportError:
    logger_init = logging.getLogger(__name__)
    logger_init.warning("dhanhq v2.2.0 not installed. Install: pip install --pre dhanhq>=2.2.0")
    DHAN_V2_2_0 = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class DhanSecurityMapping:
    """Mapping of trading symbols to Dhan Security IDs (v2.2.0)"""
    # Format: Symbol -> (exchange_segment, security_id, instrument_type)
    NSE_EQUITY = {
        "NIFTY": ("NSE_EQ", "1333", "INDEX"),      # NIFTY 50 Index
        "BANKNIFTY": ("NSE_EQ", "11915", "INDEX"),  # BANK NIFTY Index
        "FINNIFTY": ("NSE_EQ", "13748", "INDEX"),   # FIN NIFTY Index
        "SENSEX": ("BSE_EQ", "1", "INDEX"),         # BSE SENSEX Index
    }

    COMMODITIES = {
        "GOLD": ("MCX_COMM", "228", "FUTCOM"),      # Gold Futures (MCX)
        "CRUDEOIL": ("MCX_COMM", "226", "FUTCOM"),  # Crude Oil Futures (MCX)
    }

    @classmethod
    def get_security_id(cls, symbol: str) -> Optional[Tuple[str, str, str]]:
        """Get (exchange_segment, security_id, instrument_type) for symbol"""
        if symbol in cls.NSE_EQUITY:
            return cls.NSE_EQUITY[symbol]
        elif symbol in cls.COMMODITIES:
            return cls.COMMODITIES[symbol]
        return None


class Dhanv220Client:
    """
    Dhan v2.2.0 API Client
    Uses new DhanContext authentication pattern and /charts endpoints
    """

    # API Endpoints (v2)
    BASE_URL = "https://api.dhan.co/v2"
    HISTORICAL_ENDPOINT = "/charts/historical"  # Fixed: was /v2/historical
    INTRADAY_ENDPOINT = "/charts/intraday"

    # Supported intervals (in minutes)
    INTERVALS = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "1d": 1440,  # Daily
    }

    def __init__(self, client_id: str, access_token: str, max_concurrent: int = 3):
        """
        Initialize Dhan v2.2.0 client with DhanContext

        Args:
            client_id: Dhan client ID
            access_token: Dhan access token
            max_concurrent: Max concurrent requests
        """
        self.client_id = client_id
        self.access_token = access_token
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None

        # Initialize DhanContext (new v2.2.0 pattern)
        if DHAN_V2_2_0:
            try:
                self.dhan_context = DhanContext(client_id, access_token)
                self.dhan_client = dhanhq(self.dhan_context)
                logger.info("✅ DhanContext initialized (v2.2.0 pattern)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize DhanContext: {e}")
                self.dhan_context = None
                self.dhan_client = None
        else:
            logger.warning("⚠️ dhanhq v2.2.0 not available, using direct HTTP API")
            self.dhan_context = None
            self.dhan_client = None

    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()

    async def _request_historical(
        self,
        security_id: str,
        exchange_segment: str,
        instrument_type: str,
        from_date: str,
        to_date: str
    ) -> Dict[str, Any]:
        """
        Fetch historical daily OHLC data using /charts/historical endpoint (v2.2.0)

        Args:
            security_id: Dhan security ID
            exchange_segment: Exchange segment (NSE_EQ, BSE_EQ, MCX_COMM, etc.)
            instrument_type: Instrument type (INDEX, EQUITY, FUTCOM, etc.)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Response dict with OHLCV data
        """
        async with self.semaphore:
            try:
                if not self.session:
                    raise RuntimeError("Session not initialized. Use 'async with' context manager")

                headers = {
                    "access-token": self.access_token,
                    "Content-Type": "application/json"
                }

                # Prepare request body for /charts/historical
                payload = {
                    "securityId": security_id,
                    "exchangeSegment": exchange_segment,
                    "instrument": instrument_type,
                    "expiryCode": 0,  # Not applicable for indices/spot
                    "fromDate": from_date,
                    "toDate": to_date
                }

                url = f"{self.BASE_URL}{self.HISTORICAL_ENDPOINT}"

                async with self.session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Historical data fetched: {security_id} ({from_date} to {to_date})")
                        return data
                    elif response.status == 401:
                        logger.error("❌ Authentication failed (401): Check access-token")
                        raise Exception("Invalid access token")
                    elif response.status == 404:
                        logger.warning(f"⚠️ Data not found (404): {security_id} may not be available")
                        return {"error": "404_not_found", "data": []}
                    else:
                        text = await response.text()
                        logger.error(f"❌ Request failed ({response.status}): {text}")
                        raise Exception(f"API error {response.status}: {text}")

            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout fetching {security_id}")
                raise
            except Exception as e:
                logger.error(f"❌ Request failed: {e}")
                raise

    async def _request_intraday(
        self,
        security_id: str,
        exchange_segment: str,
        instrument_type: str,
        interval: int,
        from_date: str,
        to_date: str
    ) -> Dict[str, Any]:
        """
        Fetch intraday OHLC data using /charts/intraday endpoint (v2.2.0)

        Args:
            security_id: Dhan security ID
            exchange_segment: Exchange segment
            instrument_type: Instrument type
            interval: Time interval in minutes (1, 5, 15, 30, 60)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Response dict with OHLCV data
        """
        async with self.semaphore:
            try:
                if not self.session:
                    raise RuntimeError("Session not initialized")

                headers = {
                    "access-token": self.access_token,
                    "Content-Type": "application/json"
                }

                # Map interval in minutes to string format
                interval_str = str(interval)

                payload = {
                    "securityId": security_id,
                    "exchangeSegment": exchange_segment,
                    "instrument": instrument_type,
                    "interval": interval_str,  # "1", "5", "15", "30", "60"
                    "fromDate": from_date,
                    "toDate": to_date
                }

                url = f"{self.BASE_URL}{self.INTRADAY_ENDPOINT}"

                async with self.session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Intraday data ({interval}min): {security_id} ({from_date})")
                        return data
                    else:
                        text = await response.text()
                        logger.warning(f"⚠️ Intraday fetch ({response.status}): {text[:100]}")
                        return {"error": f"status_{response.status}", "data": []}

            except Exception as e:
                logger.error(f"❌ Intraday request failed: {e}")
                raise

    async def fetch_historical(
        self,
        symbol: str,
        days_back: int = 365
    ) -> pd.DataFrame:
        """
        Fetch historical daily OHLCV data for a symbol

        Args:
            symbol: Trading symbol (NIFTY, BANKNIFTY, etc.)
            days_back: Number of days of historical data

        Returns:
            DataFrame with OHLCV data
        """
        mapping = DhanSecurityMapping.get_security_id(symbol)
        if not mapping:
            logger.error(f"❌ Symbol {symbol} not mapped. Add to DhanSecurityMapping")
            return pd.DataFrame()

        exchange_segment, security_id, instrument_type = mapping

        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        try:
            response = await self._request_historical(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type=instrument_type,
                from_date=from_date,
                to_date=to_date
            )

            if "error" in response:
                logger.error(f"❌ API error for {symbol}: {response.get('error')}")
                return pd.DataFrame()

            # Parse response data into DataFrame
            data = response.get("data", [])
            if not data:
                logger.warning(f"⚠️ No data for {symbol} ({from_date} to {to_date})")
                return pd.DataFrame()

            df = pd.DataFrame(data)

            # Rename columns to standard OHLCV format
            if "open" in df.columns:
                df = df.rename(columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                    "timestamp": "Timestamp"
                })

            df["Symbol"] = symbol
            logger.info(f"✅ Fetched {len(df)} candles for {symbol}")

            return df

        except Exception as e:
            logger.error(f"❌ Failed to fetch {symbol}: {e}")
            return pd.DataFrame()

    async def fetch_intraday(
        self,
        symbol: str,
        interval: str = "15m",
        days_back: int = 30
    ) -> pd.DataFrame:
        """
        Fetch intraday OHLCV data for a symbol

        Args:
            symbol: Trading symbol
            interval: Time interval ("1m", "5m", "15m", "30m", "1h")
            days_back: Number of days of data

        Returns:
            DataFrame with OHLCV data
        """
        mapping = DhanSecurityMapping.get_security_id(symbol)
        if not mapping:
            logger.error(f"❌ Symbol {symbol} not mapped")
            return pd.DataFrame()

        exchange_segment, security_id, instrument_type = mapping

        if interval not in self.INTERVALS:
            logger.error(f"❌ Invalid interval {interval}. Use: {list(self.INTERVALS.keys())}")
            return pd.DataFrame()

        interval_minutes = self.INTERVALS[interval]

        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        try:
            response = await self._request_intraday(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type=instrument_type,
                interval=interval_minutes,
                from_date=from_date,
                to_date=to_date
            )

            if "error" in response:
                logger.warning(f"⚠️ No intraday data for {symbol} ({interval})")
                return pd.DataFrame()

            data = response.get("data", [])
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df["Symbol"] = symbol
            df["Interval"] = interval

            logger.info(f"✅ Fetched {len(df)} {interval} candles for {symbol}")

            return df

        except Exception as e:
            logger.error(f"❌ Intraday fetch failed: {e}")
            return pd.DataFrame()


async def main():
    """Main execution with argument parsing"""

    parser = argparse.ArgumentParser(
        description="Dhan v2.2.0 Historical Data Ingestion"
    )
    parser.add_argument(
        "--credentials-file",
        type=str,
        help="Path to JSON credentials file with client_id and access_token"
    )
    parser.add_argument(
        "--client-id",
        type=str,
        default=os.getenv("DHAN_CLIENT_ID"),
        help="Dhan Client ID (env: DHAN_CLIENT_ID)"
    )
    parser.add_argument(
        "--access-token",
        type=str,
        default=os.getenv("DHAN_ACCESS_TOKEN"),
        help="Dhan Access Token (env: DHAN_ACCESS_TOKEN)"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["NIFTY", "BANKNIFTY", "FINNIFTY"],
        help="Symbols to fetch (NIFTY, BANKNIFTY, FINNIFTY, SENSEX, GOLD, CRUDEOIL)"
    )
    parser.add_argument(
        "--intervals",
        nargs="+",
        default=["1d"],
        help="Intervals to fetch: 1d (daily), 1h, 15m, 5m, 1m"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=365,
        help="Number of days of historical data to fetch"
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default="gs://infinityai-backtesting-data",
        help="GCS bucket for storing data"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/dhan_historical",
        help="Local output directory for CSV files"
    )
    parser.add_argument(
        "--test-api",
        action="store_true",
        help="Test API connectivity only (fetch 1 day for 1 symbol)"
    )

    args = parser.parse_args()

    # Load credentials from file if provided
    if args.credentials_file:
        try:
            with open(args.credentials_file, 'r') as f:
                creds = json.load(f)
                args.client_id = creds.get("client_id")
                args.access_token = creds.get("access_token")
                logger.info(f"✅ Loaded credentials from {args.credentials_file}")
        except Exception as e:
            logger.error(f"❌ Failed to load credentials: {e}")
            return

    if not args.client_id or not args.access_token:
        logger.error("❌ Missing Dhan credentials. Provide via --credentials-file or env vars")
        return

    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Test mode: fetch 1 day for first symbol
    if args.test_api:
        args.symbols = [args.symbols[0]]
        args.days_back = 1
        logger.info(f"🧪 Test mode: Fetching {args.days_back} day for {args.symbols}")

    # Initialize client and fetch data
    async with Dhanv220Client(
        client_id=args.client_id,
        access_token=args.access_token,
        max_concurrent=3
    ) as client:

        logger.info(f"📊 Starting data ingestion: {args.symbols} × {args.intervals}")

        for symbol in args.symbols:
            # Fetch historical daily data
            if "1d" in args.intervals:
                logger.info(f"\n📈 Fetching daily data for {symbol}...")
                df = await client.fetch_historical(symbol, args.days_back)

                if not df.empty:
                    output_file = Path(args.output_dir) / f"{symbol}_daily.csv"
                    df.to_csv(output_file, index=False)
                    logger.info(f"✅ Saved {len(df)} records to {output_file}")
                else:
                    logger.warning(f"⚠️ No data for {symbol}")

            # Fetch intraday data
            for interval in [i for i in args.intervals if i != "1d"]:
                logger.info(f"\n📈 Fetching {interval} data for {symbol}...")
                df = await client.fetch_intraday(symbol, interval, min(args.days_back, 30))

                if not df.empty:
                    output_file = Path(args.output_dir) / f"{symbol}_{interval}.csv"
                    df.to_csv(output_file, index=False)
                    logger.info(f"✅ Saved {len(df)} {interval} records to {output_file}")

        logger.info("\n" + "="*70)
        logger.info("✅ DATA INGESTION COMPLETE")
        logger.info("="*70)


if __name__ == "__main__":
    asyncio.run(main())
