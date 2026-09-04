"""
Market Data Provider Fallback System
Retrieves live market data from multiple providers when DhanHQ broker auth fails.
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from enum import Enum

class DataProvider(Enum):
    DHAN = "dhan"
    NSE_DIRECT = "nse_direct"
    ALPHA_VANTAGE = "alpha_vantage"
    MARKETSTACK = "marketstack"
    YFINANCE = "yfinance"

class MarketDataFallbackProvider:
    """
    Multi-provider fallback system for market data.
    Tries primary provider first, falls back to alternatives on failure.
    """

    def __init__(self):
        self.providers = {
            DataProvider.DHAN: self.fetch_from_dhan,
            DataProvider.NSE_DIRECT: self.fetch_from_nse,
            DataProvider.ALPHA_VANTAGE: self.fetch_from_alpha_vantage,
            DataProvider.MARKETSTACK: self.fetch_from_marketstack,
        }

    async def get_live_quotes(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Any]:
        """
        Get live market quotes with automatic fallback.
        Tries providers in order: Dhan → NSE → Alpha Vantage → MarketStack
        """

        print(f"\n📡 Fetching live quotes for {symbols} from {exchange}")
        print("Provider order: DhanHQ → NSE Direct → Alpha Vantage → MarketStack\n")

        # Try each provider in order
        for provider in [DataProvider.DHAN, DataProvider.NSE_DIRECT,
                         DataProvider.ALPHA_VANTAGE, DataProvider.MARKETSTACK]:
            try:
                print(f"🔄 Attempting {provider.value}...", end=" ")

                if provider == DataProvider.DHAN:
                    result = await self.fetch_from_dhan(symbols, exchange)
                elif provider == DataProvider.NSE_DIRECT:
                    result = await self.fetch_from_nse(symbols, exchange)
                elif provider == DataProvider.ALPHA_VANTAGE:
                    result = await self.fetch_from_alpha_vantage(symbols, exchange)
                elif provider == DataProvider.MARKETSTACK:
                    result = await self.fetch_from_marketstack(symbols, exchange)

                if result and result.get("status") == "success":
                    print(f"✅ SUCCESS\n")
                    return {
                        "status": "success",
                        "provider": provider.value,
                        "data": result.get("data"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    print(f"❌ FAILED")

            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                continue

        return {
            "status": "error",
            "message": "All providers failed",
            "providers_tried": [p.value for p in self.providers.keys()]
        }

    async def fetch_from_dhan(self, symbols: List[str], exchange: str) -> Dict[str, Any]:
        """
        Primary: DhanHQ Broker API
        - Real-time NSE data
        - Requires valid authentication
        """
        try:
            # This would call Engine-C with broker credentials
            # Currently fails with auth error
            raise Exception("Broker authentication failed (error 808)")
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def fetch_from_nse(self, symbols: List[str], exchange: str) -> Dict[str, Any]:
        """
        Secondary: NSE Direct API
        - Official NSE endpoint
        - No authentication required
        - Real-time data
        """
        try:
            # NSE API endpoint
            nse_url = "https://www.nseindia.com/api/quote-equity"

            results = {}
            for symbol in symbols:
                # NIFTY 50, BANKNIFTY etc
                params = {
                    "symbol": symbol,
                    "section": "trade"
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }

                response = requests.get(nse_url, params=params, headers=headers, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    results[symbol] = {
                        "symbol": symbol,
                        "ltp": data.get("pricebandindicator", {}).get("cm", {}).get("ltp", 0),
                        "open": data.get("pricebandindicator", {}).get("cm", {}).get("open", 0),
                        "high": data.get("pricebandindicator", {}).get("cm", {}).get("high", 0),
                        "low": data.get("pricebandindicator", {}).get("cm", {}).get("low", 0),
                        "close": data.get("pricebandindicator", {}).get("cm", {}).get("previousClose", 0),
                        "volume": data.get("quantityTraded", 0),
                        "timestamp": datetime.utcnow().isoformat()
                    }

            if results:
                return {
                    "status": "success",
                    "provider": "nse_direct",
                    "data": results
                }
        except Exception as e:
            print(f"NSE API error: {e}")

        return {"status": "error"}

    async def fetch_from_alpha_vantage(self, symbols: List[str], exchange: str) -> Dict[str, Any]:
        """
        Tertiary: Alpha Vantage API
        - Covers Indian equities (NSE suffix)
        - Global stock data
        - Free tier available
        """
        try:
            api_key = "demo"  # Should use Secret Manager
            base_url = "https://www.alphavantage.co/query"

            results = {}
            for symbol in symbols:
                # Convert symbol: NIFTY -> NIFTY.NS (Alpha Vantage format)
                av_symbol = f"{symbol}.NS"

                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": av_symbol,
                    "apikey": api_key
                }

                response = requests.get(base_url, params=params, timeout=5)

                if response.status_code == 200:
                    data = response.json().get("Global Quote", {})
                    if data:
                        results[symbol] = {
                            "symbol": symbol,
                            "ltp": float(data.get("05. price", 0)),
                            "open": float(data.get("02. open", 0)),
                            "high": float(data.get("03. high", 0)),
                            "low": float(data.get("04. low", 0)),
                            "close": float(data.get("08. previous close", 0)),
                            "volume": int(data.get("06. volume", 0)),
                            "timestamp": datetime.utcnow().isoformat()
                        }

            if results:
                return {
                    "status": "success",
                    "provider": "alpha_vantage",
                    "data": results
                }
        except Exception as e:
            print(f"Alpha Vantage error: {e}")

        return {"status": "error"}

    async def fetch_from_marketstack(self, symbols: List[str], exchange: str) -> Dict[str, Any]:
        """
        Quaternary: MarketStack API
        - Multi-exchange support
        - Indian exchange: XNSE
        - Real-time and historical data
        """
        try:
            api_key = "demo"  # Should use Secret Manager
            base_url = "http://api.marketstack.com/v1/intraday"

            results = {}
            for symbol in symbols:
                # MarketStack uses XNSE.SYMBOL format
                ms_symbol = f"XNSE.{symbol}"

                params = {
                    "symbols": ms_symbol,
                    "access_key": api_key
                }

                response = requests.get(base_url, params=params, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("data"):
                        quote = data["data"][0]
                        results[symbol] = {
                            "symbol": symbol,
                            "ltp": quote.get("last", 0),
                            "open": quote.get("open", 0),
                            "high": quote.get("high", 0),
                            "low": quote.get("low", 0),
                            "close": quote.get("close", 0),
                            "volume": quote.get("volume", 0),
                            "timestamp": quote.get("date", datetime.utcnow().isoformat())
                        }

            if results:
                return {
                    "status": "success",
                    "provider": "marketstack",
                    "data": results
                }
        except Exception as e:
            print(f"MarketStack error: {e}")

        return {"status": "error"}

# Example usage
if __name__ == "__main__":
    async def main():
        provider = MarketDataFallbackProvider()

        # Try to get NIFTY 50 quotes
        result = await provider.get_live_quotes(
            symbols=["NIFTY50", "BANKNIFTY"],
            exchange="NSE"
        )

        print("\n" + "="*60)
        print("RESULT:")
        print("="*60)
        print(json.dumps(result, indent=2))

    asyncio.run(main())
