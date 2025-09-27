from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException, File, UploadFile
from typing import Dict
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

@router.get("/quote/{symbol}")
async def get_market_quote(symbol: str, exchange: str = "NSE"):
    """Get real-time market quote"""
    try:
        quote = await ai_manager.get_market_quote(symbol, exchange)
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quote: {str(e)}")

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

@router.websocket("/ws/chat/{user_id}")
async def chat_ws(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            response = await process_chat_command(message, user_id)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print(f"Chat disconnected for user {user_id}")
