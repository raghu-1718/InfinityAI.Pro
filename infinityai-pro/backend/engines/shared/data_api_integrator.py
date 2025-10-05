"""
Real-time Data API Integrator
InfinityAI.Pro Trading Platform

Comprehensive integration for Dhan and Angel Broking APIs
Provides unified interface for market data, OHLCV, and option chains
"""

import asyncio
import aiohttp
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import websockets
import threading
from concurrent.futures import ThreadPoolExecutor

# Dhan API SDK
try:
    from dhanhq import dhanhq
except ImportError:
    dhanhq = None

# Angel Broking SDK
try:
    from smartapi import SmartConnect
except ImportError:
    SmartConnect = None


class DataProvider(Enum):
    DHAN = "DHAN"
    ANGEL_BROKING = "ANGEL_BROKING"
    COMBINED = "COMBINED"


class SubscriptionType(Enum):
    TICK_DATA = "TICK_DATA"
    OHLC_DATA = "OHLC_DATA"
    OPTION_CHAIN = "OPTION_CHAIN"
    ORDER_UPDATES = "ORDER_UPDATES"


@dataclass
class MarketDataConfig:
    """Configuration for market data providers"""
    # Required Dhan configuration (no defaults)
    dhan_client_id: str
    dhan_access_token: str
    
    # Required Angel Broking configuration (no defaults)
    angel_api_key: str
    angel_client_code: str
    angel_password: str
    angel_totp: str
    
    # Optional configuration with defaults
    dhan_base_url: str = "https://api.dhan.co"
    angel_base_url: str = "https://apiconnect.angelbroking.com"
    primary_provider: DataProvider = DataProvider.DHAN
    fallback_provider: DataProvider = DataProvider.ANGEL_BROKING
    enable_websocket: bool = True
    enable_historical_data: bool = True
    max_retries: int = 3
    timeout: int = 30


class UnifiedDataProvider:
    """
    Unified data provider that aggregates data from multiple sources
    Provides failover and data validation capabilities
    """
    
    def __init__(self, config: MarketDataConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize providers
        self.dhan_client = None
        self.angel_client = None
        
        # WebSocket connections
        self.websocket_connections = {}
        self.subscriptions = {}
        
        # Data cache
        self.data_cache = {}
        self.last_update = {}
        
        # Initialize providers
        self._initialize_providers()
        
        self.logger.info("Unified Data Provider initialized successfully")

    def _initialize_providers(self):
        """Initialize all data providers"""
        try:
            # Initialize Dhan client
            if dhanhq and self.config.dhan_access_token:
                self.dhan_client = dhanhq(
                    client_id=self.config.dhan_client_id,
                    access_token=self.config.dhan_access_token
                )
                self.logger.info("Dhan client initialized")
            
            # Initialize Angel Broking client
            if SmartConnect and self.config.angel_api_key:
                self.angel_client = SmartConnect(
                    api_key=self.config.angel_api_key
                )
                
                # Login to Angel Broking
                angel_login = self.angel_client.generateSession(
                    self.config.angel_client_code,
                    self.config.angel_password,
                    self.config.angel_totp
                )
                
                if angel_login['status']:
                    self.logger.info("Angel Broking client initialized and logged in")
                else:
                    self.logger.error(f"Angel Broking login failed: {angel_login}")
                    
        except Exception as e:
            self.logger.error(f"Error initializing providers: {e}")

    async def get_real_time_price(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get real-time price for a symbol"""
        try:
            # Try primary provider first
            if self.config.primary_provider == DataProvider.DHAN:
                data = await self._get_dhan_price(symbol, exchange)
                if data:
                    return self._format_price_data(data, DataProvider.DHAN)
            
            # Try fallback provider
            if self.config.fallback_provider == DataProvider.ANGEL_BROKING:
                data = await self._get_angel_price(symbol, exchange)
                if data:
                    return self._format_price_data(data, DataProvider.ANGEL_BROKING)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting real-time price for {symbol}: {e}")
            return {}

    async def _get_dhan_price(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Get price data from Dhan API"""
        try:
            if not self.dhan_client:
                return None
            
            # Get instrument token (simplified mapping)
            instrument_token = self._get_dhan_instrument_token(symbol, exchange)
            if not instrument_token:
                return None
            
            # Get real-time data
            response = self.dhan_client.get_ltp_data(
                exchange_segment=exchange,
                instrument_token=instrument_token
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting Dhan price for {symbol}: {e}")
            return None

    async def _get_angel_price(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Get price data from Angel Broking API"""
        try:
            if not self.angel_client:
                return None
            
            # Get LTP data
            response = self.angel_client.ltpData(
                exchange=exchange,
                tradingsymbol=symbol,
                symboltoken=self._get_angel_symbol_token(symbol, exchange)
            )
            
            return response.get('data', {})
            
        except Exception as e:
            self.logger.error(f"Error getting Angel price for {symbol}: {e}")
            return None

    def _format_price_data(self, data: Dict, provider: DataProvider) -> Dict:
        """Format price data to unified structure"""
        try:
            if provider == DataProvider.DHAN:
                return {
                    'symbol': data.get('symbol', ''),
                    'ltp': float(data.get('ltp', 0)),
                    'open': float(data.get('open', 0)),
                    'high': float(data.get('high', 0)),
                    'low': float(data.get('low', 0)),
                    'close': float(data.get('prev_close', 0)),
                    'volume': int(data.get('volume', 0)),
                    'change': float(data.get('change', 0)),
                    'change_percent': float(data.get('change_percent', 0)),
                    'timestamp': datetime.now(),
                    'provider': 'DHAN'
                }
            
            elif provider == DataProvider.ANGEL_BROKING:
                return {
                    'symbol': data.get('symbolname', ''),
                    'ltp': float(data.get('ltp', 0)),
                    'open': float(data.get('open', 0)),
                    'high': float(data.get('high', 0)),
                    'low': float(data.get('low', 0)),
                    'close': float(data.get('close', 0)),
                    'volume': int(data.get('volume', 0)),
                    'change': float(data.get('change', 0)),
                    'change_percent': float(data.get('pChange', 0)),
                    'timestamp': datetime.now(),
                    'provider': 'ANGEL_BROKING'
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error formatting price data: {e}")
            return {}

    async def get_historical_data(
        self, 
        symbol: str, 
        exchange: str = "NSE",
        interval: str = "1minute",
        from_date: datetime = None,
        to_date: datetime = None
    ) -> pd.DataFrame:
        """Get historical OHLCV data"""
        try:
            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            if not to_date:
                to_date = datetime.now()
            
            # Try primary provider
            if self.config.primary_provider == DataProvider.DHAN:
                data = await self._get_dhan_historical_data(
                    symbol, exchange, interval, from_date, to_date
                )
                if not data.empty:
                    return data
            
            # Try fallback provider
            if self.config.fallback_provider == DataProvider.ANGEL_BROKING:
                data = await self._get_angel_historical_data(
                    symbol, exchange, interval, from_date, to_date
                )
                if not data.empty:
                    return data
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()

    async def _get_dhan_historical_data(
        self, symbol: str, exchange: str, interval: str, 
        from_date: datetime, to_date: datetime
    ) -> pd.DataFrame:
        """Get historical data from Dhan"""
        try:
            if not self.dhan_client:
                return pd.DataFrame()
            
            instrument_token = self._get_dhan_instrument_token(symbol, exchange)
            if not instrument_token:
                return pd.DataFrame()
            
            # Convert interval format
            dhan_interval = self._convert_interval_to_dhan_format(interval)
            
            # Get historical data
            response = self.dhan_client.historical_minute_charts(
                symbol=symbol,
                exchange_segment=exchange,
                instrument_type="EQUITY",
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d")
            )
            
            if response and 'data' in response:
                df = pd.DataFrame(response['data'])
                return self._format_historical_data(df, DataProvider.DHAN)
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error getting Dhan historical data: {e}")
            return pd.DataFrame()

    async def _get_angel_historical_data(
        self, symbol: str, exchange: str, interval: str,
        from_date: datetime, to_date: datetime
    ) -> pd.DataFrame:
        """Get historical data from Angel Broking"""
        try:
            if not self.angel_client:
                return pd.DataFrame()
            
            # Get symbol token
            symbol_token = self._get_angel_symbol_token(symbol, exchange)
            
            # Convert interval format
            angel_interval = self._convert_interval_to_angel_format(interval)
            
            # Get historical data
            response = self.angel_client.getCandleData(
                exchange=exchange,
                symboltoken=symbol_token,
                interval=angel_interval,
                fromdate=from_date.strftime("%Y-%m-%d %H:%M"),
                todate=to_date.strftime("%Y-%m-%d %H:%M")
            )
            
            if response['status'] and response['data']:
                df = pd.DataFrame(
                    response['data'],
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                return self._format_historical_data(df, DataProvider.ANGEL_BROKING)
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error getting Angel historical data: {e}")
            return pd.DataFrame()

    def _format_historical_data(self, df: pd.DataFrame, provider: DataProvider) -> pd.DataFrame:
        """Format historical data to unified structure"""
        try:
            if df.empty:
                return df
            
            if provider == DataProvider.DHAN:
                # Dhan format adjustment
                if 'start_time' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['start_time'])
                
            elif provider == DataProvider.ANGEL_BROKING:
                # Angel format adjustment
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Ensure standard columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 0 if col == 'volume' else 0.0
            
            # Convert to proper data types
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df[required_columns]
            
        except Exception as e:
            self.logger.error(f"Error formatting historical data: {e}")
            return pd.DataFrame()

    async def get_option_chain(self, symbol: str = "NIFTY", expiry_date: str = None) -> Dict:
        """Get complete option chain data"""
        try:
            # Try primary provider
            if self.config.primary_provider == DataProvider.DHAN:
                data = await self._get_dhan_option_chain(symbol, expiry_date)
                if data:
                    return data
            
            # Try fallback provider
            if self.config.fallback_provider == DataProvider.ANGEL_BROKING:
                data = await self._get_angel_option_chain(symbol, expiry_date)
                if data:
                    return data
            
            return {'calls': [], 'puts': []}
            
        except Exception as e:
            self.logger.error(f"Error getting option chain for {symbol}: {e}")
            return {'calls': [], 'puts': []}

    async def _get_dhan_option_chain(self, symbol: str, expiry_date: str) -> Dict:
        """Get option chain from Dhan"""
        try:
            if not self.dhan_client:
                return {}
            
            # Get option chain data
            response = self.dhan_client.get_option_chain(
                symbol=symbol,
                expiry=expiry_date
            )
            
            if response and 'data' in response:
                return self._format_option_chain(response['data'], DataProvider.DHAN)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting Dhan option chain: {e}")
            return {}

    async def _get_angel_option_chain(self, symbol: str, expiry_date: str) -> Dict:
        """Get option chain from Angel Broking"""
        try:
            if not self.angel_client:
                return {}
            
            # Angel Broking doesn't have a direct option chain API
            # We need to construct it from individual option contracts
            # This is a simplified implementation
            
            calls = []
            puts = []
            
            # Get current price for strike range
            current_price_data = await self._get_angel_price(symbol, "NSE")
            if not current_price_data:
                return {}
            
            current_price = float(current_price_data.get('ltp', 0))
            
            # Generate strike range (±10% from current price)
            base_strikes = range(
                int(current_price * 0.9 // 50) * 50,
                int(current_price * 1.1 // 50 + 1) * 50,
                50
            )
            
            for strike in base_strikes:
                # Get call option data
                call_symbol = f"{symbol}{expiry_date}{strike}CE"
                call_data = await self._get_angel_price(call_symbol, "NFO")
                if call_data:
                    calls.append({
                        'strike': strike,
                        'symbol': call_symbol,
                        'ltp': call_data.get('ltp', 0),
                        'type': 'CALL',
                        'expiry': expiry_date
                    })
                
                # Get put option data
                put_symbol = f"{symbol}{expiry_date}{strike}PE"
                put_data = await self._get_angel_price(put_symbol, "NFO")
                if put_data:
                    puts.append({
                        'strike': strike,
                        'symbol': put_symbol,
                        'ltp': put_data.get('ltp', 0),
                        'type': 'PUT',
                        'expiry': expiry_date
                    })
            
            return {'calls': calls, 'puts': puts}
            
        except Exception as e:
            self.logger.error(f"Error getting Angel option chain: {e}")
            return {}

    def _format_option_chain(self, data: List[Dict], provider: DataProvider) -> Dict:
        """Format option chain data to unified structure"""
        try:
            calls = []
            puts = []
            
            for option in data:
                formatted_option = {
                    'strike': float(option.get('strike_price', 0)),
                    'symbol': option.get('symbol', ''),
                    'ltp': float(option.get('ltp', 0)),
                    'bid': float(option.get('bid', 0)),
                    'ask': float(option.get('ask', 0)),
                    'volume': int(option.get('volume', 0)),
                    'open_interest': int(option.get('open_interest', 0)),
                    'iv': float(option.get('iv', 0)),
                    'delta': float(option.get('delta', 0)),
                    'gamma': float(option.get('gamma', 0)),
                    'theta': float(option.get('theta', 0)),
                    'vega': float(option.get('vega', 0)),
                    'days_to_expiry': int(option.get('days_to_expiry', 0)),
                    'type': option.get('option_type', ''),
                    'expiry': option.get('expiry_date', ''),
                    'provider': provider.value
                }
                
                if option.get('option_type') == 'CALL':
                    calls.append(formatted_option)
                elif option.get('option_type') == 'PUT':
                    puts.append(formatted_option)
            
            return {
                'calls': sorted(calls, key=lambda x: x['strike']),
                'puts': sorted(puts, key=lambda x: x['strike']),
                'timestamp': datetime.now(),
                'provider': provider.value
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting option chain: {e}")
            return {'calls': [], 'puts': []}

    async def get_gift_nifty_data(self) -> Dict:
        """Get Gift Nifty futures data"""
        try:
            # Gift Nifty is traded on SGX, but we can get approximate data
            # from Nifty futures or use alternative data sources
            
            symbol = "NIFTY"
            exchange = "NFO"  # Futures segment
            
            # Get current month futures data as proxy
            current_month = datetime.now().strftime("%b").upper()
            year = datetime.now().strftime("%y")
            futures_symbol = f"NIFTY{current_month}{year}FUT"
            
            price_data = await self.get_real_time_price(futures_symbol, exchange)
            
            if price_data:
                return {
                    'symbol': 'GIFT_NIFTY',
                    'price': price_data['ltp'],
                    'open': price_data['open'],
                    'high': price_data['high'],
                    'low': price_data['low'],
                    'close': price_data['close'],
                    'volume': price_data['volume'],
                    'change': price_data['change'],
                    'change_percent': price_data['change_percent'],
                    'timestamp': datetime.now(),
                    'note': 'Approximated from Nifty Futures'
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting Gift Nifty data: {e}")
            return {}

    async def subscribe_to_real_time_data(
        self, 
        symbols: List[str], 
        callback_func,
        subscription_type: SubscriptionType = SubscriptionType.TICK_DATA
    ):
        """Subscribe to real-time data stream"""
        try:
            if self.config.enable_websocket:
                # Start WebSocket connection for real-time data
                if self.config.primary_provider == DataProvider.DHAN:
                    await self._start_dhan_websocket(symbols, callback_func)
                elif self.config.primary_provider == DataProvider.ANGEL_BROKING:
                    await self._start_angel_websocket(symbols, callback_func)
            
        except Exception as e:
            self.logger.error(f"Error subscribing to real-time data: {e}")

    async def _start_dhan_websocket(self, symbols: List[str], callback_func):
        """Start Dhan WebSocket connection"""
        try:
            # This would typically use Dhan's WebSocket API
            # Simplified implementation for demonstration
            self.logger.info(f"Starting Dhan WebSocket for symbols: {symbols}")
            
            # In actual implementation, you would:
            # 1. Connect to Dhan WebSocket endpoint
            # 2. Send subscription message
            # 3. Handle incoming tick data
            # 4. Call callback_func with formatted data
            
        except Exception as e:
            self.logger.error(f"Error starting Dhan WebSocket: {e}")

    async def _start_angel_websocket(self, symbols: List[str], callback_func):
        """Start Angel Broking WebSocket connection"""
        try:
            # This would typically use Angel's WebSocket API
            # Simplified implementation for demonstration
            self.logger.info(f"Starting Angel WebSocket for symbols: {symbols}")
            
            # In actual implementation, you would:
            # 1. Connect to Angel WebSocket endpoint
            # 2. Send subscription message
            # 3. Handle incoming tick data
            # 4. Call callback_func with formatted data
            
        except Exception as e:
            self.logger.error(f"Error starting Angel WebSocket: {e}")

    def _get_dhan_instrument_token(self, symbol: str, exchange: str) -> Optional[str]:
        """Get Dhan instrument token for symbol"""
        # This would typically involve looking up instrument master file
        # Simplified implementation
        token_map = {
            "NIFTY": "13",
            "BANKNIFTY": "25",
            "FINNIFTY": "26"
        }
        return token_map.get(symbol)

    def _get_angel_symbol_token(self, symbol: str, exchange: str) -> Optional[str]:
        """Get Angel Broking symbol token"""
        # This would typically involve looking up instrument master file
        # Simplified implementation
        token_map = {
            "NIFTY": "99926000",
            "BANKNIFTY": "99926009",
            "FINNIFTY": "99926037"
        }
        return token_map.get(symbol)

    def _convert_interval_to_dhan_format(self, interval: str) -> str:
        """Convert interval to Dhan format"""
        interval_map = {
            "1minute": "1",
            "5minute": "5",
            "15minute": "15",
            "1hour": "60",
            "1day": "1D"
        }
        return interval_map.get(interval, "1")

    def _convert_interval_to_angel_format(self, interval: str) -> str:
        """Convert interval to Angel format"""
        interval_map = {
            "1minute": "ONE_MINUTE",
            "5minute": "FIVE_MINUTE",
            "15minute": "FIFTEEN_MINUTE",
            "1hour": "ONE_HOUR",
            "1day": "ONE_DAY"
        }
        return interval_map.get(interval, "ONE_MINUTE")

    async def get_market_depth(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get market depth (Level 2) data"""
        try:
            # Try to get market depth from primary provider
            if self.config.primary_provider == DataProvider.DHAN and self.dhan_client:
                response = self.dhan_client.get_market_depth(
                    exchange_segment=exchange,
                    instrument_token=self._get_dhan_instrument_token(symbol, exchange)
                )
                return self._format_market_depth(response, DataProvider.DHAN)
            
            elif self.config.fallback_provider == DataProvider.ANGEL_BROKING and self.angel_client:
                response = self.angel_client.getMarketData(
                    mode="FULL",
                    exchangeTokens={
                        exchange: [self._get_angel_symbol_token(symbol, exchange)]
                    }
                )
                return self._format_market_depth(response, DataProvider.ANGEL_BROKING)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting market depth for {symbol}: {e}")
            return {}

    def _format_market_depth(self, data: Dict, provider: DataProvider) -> Dict:
        """Format market depth data"""
        try:
            if provider == DataProvider.DHAN:
                return {
                    'bids': data.get('bids', []),
                    'asks': data.get('asks', []),
                    'total_buy_quantity': data.get('total_buy_qty', 0),
                    'total_sell_quantity': data.get('total_sell_qty', 0),
                    'timestamp': datetime.now(),
                    'provider': 'DHAN'
                }
            
            elif provider == DataProvider.ANGEL_BROKING:
                market_data = data.get('data', {}).get('fetched', [])
                if market_data:
                    md = market_data[0]
                    return {
                        'bids': [
                            {'price': md.get(f'buyPrice{i}', 0), 'quantity': md.get(f'buyQuantity{i}', 0)}
                            for i in range(1, 6)
                        ],
                        'asks': [
                            {'price': md.get(f'sellPrice{i}', 0), 'quantity': md.get(f'sellQuantity{i}', 0)}
                            for i in range(1, 6)
                        ],
                        'total_buy_quantity': sum([md.get(f'buyQuantity{i}', 0) for i in range(1, 6)]),
                        'total_sell_quantity': sum([md.get(f'sellQuantity{i}', 0) for i in range(1, 6)]),
                        'timestamp': datetime.now(),
                        'provider': 'ANGEL_BROKING'
                    }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error formatting market depth: {e}")
            return {}

    async def get_portfolio_data(self) -> Dict:
        """Get portfolio/holdings data"""
        try:
            portfolio_data = {
                'holdings': [],
                'positions': [],
                'funds': {},
                'total_pnl': 0.0,
                'timestamp': datetime.now()
            }
            
            # Get data from primary provider
            if self.config.primary_provider == DataProvider.DHAN and self.dhan_client:
                holdings = self.dhan_client.get_holdings()
                positions = self.dhan_client.get_positions()
                funds = self.dhan_client.get_fund_limits()
                
                portfolio_data.update({
                    'holdings': holdings.get('data', []),
                    'positions': positions.get('data', []),
                    'funds': funds.get('data', {}),
                    'provider': 'DHAN'
                })
            
            elif self.config.fallback_provider == DataProvider.ANGEL_BROKING and self.angel_client:
                holdings = self.angel_client.holding()
                positions = self.angel_client.position()
                rms = self.angel_client.rmsLimit()
                
                portfolio_data.update({
                    'holdings': holdings.get('data', []),
                    'positions': positions.get('data', []),
                    'funds': rms.get('data', {}),
                    'provider': 'ANGEL_BROKING'
                })
            
            return portfolio_data
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio data: {e}")
            return {}

    async def validate_data_integrity(self, data: Dict) -> bool:
        """Validate data integrity and consistency"""
        try:
            if not data:
                return False
            
            # Basic validation checks
            required_fields = ['ltp', 'timestamp']
            for field in required_fields:
                if field not in data:
                    return False
            
            # Price validation
            ltp = float(data.get('ltp', 0))
            if ltp <= 0:
                return False
            
            # Timestamp validation
            timestamp = data.get('timestamp')
            if not isinstance(timestamp, datetime):
                return False
            
            # Check if data is not too old (more than 5 minutes)
            if datetime.now() - timestamp > timedelta(minutes=5):
                self.logger.warning("Data is older than 5 minutes")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating data integrity: {e}")
            return False

    async def health_check(self) -> Dict:
        """Perform health check on all providers"""
        try:
            health_status = {
                'dhan': {'status': 'DOWN', 'error': None},
                'angel_broking': {'status': 'DOWN', 'error': None},
                'overall': 'DOWN',
                'timestamp': datetime.now()
            }
            
            # Check Dhan connectivity
            if self.dhan_client:
                try:
                    # Try to get a simple data point
                    test_response = await self._get_dhan_price("NIFTY", "NSE")
                    if test_response:
                        health_status['dhan']['status'] = 'UP'
                except Exception as e:
                    health_status['dhan']['error'] = str(e)
            
            # Check Angel Broking connectivity
            if self.angel_client:
                try:
                    # Try to get profile data
                    profile = self.angel_client.getProfile()
                    if profile.get('status'):
                        health_status['angel_broking']['status'] = 'UP'
                except Exception as e:
                    health_status['angel_broking']['error'] = str(e)
            
            # Determine overall status
            if (health_status['dhan']['status'] == 'UP' or 
                health_status['angel_broking']['status'] == 'UP'):
                health_status['overall'] = 'UP'
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return {'overall': 'DOWN', 'error': str(e)}


# Factory function to create data provider
def create_data_provider(config: MarketDataConfig) -> UnifiedDataProvider:
    """Create unified data provider with configuration"""
    return UnifiedDataProvider(config)


# Configuration helper
def create_default_config(
    dhan_client_id: str,
    dhan_access_token: str,
    angel_api_key: str = "",
    angel_client_code: str = "",
    angel_password: str = "",
    angel_totp: str = ""
) -> MarketDataConfig:
    """Create default configuration"""
    return MarketDataConfig(
        dhan_client_id=dhan_client_id,
        dhan_access_token=dhan_access_token,
        angel_api_key=angel_api_key,
        angel_client_code=angel_client_code,
        angel_password=angel_password,
        angel_totp=angel_totp
    )


# Example usage and testing
async def test_data_provider():
    """Test the data provider functionality"""
    # Create configuration
    config = create_default_config(
        dhan_client_id="1101302170",
        dhan_access_token="your_dhan_token_here"
    )
    
    # Create provider
    provider = create_data_provider(config)
    
    # Test health check
    health = await provider.health_check()
    print(f"Health Status: {health}")
    
    # Test real-time price
    price_data = await provider.get_real_time_price("NIFTY", "NSE")
    print(f"NIFTY Price: {price_data}")
    
    # Test historical data
    hist_data = await provider.get_historical_data("NIFTY", "NSE")
    print(f"Historical Data Shape: {hist_data.shape}")
    
    # Test option chain
    option_chain = await provider.get_option_chain("NIFTY")
    print(f"Option Chain - Calls: {len(option_chain.get('calls', []))}, Puts: {len(option_chain.get('puts', []))}")


if __name__ == "__main__":
    asyncio.run(test_data_provider())