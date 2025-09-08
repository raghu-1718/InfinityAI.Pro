from core.broker.dhan_adapter import DhanAdapter
from core.broker.angel_adapter import AngelAdapter

def get_adapter(broker: str):
    if broker.lower() == "dhan":
        return DhanAdapter()
    elif broker.lower() == "angel":
        return AngelAdapter()
    else:
        raise ValueError(f"Unsupported broker: {broker}")
