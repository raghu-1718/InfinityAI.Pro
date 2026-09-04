import requests
from ..core.config import Config
from ..core.utils import setup_logger

log = setup_logger("DhanREST")

class DhanREST:
    def __init__(self):
        self.base = Config.DHAN_API_BASE
        self.headers = {"access-token": Config.DHAN_ACCESS_TOKEN, "client-id": Config.CLIENT_ID}

    def _get(self, endpoint):
        resp = requests.get(f"{self.base}{endpoint}", headers=self.headers, timeout=10)
        return resp.json()

    def _post(self, endpoint, payload):
        resp = requests.post(f"{self.base}{endpoint}", json=payload, headers=self.headers, timeout=10)
        return resp.json()

    def _put(self, endpoint, payload):
        resp = requests.put(f"{self.base}{endpoint}", json=payload, headers=self.headers, timeout=10)
        return resp.json()

    def _delete(self, endpoint):
        resp = requests.delete(f"{self.base}{endpoint}", headers=self.headers, timeout=10)
        return resp.json()

    # --- ORDERS ---
    def place_order(self, payload): return self._post("/orders", payload)
    def modify_order(self, oid, payload): return self._put(f"/orders/{oid}", payload)
    def cancel_order(self, oid): return self._delete(f"/orders/{oid}")
    def get_orders(self): return self._get("/orders")
    def get_trades(self): return self._get("/trades")
    def get_positions(self): return self._get("/positions")
    def get_holdings(self): return self._get("/holdings")
    def get_fund_limit(self): return self._get("/fundlimit")
