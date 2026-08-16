"""
DhanHQ Client Wrapper with Sandbox Support & Telemetry Rate-Limit Cache

This module provides a robust wrapper around the dhanhq library that supports
both sandbox and production environments, with an intelligent short-lived cache
to absorb burst queries and shield against DhanHQ 429 rate limit exceptions.
"""
import os
import time
import logging
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


class DhanClient:
    """
    Enhanced DhanHQ client with sandbox support and rate-limit mitigation caching.
    """
    
    def __init__(self, client_id: str, access_token: str, environment: str = None):
        self.client_id = client_id
        self.access_token = access_token
        
        # Determine environment
        if environment is None:
            environment = os.getenv("DHAN_ENVIRONMENT", DhanEnvironment.PRODUCTION)
        
        self.environment = environment.lower()
        self.is_sandbox = (self.environment == DhanEnvironment.SANDBOX)
        
        # Initialize the underlying dhanhq client
        self._client = dhanhq(client_id, access_token)
        
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
        """Execute Dhan SDK method with short-lived cache and 429 fallback"""
        cache_key = f"{self.client_id}:{method_name}:{str(args)}:{str(kwargs)}"
        now = time.time()
        
        # Check cache freshness
        if cache_key in _TELEMETRY_CACHE:
            cached_time, cached_val = _TELEMETRY_CACHE[cache_key]
            if (now - cached_time) < CACHE_TTL_SECONDS:
                return cached_val

        try:
            result = func(*args, **kwargs)
            # If Dhan returned an error dict indicating rate limit, use stale cache if available
            if isinstance(result, dict) and result.get("status") == "failure":
                err_msg = str(result.get("remarks", ""))
                if "rate" in err_msg.lower() or "limit" in err_msg.lower():
                    if cache_key in _TELEMETRY_CACHE:
                        return _TELEMETRY_CACHE[cache_key][1]
            
            _TELEMETRY_CACHE[cache_key] = (now, result)
            return result
        except Exception as e:
            if "rate" in str(e).lower() or "429" in str(e):
                if cache_key in _TELEMETRY_CACHE:
                    logger.warning(f"Rate limited on {method_name} - serving cached telemetry")
                    return _TELEMETRY_CACHE[cache_key][1]
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
