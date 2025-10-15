#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine A: Market Data + Option Chain Ingestion Service
Enhanced real-time market data + option chain integration for Indian exchanges (NSE, BSE, MCX)
Includes Google Vertex & Gemini AI summarization.
Deployable on GCP Cloud Run
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import aiohttp
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Security middleware import (safe fallback)
sys.path.append('/app')
try:
    from security_middleware import add_security_headers
except ImportError:
    def add_security_headers(app):
        pass

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - ENGINE-A - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("engine_a_market_data.log")
    ]
)
logger = logging.getLogger("engine-a")

# ========== Data Models ==========

@dataclass
class TechnicalIndicators:
    rsi: float
    ema_20: float
    ema_50: float
    bollinger_upper: float
    bollinger_lower: float
    macd: float

@dataclass
class MarketSignal:
    symbol: str
    price: float
    timestamp: datetime
    signal_type: str  # BUY, SELL, HOLD
    confidence: float
    indicators: Dict[str, float]

@dataclass
class OptionChainEntry:
    strikePrice: float
    callLtp: float
    putLtp: float
    callOi: float
    putOi: float
    iv: float
    delta: float
    gamma: float
    theta: float
    vega: float


# ========== Main Service Class ==========

class MarketDataService:
    def __init__(self):
        # Dhan API Setup
        self.base_url = "https://api.dhan.co/v2"
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN", "")
        self.client_id = os.getenv("DHAN_CLIENT_ID", "")

        self.headers = {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json"
        }

        # Vertex/Gemini (Optional)
        self.vertex_url = os.getenv("GCP_VERTEX_ENDPOINT", "")
        self.gemini_url = os.getenv("GCP_GEMINI_ENDPOINT", "")

        # Cache
        self.signals_cache: List[MarketSignal] = []
        self.option_chain_cache: Dict[str, Any] = {}
        self.market_data_cache = {}

        # Symbols (You can dynamically load these)
        self.symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK"]
        logger.info("✅ Engine A initialized with Dhan + Vertex/Gemini support.")

    # ========== Core Dhan APIs ==========

    async def fetch_positions(self) -> Optional[Dict]:
        url = f"{self.base_url}/positions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as r:
                return await r.json() if r.status == 200 else {}

    async def fetch_orders(self) -> Optional[Dict]:
        url = f"{self.base_url}/orders"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as r:
                return await r.json() if r.status == 200 else {}

    async def fetch_live_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch live quotes from Dhan API or mock data"""
        try:
            # In production, implement actual Dhan API call
            # For now, return mock data
            quotes = {}
            for symbol in symbols:
                quotes[symbol] = {
                    "ltp": 1000 + hash(symbol) % 500,  # Mock price
                    "change": (hash(symbol) % 20) - 10,  # Mock change
                    "volume": hash(symbol) % 100000,
                    "timestamp": datetime.now().isoformat()
                }
            
            self.market_data_cache.update(quotes)
            return quotes
            
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return {}

    # ========== Option Chain ==========

    async def fetch_expiry_list(self, symbol: str) -> List[str]:
        url = f"{self.base_url}/optionchain/expirylist"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json={"symbol": symbol}) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("expiryDates", [])
                logger.error(f"Failed expiry list {symbol}: {r.status}")
                return []

    async def fetch_option_chain(self, symbol: str, expiry: str) -> Optional[Dict]:
        url = f"{self.base_url}/optionchain"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json={"symbol": symbol, "expiry": expiry}) as r:
                if r.status == 200:
                    return await r.json()
                logger.error(f"Option chain fetch failed for {symbol}: {r.status}")
                return None

    async def get_option_chain(self, symbol: str, expiry: str) -> Dict[str, Any]:
        """Get option chain data with fallback to mock data"""
        try:
            # Try to fetch real data first
            real_data = await self.fetch_option_chain(symbol, expiry)
            if real_data:
                return real_data
                
            # Fallback to mock data
            return {
                "symbol": symbol,
                "expiry": expiry,
                "strikes": [
                    {
                        "strike": 21000 + i * 50,
                        "call_ltp": 50 + i,
                        "put_ltp": 45 + i,
                        "call_oi": 1000 * i,
                        "put_oi": 950 * i
                    } for i in range(10)
                ],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            return {}

    # ========== Vertex/Gemini AI (Optional summarization) ==========

    async def summarize_with_vertex(self, text: str) -> str:
        if not self.vertex_url:
            return "Vertex not configured"
        payload = {"instances": [{"content": text}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.vertex_url, json=payload) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("predictions", [{}])[0].get("summary", "No summary")
                return f"Vertex Error {r.status}"

    async def summarize_with_gemini(self, text: str) -> str:
        if not self.gemini_url:
            return "Gemini not configured"
        payload = {"contents": [{"role": "user", "parts": [{"text": text}]}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.gemini_url, json=payload) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return f"Gemini Error {r.status}"

    # ========== Technical Calculations ==========

    def calculate_indicators(self, prices: List[float]) -> TechnicalIndicators:
        df = pd.DataFrame({"close": prices})
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        ema_20 = df["close"].ewm(span=20).mean()
        ema_50 = df["close"].ewm(span=50).mean()
        rolling_mean = df["close"].rolling(window=20).mean()
        rolling_std = df["close"].rolling(window=20).std()
        bollinger_upper = rolling_mean + (rolling_std * 2)
        bollinger_lower = rolling_mean - (rolling_std * 2)
        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        macd = ema_12 - ema_26
        return TechnicalIndicators(
            rsi=float(rsi.iloc[-1]),
            ema_20=float(ema_20.iloc[-1]),
            ema_50=float(ema_50.iloc[-1]),
            bollinger_upper=float(bollinger_upper.iloc[-1]),
            bollinger_lower=float(bollinger_lower.iloc[-1]),
            macd=float(macd.iloc[-1])
        )

    def generate_signal(self, symbol: str, price: float, indicators: TechnicalIndicators) -> MarketSignal:
        buys, sells = 0, 0
        if indicators.rsi < 30: buys += 1
        if indicators.rsi > 70: sells += 1
        if indicators.ema_20 > indicators.ema_50: buys += 1
        if indicators.ema_20 < indicators.ema_50: sells += 1
        signal = "BUY" if buys > sells else "SELL" if sells > buys else "HOLD"
        conf = 60 + 10 * abs(buys - sells)
        return MarketSignal(symbol, price, datetime.now(), signal, conf, asdict(indicators))

    async def process_signals(self):
        logger.info("🔁 Processing live signals...")
        all_signals = []
        for sym in self.symbols:
            prices = np.random.normal(1000, 10, 50).tolist()  # Replace with live fetch
            ind = self.calculate_indicators(prices)
            sig = self.generate_signal(sym, prices[-1], ind)
            all_signals.append(sig)
        self.signals_cache = all_signals
        return all_signals


# ========== FastAPI Initialization ==========

service = MarketDataService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Engine A starting ...")
    yield
    logger.info("🛑 Engine A stopping ...")

app = FastAPI(
    title="InfinityAI.Pro - Engine A",
    description="Market Data + Option Chain + Vertex AI",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
add_security_headers(app)

# ========== Routes ==========

@app.get("/")
async def root():
    return {"status": "active", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/signals")
async def get_signals():
    data = await service.process_signals()
    return {"count": len(data), "signals": [asdict(s) for s in data]}

@app.get("/api/optionchain/{symbol}")
async def get_option_chain(symbol: str):
    expiries = await service.fetch_expiry_list(symbol)
    if not expiries:
        raise HTTPException(404, f"No expiries found for {symbol}")
    latest_expiry = expiries[0]
    data = await service.fetch_option_chain(symbol, latest_expiry)
    if not data:
        raise HTTPException(500, f"Failed to fetch option chain for {symbol}")
    service.option_chain_cache[symbol] = data
    return {"symbol": symbol, "expiry": latest_expiry, "data": data}

@app.post("/api/vertex/summary")
async def summarize_vertex(body: Dict[str, str]):
    text = body.get("text", "")
    summary = await service.summarize_with_vertex(text)
    return {"summary": summary}

@app.post("/api/gemini/summary")
async def summarize_gemini(body: Dict[str, str]):
    text = body.get("text", "")
    summary = await service.summarize_with_gemini(text)
    return {"summary": summary}

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Market data endpoint for cross-engine communication"""
    try:
        # For demo, return mock data. In production, fetch from Dhan API
        mock_data = {
            "symbol": symbol,
            "price": 1250.50 + hash(symbol) % 100,
            "change": 15.25,
            "change_percent": 1.23,
            "volume": 125000,
            "high": 1275.00,
            "low": 1240.25,
            "timestamp": datetime.now().isoformat()
        }
        return {
            "status": "success",
            "symbol": symbol,
            "data": mock_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        return {
            "status": "error",
            "symbol": symbol,
            "data": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/quotes")
async def get_live_quotes(symbols: str = None):
    """Get live market quotes"""
    try:
        if symbols:
            symbol_list = symbols.split(",")
        else:
            symbol_list = service.symbols[:5]  # Default to first 5
        
        quotes = await service.fetch_live_quotes(symbol_list)
        
        return {
            "status": "success",
            "quotes": quotes,
            "count": len(quotes),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_live_quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/option-chain/{symbol}")
async def get_option_chain_route(symbol: str, expiry: str = None):
    """Get option chain for a symbol"""
    try:
        if not expiry:
            # Default to next Thursday for weekly options
            today = datetime.now()
            days_ahead = 3 - today.weekday()  # Thursday is 3
            if days_ahead <= 0:
                days_ahead += 7
            expiry = (today + timedelta(days_ahead)).strftime("%Y-%m-%d")
        
        option_data = await service.get_option_chain(symbol, expiry)
        
        return {
            "status": "success",
            "data": option_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting option chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "engine-a-market-data",
        "cached_symbols": len(service.market_data_cache),
        "tracked_symbols": len(service.symbols),
        "cached_signals": len(service.signals_cache),
        "timestamp": datetime.now().isoformat()
    }

# ========== Entrypoint ==========

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting Engine A on port {port}")
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port)