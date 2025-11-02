from dataclasses import dataclass
from typing import Optional

@dataclass
class OrderPayload:
    dhanClientId: str
    transactionType: str  # BUY/SELL
    exchangeSegment: str
    productType: str
    orderType: str
    securityId: str
    quantity: int
    validity: str
    price: Optional[float] = 0.0
