"""
WebSocket Server for Real-Time Updates
Provides live position updates, news streams, and market data
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of topics
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
            self.subscriptions[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.subscriptions[user_id]
        logger.info(f"WebSocket disconnected: {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict, topic: str = None):
        """Broadcast message to all users or specific topic subscribers"""
        for user_id, connections in self.active_connections.items():
            # Check if user is subscribed to topic
            if topic and topic not in self.subscriptions.get(user_id, set()):
                continue
            
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
    
    def subscribe(self, user_id: str, topic: str):
        """Subscribe user to a topic"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].add(topic)
            logger.info(f"User {user_id} subscribed to {topic}")
    
    def unsubscribe(self, user_id: str, topic: str):
        """Unsubscribe user from a topic"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(topic)
            logger.info(f"User {user_id} unsubscribed from {topic}")


# Global connection manager
manager = ConnectionManager()


async def handle_websocket_message(data: dict, user_id: str):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "subscribe":
        topic = data.get("topic")
        if topic:
            manager.subscribe(user_id, topic)
            await manager.send_personal_message({
                "type": "subscribed",
                "topic": topic,
                "timestamp": datetime.now().isoformat()
            }, user_id)
    
    elif message_type == "unsubscribe":
        topic = data.get("topic")
        if topic:
            manager.unsubscribe(user_id, topic)
            await manager.send_personal_message({
                "type": "unsubscribed",
                "topic": topic,
                "timestamp": datetime.now().isoformat()
            }, user_id)
    
    elif message_type == "ping":
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, user_id)


async def broadcast_position_update(user_id: str, position_data: dict):
    """Broadcast position update to user"""
    await manager.send_personal_message({
        "type": "position_update",
        "data": position_data,
        "timestamp": datetime.now().isoformat()
    }, user_id)


async def broadcast_news_update(news_article: dict):
    """Broadcast news update to all subscribers"""
    await manager.broadcast({
        "type": "news_update",
        "data": news_article,
        "timestamp": datetime.now().isoformat()
    }, topic="news")


async def broadcast_market_data(symbol: str, price: float, change: float):
    """Broadcast market data update"""
    await manager.broadcast({
        "type": "market_data",
        "symbol": symbol,
        "price": price,
        "change": change,
        "timestamp": datetime.now().isoformat()
    }, topic=f"market_{symbol}")


# Export for use in main.py
__all__ = ['manager', 'handle_websocket_message', 'broadcast_position_update', 
           'broadcast_news_update', 'broadcast_market_data']
