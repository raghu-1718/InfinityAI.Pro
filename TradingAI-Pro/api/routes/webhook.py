from fastapi import APIRouter, Request, HTTPException
from core.user_manager import get_user_credentials
from core.strategies.breakout import BreakoutStrategy
from core.broker.adapter_factory import get_adapter
from core.trade_logger import log_trade
from core.telegram_alerts import send_telegram

router = APIRouter()

@router.post("/{user_id}")
async def webhook_listener(user_id: str, request: Request):
	data = await request.json()

	creds = get_user_credentials(user_id)
	if not creds:
		raise HTTPException(status_code=403, detail="User credentials not found")

	strategy = BreakoutStrategy()
	decision = strategy.evaluate(data)

	adapter = get_adapter(creds["broker"])
	result = adapter.execute_trade(decision, creds)

	log_trade(user_id, result)
	send_telegram(creds["telegram_chat_id"], f"{result['action']} {result['symbol']} via {creds['broker']}")

	return {"status": "success", "result": result}
