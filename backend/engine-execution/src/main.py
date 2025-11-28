import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dhanhq import dhanhq
import uvicorn

app = FastAPI(title="Iaminfinity - Engine C (Execution)")

# --- Models ---
class OrderRequest(BaseModel):
    transaction_type: str  # BUY/SELL
    exchange_segment: str # NSE_EQ, NSE_FNO, etc.
    product_type: str # INTRADAY, CNC, etc.
    order_type: str # MARKET, LIMIT, etc.
    validity: str # DAY, IOC
    security_id: str
    quantity: int
    price: Optional[float] = 0.0
    trigger_price: Optional[float] = 0.0
    disclosed_quantity: Optional[int] = 0
    after_market_order: Optional[bool] = False
    amo_time: Optional[str] = "OPEN"
    bo_profit_value: Optional[float] = 0.0
    bo_stop_loss_value: Optional[float] = 0.0
    drv_expiry_date: Optional[str] = None
    drv_options_type: Optional[str] = None
    drv_strike_price: Optional[float] = 0.0

# --- Config ---
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

# --- Health ---
@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "service": "engine-c-execution"}

@app.get("/")
async def root():
    return {"service": "Iaminfinity Engine C (Execution)", "status": "ready"}

# --- Execution Endpoint ---
@app.post("/api/dhan/place-order")
async def place_order(order: OrderRequest):
    if not DHAN_CLIENT_ID or not DHAN_ACCESS_TOKEN:
        raise HTTPException(500, "Dhan credentials not configured (DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN).")

    try:
        dhan = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        
        response = dhan.place_order(
            transaction_type=order.transaction_type,
            exchange_segment=order.exchange_segment,
            product_type=order.product_type,
            order_type=order.order_type,
            validity=order.validity,
            security_id=order.security_id,
            quantity=order.quantity,
            price=order.price,
            trigger_price=order.trigger_price,
            disclosed_quantity=order.disclosed_quantity,
            after_market_order=order.after_market_order,
            amo_time=order.amo_time,
            bo_profit_value=order.bo_profit_value,
            bo_stop_loss_value=order.bo_stop_loss_value,
            drv_expiry_date=order.drv_expiry_date,
            drv_options_type=order.drv_options_type,
            drv_strike_price=order.drv_strike_price
        )
        
        if isinstance(response, dict) and response.get("status") == "failure":
             raise HTTPException(400, detail=f"Dhan Order Failed: {response.get("remarks", "Unknown error")}")
             
        return {"status": "success", "dhan_response": response}

    except Exception as e:
        raise HTTPException(500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
