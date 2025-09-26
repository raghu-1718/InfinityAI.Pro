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

def list_users():
	try:
		with open(USER_STORE_PATH, "r") as f:
			users = json.load(f)
		return list(users.keys())
	except Exception as e:
		print(f"User Loader error: {e}")
		return []

def update_user_token(client_id: str, access_token: str, user_id: str = None, data_api_key: str = None, api_secret: str = None) -> bool:
    """
    Update or store access token and API credentials for a user.
    If user_id is not provided, use client_id as user_id.
    """
    try:
        # Load existing users
        users = {}
        if os.path.exists(USER_STORE_PATH):
            with open(USER_STORE_PATH, "r") as f:
                users = json.load(f)

        # Use client_id as user_id if not provided
        if not user_id:
            user_id = client_id

        # Update or create user entry
        if user_id not in users:
            users[user_id] = {}

        users[user_id]["client_id"] = client_id
        users[user_id]["access_token"] = access_token
        users[user_id]["broker"] = "dhan"

        # Add API credentials if provided
        if data_api_key:
            users[user_id]["data_api_key"] = data_api_key
        if api_secret:
            users[user_id]["api_secret"] = api_secret

        # Save updated users
        with open(USER_STORE_PATH, "w") as f:
            json.dump(users, f, indent=2)

        return True

    except Exception as e:
        print(f"Error updating user token: {e}")
        return False

def get_user_by_client_id(client_id: str):
    """
    Find user by Dhan client ID.
    """
    try:
        with open(USER_STORE_PATH, "r") as f:
            users = json.load(f)

        for user_id, creds in users.items():
            if creds.get("client_id") == client_id:
                return {**creds, "user_id": user_id}

        return None

    except Exception as e:
        print(f"Error finding user by client_id: {e}")
        return None
