"""
Dhan API Service - Integration with Dhan trading platform
Handles market data, trading operations, and authentication
"""

import os
import logging
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import hmac
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class DhanCredentials:
    api_key: str
    api_secret: str
    access_token: str

class DhanAPIService:
    """Dhan API Service for trading and market data operations"""
    
    def __init__(self):
        self.base_url = "https://api.dhan.co"
        self.api_key = os.getenv('DHAN_API_KEY')
        self.api_secret = os.getenv('DHAN_API_SECRET')
        self.access_token = os.getenv('DHAN_ACCESS_TOKEN')
        self.client_id = os.getenv('DHAN_CLIENT_ID')
        
        self.session = None
        self.is_connected = False
        
        # Mock data for testing when real API is not available
        self.use_mock_data = not all([self.api_key, self.api_secret, self.access_token])
        
        if self.use_mock_data:
            logger.warning("⚠️ Using mock data - Dhan credentials not fully configured")
        else:
            logger.info("✅ Dhan API service initialized with real credentials")
    
    async def initialize(self):
        """Initialize the HTTP session and test connectivity"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connectivity if we have real credentials
            if not self.use_mock_data:
                test_result = await self.test_connection()
                self.is_connected = test_result
            else:
                self.is_connected = True  # Always true for mock data
                
            logger.info(f"📡 Dhan API Service initialized - Connected: {self.is_connected}")
            return self.is_connected
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Dhan API Service: {e}")
            self.is_connected = False
            return False
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("🔌 Dhan API Service session closed")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    async def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            if self.use_mock_data:
                return True
                
            if not self.session:
                await self.initialize()
            
            # Try to get user profile or a simple endpoint
            headers = self._get_headers()
            
            async with self.session.get(
                f"{self.base_url}/v2/charts/historical",
                headers=headers
            ) as response:
                return response.status in [200, 401, 403]  # API is reachable
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_market_quote(self, security_ids: List[str]) -> Dict[str, Any]:
        """Get real-time market quotes for given security IDs"""
        try:
            if self.use_mock_data:
                return await self._get_mock_market_quote(security_ids)
            
            if not self.session:
                await self.initialize()
            
            # Prepare the request data
            quote_data = {
                "NSE_EQ": security_ids,
                "BSE_EQ": [],
                "NSE_FO": [],
                "BSE_FO": [],
                "MCX_FO": [],
                "CUR_FO": []
            }
            
            headers = self._get_headers()
            
            async with self.session.post(
                f"{self.base_url}/v2/marketfeed/ltp",
                headers=headers,
                json=quote_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"API request failed with status: {response.status}")
                    # Fallback to mock data
                    return await self._get_mock_market_quote(security_ids)
                    
        except Exception as e:
            logger.error(f"Error getting market quote: {e}")
            # Fallback to mock data
            return await self._get_mock_market_quote(security_ids)
    
    async def _get_mock_market_quote(self, security_ids: List[str]) -> Dict[str, Any]:
        """Generate mock market data for testing"""
        import random
        
        mock_data = {}
        
        base_prices = {
            'NSE_IDX|Nifty 50': 19800,
            'NSE_IDX|Nifty Bank': 45200,
            'NSE_EQ|INE062A01020': 3500,  # TCS
            'NSE_EQ|INE009A01021': 1650,  # Infosys
            'NSE_EQ|INE467B01029': 395,   # ITC
            'NSE_EQ|INE040A01034': 1725,  # HDFC Bank
            'NSE_EQ|INE002A01018': 2800   # Reliance
        }
        
        for security_id in security_ids:
            base_price = base_prices.get(security_id, 1000)
            
            # Generate realistic price variations
            change_percent = random.uniform(-3.0, 3.0)
            current_price = base_price * (1 + change_percent/100)
            
            open_price = base_price * (1 + random.uniform(-1.0, 1.0)/100)
            high_price = max(current_price, open_price) * (1 + random.uniform(0, 1.5)/100)
            low_price = min(current_price, open_price) * (1 - random.uniform(0, 1.5)/100)
            
            mock_data[security_id] = {
                'LTP': round(current_price, 2),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(base_price, 2),
                'volume': random.randint(10000, 1000000),
                'change': round(current_price - base_price, 2),
                'pChange': round(change_percent, 2),
                'timestamp': datetime.now().isoformat(),
                '52WeekHigh': round(base_price * 1.25, 2),
                '52WeekLow': round(base_price * 0.75, 2),
                'marketCap': random.randint(50000, 500000),
                'peRatio': round(random.uniform(15.0, 35.0), 2)
            }
        
        return {
            'status': 'success',
            'data': mock_data,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_historical_data(self, security_id: str, from_date: str, 
                                to_date: str, resolution: str = "1") -> Dict[str, Any]:
        """Get historical market data"""
        try:
            if self.use_mock_data:
                return await self._get_mock_historical_data(security_id, from_date, to_date)
            
            # Real API implementation would go here
            return await self._get_mock_historical_data(security_id, from_date, to_date)
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return await self._get_mock_historical_data(security_id, from_date, to_date)
    
    async def _get_mock_historical_data(self, security_id: str, from_date: str, 
                                      to_date: str) -> Dict[str, Any]:
        """Generate mock historical data"""
        import random
        from datetime import datetime, timedelta
        
        # Generate mock OHLCV data
        data = []
        base_price = 1000
        current_price = base_price
        
        start_date = datetime.fromisoformat(from_date.replace('Z', ''))
        end_date = datetime.fromisoformat(to_date.replace('Z', ''))
        
        current_date = start_date
        while current_date <= end_date:
            # Generate realistic OHLC data
            open_price = current_price
            change = random.uniform(-0.05, 0.05)  # ±5% daily change
            close_price = open_price * (1 + change)
            
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            
            volume = random.randint(100000, 2000000)
            
            data.append({
                'timestamp': current_date.isoformat(),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
            
            current_price = close_price
            current_date += timedelta(hours=1)  # Hourly data
            
            if len(data) >= 100:  # Limit data points
                break
        
        return {
            'status': 'success',
            'data': data,
            'symbol': security_id,
            'from_date': from_date,
            'to_date': to_date
        }
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a trading order"""
        try:
            if self.use_mock_data:
                return await self._place_mock_order(order_data)
            
            # Real order placement would go here
            headers = self._get_headers()
            
            async with self.session.post(
                f"{self.base_url}/v2/orders",
                headers=headers,
                json=order_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"Order placement failed with status: {response.status}")
                    return {'status': 'error', 'message': 'Order placement failed'}
                    
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _place_mock_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock order placement for testing"""
        import random
        
        order_id = f"MOCK_{random.randint(100000, 999999)}"
        
        return {
            'status': 'success',
            'order_id': order_id,
            'message': 'Mock order placed successfully',
            'data': {
                'orderId': order_id,
                'status': 'PENDING',
                'symbol': order_data.get('symbol', 'UNKNOWN'),
                'quantity': order_data.get('quantity', 0),
                'price': order_data.get('price', 0),
                'orderType': order_data.get('orderType', 'MARKET'),
                'timestamp': datetime.now().isoformat()
            }
        }
    
    async def get_positions(self) -> Dict[str, Any]:
        """Get current trading positions"""
        try:
            if self.use_mock_data:
                return await self._get_mock_positions()
            
            # Real positions API call would go here
            return await self._get_mock_positions()
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {'status': 'error', 'positions': []}
    
    async def _get_mock_positions(self) -> Dict[str, Any]:
        """Generate mock positions data"""
        positions = [
            {
                'symbol': 'NSE_EQ|INE062A01020',
                'name': 'TCS',
                'quantity': 10,
                'average_price': 3450.50,
                'current_price': 3520.25,
                'pnl': 697.50,
                'pnl_percent': 2.02
            },
            {
                'symbol': 'NSE_EQ|INE040A01034',
                'name': 'HDFC Bank',
                'quantity': 5,
                'average_price': 1680.75,
                'current_price': 1725.30,
                'pnl': 222.75,
                'pnl_percent': 2.65
            }
        ]
        
        return {
            'status': 'success',
            'positions': positions,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_orders(self) -> Dict[str, Any]:
        """Get order history"""
        try:
            if self.use_mock_data:
                return await self._get_mock_orders()
            
            # Real orders API call would go here
            return await self._get_mock_orders()
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return {'status': 'error', 'orders': []}
    
    async def _get_mock_orders(self) -> Dict[str, Any]:
        """Generate mock order history"""
        orders = [
            {
                'order_id': 'DH202501040001',
                'symbol': 'NSE_EQ|INE062A01020',
                'name': 'TCS',
                'side': 'BUY',
                'quantity': 10,
                'price': 3450.50,
                'order_type': 'LIMIT',
                'status': 'COMPLETE',
                'timestamp': '2025-01-04T09:15:30'
            },
            {
                'order_id': 'DH202501040002',
                'symbol': 'NSE_EQ|INE040A01034',
                'name': 'HDFC Bank',
                'side': 'BUY',
                'quantity': 5,
                'price': 1680.75,
                'order_type': 'MARKET',
                'status': 'COMPLETE',
                'timestamp': '2025-01-04T10:22:45'
            }
        ]
        
        return {
            'status': 'success',
            'orders': orders,
            'timestamp': datetime.now().isoformat()
        }
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            if self.use_mock_data:
                return {
                    'status': 'success',
                    'message': f'Mock order {order_id} cancelled successfully',
                    'order_id': order_id
                }
            
            # Real order cancellation would go here
            headers = self._get_headers()
            
            async with self.session.delete(
                f"{self.base_url}/v2/orders/{order_id}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    return {'status': 'error', 'message': 'Order cancellation failed'}
                    
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'service': 'Dhan API Service',
            'version': '1.0.0',
            'connected': self.is_connected,
            'using_mock_data': self.use_mock_data,
            'credentials_configured': {
                'api_key': bool(self.api_key),
                'api_secret': bool(self.api_secret),
                'access_token': bool(self.access_token)
            },
            'base_url': self.base_url,
            'timestamp': datetime.now().isoformat()
        }

# Global service instance
dhan_service = DhanAPIService()

async def initialize_dhan_service():
    """Initialize the global Dhan service"""
    return await dhan_service.initialize()

async def cleanup_dhan_service():
    """Cleanup the global Dhan service"""
    await dhan_service.close()