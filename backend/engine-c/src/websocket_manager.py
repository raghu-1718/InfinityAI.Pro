"""
DhanHQ WebSocket Manager
Manages WebSocket connections for live market data streaming
"""
import asyncio
import websocket
import json
import struct
import logging
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DhanWebSocketManager:
    """
    Manage DhanHQ WebSocket connection for real-time market data
    
    DhanHQ WebSocket Protocol:
    - Connection: wss://api-feed.dhan.co
    - Binary messages in Little Endian format
    - Tick data structure defined by DhanHQ
    """
    
    def __init__(self, client_id: str, access_token: str, on_tick: Optional[Callable] = None):
        self.client_id = client_id
        self.access_token = access_token
        self.ws = None
        self.is_connected = False
        self.subscribed_instruments = set()
        self.on_tick = on_tick or self._default_tick_handler
    
    def connect(self):
        """Establish WebSocket connection"""
        try:
            # DhanHQ WebSocket URL
            ws_url = f"wss://api-feed.dhan.co?version=2&token={self.access_token}&clientId={self.client_id}"
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Run in separate thread
            import threading
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            logger.info("✅ WebSocket connection initiated")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
    
    def _on_open(self, ws):
        """WebSocket connection opened"""
        self.is_connected = True
        logger.info("🟢 WebSocket connected to DhanHQ")
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            # DhanHQ sends binary data
            if isinstance(message, bytes):
                tick_data = self._parse_binary_tick(message)
                self.on_tick(tick_data)
            else:
                # Text message (e.g., acknowledgments)
                logger.info(f"WebSocket message: {message}")
        
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _parse_binary_tick(self, binary_data: bytes) -> Dict[str, Any]:
        """
        Parse DhanHQ binary tick data (Little Endian)
        
        Structure (example):
        - Security ID: 4 bytes (int)
        - LTP: 8 bytes (double)
        - Volume: 4 bytes (int)
        - etc.
        """
        try:
            # Unpack binary data (Little Endian '<')
            # This is a simplified example - actual format depends on DhanHQ spec
            security_id = struct.unpack('<I', binary_data[0:4])[0]
            ltp = struct.unpack('<d', binary_data[4:12])[0]
            volume = struct.unpack('<I', binary_data[12:16])[0]
            
            return {
                'security_id': security_id,
                'ltp': ltp,
                'volume': volume,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error parsing binary tick: {e}")
            return {}
    
    def _default_tick_handler(self, tick_data: Dict[str, Any]):
        """Default handler - store in Supabase"""
        try:
            security_id = tick_data.get('security_id')
            if security_id:
                from src.user_credentials import get_credentials_manager
                manager = get_credentials_manager()
                if manager and manager.db:
                    manager.db.table("live_prices").upsert({
                        "security_id": str(security_id),
                        "ltp": tick_data.get('ltp'),
                        "volume": tick_data.get('volume'),
                        "updated_at": tick_data.get('timestamp')
                    }).execute()
                
                logger.debug(f"Tick: {security_id} LTP: {tick_data.get('ltp')}")
        
        except Exception as e:
            logger.error(f"Error storing tick data: {e}")
    
    def subscribe(self, security_ids: List[str], exchange_segment: str = "NSE_EQ"):
        """Subscribe to instruments"""
        try:
            if not self.is_connected:
                logger.warning("WebSocket not connected")
                return
            
            # DhanHQ subscription message format
            subscribe_msg = {
                "RequestCode": 15,  # Subscribe request code
                "InstrumentCount": len(security_ids),
                "InstrumentList": [
                    {
                        "ExchangeSegment": exchange_segment,
                        "SecurityId": sec_id
                    }
                    for sec_id in security_ids
                ]
            }
            
            self.ws.send(json.dumps(subscribe_msg))
            self.subscribed_instruments.update(security_ids)
            
            logger.info(f"✅ Subscribed to {len(security_ids)} instruments")
        
        except Exception as e:
            logger.error(f"Subscription error: {e}")
    
    def unsubscribe(self, security_ids: List[str]):
        """Unsubscribe from instruments"""
        try:
            if not self.is_connected:
                return
            
            unsubscribe_msg = {
                "RequestCode": 16,  # Unsubscribe request code
                "InstrumentCount": len(security_ids),
                "InstrumentList": security_ids
            }
            
            self.ws.send(json.dumps(unsubscribe_msg))
            self.subscribed_instruments.difference_update(security_ids)
            
            logger.info(f"✅ Unsubscribed from {len(security_ids)} instruments")
        
        except Exception as e:
            logger.error(f"Unsubscription error: {e}")
    
    def _on_error(self, ws, error):
        """WebSocket error handler"""
        logger.error(f"❌ WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket connection closed"""
        self.is_connected = False
        logger.warning(f"🔴 WebSocket closed: {close_msg}")
        
        # Auto-reconnect after 5 seconds
        asyncio.sleep(5)
        logger.info("Attempting to reconnect...")
        self.connect()
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
            self.is_connected = False
            logger.info("WebSocket disconnected")


# Singleton instance management
_ws_managers: Dict[str, DhanWebSocketManager] = {}


def get_websocket_manager(user_id: str, client_id: str, access_token: str) -> DhanWebSocketManager:
    """Get or create WebSocket manager for user"""
    if user_id not in _ws_managers:
        _ws_managers[user_id] = DhanWebSocketManager(client_id, access_token)
        _ws_managers[user_id].connect()
    
    return _ws_managers[user_id]


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  DHAN WEBSOCKET MANAGER")
    print("=" * 80)
    
    # Example usage
    print("\n[INFO] WebSocket Manager Structure:")
    print("  - Binary tick parsing (Little Endian)")
    print("  - Auto-reconnection")
    print("  - Supabase storage")
    print("  - Multi-user support")
    
    print("\n[INFO] Integration points:")
    print("  1. Connect with user credentials")
    print("  2. Subscribe to instruments")
    print("  3. Real-time tick updates → Supabase")
    print("  4. Frontend WebSocket endpoint")
    
    print("\n" + "=" * 80)
    print("  WEBSOCKET INFRASTRUCTURE READY")
    print("=" * 80)
