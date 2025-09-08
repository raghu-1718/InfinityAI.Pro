from core.user_manager import get_user_credentials
from core.broker.adapter_factory import get_adapter
from core.trade_logger import log_trade
from core.telegram_alerts import send_telegram

def execute_trade(decision, user_id):
	creds = get_user_credentials(user_id)
	if not creds:
		return {"status": "error", "message": "Credentials missing"}
	try:
		adapter = get_adapter(creds["broker"])
		result = adapter.execute_trade(decision, creds)
		log_trade(user_id, result)
		send_telegram(creds["telegram_chat_id"], f"Executed {result['action']} on {result['symbol']}")
		return result
	except Exception as e:
		return {"status": "error", "message": str(e)}
