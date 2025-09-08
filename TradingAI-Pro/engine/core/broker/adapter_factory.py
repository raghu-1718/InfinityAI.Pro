from engine.core.broker.dhan_adapter import DhanAdapter
from engine.core.broker.angel_adapter import AngelAdapter

def get_adapter(broker: str):
    b = broker.lower()
    if b == "dhan":
        return DhanAdapter()
    if b == "angel":
        return AngelAdapter()
    raise ValueError(f"Unsupported broker: {broker}")
