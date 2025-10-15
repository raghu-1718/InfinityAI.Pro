from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
import random
from typing import Dict, List, Any
from pydantic import BaseModel
import asyncio

app = FastAPI(
    title="InfinityAI Engine A - Market Data",
    description="Real-time market data ingestion and technical analysis for NSE/BSE/MCX",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Indian market symbols
INDIAN_SYMBOLS = [
    "NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", 
    "HDFC", "ICICIBANK", "BHARTIARTL", "KOTAKBANK", "SBIN"
]

# Market exchanges
EXCHANGES = ["NSE", "BSE", "MCX"]

class MarketSignal(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    exchange: str
    technical_indicators: Dict[str, float]
    signal_type: str
    timestamp: str

def generate_mock_market_data(symbol: str) -> Dict[str, Any]:
    """Generate realistic mock market data for Indian markets"""
    base_price = random.uniform(100, 5000)  # INR price range
    change = random.uniform(-50, 50)
    change_percent = (change / base_price) * 100
    
    # Technical indicators
    technical_indicators = {
        "rsi": random.uniform(20, 80),
        "ema_20": base_price * random.uniform(0.95, 1.05),
        "ema_50": base_price * random.uniform(0.90, 1.10),
        "bollinger_upper": base_price * random.uniform(1.02, 1.08),
        "bollinger_lower": base_price * random.uniform(0.92, 0.98),
        "macd": random.uniform(-10, 10),
        "volume_ratio": random.uniform(0.5, 2.0),
        "price_change_1h": random.uniform(-2, 2),
        "price_change_4h": random.uniform(-5, 5),
        "support_level": base_price * random.uniform(0.95, 0.99),
        "resistance_level": base_price * random.uniform(1.01, 1.05)
    }
    
    # Determine signal type based on technical indicators
    rsi = technical_indicators["rsi"]
    if rsi < 30:
        signal_type = "BUY"
    elif rsi > 70:
        signal_type = "SELL"
    else:
        signal_type = "HOLD"
    
    return {
        "symbol": symbol,
        "price": round(base_price, 2),
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "volume": random.randint(10000, 1000000),
        "exchange": random.choice(EXCHANGES),
        "technical_indicators": technical_indicators,
        "signal_type": signal_type,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        "market_status": "OPEN" if 9 <= time.gmtime().tm_hour <= 15 else "CLOSED"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "engine-a-market-data",
        "version": "2.0.0",
        "market_focus": "NSE/BSE/MCX",
        "supported_symbols": len(INDIAN_SYMBOLS),
        "data_sources": "Live market feeds (mock)",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        "uptime": "running"
    }

@app.get("/api/signals")
async def get_market_signals():
    """Get trading signals for all tracked symbols"""
    try:
        signals = []
        for symbol in INDIAN_SYMBOLS[:5]:  # Limit to 5 for demo
            market_data = generate_mock_market_data(symbol)
            signals.append(market_data)
        
        return {
            "status": "success",
            "signals": signals,
            "count": len(signals),
            "exchanges": EXCHANGES,
            "market_focus": "Indian Markets (NSE/BSE/MCX)",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signals: {str(e)}")

@app.get("/api/market-data/{symbol}")
async def get_symbol_data(symbol: str):
    """Get detailed market data for a specific symbol"""
    try:
        # Validate symbol
        if symbol.upper() not in INDIAN_SYMBOLS:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not tracked")
        
        market_data = generate_mock_market_data(symbol.upper())
        
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "data": market_data,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market data: {str(e)}")

@app.post("/api/refresh")
async def refresh_market_data():
    """Refresh market data cache"""
    try:
        # Simulate data refresh
        await asyncio.sleep(1)
        
        return {
            "status": "success",
            "message": "Market data refreshed",
            "symbols_updated": len(INDIAN_SYMBOLS),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh data: {str(e)}")

@app.get("/api/exchanges")
async def get_exchanges():
    """Get supported exchanges information"""
    return {
        "status": "success",
        "exchanges": [
            {
                "code": "NSE",
                "name": "National Stock Exchange of India",
                "timezone": "Asia/Kolkata",
                "trading_hours": "09:15 - 15:30 IST"
            },
            {
                "code": "BSE", 
                "name": "Bombay Stock Exchange",
                "timezone": "Asia/Kolkata",
                "trading_hours": "09:15 - 15:30 IST"
            },
            {
                "code": "MCX",
                "name": "Multi Commodity Exchange",
                "timezone": "Asia/Kolkata", 
                "trading_hours": "09:00 - 23:30 IST"
            }
        ],
        "count": len(EXCHANGES),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }

@app.get("/api/symbols")
async def get_symbols():
    """Get all tracked symbols"""
    return {
        "status": "success",
        "symbols": INDIAN_SYMBOLS,
        "count": len(INDIAN_SYMBOLS),
        "market_focus": "Indian equities and indices",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "InfinityAI Engine A - Market Data",
        "version": "2.0.0",
        "status": "operational",
        "description": "Real-time market data ingestion and technical analysis for Indian markets",
        "features": [
            "NSE/BSE/MCX market data",
            "Technical indicator calculations",
            "Trading signal generation",
            "Real-time price updates",
            "Indian market focus"
        ],
        "endpoints": [
            "/health - Service health check",
            "/api/signals - Get trading signals",
            "/api/market-data/{symbol} - Get symbol data",
            "/api/exchanges - Get exchange information", 
            "/api/symbols - Get tracked symbols",
            "/api/refresh - Refresh market data"
        ],
        "supported_symbols": len(INDIAN_SYMBOLS),
        "exchanges": EXCHANGES
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)