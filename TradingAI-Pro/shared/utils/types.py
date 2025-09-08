from typing import TypedDict, Literal, Optional

Action = Literal["BUY", "SELL", "HOLD"]

class Decision(TypedDict, total=False):
    action: Action
    symbol: str
    quantity: int
    price: float
    reason: str

class Postback(TypedDict, total=False):
    dhanClientId: str
    orderId: str
    orderStatus: str
    transactionType: str
    tradingSymbol: str
    quantity: int
