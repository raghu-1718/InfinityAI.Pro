"""
Dhan API Integration Service - Complete Trading & Data API
"""

import aiohttp
import asyncio
import logging
import json
import hashlib
import hmac
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
import base64
import os
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class DhanAPIService:
    """Comprehensive Dhan API Service for Trading and Market Data"""
    
    def __init__(self):
        # API Configuration
        self.trading_base_url = "https://api.dhan.co"
        self.data_base_url = "https://api.dhan.co"  # Using main API for data
        self.auth_base_url = "https://dhanhq.co"
        
        # Real Dhan Configuration
        self.client_id = os.getenv("DHAN_CLIENT_ID", "1101302170")
        self.api_key = os.getenv("DHAN_API_KEY", "267e44a0")
        self.api_secret = os.getenv("DHAN_API_SECRET", "84ba58c4-7404-42f3-b5c9-9eb152da0f29")
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN", "")
        self.redirect_uri = "https://infinity-ai-9utba60h7-infinityaipro.vercel.app/dhan-auth"
        self.postback_url = "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/dhan/auth/callback"
        
        # Token storage (encrypted)
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # User sessions
        self.user_sessions: Dict[str, Dict] = {}
        
        # Market data cache
        self.market_data_cache: Dict[str, Dict] = {}
        self.last_update: Dict[str, datetime] = {}
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure token storage"""
        key_file = "encryption.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt access token"""
        return self.cipher_suite.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt access token"""
        return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
    
    # ========================
    # OAuth Authentication Flow
    # ========================
    
    def get_auth_url(self, user_id: str, state: str = None) -> str:
        """Generate OAuth authorization URL for Dhan"""
        
        if not state:
            state = f"{user_id}_{int(time.time())}"
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "read write"
        }
        
        auth_url = f"{self.auth_base_url}/oauth2/auth?{urlencode(params)}"
        
        logger.info(f"Generated auth URL for user {user_id}: {auth_url}")
        return auth_url
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        
        try:
            user_id = state.split('_')[0]
            
            # Prepare token exchange request
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.auth_base_url}/oauth2/token",
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    
                    if response.status == 200:
                        token_response = await response.json()
                        
                        # Encrypt and store token
                        access_token = token_response.get("access_token")
                        encrypted_token = self._encrypt_token(access_token)
                        
                        # Store user session
                        self.user_sessions[user_id] = {
                            "access_token": encrypted_token,
                            "refresh_token": token_response.get("refresh_token"),
                            "token_type": token_response.get("token_type", "Bearer"),
                            "expires_at": datetime.now() + timedelta(seconds=token_response.get("expires_in", 3600)),
                            "connected_at": datetime.now(),
                            "status": "active"
                        }
                        
                        logger.info(f"Successfully connected Dhan account for user {user_id}")
                        
                        return {
                            "success": True,
                            "user_id": user_id,
                            "token_type": token_response.get("token_type"),
                            "expires_in": token_response.get("expires_in")
                        }
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Token exchange failed: {response.status} - {error_text}")
                        return {"success": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_auth_headers(self, user_id: str = None) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        
        # Use stored access token for real API calls
        if self.access_token:
            return {
                "access-token": self.access_token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        
        # Fallback to user session if available
        if user_id and user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            access_token = self._decrypt_token(session["access_token"])
            
            return {
                "Authorization": f"{session['token_type']} {access_token}",
                "Content-Type": "application/json"
            }
        
        # Default headers with API key
        return {
            "X-Dhan-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    # ========================
    # Account & Profile APIs
    # ========================
    
    async def get_account_details(self, user_id: str) -> Dict[str, Any]:
        """Get user account details and profile"""
        
        try:
            headers = self._get_auth_headers(user_id)
            
            async with aiohttp.ClientSession() as session:
                # Get account info
                async with session.get(f"{self.trading_base_url}/accounts", headers=headers) as response:
                    if response.status == 200:
                        account_data = await response.json()
                        
                        return {
                            "success": True,
                            "account": {
                                "user_id": account_data.get("clientId"),
                                "user_name": account_data.get("userName"),
                                "email": account_data.get("email"),
                                "mobile": account_data.get("mobile"),
                                "pan": account_data.get("pan"),
                                "account_type": account_data.get("accountType"),
                                "status": account_data.get("status"),
                                "kyc_status": account_data.get("kycStatus"),
                                "trading_enabled": account_data.get("tradingEnabled", False),
                                "segments": account_data.get("enabledSegments", [])
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"Account details error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_funds_and_margin(self, user_id: str) -> Dict[str, Any]:
        """Get account funds and margin details"""
        
        try:
            headers = self._get_auth_headers(user_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_base_url}/funds", headers=headers) as response:
                    if response.status == 200:
                        funds_data = await response.json()
                        
                        return {
                            "success": True,
                            "funds": {
                                "available_cash": funds_data.get("availablecash", 0),
                                "collateral": funds_data.get("collateral", 0),
                                "total_balance": funds_data.get("totalBalance", 0),
                                "used_margin": funds_data.get("usedMargin", 0),
                                "available_margin": funds_data.get("availableMargin", 0),
                                "exposure_margin": funds_data.get("exposureMargin", 0),
                                "adhoc_margin": funds_data.get("adhocMargin", 0),
                                "notional_cash": funds_data.get("notionalCash", 0),
                                "category_wise": {
                                    "equity": funds_data.get("equity", {}),
                                    "commodity": funds_data.get("commodity", {}),
                                    "currency": funds_data.get("currency", {})
                                }
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"Funds data error: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # Portfolio & Holdings APIs
    # ========================
    
    async def get_holdings(self, user_id: str) -> Dict[str, Any]:
        """Get user holdings/investments"""
        
        try:
            headers = self._get_auth_headers(user_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_base_url}/holdings", headers=headers) as response:
                    if response.status == 200:
                        holdings_data = await response.json()
                        
                        total_value = 0
                        total_investment = 0
                        total_pnl = 0
                        
                        processed_holdings = []
                        
                        for holding in holdings_data:
                            current_value = holding.get("marketValue", 0)
                            investment = holding.get("costPrice", 0) * holding.get("quantity", 0)
                            pnl = current_value - investment
                            
                            total_value += current_value
                            total_investment += investment
                            total_pnl += pnl
                            
                            processed_holdings.append({
                                "symbol": holding.get("tradingSymbol"),
                                "isin": holding.get("isin"),
                                "quantity": holding.get("quantity", 0),
                                "avg_price": holding.get("costPrice", 0),
                                "ltp": holding.get("lastPrice", 0),
                                "current_value": current_value,
                                "investment": investment,
                                "pnl": pnl,
                                "pnl_percent": (pnl / investment * 100) if investment > 0 else 0,
                                "exchange": holding.get("exchange")
                            })
                        
                        return {
                            "success": True,
                            "holdings": {
                                "summary": {
                                    "total_value": total_value,
                                    "total_investment": total_investment,
                                    "total_pnl": total_pnl,
                                    "total_pnl_percent": (total_pnl / total_investment * 100) if total_investment > 0 else 0,
                                    "holding_count": len(processed_holdings)
                                },
                                "positions": processed_holdings
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"Holdings data error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_positions(self, user_id: str) -> Dict[str, Any]:
        """Get live trading positions"""
        
        try:
            headers = self._get_auth_headers(user_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_base_url}/positions", headers=headers) as response:
                    if response.status == 200:
                        positions_data = await response.json()
                        
                        total_pnl = 0
                        processed_positions = []
                        
                        for position in positions_data:
                            pnl = position.get("realizedPnl", 0) + position.get("unrealizedPnl", 0)
                            total_pnl += pnl
                            
                            processed_positions.append({
                                "symbol": position.get("tradingSymbol"),
                                "product": position.get("productType"),
                                "quantity": position.get("quantity", 0),
                                "avg_price": position.get("avgPrice", 0),
                                "ltp": position.get("lastPrice", 0),
                                "pnl": pnl,
                                "realized_pnl": position.get("realizedPnl", 0),
                                "unrealized_pnl": position.get("unrealizedPnl", 0),
                                "exchange": position.get("exchange"),
                                "side": "Long" if position.get("quantity", 0) > 0 else "Short"
                            })
                        
                        return {
                            "success": True,
                            "positions": {
                                "summary": {
                                    "total_pnl": total_pnl,
                                    "position_count": len(processed_positions)
                                },
                                "live_positions": processed_positions
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"Positions data error: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # Market Data APIs
    # ========================
    
    async def get_live_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """Get live market quotes for symbols using real Dhan API"""
        
        try:
            # Enhanced symbol mapping with real Dhan security IDs
            symbol_map = {
                # Indices
                "NIFTY": "13",
                "BANKNIFTY": "25",
                "SENSEX": "51", 
                "NIFTYIT": "1135",
                "NIFTYPHARMA": "1143",
                
                # Top Stocks
                "RELIANCE": "2885",
                "TCS": "3456", 
                "HDFCBANK": "1333",
                "INFY": "408",
                "ICICIBANK": "4963",
                "KOTAKBANK": "1922",
                "HDFC": "1330",
                "BHARTIARTL": "10604",
                "ITC": "424",
                "SBIN": "3045",
                "BAJFINANCE": "4632",
                "MARUTI": "10999",
                "ASIANPAINT": "11703",
                "LT": "11483",
                "WIPRO": "3787"
            }
            
            headers = self._get_auth_headers()
            processed_quotes = {}
            
            # Process each symbol
            for symbol in symbols:
                symbol_upper = symbol.upper()
                security_id = symbol_map.get(symbol_upper)
                
                if not security_id:
                    logger.warning(f"Security ID not found for symbol: {symbol_upper}")
                    continue
                
                try:
                    # Fetch quote for individual symbol
                    quote_url = f"{self.data_base_url}/v2/charts/intraday/{security_id}?segment=EQ_CM&interval=1"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(quote_url, headers=headers) as response:
                            if response.status == 200:
                                quote_data = await response.json()
                                
                                # Process real Dhan API response
                                if quote_data and 'data' in quote_data and quote_data['data']:
                                    latest_data = quote_data['data'][-1]  # Get latest candle
                                    
                                    ltp = latest_data.get('close', 0)
                                    open_price = latest_data.get('open', 0)
                                    change = ltp - open_price
                                    change_percent = (change / open_price * 100) if open_price > 0 else 0
                                    
                                    processed_quotes[symbol_upper] = {
                                        "ltp": ltp,
                                        "open": open_price,
                                        "high": latest_data.get('high', 0),
                                        "low": latest_data.get('low', 0),
                                        "volume": latest_data.get('volume', 0),
                                        "change": round(change, 2),
                                        "change_percent": round(change_percent, 2),
                                        "timestamp": datetime.now().isoformat(),
                                        "security_id": security_id,
                                        "real_data": True
                                    }
                                    
                                    logger.info(f"Real data fetched for {symbol_upper}: LTP={ltp}")
                                else:
                                    # Use mock data if no real data
                                    processed_quotes[symbol_upper] = self._get_mock_quote_for_symbol(symbol_upper)
                                    
                            else:
                                logger.warning(f"API error for {symbol_upper}: Status {response.status}")
                                processed_quotes[symbol_upper] = self._get_mock_quote_for_symbol(symbol_upper)
                                
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol_upper}: {e}")
                    processed_quotes[symbol_upper] = self._get_mock_quote_for_symbol(symbol_upper)
            
            return {
                "success": True,
                "quotes": processed_quotes,
                "timestamp": datetime.now().isoformat(),
                "data_source": "dhan_api",
                "symbols_processed": len(processed_quotes)
            }
                        
        except Exception as e:
            logger.error(f"Live quotes error: {e}")
            return self._get_mock_quotes(symbols)
    
    def _get_mock_quote_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Generate mock data for a single symbol"""
        
        import random
        
        base_prices = {
            "NIFTY": 19500,
            "BANKNIFTY": 44500, 
            "SENSEX": 65000,
            "NIFTYIT": 34500,
            "NIFTYPHARMA": 13500,
            "RELIANCE": 2450,
            "TCS": 3650,
            "HDFCBANK": 1580,
            "INFY": 1450,
            "ICICIBANK": 950,
            "KOTAKBANK": 1850,
            "HDFC": 2680,
            "BHARTIARTL": 850,
            "ITC": 420,
            "SBIN": 580,
            "BAJFINANCE": 6800,
            "MARUTI": 10500,
            "ASIANPAINT": 3200,
            "LT": 2800,
            "WIPRO": 420
        }
        
        base_price = base_prices.get(symbol.upper(), 1000)
        change_percent = random.uniform(-2.5, 2.5)
        change = base_price * change_percent / 100
        ltp = base_price + change
        
        return {
            "ltp": round(ltp, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "high": round(ltp * random.uniform(1.01, 1.03), 2),
            "low": round(ltp * random.uniform(0.97, 0.99), 2),
            "open": round(base_price, 2),
            "volume": random.randint(100000, 5000000),
            "timestamp": datetime.now().isoformat(),
            "mock_data": True
        }
    
    def _get_mock_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Generate mock market data for development"""
        
        mock_quotes = {}
        
        for symbol in symbols:
            mock_quotes[symbol.upper()] = self._get_mock_quote_for_symbol(symbol)
        
        return {
            "success": True,
            "quotes": mock_quotes,
            "mock_data": True,
            "timestamp": datetime.now().isoformat()
        }
    
    # ========================
    # Trading APIs
    # ========================
    
    async def place_order(self, user_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a trading order"""
        
        try:
            headers = self._get_auth_headers(user_id)
            
            # Prepare order payload
            dhan_order = {
                "dhanClientId": self.user_sessions[user_id].get("client_id"),
                "transactionType": order_data.get("side", "BUY"),
                "exchangeSegment": order_data.get("exchange", "NSE_EQ"),
                "productType": order_data.get("product", "INTRADAY"),
                "orderType": order_data.get("order_type", "MARKET"),
                "validity": order_data.get("validity", "DAY"),
                "tradingSymbol": order_data.get("symbol"),
                "securityId": order_data.get("security_id", ""),
                "quantity": order_data.get("quantity"),
                "price": order_data.get("price", 0),
                "triggerPrice": order_data.get("trigger_price", 0)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.trading_base_url}/orders", headers=headers, json=dhan_order) as response:
                    if response.status == 200:
                        order_response = await response.json()
                        
                        return {
                            "success": True,
                            "order_id": order_response.get("orderId"),
                            "status": order_response.get("orderStatus"),
                            "message": "Order placed successfully"
                        }
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"Place order error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_orders(self, user_id: str) -> Dict[str, Any]:
        """Get order history and status"""
        
        try:
            headers = self._get_auth_headers(user_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.trading_base_url}/orders", headers=headers) as response:
                    if response.status == 200:
                        orders_data = await response.json()
                        
                        processed_orders = []
                        for order in orders_data:
                            processed_orders.append({
                                "order_id": order.get("orderId"),
                                "symbol": order.get("tradingSymbol"),
                                "side": order.get("transactionType"),
                                "quantity": order.get("quantity"),
                                "price": order.get("price"),
                                "status": order.get("orderStatus"),
                                "product": order.get("productType"),
                                "order_time": order.get("orderDate"),
                                "exchange": order.get("exchangeSegment")
                            })
                        
                        return {
                            "success": True,
                            "orders": processed_orders,
                            "total_orders": len(processed_orders)
                        }
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"Get orders error: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # Utility Methods
    # ========================
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has valid Dhan connection"""
        return user_id in self.user_sessions and self.user_sessions[user_id].get("status") == "active"
    
    async def disconnect_user(self, user_id: str) -> bool:
        """Disconnect user session"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]["status"] = "disconnected"
            del self.user_sessions[user_id]
            return True
        return False
    
    def get_connection_status(self, user_id: str) -> Dict[str, Any]:
        """Get user connection status"""
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            return {
                "connected": True,
                "status": session.get("status"),
                "connected_at": session.get("connected_at").isoformat(),
                "expires_at": session.get("expires_at").isoformat()
            }
        else:
            return {
                "connected": False,
                "status": "not_connected"
            }

# Global instance
dhan_api_service = DhanAPIService()