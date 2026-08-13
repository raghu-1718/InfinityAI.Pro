"""
Frontend WebSocket Endpoint for Real-Time Market Data
Stream live market data to connected web clients
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set, Dict
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create WebSocket router
ws_router = APIRouter(prefix="/api/ws", tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections for multiple clients"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected: {user_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast_to_user(self, message: dict, user_id: str):
        """Broadcast message to all connections of a user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")


# Global connection manager
manager = ConnectionManager()


@ws_router.websocket("/market-feed")
async def market_feed_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time market data streaming
    
    Usage from frontend:
    ```javascript
    const ws = new WebSocket('wss://engine-c.../api/ws/market-feed?user_id=123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data);
    };
    ```
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial connection message
        await manager.send_personal_message({
            'type': 'connection',
            'status': 'connected',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get('type')
            
            if msg_type == 'subscribe':
                # Subscribe to instruments
                instruments = message.get('instruments', [])
                
                # TODO: Subscribe to DhanHQ WebSocket for these instruments
                # For now, acknowledge
                await manager.send_personal_message({
                    'type': 'subscribed',
                    'instruments': instruments,
                    'timestamp': datetime.utcnow().isoformat()
                }, websocket)
            
            elif msg_type == 'unsubscribe':
                # Unsubscribe from instruments
                instruments = message.get('instruments', [])
                
                await manager.send_personal_message({
                    'type': 'unsubscribed',
                    'instruments': instruments,
                    'timestamp': datetime.utcnow().isoformat()
                }, websocket)
            
            elif msg_type == 'ping':
                # Heartbeat
                await manager.send_personal_message({
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"Client {user_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


@ws_router.websocket("/order-updates")
async def order_updates_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time order updates
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial message
        await manager.send_personal_message({
            'type': 'connection',
            'status': 'connected',
            'stream': 'order_updates',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'ping':
                await manager.send_personal_message({
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


async def broadcast_market_tick(security_id: str, tick_data: dict):
    """
    Helper function to broadcast market tick to all connected clients
    Call this from DhanHQ WebSocket handler
    """
    message = {
        'type': 'market_tick',
        'security_id': security_id,
        'data': tick_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_to_all(message)


async def broadcast_order_update(user_id: str, order_data: dict):
    """
    Helper function to broadcast order update to specific user
    Call this from DhanHQ postback handler
    """
    message = {
        'type': 'order_update',
        'data': order_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_to_user(message, user_id)


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  FRONTEND WEBSOCKET ENDPOINTS")
    print("=" * 80)
    
    print("\n[INFO] WebSocket Endpoints:")
    print("  - ws://engine-c.../api/ws/market-feed?user_id=xxx")
    print("  - ws://engine-c.../api/ws/order-updates?user_id=xxx")
    
    print("\n[INFO] Message Types:")
    print("  Client -> Server:")
    print("    - subscribe: Subscribe to instruments")
    print("    - unsubscribe: Unsubscribe from instruments")
    print("    - ping: Heartbeat")
    
    print("\n  Server -> Client:")
    print("    - connection: Connection established")
    print("    - market_tick: Real-time price update")
    print("    - order_update: Order status change")
    print("    - pong: Heartbeat response")
    
    print("\n[INFO] Connection Management:")
    print("  - Multi-user support")
    print("  - Automatic disconnection handling")
    print("  - Broadcast capabilities")
    
    print("\n" + "=" * 80)
    print("  WEBSOCKET ENDPOINTS READY")
    print("=" * 80)
