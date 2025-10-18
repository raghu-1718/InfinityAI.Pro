#!/usr/bin/env python3
"""
InfinityAI.Pro - Engine A: Market Data + Option Chain + AI Integration Service
Complete integration with Vertex AI Gemini 2.5 Flash Lite, Dhan API, and Hugging Face
Deployable on GCP Cloud Run with Secret Manager
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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from google.cloud import secretmanager
import google.auth

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

# ========== Pydantic Models ==========

class TextRequest(BaseModel):
    text: str

class SymbolRequest(BaseModel):
    symbol: str

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

# ========== Secret Manager Helper ==========

class SecretManager:
    def __init__(self):
        try:
            _, self.project_id = google.auth.default()
            self.client = secretmanager.SecretManagerServiceClient()
            logger.info(f"✅ Secret Manager initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"❌ Secret Manager init failed: {e}")
            self.client = None
            self.project_id = None

    def get_secret(self, secret_name: str) -> str:
        if not self.client or not self.project_id:
            return os.getenv(secret_name.upper().replace('-', '_'), "")
        
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.warning(f"⚠️ Failed to get secret {secret_name}: {e}")
            return os.getenv(secret_name.upper().replace('-', '_'), "")

# ========== Main Service Class ==========

class MarketDataService:
    def __init__(self):
        self.secret_manager = SecretManager()
        
        # Dhan API Setup
        self.dhan_base_url = "https://api.dhan.co"
        self.dhan_access_token = self.secret_manager.get_secret("dhan-access-token")
        self.dhan_api_key = self.secret_manager.get_secret("dhan-api-key")
        self.dhan_api_secret = self.secret_manager.get_secret("dhan-api-secret")
        self.dhan_client_id = "1101302170"  # From JWT token

        self.dhan_headers = {
            "access-token": self.dhan_access_token,
            "client-id": self.dhan_client_id,
            "Content-Type": "application/json"
        }

        # Vertex AI Gemini Setup
        self.vertex_api_key = self.secret_manager.get_secret("vertex-ai-api-key")
        self.gemini_model = "gemini-2.5-flash-lite"
        self.gemini_url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{self.gemini_model}:generateContent"

        # Hugging Face Setup
        self.hf_token = self.secret_manager.get_secret("huggingface-api-token")
        self.hf_model = "distilbert-base-uncased"
        self.hf_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"

        # Cache
        self.signals_cache: List[MarketSignal] = []
        self.option_chain_cache: Dict[str, Any] = {}

        # Symbols
        self.symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK"]
        logger.info("✅ Engine A initialized with Dhan + Vertex AI + Hugging Face support.")

    # ========== Vertex AI Gemini Methods ==========

    async def generate_with_gemini(self, text: str) -> Dict[str, Any]:
        if not self.vertex_api_key:
            return {"error": "Vertex AI key not configured", "summary": ""}

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": text}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 200
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gemini_url}?key={self.vertex_api_key}",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error: {error_text}")
                        return {"error": f"API Error {response.status}", "summary": ""}
                    
                    data = await response.json()
                    summary = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {"model": self.gemini_model, "summary": summary}
        except Exception as e:
            logger.error(f"Gemini request failed: {e}")
            return {"error": str(e), "summary": ""}

    # ========== Dhan API Methods ==========

    async def fetch_positions(self) -> Optional[Dict]:
        if not self.dhan_access_token:
            return {"error": "Dhan credentials not configured"}
        
        url = f"{self.dhan_base_url}/positions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.dhan_headers) as r:
                if r.status == 200:
                    return await r.json()
                logger.error(f"Dhan positions failed: {r.status}")
                return {"error": f"API Error {r.status}"}

    async def fetch_orders(self) -> Optional[Dict]:
        if not self.dhan_access_token:
            return {"error": "Dhan credentials not configured"}
        
        url = f"{self.dhan_base_url}/orders"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.dhan_headers) as r:
                if r.status == 200:
                    return await r.json()
                logger.error(f"Dhan orders failed: {r.status}")
                return {"error": f"API Error {r.status}"}

    async def fetch_option_chain(self, symbol: str) -> Optional[Dict]:
        if not self.dhan_access_token:
            return {"error": "Dhan credentials not configured"}
        
        url = f"{self.dhan_base_url}/optionchain"
        payload = {"symbol": symbol}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.dhan_headers, json=payload) as r:
                if r.status == 200:
                    data = await r.json()
                    self.option_chain_cache[symbol] = data
                    return data
                logger.error(f"Dhan option chain failed for {symbol}: {r.status}")
                return {"error": f"API Error {r.status}"}

    # ========== Hugging Face Methods ==========

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        if not self.hf_token:
            return {"error": "Hugging Face token not configured"}

        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": text}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.hf_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {"error": f"HF API Error {response.status}: {error_text}"}
                    
                    data = await response.json()
                    return {"model": self.hf_model, "result": data}
        except Exception as e:
            logger.error(f"Hugging Face request failed: {e}")
            return {"error": str(e)}

    # ========== Technical Analysis ==========

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
    logger.info("🚀 Engine A starting with full API integrations...")
    yield
    logger.info("🛑 Engine A stopping...")

app = FastAPI(
    title="InfinityAI.Pro - Engine A",
    description="Market Data + Option Chain + AI Integration (Gemini 2.5 Flash Lite + Dhan + Hugging Face)",
    version="3.0.0",
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
    return {
        "status": "active", 
        "timestamp": datetime.now().isoformat(),
        "engines": ["Gemini 2.5 Flash Lite", "Dhan API", "Hugging Face"],
        "version": "3.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/signals")
async def get_signals():
    data = await service.process_signals()
    return {"count": len(data), "signals": [asdict(s) for s in data]}

@app.get("/api/dhan/positions")
async def get_positions():
    data = await service.fetch_positions()
    return data

@app.get("/api/dhan/orders")
async def get_orders():
    data = await service.fetch_orders()
    return data

@app.get("/api/dhan/optionchain/{symbol}")
async def get_option_chain(symbol: str):
    data = await service.fetch_option_chain(symbol)
    if not data or "error" in data:
        raise HTTPException(500, data.get("error", f"Failed to fetch option chain for {symbol}"))
    return {"symbol": symbol, "data": data}

@app.post("/api/gemini/generate")
async def generate_text(request: TextRequest):
    result = await service.generate_with_gemini(request.text)
    if "error" in result and result["error"]:
        raise HTTPException(500, result["error"])
    return result

@app.post("/api/gemini/summary")
async def summarize_text(request: TextRequest):
    prompt = f"Summarize this in a few sentences: {request.text}"
    result = await service.generate_with_gemini(prompt)
    if "error" in result and result["error"]:
        raise HTTPException(500, result["error"])
    return result

@app.post("/api/huggingface/sentiment")
async def analyze_text_sentiment(request: TextRequest):
    result = await service.analyze_sentiment(request.text)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result

@app.post("/api/dhan/postback")
async def dhan_postback(request: Request):
    """Deprecated legacy Dhan postback endpoint.
    Use unified webhook at https://infinityai.pro/api/webhooks/dhan (Engine C)"""
    try:
        data = await request.json()
        logger.warning(f"⚠️ Legacy postback hit on Engine A. Forward clients to unified webhook. Payload: {data}")
    except Exception:
        pass
    # Return 410 Gone with guidance
    from fastapi import Response
    return Response(
        content=json.dumps({
            "status": "gone",
            "message": "This endpoint is deprecated. Use https://infinityai.pro/api/webhooks/dhan",
            "redirect_to": "https://infinityai.pro/api/webhooks/dhan"
        }),
        status_code=410,
        media_type="application/json"
    )

@app.get("/api/dhan/callback")
async def dhan_callback(code: str = None):
    """Handle OAuth callback from Dhan"""
    logger.info(f"📥 Dhan callback received with code: {code}")
    return {"status": "callback_received", "code": code, "timestamp": datetime.now().isoformat()}

# ========== Entrypoint ==========

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting Engine A on port {port}")
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port)