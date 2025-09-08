import requests

class AngelAdapter:
    def execute_trade(self, strategy, creds):
        if strategy["action"] == "HOLD":
            return {"status": "skipped", "reason": "HOLD action"}

        headers = {
            "Authorization": f"Bearer {creds['access_token']}",
            "Content-Type": "application/json",
            "X-PrivateKey": creds["api_key"],
            "X-SourceID": "WEB",
            "X-ClientLocalIP": creds["local_ip"],
            "X-ClientPublicIP": creds["public_ip"],
            "X-MACAddress": creds["mac_address"]
        }

        payload = {
            "variety": "NORMAL",
            "tradingsymbol": strategy["symbol"],
            "symboltoken": self._get_symbol_token(strategy["symbol"]),
            "transactiontype": strategy["action"],
            "exchange": "NSE",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": strategy.get("quantity",1)
        }

        try:
            response = requests.post("https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder", json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "symbol": strategy["symbol"],
                    "action": strategy["action"],
                    "orderId": data.get("data", {}).get("orderid", ""),
                    "message": "Order placed successfully"
                }
            else:
                return {"status": "error", "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_symbol_token(self, symbol):
        symbol_tokens = {
            "RELIANCE": "2885",
            "TCS": "11536",
            "HDFCBANK": "1333",
            "INFY": "1594",
            "ICICIBANK": "4963"
        }
        return symbol_tokens.get(symbol, "0")
