import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_telegram(chat_id, message):
	if not TELEGRAM_BOT_TOKEN or not chat_id:
		print("Telegram credentials missing")
		return False
	url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
	try:
		response = requests.post(url, data={"chat_id": chat_id, "text": message})
		return response.status_code == 200
	except Exception as e:
		print(f"Telegram send error: {e}")
		return False
