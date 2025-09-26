from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from services.chat_service import process_chat_command
import httpx
import os
import logging

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
    return await proxy_to_runpod(RUNPOD_SD_ENDPOINT, request)

@router.post("/yolo")
async def yolo_detection(request: Request):
    """Proxy to YOLO object detection on RunPod"""
    return await proxy_to_runpod(RUNPOD_YOLO_ENDPOINT, request)

@router.post("/whisper")
async def whisper_transcription(request: Request):
    """Proxy to Whisper STT on RunPod"""
    return await proxy_to_runpod(RUNPOD_WHISPER_ENDPOINT, request)

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
