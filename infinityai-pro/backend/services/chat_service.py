import json
from services.trade_execution import execute_trade
from data.db import get_user_credentials

def parse_command(message: str):
    # Example: "place buy RELIANCE 5"
    tokens = message.lower().split()
    if tokens[0] == "place" and tokens[1] in ["buy", "sell"]:
        return {
            "action": tokens[1].upper(),
            "symbol": tokens[2].upper(),
            "quantity": int(tokens[3]) if len(tokens) > 3 else 1
        }
    return None

async def process_chat_command(message: str, user_id: str) -> str:
    command = parse_command(message)
    if not command:
        return json.dumps({"status": "error", "message": "Invalid command"})
    creds = get_user_credentials(user_id)
    if not creds:
        return json.dumps({"status": "error", "message": "User credentials not found"})
    result = execute_trade(command, user_id)
    return json.dumps(result)
