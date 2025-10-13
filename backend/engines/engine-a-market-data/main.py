#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine A: Market Data Ingestion Service
Real-time market data processing with advanced technical indicators
Deployed on GCP Cloud Run
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import json
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ENGINE-A - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('engine_a_market_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MarketSignal:
    symbol: str
    price: float
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    indicators: Dict[str, float]
    volume: float
    change_percent: float

@dataclass
class TechnicalIndicators:
    rsi: float
    ema_20: float
    ema_50: float
    bollinger_upper: float
    bollinger_lower: float
    macd: float
    volume_ma: float

class MarketDataService:
    def __init__(self):
        self.dhan_token = os.getenv('DHAN_ACCESS_TOKEN', 'PLACEHOLDER_TOKEN')
        self.dhan_client_id = os.getenv('DHAN_CLIENT_ID', 'PLACEHOLDER_CLIENT_ID')
        self.dhan_api_key = os.getenv('DHAN_API_KEY', '')
        self.dhan_api_secret = os.getenv('DHAN_API_SECRET', '')
        self.base_url = "https://api.dhan.co/v2"
        
        self.headers = {
            "access-token": self.dhan_token,
            "client-id": self.dhan_client_id,
            "Content-Type": "application/json"
        }
        
        # for Real-Time Advantage (if required by WS/gateway services)
        self.rt_headers = {
            "x-api-key": self.dhan_api_key,
            "x-api-secret": self.dhan_api_secret,
            "client-id": self.dhan_client_id
        }
        
        # Market data cache
        self.market_cache: Dict[str, List[Dict]] = {}
        self.signals_cache: List[MarketSignal] = []
        
        # Monitoring symbols
        self.symbols = [
            "NSE_EQ|2885",  # NIFTY
            "NSE_EQ|26000", # BANKNIFTY
            "NSE_EQ|1333",  # RELIANCE
            "NSE_EQ|11536", # TCS
            "NSE_EQ|1922",  # INFY
        ]
        
        logger.info("🎯 Engine A - Market Data Service Initialized")
    
    async def fetch_live_market_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time market data from Dhan API"""
        try:
            url = f"{self.base_url}/charts/historical"
            payload = {
                "symbol": symbol,
                "exchangeSegment": "NSE_EQ",
                "instrument": "EQUITY",
                "interval": "1",
                "fromDate": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "toDate": datetime.now().strftime("%Y-%m-%d")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"Failed to fetch data for {symbol}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, prices: List[float]) -> TechnicalIndicators:
        """Calculate technical indicators from price data"""
        if len(prices) < 50:
            # Return default values if insufficient data
            return TechnicalIndicators(
                rsi=50.0, ema_20=prices[-1] if prices else 0,
                ema_50=prices[-1] if prices else 0,
                bollinger_upper=prices[-1] * 1.02 if prices else 0,
                bollinger_lower=prices[-1] * 0.98 if prices else 0,
                macd=0.0, volume_ma=0.0
            )
        
        df = pd.DataFrame({'close': prices})
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # EMA calculation
        ema_20 = df['close'].ewm(span=20).mean()
        ema_50 = df['close'].ewm(span=50).mean()
        
        # Bollinger Bands
        rolling_mean = df['close'].rolling(window=20).mean()
        rolling_std = df['close'].rolling(window=20).std()
        bollinger_upper = rolling_mean + (rolling_std * 2)
        bollinger_lower = rolling_mean - (rolling_std * 2)
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        
        return TechnicalIndicators(
            rsi=float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0,
            ema_20=float(ema_20.iloc[-1]),
            ema_50=float(ema_50.iloc[-1]),
            bollinger_upper=float(bollinger_upper.iloc[-1]),
            bollinger_lower=float(bollinger_lower.iloc[-1]),
            macd=float(macd.iloc[-1]),
            volume_ma=0.0  # Simplified
        )
    
    def generate_trading_signal(self, symbol: str, current_price: float, indicators: TechnicalIndicators) -> MarketSignal:
        """Generate trading signal based on technical analysis"""
        signal_type = "HOLD"
        confidence = 50.0
        
        # Signal generation logic
        buy_signals = 0
        sell_signals = 0
        
        # RSI signals
        if indicators.rsi < 30:
            buy_signals += 1
        elif indicators.rsi > 70:
            sell_signals += 1
        
        # EMA crossover
        if indicators.ema_20 > indicators.ema_50:
            buy_signals += 1
        else:
            sell_signals += 1
        
        # Bollinger Bands
        if current_price < indicators.bollinger_lower:
            buy_signals += 1
        elif current_price > indicators.bollinger_upper:
            sell_signals += 1
        
        # MACD
        if indicators.macd > 0:
            buy_signals += 1
        else:
            sell_signals += 1
        
        # Determine signal
        if buy_signals > sell_signals:
            signal_type = "BUY"
            confidence = min(90.0, 50.0 + (buy_signals * 10))
        elif sell_signals > buy_signals:
            signal_type = "SELL"
            confidence = min(90.0, 50.0 + (sell_signals * 10))
        
        return MarketSignal(
            symbol=symbol,
            price=current_price,
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=confidence,
            indicators=asdict(indicators),
            volume=0.0,  # Simplified
            change_percent=0.0  # Simplified
        )
    
    async def process_market_data(self):
        """Main market data processing loop"""
        logger.info("🔄 Starting market data processing...")
        
        all_signals = []
        
        for symbol in self.symbols:
            try:
                # Fetch market data
                market_data = await self.fetch_live_market_data(symbol)
                
                if market_data and 'data' in market_data:
                    prices = [float(candle[4]) for candle in market_data['data']]  # Close prices
                    current_price = prices[-1] if prices else 0.0
                    
                    # Calculate technical indicators
                    indicators = self.calculate_technical_indicators(prices)
                    
                    # Generate trading signal
                    signal = self.generate_trading_signal(symbol, current_price, indicators)
                    all_signals.append(signal)
                    
                    logger.info(f"📊 {symbol}: {signal.signal_type} @ ₹{current_price:.2f} (Confidence: {signal.confidence:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        # Update cache
        self.signals_cache = all_signals
        return all_signals

# Global service instance
market_service = MarketDataService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Engine A - Market Data Service starting...")
    yield
    # Shutdown
    logger.info("🛑 Engine A - Market Data Service shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="🎯 InfinityAI.Pro - Engine A: Market Data Service",
    description="Real-time market data ingestion and technical analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "Engine A - Market Data Service",
        "status": "active",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "engine-a-market-data",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }

@app.get("/api/signals")
async def get_trading_signals():
    """Get latest trading signals"""
    try:
        signals = await market_service.process_market_data()
        return {
            "status": "success",
            "signals": [asdict(signal) for signal in signals],
            "count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for specific symbol"""
    try:
        data = await market_service.fetch_live_market_data(symbol)
        return {
            "status": "success",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/refresh")
async def refresh_market_data():
    """Manually refresh market data"""
    try:
        signals = await market_service.process_market_data()
        return {
            "status": "refreshed",
            "signals_count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error refreshing market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "engine-a-market-data",
        "active_symbols": len(market_service.symbols),
        "cached_signals": len(market_service.signals_cache),
        "last_update": datetime.now().isoformat(),
        "status": "operational"
    }

@app.post("/api/config/dhan")
async def update_dhan_config(config: Dict[str, str]):
    """Update DHAN access token at runtime (API key/secret/client id remain stable)."""
    try:
        token = config.get("access_token") or config.get("DHAN_ACCESS_TOKEN")
        if token:
            market_service.dhan_token = token
            market_service.headers["access-token"] = token
        # Optional: allow updating client id if passed explicitly
        if config.get("client_id"):
            market_service.dhan_client_id = config["client_id"]
            market_service.headers["client-id"] = config["client_id"]
        return {"status": "updated", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error updating DHAN config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True
    )