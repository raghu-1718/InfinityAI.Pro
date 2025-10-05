"""
Real-time WebSocket Service - Live Market Data & Portfolio Updates
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Set, Optional
from datetime import datetime, timedelta
import websockets
from websockets import ConnectionClosed
import aiohttp

from services.dhan_api_service import dhan_api_service

logger = logging.getLogger(__name__)

class RealtimeWebSocketService:
    """Real-time WebSocket service for live data streaming"""
    
    def __init__(self):
        # WebSocket connections
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_subscriptions: Dict[str, Dict[str, Any]] = {}
        
        # Market data subscriptions
        self.market_subscriptions: Dict[str, Set[str]] = {}  # symbol -> user_ids
        self.portfolio_subscriptions: Set[str] = set()  # user_ids with portfolio updates
        
        # Cache for recent data
        self.market_data_cache: Dict[str, Dict[str, Any]] = {}
        self.portfolio_cache: Dict[str, Dict[str, Any]] = {}
        
        # Update intervals
        self.market_data_interval = 2  # seconds
        self.portfolio_interval = 5  # seconds
        
        # Background tasks
        self.market_data_task: Optional[asyncio.Task] = None
        self.portfolio_update_task: Optional[asyncio.Task] = None
        
        # Running status
        self.is_running = False
    
    async def start_service(self):
        """Start the WebSocket service and background tasks"""
        
        if self.is_running:
            return
        
        logger.info("🚀 Starting Real-time WebSocket Service...")
        
        self.is_running = True
        
        # Start background data update tasks
        self.market_data_task = asyncio.create_task(self._market_data_updater())
        self.portfolio_update_task = asyncio.create_task(self._portfolio_updater())
        
        logger.info("✅ Real-time WebSocket Service started")
    
    async def stop_service(self):
        """Stop the WebSocket service and cleanup"""
        
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping Real-time WebSocket Service...")
        
        self.is_running = False
        
        # Cancel background tasks
        if self.market_data_task:
            self.market_data_task.cancel()
        
        if self.portfolio_update_task:
            self.portfolio_update_task.cancel()
        
        # Close all connections
        for user_id, websocket in list(self.connections.items()):
            try:
                await websocket.close()
            except:
                pass
        
        self.connections.clear()
        self.user_subscriptions.clear()
        
        logger.info("✅ Real-time WebSocket Service stopped")
    
    async def register_connection(self, user_id: str, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket connection"""
        
        logger.info(f"🔗 Registering WebSocket connection for user: {user_id}")
        
        # Store connection
        self.connections[user_id] = websocket
        
        # Initialize user subscriptions
        self.user_subscriptions[user_id] = {
            "market_symbols": set(),
            "portfolio_updates": False,
            "trading_notifications": True,
            "connected_at": datetime.now(),
            "last_activity": datetime.now()
        }
        
        # Send welcome message
        welcome_msg = {
            "type": "connection_established",
            "message": "🚀 Connected to InfinityAI Real-time Data Service",
            "user_id": user_id,
            "features": [
                "Live market data",
                "Portfolio updates", 
                "Trading notifications",
                "AI analysis updates"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_to_user(user_id, welcome_msg)
        
        logger.info(f"✅ User {user_id} connected to WebSocket service")
    
    async def unregister_connection(self, user_id: str):
        """Unregister a WebSocket connection"""
        
        logger.info(f"❌ Unregistering WebSocket connection for user: {user_id}")
        
        # Remove from market subscriptions
        if user_id in self.user_subscriptions:
            subscribed_symbols = self.user_subscriptions[user_id].get("market_symbols", set())
            
            for symbol in subscribed_symbols:
                if symbol in self.market_subscriptions:
                    self.market_subscriptions[symbol].discard(user_id)
                    
                    # Remove symbol if no more subscribers
                    if not self.market_subscriptions[symbol]:
                        del self.market_subscriptions[symbol]
        
        # Remove from portfolio subscriptions
        self.portfolio_subscriptions.discard(user_id)
        
        # Clean up
        self.connections.pop(user_id, None)
        self.user_subscriptions.pop(user_id, None)
        self.portfolio_cache.pop(user_id, None)
    
    async def handle_client_message(self, user_id: str, message: str):
        """Handle incoming message from client"""
        
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            logger.info(f"📨 Received message from {user_id}: {message_type}")
            
            if message_type == "subscribe_market_data":
                await self._handle_market_subscription(user_id, data)
                
            elif message_type == "subscribe_portfolio":
                await self._handle_portfolio_subscription(user_id, data)
                
            elif message_type == "unsubscribe_market_data":
                await self._handle_market_unsubscription(user_id, data)
                
            elif message_type == "unsubscribe_portfolio":
                await self._handle_portfolio_unsubscription(user_id, data)
                
            elif message_type == "request_snapshot":
                await self._handle_snapshot_request(user_id, data)
                
            elif message_type == "ping":
                await self._handle_ping(user_id)
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
            # Update last activity
            if user_id in self.user_subscriptions:
                self.user_subscriptions[user_id]["last_activity"] = datetime.now()
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from user {user_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {user_id}: {e}")
    
    async def _handle_market_subscription(self, user_id: str, data: Dict[str, Any]):
        """Handle market data subscription"""
        
        symbols = data.get("symbols", [])
        
        if not symbols:
            return
        
        user_symbols = self.user_subscriptions[user_id]["market_symbols"]
        
        for symbol in symbols:
            symbol = symbol.upper()
            user_symbols.add(symbol)
            
            # Add to global subscriptions
            if symbol not in self.market_subscriptions:
                self.market_subscriptions[symbol] = set()
            
            self.market_subscriptions[symbol].add(user_id)
        
        # Send confirmation
        response = {
            "type": "subscription_confirmed",
            "category": "market_data",
            "symbols": list(symbols),
            "message": f"Subscribed to {len(symbols)} symbols",
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_to_user(user_id, response)
        
        # Send current data if available
        for symbol in symbols:
            if symbol.upper() in self.market_data_cache:
                market_update = {
                    "type": "market_data_update",
                    "symbol": symbol.upper(),
                    "data": self.market_data_cache[symbol.upper()],
                    "timestamp": datetime.now().isoformat()
                }
                await self._send_to_user(user_id, market_update)
    
    async def _handle_portfolio_subscription(self, user_id: str, data: Dict[str, Any]):
        """Handle portfolio updates subscription"""
        
        # Check if user is connected to Dhan
        if not dhan_api_service.is_user_connected(user_id):
            error_response = {
                "type": "subscription_error",
                "category": "portfolio",
                "error": "Dhan account not connected",
                "message": "Please connect your Dhan account to receive portfolio updates",
                "timestamp": datetime.now().isoformat()
            }
            await self._send_to_user(user_id, error_response)
            return
        
        # Enable portfolio updates for user
        self.user_subscriptions[user_id]["portfolio_updates"] = True
        self.portfolio_subscriptions.add(user_id)
        
        # Send confirmation
        response = {
            "type": "subscription_confirmed",
            "category": "portfolio",
            "message": "Subscribed to portfolio updates",
            "features": ["holdings", "positions", "pnl", "orders"],
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_to_user(user_id, response)
        
        # Send current portfolio data if cached
        if user_id in self.portfolio_cache:
            portfolio_update = {
                "type": "portfolio_update",
                "data": self.portfolio_cache[user_id],
                "timestamp": datetime.now().isoformat()
            }
            await self._send_to_user(user_id, portfolio_update)
    
    async def _handle_snapshot_request(self, user_id: str, data: Dict[str, Any]):
        """Handle request for current data snapshot"""
        
        snapshot_type = data.get("snapshot_type", "all")
        
        snapshot = {
            "type": "data_snapshot",
            "timestamp": datetime.now().isoformat()
        }
        
        if snapshot_type in ["all", "market"]:
            # Include subscribed market data
            user_symbols = self.user_subscriptions[user_id]["market_symbols"]
            market_data = {}
            
            for symbol in user_symbols:
                if symbol in self.market_data_cache:
                    market_data[symbol] = self.market_data_cache[symbol]
            
            snapshot["market_data"] = market_data
        
        if snapshot_type in ["all", "portfolio"]:
            # Include portfolio data if available
            if user_id in self.portfolio_cache:
                snapshot["portfolio"] = self.portfolio_cache[user_id]
        
        await self._send_to_user(user_id, snapshot)
    
    async def _handle_ping(self, user_id: str):
        """Handle ping message"""
        
        pong_response = {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_to_user(user_id, pong_response)
    
    async def _market_data_updater(self):
        """Background task to fetch and broadcast market data"""
        
        logger.info("📊 Market data updater started")
        
        while self.is_running:
            try:
                if self.market_subscriptions:
                    # Get all subscribed symbols
                    all_symbols = list(self.market_subscriptions.keys())
                    
                    if all_symbols:
                        # Fetch live quotes
                        quotes_result = await dhan_api_service.get_live_quote(all_symbols)
                        
                        if quotes_result.get("success"):
                            quotes = quotes_result.get("quotes", {})
                            
                            # Update cache and broadcast to subscribers
                            for symbol, quote_data in quotes.items():
                                self.market_data_cache[symbol] = quote_data
                                
                                # Send to all subscribers of this symbol
                                if symbol in self.market_subscriptions:
                                    market_update = {
                                        "type": "market_data_update",
                                        "symbol": symbol,
                                        "data": quote_data,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    
                                    # Broadcast to all subscribers
                                    for user_id in self.market_subscriptions[symbol]:
                                        await self._send_to_user(user_id, market_update)
                
                # Wait for next update
                await asyncio.sleep(self.market_data_interval)
                
            except Exception as e:
                logger.error(f"Market data update error: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _portfolio_updater(self):
        """Background task to fetch and broadcast portfolio updates"""
        
        logger.info("💼 Portfolio updater started")
        
        while self.is_running:
            try:
                if self.portfolio_subscriptions:
                    # Update portfolio for each subscribed user
                    for user_id in list(self.portfolio_subscriptions):
                        try:
                            # Check if user is still connected
                            if user_id not in self.connections:
                                self.portfolio_subscriptions.discard(user_id)
                                continue
                            
                            # Check if Dhan is connected
                            if not dhan_api_service.is_user_connected(user_id):
                                continue
                            
                            # Fetch portfolio data
                            portfolio_data = await self._fetch_user_portfolio(user_id)
                            
                            if portfolio_data:
                                # Cache the data
                                self.portfolio_cache[user_id] = portfolio_data
                                
                                # Send update
                                portfolio_update = {
                                    "type": "portfolio_update",
                                    "data": portfolio_data,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                await self._send_to_user(user_id, portfolio_update)
                                
                        except Exception as e:
                            logger.error(f"Portfolio update error for user {user_id}: {e}")
                
                # Wait for next update
                await asyncio.sleep(self.portfolio_interval)
                
            except Exception as e:
                logger.error(f"Portfolio updater error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _fetch_user_portfolio(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch complete portfolio data for user"""
        
        try:
            # Fetch all portfolio components concurrently
            tasks = [
                dhan_api_service.get_account_details(user_id),
                dhan_api_service.get_funds_and_margin(user_id),
                dhan_api_service.get_holdings(user_id),
                dhan_api_service.get_positions(user_id)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            account_result, funds_result, holdings_result, positions_result = results
            
            # Compile portfolio data
            portfolio = {
                "account": None,
                "funds": None,
                "holdings": None,
                "positions": None,
                "summary": {
                    "total_value": 0,
                    "total_pnl": 0,
                    "day_pnl": 0,
                    "available_margin": 0
                }
            }
            
            # Process results
            if isinstance(account_result, dict) and account_result.get("success"):
                portfolio["account"] = account_result.get("account")
            
            if isinstance(funds_result, dict) and funds_result.get("success"):
                portfolio["funds"] = funds_result.get("funds")
                portfolio["summary"]["available_margin"] = funds_result.get("funds", {}).get("available_margin", 0)
            
            if isinstance(holdings_result, dict) and holdings_result.get("success"):
                portfolio["holdings"] = holdings_result.get("holdings")
                holdings_summary = holdings_result.get("holdings", {}).get("summary", {})
                portfolio["summary"]["total_value"] += holdings_summary.get("total_value", 0)
                portfolio["summary"]["total_pnl"] += holdings_summary.get("total_pnl", 0)
            
            if isinstance(positions_result, dict) and positions_result.get("success"):
                portfolio["positions"] = positions_result.get("positions")
                positions_summary = positions_result.get("positions", {}).get("summary", {})
                portfolio["summary"]["day_pnl"] += positions_summary.get("total_pnl", 0)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Portfolio fetch error for {user_id}: {e}")
            return None
    
    async def _send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        
        if user_id not in self.connections:
            return
        
        try:
            websocket = self.connections[user_id]
            await websocket.send(json.dumps(message))
            
        except ConnectionClosed:
            logger.warning(f"WebSocket connection closed for user {user_id}")
            await self.unregister_connection(user_id)
            
        except Exception as e:
            logger.error(f"Error sending message to {user_id}: {e}")
    
    async def broadcast_trading_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send trading notification to specific user"""
        
        if user_id in self.connections:
            trading_msg = {
                "type": "trading_notification",
                "notification": notification,
                "timestamp": datetime.now().isoformat()
            }
            
            await self._send_to_user(user_id, trading_msg)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket service statistics"""
        
        return {
            "active_connections": len(self.connections),
            "market_subscriptions": len(self.market_subscriptions),
            "portfolio_subscriptions": len(self.portfolio_subscriptions),
            "cached_symbols": len(self.market_data_cache),
            "cached_portfolios": len(self.portfolio_cache),
            "service_running": self.is_running
        }

# Global instance
realtime_websocket_service = RealtimeWebSocketService()
