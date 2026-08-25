"""
DhanHQ Client Wrapper with Sandbox Support & Telemetry Rate-Limit Cache

This module provides a robust wrapper around the dhanhq library that supports
both sandbox and production environments, with an intelligent short-lived cache
to absorb burst queries and shield against DhanHQ 429 rate limit exceptions.
"""
import os
import time
import logging
import httpx
from typing import Optional, Dict, Any
from dhanhq import dhanhq

logger = logging.getLogger(__name__)

# In-memory telemetry cache: { (client_id, method_name, args_key): (timestamp, result) }
_TELEMETRY_CACHE: Dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 3.0  # 3-second cache to prevent Dhan 429 rate limiting


class DhanEnvironment:
    """Environment configuration for DhanHQ"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"
    
    # Base URLs
    SANDBOX_URL = "https://sandbox.dhan.co/v2"
    PRODUCTION_URL = "https://api.dhan.co/v2"


async def safe_dhan_request(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    """Safely execute an async Dhan request with 5xx maintenance fallback"""
    try:
        response = await client.request(method, url, **kwargs)
        if response.status_code >= 500:
            logger.warning(f"DhanHQ upstream maintenance/5xx at {url}: {response.status_code}")
            return {"status": "upstream_maintenance", "data": None, "code": response.status_code}
        response.raise_for_status()
        return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
        logger.error(f"DhanHQ gateway error on {url}: {str(e)}")
        return {"status": "error", "message": "Broker API temporarily unavailable", "data": None}


class DhanClient:
    """
    Enhanced DhanHQ client with sandbox support and rate-limit/maintenance mitigation caching.
    """
    
    def __init__(self, client_id: str, access_token: str, environment: str = None):
        # CRITICAL: Strip trailing \r\n and whitespace from credentials.
        # Dhan token renewal responses and Firestore reads can inject trailing
        # newlines that cause "Invalid leading whitespace, reserved character(s)"
        # HTTP header errors when the token is passed in the access-token header.
        self.client_id = str(client_id).strip()
        self.access_token = str(access_token).strip()
        
        # Determine environment
        if environment is None:
            environment = os.getenv("DHAN_ENVIRONMENT", DhanEnvironment.PRODUCTION)
        
        self.environment = environment.lower()
        self.is_sandbox = (self.environment == DhanEnvironment.SANDBOX)
        
        # Initialize the underlying dhanhq client with sanitized credentials
        self._client = dhanhq(self.client_id, self.access_token)
        
        # Override base URL if sandbox
        if self.is_sandbox:
            self._configure_sandbox()
    
    def _configure_sandbox(self):
        """Configure the client for sandbox environment."""
        if hasattr(self._client, 'base_url'):
            self._client.base_url = DhanEnvironment.SANDBOX_URL
        elif hasattr(self._client, '_base_url'):
            self._client._base_url = DhanEnvironment.SANDBOX_URL
    
    def _cached_call(self, method_name: str, func, *args, **kwargs):
        """Execute Dhan SDK method with short-lived cache, 429 rate limit, and 5xx maintenance fallback"""
        cache_key = f"{self.client_id}:{method_name}:{str(args)}:{str(kwargs)}"
        now = time.time()
        
        # Check cache freshness
        if cache_key in _TELEMETRY_CACHE:
            cached_time, cached_val = _TELEMETRY_CACHE[cache_key]
            if (now - cached_time) < CACHE_TTL_SECONDS:
                return cached_val

        try:
            result = func(*args, **kwargs)
            # If Dhan returned an error dict indicating rate limit or maintenance
            if isinstance(result, dict) and result.get("status") == "failure":
                err_msg = str(result.get("remarks", "")).lower()
                if "rate" in err_msg or "limit" in err_msg or "maintenance" in err_msg or "blocked" in err_msg:
                    if cache_key in _TELEMETRY_CACHE:
                        return _TELEMETRY_CACHE[cache_key][1]
            
            _TELEMETRY_CACHE[cache_key] = (now, result)
            return result
        except Exception as e:
            err_str = str(e).lower()
            if "rate" in err_str or "429" in err_str:
                if cache_key in _TELEMETRY_CACHE:
                    logger.warning(f"Rate limited on {method_name} - serving cached telemetry")
                    return _TELEMETRY_CACHE[cache_key][1]
            if "500" in err_str or "502" in err_str or "503" in err_str or "504" in err_str or "timeout" in err_str or "connection" in err_str:
                logger.warning(f"DhanHQ upstream 5xx/maintenance during {method_name}: {e}")
                if cache_key in _TELEMETRY_CACHE:
                    return _TELEMETRY_CACHE[cache_key][1]
                return {
                    "status": "upstream_maintenance",
                    "data": {},
                    "remarks": "Broker API undergoing nightly maintenance/settlement. Retrying automatically."
                }
            raise

    def get_fund_limits(self, *args, **kwargs):
        return self._cached_call("get_fund_limits", self._client.get_fund_limits, *args, **kwargs)

    def get_positions(self, *args, **kwargs):
        return self._cached_call("get_positions", self._client.get_positions, *args, **kwargs)

    def get_holdings(self, *args, **kwargs):
        return self._cached_call("get_holdings", self._client.get_holdings, *args, **kwargs)

    def get_order_list(self, *args, **kwargs):
        return self._cached_call("get_order_list", self._client.get_order_list, *args, **kwargs)

    def get_trade_book(self, *args, **kwargs):
        return self._cached_call("get_trade_book", self._client.get_trade_book, *args, **kwargs)

    def ohlc_data(self, *args, **kwargs):
        return self._cached_call("ohlc_data", self._client.ohlc_data, *args, **kwargs)

    def option_chain(self, *args, **kwargs):
        return self._cached_call("option_chain", self._client.option_chain, *args, **kwargs)

    def quote_data(self, *args, **kwargs):
        return self._cached_call("quote_data", self._client.quote_data, *args, **kwargs)
    
    def __getattr__(self, name):
        """Proxy all other method calls to the underlying dhanhq client."""
        return getattr(self._client, name)
    
    def get_environment(self) -> str:
        return self.environment
    
    def is_sandbox_mode(self) -> bool:
        return self.is_sandbox


def create_dhan_client(
    client_id: str,
    access_token: str,
    environment: Optional[str] = None,
    force_production: bool = False
) -> DhanClient:
    """Factory function to create a DhanHQ client with environment support."""
    if force_production:
        environment = DhanEnvironment.PRODUCTION
    
    return DhanClient(client_id, access_token, environment)
