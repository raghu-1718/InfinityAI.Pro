"""
NSE Direct API Provider - Official Real-Time Data
Connects directly to National Stock Exchange (NSE) India API
Provides official, real-time data for Indian stocks
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from .interfaces import MarketDataProvider
from .models import Quote


class NSEDirectAPIProvider(MarketDataProvider):
    """
    NSE Direct API Provider for official real-time Indian stock market data.

    Source: National Stock Exchange of India (NSE) - https://www.nseindia.com/
    Data: Real-time quotes, historical data, market statistics
    Coverage: All NSE-listed stocks (2000+ symbols)

    Note: NSE API requires proper User-Agent and referer headers.
    Free tier: Limited calls/day; requires registration with NSE.
    """

    @property
    def name(self) -> str:
        return "nse-direct"

    def __init__(self):
        """Initialize NSE Direct API provider with required headers."""
        self.base_url = "https://www.nseindia.com/api"
        self.timeout = 30
        self.session_cookies = None

        # NSE API requires specific headers to prevent blocking
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.nseindia.com/",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Initialize session to maintain cookies
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Create or return existing aiohttp session with proper cookies."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)
            # Initialize session by fetching main page (establishes cookies)
            try:
                async with self._session.get("https://www.nseindia.com/", timeout=self.timeout) as resp:
                    pass  # Just establish the session
            except Exception as e:
                print(f"Error initializing NSE session: {e}")
        return self._session

    async def fetch_quotes(self, symbols: List[str]) -> List[Quote]:
        """
        Fetch real-time quotes from NSE API.

        Args:
            symbols: List of NSE symbols (e.g., ['TCS', 'INFY', 'HDFC BANK'])

        Returns:
            List of Quote objects with real-time data

        Endpoint: /allQuotes?index=equities
        """
        quotes = []
        session = await self._get_session()

        try:
            # NSE provides quotes for equity segments
            params = {
                "index": "equities"  # Or "nifty50" for Nifty 50 stocks only
            }

            url = f"{self.base_url}/allQuotes"
            async with session.get(url, params=params, timeout=self.timeout) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json()

                        # NSE returns data in 'data' key
                        all_quotes = data.get("data", [])

                        # Filter for requested symbols
                        symbol_set = set(symbols)
                        for quote_data in all_quotes:
                            symbol = quote_data.get("symbol", "")
                            if symbol in symbol_set:
                                try:
                                    # Extract price data
                                    quote = self._parse_nse_quote(quote_data, symbol)
                                    if quote:
                                        quotes.append(quote)
                                except Exception as e:
                                    print(f"Error parsing quote for {symbol}: {e}")
                    except Exception as e:
                        print(f"Error parsing NSE response: {e}")
        except Exception as e:
            print(f"Error fetching quotes from NSE Direct API: {e}")

        return quotes

    def _parse_nse_quote(self, quote_data: Dict[str, Any], symbol: str) -> Optional[Quote]:
        """
        Parse NSE quote data into Quote object.

        NSE response format:
        {
            "symbol": "TCS",
            "netPrice": 3850.50,
            "buyPrice": 3850.00,
            "sellPrice": 3851.00,
            "lastPrice": 3850.50,
            "prevClose": 3840.00,
            "dayHigh": 3860.00,
            "dayLow": 3840.00,
            "52WeekHigh": 4200.00,
            "52WeekLow": 3200.00,
            "ttm": "12:30:45",
            "totalTradedVolume": 1234567,
            "totalTradedValue": 4761234890.50
        }
        """
        try:
            # Get latest price - NSE provides multiple price fields
            price = float(
                quote_data.get("netPrice") or
                quote_data.get("lastPrice") or
                quote_data.get("previousClose") or
                0
            )

            if price == 0:
                return None

            bid = float(quote_data.get("buyPrice", 0)) or None
            ask = float(quote_data.get("sellPrice", 0)) or None
            volume = float(quote_data.get("totalTradedVolume", 0)) or None

            # Parse timestamp from NSE time (TTM = Time to Market)
            ttm_str = quote_data.get("ttm", "")
            timestamp = self._parse_nse_timestamp(ttm_str)

            quote = Quote(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                source=self.name,
                currency="INR",
                bid=bid,
                ask=ask,
                volume=volume,
            )
            return quote
        except Exception as e:
            print(f"Error in _parse_nse_quote for {symbol}: {e}")
            return None

    def _parse_nse_timestamp(self, ttm_str: str) -> datetime:
        """
        Parse NSE time format (HH:MM:SS) to UTC timestamp.

        NSE sends time in IST, convert to UTC or store as IST.
        """
        try:
            if ttm_str:
                # NSE format: "HH:MM:SS" in IST
                today = datetime.utcnow().date()
                time_parts = ttm_str.split(":")
                if len(time_parts) == 3:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    second = int(time_parts[2])

                    # Create IST timestamp and convert to UTC
                    # IST is UTC+5:30
                    from datetime import timezone, timedelta
                    ist = timezone(timedelta(hours=5, minutes=30))
                    dt_ist = datetime(today.year, today.month, today.day,
                                     hour, minute, second, tzinfo=ist)
                    return dt_ist.astimezone(timezone.utc)
        except Exception as e:
            print(f"Error parsing NSE timestamp {ttm_str}: {e}")

        # Fallback to current UTC time
        return datetime.utcnow()

    async def fetch_intraday(self, symbol: str, interval: str = "1min") -> List[Dict[str, Any]]:
        """
        Fetch intraday chart data for a symbol.

        Args:
            symbol: NSE symbol (e.g., 'TCS')
            interval: Time interval - Not all intervals supported by NSE API

        Returns:
            List of OHLCV candles

        Note: NSE API has limited intraday endpoints.
        May need to use alternative provider for intraday data.
        """
        session = await self._get_session()
        intraday_data = []

        try:
            # NSE intraday endpoint (limited availability)
            url = f"{self.base_url}/chart-data"
            params = {
                "symbol": symbol,
                "series": "EQ",  # Equity
            }

            async with session.get(url, params=params, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    # Parse candle data
                    candles = data.get("grapthData", [])  # Note: NSE typo in API
                    for candle in candles:
                        try:
                            intraday_data.append({
                                "timestamp": candle[0],
                                "open": float(candle[1]),
                                "high": float(candle[2]),
                                "low": float(candle[3]),
                                "close": float(candle[4]),
                                "volume": float(candle[5]) if len(candle) > 5 else 0,
                            })
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            print(f"Error fetching intraday data for {symbol} from NSE: {e}")

        return intraday_data

    async def fetch_nifty50_data(self) -> Dict[str, Any]:
        """
        Fetch Nifty 50 index data and constituent stocks.

        Returns:
            Dictionary with index data and 50 constituent symbols
        """
        session = await self._get_session()

        try:
            url = f"{self.base_url}/allIndices"
            params = {"index": "NIFTY 50"}

            async with session.get(url, params=params, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
        except Exception as e:
            print(f"Error fetching Nifty50 data from NSE: {e}")

        return {}

    async def search_symbol(self, query: str) -> List[Dict[str, str]]:
        """
        Search for symbols in NSE database.

        Args:
            query: Search query (company name or symbol prefix)

        Returns:
            List of matching symbols with company names
        """
        session = await self._get_session()
        results = []

        try:
            url = f"{self.base_url}/search-symbol"
            params = {"q": query}

            async with session.get(url, params=params, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data.get("data", []):
                        results.append({
                            "symbol": item.get("symbol", ""),
                            "company_name": item.get("company_name", ""),
                            "isin": item.get("isin", ""),
                        })
        except Exception as e:
            print(f"Error searching NSE symbols: {e}")

        return results

    async def get_market_status(self) -> Dict[str, Any]:
        """
        Get current NSE market status.

        Returns:
            Market open/close status, trading hours, etc.
        """
        session = await self._get_session()

        try:
            url = f"{self.base_url}/marketStatus"
            async with session.get(url, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
        except Exception as e:
            print(f"Error fetching NSE market status: {e}")

        return {"status": "unknown"}

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup session."""
        if self._session:
            await self._session.close()

    def __del__(self):
        """Cleanup session on deletion."""
        if self._session and not self._session.closed:
            try:
                asyncio.get_event_loop().run_until_complete(self._session.close())
            except:
                pass


# Usage Example:
"""
async def main():
    async with NSEDirectAPIProvider() as provider:
        # Fetch quotes for specific stocks
        symbols = ['TCS', 'INFY', 'HDFC BANK']
        quotes = await provider.fetch_quotes(symbols)

        for quote in quotes:
            print(f"{quote.symbol}: ₹{quote.price} ({quote.source})")

        # Get Nifty 50 data
        nifty_data = await provider.fetch_nifty50_data()
        print(f"Nifty 50 Index: {nifty_data}")

        # Search for symbols
        results = await provider.search_symbol("TCS")
        print(f"Search results: {results}")

        # Check market status
        status = await provider.get_market_status()
        print(f"Market Status: {status}")

# asyncio.run(main())
"""
