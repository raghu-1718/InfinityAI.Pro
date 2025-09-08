from core.user_manager import get_user_credentials
from core.broker.adapter_factory import get_adapter
from core.trade_logger import log_trade
from core.telegram_alerts import send_telegram
import asyncio

async def execute_trade(decision, user_id):
    creds = get_user_credentials(user_id)
    if not creds:
        return {"status": "error", "message": "Missing credentials"}
    adapter = get_adapter(creds["broker"])
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, adapter.execute_trade, decision, creds)
    log_trade(user_id, result)
    send_telegram(creds.get("telegram_chat_id"), f"{result['action']} {result.get('symbol', '')} executed")
    return result