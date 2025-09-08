from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.services.chat_service import process_chat_command

router = APIRouter()

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
