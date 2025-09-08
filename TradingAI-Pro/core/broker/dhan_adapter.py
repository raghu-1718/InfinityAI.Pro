import requests

class DhanAdapter:
    def execute_trade(self, strategy, creds):
        if strategy["action"] == "HOLD":
            return {"status": "skipped", "reason": "HOLD action"}

        headers = {
            "access-token": creds["access_token"],
            "X-Client-Id": creds["client_id"],
        }

        payload = {
            "transactionType": strategy["action"],
            "exchange": "NSE",
            "symbolName": strategy["symbol"],
            "productType": "INTRADAY",
            "quantity": strategy.get("quantity", 1),
            "validity": "DAY",
            "orderType": "MARKET",
            "price": 0.0,
            "source": "API"
        }

        try:
            response = requests.post("https://api.dhan.co/orders", json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "symbol": strategy["symbol"],
                    "action": strategy["action"],
                    "orderId": data.get("orderId", ""),
                    "message": "Order placed successfully"
                }
            else:
                return {"status": "error", "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
