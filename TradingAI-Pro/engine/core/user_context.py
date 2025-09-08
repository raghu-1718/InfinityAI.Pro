import json
import os

USER_STORE_PATH = os.getenv("USER_STORE_PATH", "config/user_store.json")

def get_user_credentials(user_id):
	try:
		with open(USER_STORE_PATH, "r") as f:
			users = json.load(f)
		return users.get(user_id)
	except Exception as e:
		print(f"User Loader error: {e}")
		return None
