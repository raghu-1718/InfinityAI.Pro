import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import logging
import json

from dhanhq import dhanhq, DhanContext
from .dhan_adapter import DhanAdapter

logger = logging.getLogger(__name__)

class EnhancedDhanAdapter(DhanAdapter):
    """Enhanced Dhan adapter with async capabilities and advanced features"""
    
    def __init__(self, client_id: str, access_token: str):
        super().__init__(client_id, access_token)
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self.order_callbacks: List[Callable] = []
        self.base_url = "https://api.dhan.co"
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
            
    def add_order_callback(self, callback: Callable):
        """Add callback for order updates"""
        self.order_callbacks.append(callback)
        
    async def execute_order_async(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute order asynchronously"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self.get_auth_headers()
        headers["Content-Type"] = "application/json"
        
        # Convert order to Dhan format
        dhan_order = self._convert_to_dhan_order(order)
        
        try:
            async with self.session.post(
                f"{self.base_url}/orders",
                headers=headers,
                json=dhan_order
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "success",
                        "broker_order_id": result.get("orderId"),
                        "message": "Order placed successfully",
                        "raw_response": result
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"Order failed: {error_text}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    async def cancel_order_async(self, order_id: str) -> Dict[str, Any]:
        """Cancel order asynchronously"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self.get_auth_headers()
        
        try:
            async with self.session.delete(
                f"{self.base_url}/orders/{order_id}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "success",
                        "message": "Order cancelled successfully",
                        "raw_response": result
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"Cancel failed: {error_text}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    async def get_order_status_async(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status asynchronously"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(
                f"{self.base_url}/orders/{order_id}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return self._parse_order_status(result)
                else:
                    logger.warning(f"Failed to get order status: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
            
    async def get_positions_async(self) -> List[Dict[str, Any]]:
        """Get positions asynchronously"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(
                f"{self.base_url}/positions",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", [])
                else:
                    logger.warning(f"Failed to get positions: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
            
    async def get_holdings_async(self) -> List[Dict[str, Any]]:
        """Get holdings asynchronously"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(
                f"{self.base_url}/holdings",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", [])
                else:
                    logger.warning(f"Failed to get holdings: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return []
            
    async def get_funds_async(self) -> Dict[str, Any]:
        """Get fund information asynchronously"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(
                f"{self.base_url}/funds",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", {})
                else:
                    logger.warning(f"Failed to get funds: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting funds: {e}")
            return {}
            
    async def start_order_updates_stream(self):
        """Start streaming order updates"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self.get_auth_headers()
        
        try:
            self.websocket = await self.session.ws_connect(
                f"wss://api.dhan.co/orders/stream",
                headers=headers
            )
            
            logger.info("Started order updates stream")
            
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_order_update(data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in order update: {msg.data}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.websocket.exception()}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in order updates stream: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
                
    async def _handle_order_update(self, data: Dict[str, Any]):
        """Handle order update from stream"""
        try:
            order_update = self._parse_order_status(data)
            
            # Notify all callbacks
            for callback in self.order_callbacks:
                try:
                    await callback(order_update)
                except Exception as e:
                    logger.error(f"Error in order callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling order update: {e}")
            
    def _convert_to_dhan_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal order format to Dhan format"""
        order_type_mapping = {
            "MARKET": "MARKET",
            "LIMIT": "LIMIT",
            "STOP_LOSS": "SL",
            "STOP_LIMIT": "SL-M"
        }
        
        return {
            "dhanClientId": self.context.client_id,
            "transactionType": order["side"],
            "exchangeSegment": "NSE_EQ",  # Default to NSE equity
            "productType": "INTRADAY",
            "orderType": order_type_mapping.get(order["order_type"], "MARKET"),
            "validity": "DAY",
            "tradingSymbol": order["symbol"],
            "securityId": self._get_security_id(order["symbol"]),
            "quantity": order["quantity"],
            "disclosedQuantity": 0,
            "price": order.get("price", 0),
            "triggerPrice": order.get("stop_price", 0),
            "afterMarketOrder": False,
            "boProfitValue": 0,
            "boStopLossValue": 0
        }
        
    def _parse_order_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse order status from Dhan response"""
        status_mapping = {
            "PENDING": "PENDING",
            "OPEN": "SUBMITTED",
            "PARTIAL": "PARTIALLY_FILLED",
            "COMPLETE": "FILLED",
            "CANCELLED": "CANCELLED",
            "REJECTED": "REJECTED",
            "EXPIRED": "EXPIRED"
        }
        
        return {
            "order_id": data.get("orderId"),
            "status": status_mapping.get(data.get("orderStatus"), "UNKNOWN"),
            "filled_quantity": data.get("filledQty", 0),
            "remaining_quantity": data.get("quantity", 0) - data.get("filledQty", 0),
            "fill_price": data.get("price", 0),
            "timestamp": data.get("createTime"),
            "raw_data": data
        }
        
    def _get_security_id(self, symbol: str) -> str:
        """Get security ID for symbol (simplified mapping)"""
        # In production, this would use a proper symbol master
        symbol_mapping = {
            "RELIANCE": "2885",
            "TCS": "11536",
            "HDFCBANK": "1333",
            "INFY": "1594",
            "ICICIBANK": "4963",
            "HINDUNILVR": "356",
            "BHARTIARTL": "10604",
            "ITC": "424",
            "KOTAKBANK": "1922",
            "LT": "2939"
        }
        
        return symbol_mapping.get(symbol, "0")