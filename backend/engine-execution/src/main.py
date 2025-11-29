import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dhanhq import dhanhq
from google.cloud import secretmanager
import uvicorn

app = FastAPI(title="InfinityAI.Pro - Engine C (Dhan Trade Execution)")

# --- Secret Manager Helper ---
def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "after-yesterday-473512-k3")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error fetching secret {secret_id}: {e}")
        return ""

# --- Models ---
class OrderRequest(BaseModel):
    transaction_type: str  # BUY/SELL
    exchange_segment: str  # NSE_EQ, NSE_FNO, BSE_EQ, etc.
    product_type: str      # INTRADAY, CNC, MARGIN, etc.
    order_type: str        # MARKET, LIMIT, STOP_LOSS, etc.
    validity: str          # DAY, IOC
    security_id: str       # Dhan Security ID
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

class OrderCancelRequest(BaseModel):
    order_id: str

class OrderModifyRequest(BaseModel):
    order_id: str
    order_type: str
    leg_name: str
    quantity: int
    price: float
    trigger_price: Optional[float] = 0.0
    disclosed_quantity: Optional[int] = 0
    validity: str = "DAY"

# --- DhanHQ Client Helper ---
def get_dhan_client() -> dhanhq:
    """Create authenticated DhanHQ client"""
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")

    # Fallback to Secret Manager
    if not client_id:
        client_id = get_secret("dhan-client-id")
    if not access_token:
        access_token = get_secret("dhan-access-token")

    if not client_id or not access_token:
        raise HTTPException(
            status_code=500,
            detail="Dhan credentials not configured (DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)"
        )

    return dhanhq(client_id, access_token)

# --- Health & Root ---
@app.get("/healthz")
async def healthz():
    return {
        "status": "healthy",
        "service": "engine-c-execution",
        "broker": "DhanHQ"
    }

@app.get("/")
async def root():
    return {
        "service": "InfinityAI.Pro Engine C (DhanHQ Trade Execution)",
        "status": "ready",
        "version": "3.0-dhan-only"
    }

# --- Order Placement Endpoint ---
@app.post("/api/dhan/place-order")
async def place_order(order: OrderRequest):
    """
    Place order via DhanHQ API
    Supports: Equity, F&O, Intraday, CNC, Market, Limit, SL orders
    """
    try:
        dhan_client = get_dhan_client()

        response = dhan_client.place_order(
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

        # Check response status
        if isinstance(response, dict):
            if response.get("status") == "failure":
                raise HTTPException(
                    status_code=400,
                    detail=f"Dhan Order Failed: {response.get('remarks', 'Unknown error')}"
                )
            elif response.get("status") == "success":
                return {
                    "status": "success",
                    "order_id": response.get("data", {}).get("orderId"),
                    "dhan_response": response
                }

        return {"status": "success", "dhan_response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")

# --- Order Cancellation Endpoint ---
@app.post("/api/dhan/cancel-order")
async def cancel_order(request: OrderCancelRequest):
    """Cancel existing order by order_id"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.cancel_order(order_id=request.order_id)

        if isinstance(response, dict) and response.get("status") == "failure":
            raise HTTPException(
                status_code=400,
                detail=f"Order cancellation failed: {response.get('remarks', 'Unknown error')}"
            )

        return {"status": "success", "dhan_response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order cancellation error: {str(e)}")

# --- Order Modification Endpoint ---
@app.post("/api/dhan/modify-order")
async def modify_order(request: OrderModifyRequest):
    """Modify existing order"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.modify_order(
            order_id=request.order_id,
            order_type=request.order_type,
            leg_name=request.leg_name,
            quantity=request.quantity,
            price=request.price,
            trigger_price=request.trigger_price,
            disclosed_quantity=request.disclosed_quantity,
            validity=request.validity
        )

        if isinstance(response, dict) and response.get("status") == "failure":
            raise HTTPException(
                status_code=400,
                detail=f"Order modification failed: {response.get('remarks', 'Unknown error')}"
            )

        return {"status": "success", "dhan_response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order modification error: {str(e)}")

# --- Order Status & Data Endpoints ---
@app.get("/api/dhan/orders")
async def get_orders():
    """Fetch all orders for the day"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_order_list()

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", [])}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

@app.get("/api/dhan/order/{order_id}")
async def get_order_by_id(order_id: str):
    """Fetch specific order details by order_id"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_order_by_id(order_id=order_id)

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", {})}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")

@app.get("/api/dhan/positions")
async def get_positions():
    """Fetch open positions"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_positions()

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", [])}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

@app.get("/api/dhan/holdings")
async def get_holdings():
    """Fetch user holdings"""
    try:
        dhan_client = get_dhan_client()
        response = dhan_client.get_holdings()

        if isinstance(response, dict) and response.get("status") == "success":
            return {"status": "success", "data": response.get("data", [])}

        return {"status": "success", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch holdings: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
