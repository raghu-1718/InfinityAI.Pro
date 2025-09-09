import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class FeedStatus(Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"

@dataclass
class MarketTick:
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: float = 0.0
    ask: float = 0.0
    bid_size: int = 0
    ask_size: int = 0
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    close: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0

class MarketDataFeed:
    def __init__(self, feed_url: str, auth_headers: Dict[str, str]):
        self.feed_url = feed_url
        self.auth_headers = auth_headers
        self.status = FeedStatus.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.subscribed_symbols: set = set()
        self.callbacks: List[Callable[[MarketTick], None]] = []
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5
        self.running = False
        
    def add_callback(self, callback: Callable[[MarketTick], None]):
        """Add callback for market data updates"""
        self.callbacks.append(callback)
        
    async def connect(self):
        """Connect to market data feed"""
        if self.status in [FeedStatus.CONNECTED, FeedStatus.CONNECTING]:
            return
            
        self.status = FeedStatus.CONNECTING
        logger.info(f"Connecting to market data feed: {self.feed_url}")
        
        try:
            self.websocket = await websockets.connect(
                self.feed_url,
                extra_headers=self.auth_headers,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.status = FeedStatus.CONNECTED
            self.reconnect_attempts = 0
            logger.info("Connected to market data feed")
            
            # Resubscribe to symbols
            if self.subscribed_symbols:
                await self._send_subscription_message(list(self.subscribed_symbols))
                
        except Exception as e:
            self.status = FeedStatus.ERROR
            logger.error(f"Failed to connect to market data feed: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from market data feed"""
        self.running = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        self.status = FeedStatus.DISCONNECTED
        logger.info("Disconnected from market data feed")
        
    async def subscribe(self, symbols: List[str]):
        """Subscribe to market data for symbols"""
        new_symbols = set(symbols) - self.subscribed_symbols
        
        if new_symbols:
            self.subscribed_symbols.update(new_symbols)
            
            if self.status == FeedStatus.CONNECTED:
                await self._send_subscription_message(list(new_symbols))
                
            logger.info(f"Subscribed to symbols: {list(new_symbols)}")
            
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from market data for symbols"""
        symbols_to_remove = set(symbols) & self.subscribed_symbols
        
        if symbols_to_remove:
            self.subscribed_symbols -= symbols_to_remove
            
            if self.status == FeedStatus.CONNECTED:
                await self._send_unsubscription_message(list(symbols_to_remove))
                
            logger.info(f"Unsubscribed from symbols: {list(symbols_to_remove)}")
            
    async def start_listening(self):
        """Start listening for market data"""
        self.running = True
        
        while self.running:
            try:
                if self.status != FeedStatus.CONNECTED:
                    await self.connect()
                    
                await self._listen_for_messages()
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Market data connection closed")
                await self._handle_reconnection()
                
            except Exception as e:
                logger.error(f"Error in market data listener: {e}")
                await self._handle_reconnection()
                
    async def _listen_for_messages(self):
        """Listen for incoming market data messages"""
        if not self.websocket:
            return
            
        async for message in self.websocket:
            try:
                data = json.loads(message)
                tick = self._parse_market_tick(data)
                
                if tick:
                    # Notify all callbacks
                    for callback in self.callbacks:
                        try:
                            await callback(tick)
                        except Exception as e:
                            logger.error(f"Error in market data callback: {e}")
                            
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {message}")
            except Exception as e:
                logger.error(f"Error processing market data message: {e}")
                
    async def _send_subscription_message(self, symbols: List[str]):
        """Send subscription message to feed"""
        if not self.websocket:
            return
            
        message = {
            "action": "subscribe",
            "symbols": symbols,
            "mode": "full"  # full market data
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent subscription for {len(symbols)} symbols")
        except Exception as e:
            logger.error(f"Failed to send subscription message: {e}")
            
    async def _send_unsubscription_message(self, symbols: List[str]):
        """Send unsubscription message to feed"""
        if not self.websocket:
            return
            
        message = {
            "action": "unsubscribe",
            "symbols": symbols
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent unsubscription for {len(symbols)} symbols")
        except Exception as e:
            logger.error(f"Failed to send unsubscription message: {e}")
            
    def _parse_market_tick(self, data: Dict[str, Any]) -> Optional[MarketTick]:
        """Parse market data message into MarketTick"""
        try:
            # This would be customized based on your data provider's format
            # Example for a generic format:
            
            if data.get("type") != "tick":
                return None
                
            return MarketTick(
                symbol=data.get("symbol", ""),
                price=float(data.get("ltp", 0)),
                volume=int(data.get("volume", 0)),
                timestamp=datetime.fromtimestamp(data.get("timestamp", 0)),
                bid=float(data.get("bid", 0)),
                ask=float(data.get("ask", 0)),
                bid_size=int(data.get("bid_size", 0)),
                ask_size=int(data.get("ask_size", 0)),
                high=float(data.get("high", 0)),
                low=float(data.get("low", 0)),
                open=float(data.get("open", 0)),
                close=float(data.get("close", 0)),
                change=float(data.get("change", 0)),
                change_percent=float(data.get("change_percent", 0))
            )
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing market tick: {e}")
            return None
            
    async def _handle_reconnection(self):
        """Handle reconnection logic"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self.status = FeedStatus.ERROR
            return
            
        self.status = FeedStatus.RECONNECTING
        self.reconnect_attempts += 1
        
        delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 60)
        logger.info(f"Reconnecting in {delay} seconds (attempt {self.reconnect_attempts})")
        
        await asyncio.sleep(delay)

class FeedManager:
    def __init__(self):
        self.feeds: Dict[str, MarketDataFeed] = {}
        self.symbol_feed_mapping: Dict[str, str] = {}
        self.callbacks: List[Callable[[MarketTick], None]] = []
        
    def add_callback(self, callback: Callable[[MarketTick], None]):
        """Add global callback for all market data"""
        self.callbacks.append(callback)
        
    def add_feed(self, feed_name: str, feed_url: str, auth_headers: Dict[str, str]):
        """Add a market data feed"""
        feed = MarketDataFeed(feed_url, auth_headers)
        feed.add_callback(self._on_market_tick)
        self.feeds[feed_name] = feed
        logger.info(f"Added market data feed: {feed_name}")
        
    async def start_feed(self, feed_name: str):
        """Start a market data feed"""
        if feed_name not in self.feeds:
            raise ValueError(f"Feed {feed_name} not found")
            
        feed = self.feeds[feed_name]
        asyncio.create_task(feed.start_listening())
        logger.info(f"Started market data feed: {feed_name}")
        
    async def stop_feed(self, feed_name: str):
        """Stop a market data feed"""
        if feed_name not in self.feeds:
            return
            
        feed = self.feeds[feed_name]
        await feed.disconnect()
        logger.info(f"Stopped market data feed: {feed_name}")
        
    async def subscribe_symbol(self, symbol: str, feed_name: str):
        """Subscribe to a symbol on a specific feed"""
        if feed_name not in self.feeds:
            raise ValueError(f"Feed {feed_name} not found")
            
        feed = self.feeds[feed_name]
        await feed.subscribe([symbol])
        self.symbol_feed_mapping[symbol] = feed_name
        
    async def unsubscribe_symbol(self, symbol: str):
        """Unsubscribe from a symbol"""
        if symbol not in self.symbol_feed_mapping:
            return
            
        feed_name = self.symbol_feed_mapping[symbol]
        if feed_name in self.feeds:
            feed = self.feeds[feed_name]
            await feed.unsubscribe([symbol])
            
        del self.symbol_feed_mapping[symbol]
        
    async def _on_market_tick(self, tick: MarketTick):
        """Handle market tick from any feed"""
        # Notify all global callbacks
        for callback in self.callbacks:
            try:
                await callback(tick)
            except Exception as e:
                logger.error(f"Error in global market data callback: {e}")

# Global feed manager instance
feed_manager = FeedManager()