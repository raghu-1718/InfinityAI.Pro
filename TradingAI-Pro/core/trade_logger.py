import csv
import os
import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log_trade(user_id, trade_data):
	filename = os.path.join(LOG_DIR, f"{user_id}_trades.csv")
	file_exists = os.path.isfile(filename)

	trade_data.setdefault("timestamp", datetime.datetime.now().isoformat())
	trade_data["user_id"] = user_id

	with open(filename, "a", newline="") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=trade_data.keys())
		if not file_exists:
			writer.writeheader()
		writer.writerow(trade_data)

def get_trade_logs(user_id, limit=100):
	filename = os.path.join(LOG_DIR, f"{user_id}_trades.csv")
	if not os.path.exists(filename):
		return []
	with open(filename, "r") as csvfile:
		reader = list(csv.DictReader(csvfile))
		return list(reversed(reader[-limit:]))
