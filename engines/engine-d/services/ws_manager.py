"""
WebSocket Manager for Engine D
Manages WebSocket connections and broadcasts real-time events to dashboard
"""
from fastapi import WebSocket
from typing import Dict, List, Set, Any
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "trades": set(),
            "signals": set(),
            "health": set()
        }
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket, channel: str = "dashboard"):
        """Accept new WebSocket connection"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        self.connection_count += 1
        logger.info(f"WebSocket connected to {channel}. Total connections: {self.connection_count}")
    
    def disconnect(self, websocket: WebSocket, channel: str = "dashboard"):
        """Remove WebSocket connection"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            self.connection_count -= 1
            logger.info(f"WebSocket disconnected from {channel}. Total connections: {self.connection_count}")
    
    async def broadcast(self, message: Dict[str, Any], channel: str = "dashboard"):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection, channel)
    
    async def broadcast_all(self, message: dict):
        """Broadcast message to all channels"""
        for channel in self.active_connections.keys():
            await self.broadcast(message, channel)
    
    async def send_personal(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        return {
            "total_connections": self.connection_count,
            "channels": {
                channel: len(connections) 
                for channel, connections in self.active_connections.items()
            }
        }

# Global connection manager instance
ws_manager = ConnectionManager()
