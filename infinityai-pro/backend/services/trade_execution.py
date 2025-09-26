from data.db import get_user_credentials
from services.broker_dhan import DhanAdapter
from utils.logger import get_logger
from utils.settings import settings
import asyncio

async def execute_trade(decision, user_id):
    creds = get_user_credentials(user_id)
    if not creds:
        return {"status": "error", "message": "Missing credentials"}
    adapter = DhanAdapter()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, adapter.execute_trade, decision, creds)
    # log_trade(user_id, result)
    # send_telegram(creds.get("telegram_chat_id"), f"{result['action']} {result.get('symbol', '')} executed")
    return result