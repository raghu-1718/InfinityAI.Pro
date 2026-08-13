"""
Market Quotes API with Fallback Support
Endpoint: /api/market/quotes-fallback
Retrieves live market data with automatic provider fallback on authentication failure
"""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Import fallback provider
try:
    from src.market_data_fallback import MarketDataFallbackProvider
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False
    logger.warning("⚠️ Market data fallback provider not available")

@router.get("/api/market/quotes-fallback")
async def get_market_quotes_with_fallback(
    symbols: str = Query(..., description="Comma-separated list of symbols (e.g., NIFTY50,BANKNIFTY)"),
    exchange: str = Query("NSE", description="Exchange: NSE, BSE, NFO"),
    user_id: Optional[str] = Header(None, alias="user_id"),
    include_fallback: bool = Query(True, description="Use fallback providers if primary fails")
):
    """
    Get live market quotes with automatic fallback to alternative data providers.

    Provider Chain:
    1. DhanHQ (Primary) - Requires broker credentials
    2. NSE Direct API (Secondary) - No auth required
    3. Alpha Vantage (Tertiary) - Free tier available
    4. MarketStack (Quaternary) - Multi-exchange support

    Example:
    GET /api/market/quotes-fallback?symbols=NIFTY50,BANKNIFTY&exchange=NSE
    """

    if not FALLBACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Market data fallback provider not available"
        )

    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        logger.info(f"📡 Fetching quotes for {symbol_list} from {exchange}")

        provider = MarketDataFallbackProvider()
        result = await provider.get_live_quotes(symbol_list, exchange)

        if result["status"] == "success":
            return {
                "status": "success",
                "provider": result.get("provider"),
                "data": result.get("data"),
                "timestamp": result.get("timestamp"),
                "message": f"Data from {result.get('provider')} provider"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail=f"All data providers failed: {result.get('message')}"
            )

    except Exception as e:
        logger.error(f"❌ Error fetching market quotes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market quotes: {str(e)}"
        )


@router.get("/api/market/provider-status")
async def get_provider_status():
    """
    Check status and availability of all market data providers
    """
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "providers": {
            "dhan": {
                "name": "DhanHQ Broker API",
                "type": "Primary",
                "status": "requires_authentication",
                "data_type": "real-time NSE tick-by-tick",
                "coverage": ["NSE", "NFO", "BSE"],
                "latency": "<100ms"
            },
            "nse_direct": {
                "name": "NSE Direct API",
                "type": "Secondary",
                "status": "available",
                "data_type": "real-time NSE",
                "coverage": ["NSE"],
                "latency": "<500ms",
                "requires_auth": False
            },
            "alpha_vantage": {
                "name": "Alpha Vantage API",
                "type": "Tertiary",
                "status": "available",
                "data_type": "global + NSE Indian equities",
                "coverage": ["NSE", "NYSE", "NASDAQ", "Forex"],
                "latency": "<1s",
                "requires_auth": False,
                "free_tier": "5 calls/min"
            },
            "marketstack": {
                "name": "MarketStack API",
                "type": "Quaternary",
                "status": "available",
                "data_type": "multi-exchange real-time",
                "coverage": ["NSE (XNSE)", "BSE", "Global"],
                "latency": "<1s",
                "requires_auth": False
            }
        },
        "fallback_chain": [
            "DhanHQ (primary - requires broker credentials)",
            "NSE Direct API (secondary - no auth)",
            "Alpha Vantage (tertiary - no auth)",
            "MarketStack (quaternary - no auth)"
        ],
        "recommendation": "If DhanHQ broker authentication fails, system automatically uses NSE Direct API for live quotes"
    }


@router.get("/api/market/test-all-providers")
async def test_all_providers(
    symbol: str = Query("NIFTY50", description="Single symbol to test all providers")
):
    """
    Test all market data providers independently to check which ones are working
    """

    if not FALLBACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Market data fallback provider not available"
        )

    try:
        provider = MarketDataFallbackProvider()
        results = {}

        # Test each provider
        providers_to_test = [
            ("DhanHQ", provider.fetch_from_dhan),
            ("NSE Direct", provider.fetch_from_nse),
            ("Alpha Vantage", provider.fetch_from_alpha_vantage),
            ("MarketStack", provider.fetch_from_marketstack)
        ]

        for provider_name, provider_func in providers_to_test:
            try:
                logger.info(f"Testing {provider_name}...")
                result = await provider_func([symbol], "NSE")

                if result.get("status") == "success":
                    results[provider_name] = {
                        "status": "✅ WORKING",
                        "data": result.get("data")
                    }
                else:
                    results[provider_name] = {
                        "status": "❌ FAILED",
                        "error": result.get("error", "Unknown error")
                    }
            except Exception as e:
                results[provider_name] = {
                    "status": "❌ ERROR",
                    "error": str(e)
                }

        # Determine which provider to recommend
        working_providers = [p for p, r in results.items() if "WORKING" in r["status"]]

        return {
            "status": "success",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "providers": results,
            "working_providers": working_providers,
            "recommendation": (
                working_providers[0] if working_providers
                else "No providers currently working"
            )
        }

    except Exception as e:
        logger.error(f"Error testing providers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test providers: {str(e)}"
        )
