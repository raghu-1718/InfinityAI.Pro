from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException, File, UploadFile
from typing import Dict, List, Optional
from services.chat_service import process_chat_command
import httpx
import os
import logging

# Import ai_manager after other imports to avoid circular imports
from services.ai import ai_manager

router = APIRouter()
logger = logging.getLogger(__name__)

# RunPod endpoints
RUNPOD_SD_ENDPOINT = os.getenv("RUNPOD_SD_ENDPOINT", "")
RUNPOD_YOLO_ENDPOINT = os.getenv("RUNPOD_YOLO_ENDPOINT", "")
RUNPOD_WHISPER_ENDPOINT = os.getenv("RUNPOD_WHISPER_ENDPOINT", "")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")

async def proxy_to_runpod(endpoint: str, request: Request):
    """Proxy request to RunPod endpoint"""
    if not endpoint:
        raise HTTPException(status_code=503, detail="RunPod endpoint not configured")

    try:
        # Handle different content types
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            # For file uploads (YOLO, Whisper)
            form_data = await request.form()
            files = {}
            data = {}

            for key, value in form_data.items():
                if hasattr(value, 'filename'):  # It's a file
                    files[key] = (value.filename, await value.read(), value.content_type)
                else:  # It's form data
                    data[key] = value

            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"} if RUNPOD_API_KEY else {}

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(endpoint, files=files, data=data, headers=headers)
                return response.json()
        else:
            # For JSON requests (Stable Diffusion)
            payload = await request.json()
            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"} if RUNPOD_API_KEY else {}

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                return response.json()
    except Exception as e:
        logger.error(f"RunPod proxy error: {e}")
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable")

@router.post("/sd")
async def stable_diffusion(request: Request):
    """Proxy to Stable Diffusion on RunPod"""
    endpoint = f"{RUNPOD_SD_ENDPOINT}/sdapi/v1/txt2img"
    return await proxy_to_runpod(endpoint, request)

@router.post("/yolo")
async def yolo_detection(request: Request):
    """Proxy to YOLO object detection on RunPod"""
    endpoint = f"{RUNPOD_YOLO_ENDPOINT}/detect"
    return await proxy_to_runpod(endpoint, request)

@router.post("/whisper")
async def whisper_transcription(request: Request):
    """Proxy to Whisper STT on RunPod"""
    endpoint = f"{RUNPOD_WHISPER_ENDPOINT}/transcribe"
    return await proxy_to_runpod(endpoint, request)

@router.post("/start-simulation")
async def start_trading_simulation(days: int = 30):
    """Start AI-powered trading simulation"""
    try:
        result = await ai_manager.start_trading_simulation(days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.post("/simulate-day")
async def simulate_trading_day(symbols: List[str] = None):
    """Run one day of AI trading simulation"""
    try:
        result = await ai_manager.simulate_trading_day(symbols)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Day simulation failed: {str(e)}")

@router.get("/performance")
async def get_trading_performance():
    """Get trading simulation performance metrics"""
    try:
        result = await ai_manager.get_trading_performance()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance fetch failed: {str(e)}")

@router.get("/realtime-quote/{symbol}")
async def get_realtime_market_quote(symbol: str):
    """Get real-time market quote"""
    try:
        result = await ai_manager.get_realtime_quote(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote fetch failed: {str(e)}")

@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str, interval: str = "5min"):
    """Get historical market data"""
    try:
        data = await ai_manager.get_historical_data(symbol, interval)
        if data is not None:
            return data.to_dict('records')
        return {"error": "No data available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")

@router.post("/analyze-chart")
async def analyze_chart(file: UploadFile = File(...), symbol: str = None):
    """Analyze chart image for technical patterns"""
    try:
        chart_data = await file.read()
        result = await ai_manager.analyze_chart_patterns(chart_data, symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart analysis failed: {str(e)}")

@router.post("/analyze-price-data")
async def analyze_price_data(price_data: Dict, symbol: str):
    """Analyze price data for technical indicators"""
    try:
        import pandas as pd
        df = pd.DataFrame(price_data)
        result = await ai_manager.analyze_price_data(df, symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price analysis failed: {str(e)}")

@router.get("/crypto/quote/{symbol}")
async def get_crypto_quote(symbol: str):
    """Get real-time crypto quote from CoinSwitch"""
    try:
        result = await ai_manager.get_crypto_quote(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto quote fetch failed: {str(e)}")

@router.get("/crypto/historical/{symbol}")
async def get_crypto_historical_data(symbol: str, interval: str = "5min"):
    """Get historical crypto market data"""
    try:
        data = await ai_manager.get_crypto_historical_data(symbol, interval)
        if data is not None and not data.empty:
            return data.to_dict('records')
        return {"error": "No crypto data available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crypto historical data: {str(e)}")

@router.get("/crypto/ticker/{symbol}")
async def get_crypto_ticker(symbol: str):
    """Get crypto ticker data from CoinSwitch"""
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_ticker(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto ticker fetch failed: {str(e)}")

@router.get("/crypto/depth/{symbol}")
async def get_crypto_depth(symbol: str, limit: int = 50):
    """Get crypto order book depth from CoinSwitch"""
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_depth(symbol, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto depth fetch failed: {str(e)}")

@router.get("/crypto/portfolio")
async def get_crypto_portfolio():
    """Get crypto portfolio from CoinSwitch"""
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_portfolio()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto portfolio fetch failed: {str(e)}")

@router.get("/crypto/orders")
async def get_crypto_orders(symbol: Optional[str] = None):
    """Get crypto open orders from CoinSwitch"""
    try:
        if 'crypto_market_data' not in ai_manager.services:
            raise HTTPException(status_code=503, detail="Crypto market data service not available")

        result = ai_manager.services['crypto_market_data'].get_open_orders(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto orders fetch failed: {str(e)}")
