from fastapi import APIRouter, Request, HTTPException
from core.user_manager import get_user_credentials
from core.trade_logger import log_trade
from core.telegram_alerts import send_telegram

router = APIRouter()

@router.post("/{user_id}")
async def webhook_handler(user_id: str, request: Request):
	payload = await request.json()
	creds = get_user_credentials(user_id)
	if not creds:
		raise HTTPException(status_code=403, detail="User credentials not found")
	if payload.get("dhanClientId") != creds["client_id"]:
		raise HTTPException(status_code=400, detail="dhanClientId mismatch")
	log_trade(user_id, payload)
	msg = (
		f"Order Update: {payload.get('orderStatus')} - "
		f"{payload.get('transactionType')} {payload.get('tradingSymbol')} "
		f"Qty: {payload.get('quantity')}"
	)
	send_telegram(creds.get("telegram_chat_id"), msg)
	return {"status": "received"}
