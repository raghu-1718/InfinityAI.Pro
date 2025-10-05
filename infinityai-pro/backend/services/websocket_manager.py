"""
Mock WebSocket Manager for InfinityAI.Pro
Minimal implementation for testing backend functionality
"""
import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"🔌 WebSocket connected for user: {user_id}")
        
    def disconnect(self, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"🔌 WebSocket disconnected for user: {user_id}")
            
    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False
        
    async def broadcast_message(self, message: str):
        """Broadcast message to all connected users"""
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {user_id}: {e}")
                disconnected_users.append(user_id)
                
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
            
    async def close_all_connections(self):
        """Close all WebSocket connections"""
        logger.info("🛑 Closing all WebSocket connections")
        
        for user_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection for {user_id}: {e}")
                
        self.active_connections.clear()
        logger.info("✅ All WebSocket connections closed")

# Global instance
websocket_manager = WebSocketManager()