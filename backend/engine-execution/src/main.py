
import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from dhanhq import dhanhq

# --- Pydantic Models for Request & Response ---

class PlaceOrderRequest(BaseModel):
    """Defines the structure for a trade execution request, aligned with DhanHQ SDK."""
    transaction_type: str = Field(..., description="BUY or SELL")
    exchange_segment: str = Field(..., description="e.g., NSE_EQ, BSE_EQ, NSE_FNO")
    product_type: str = Field(..., description="e.g., INTRADAY, CNC, MARGIN")
    order_type: str = Field(..., description="e.g., MARKET, LIMIT, STOP_LOSS")
    validity: str = Field(..., description="e.g., DAY, IOC")
    security_id: str = Field(..., description="Dhan security ID for the instrument")
    quantity: int = Field(..., gt=0, description="Order quantity")
    price: float = Field(0, description="Required for LIMIT orders")

class OrderResponse(BaseModel):
    """Standard response for order placement."""
    status: str
    order_id: str | None = None
    message: str | None = None
    
# --- FastAPI Application Setup ---

app = FastAPI(
    title="InfinityAI - Engine C (DhanHQ Execution)",
    description="Handles live trade execution using the DhanHQ Python SDK.",
    version="1.1.0" # Version updated to reflect SDK integration
)

# --- DhanHQ API Client Dependency ---

def get_dhan_client():
    """
    Dependency that provides an initialized DhanHQ client.
    Requires DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN env vars.
    """
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    
    if not client_id or not access_token:
        raise HTTPException(
            status_code=500, 
            detail="DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN must be configured."
        )
    
    return dhanhq(client_id, access_token)

# --- API Endpoints ---

@app.get("/", tags=["System"])
async def root():
    """Root endpoint describing Engine C capabilities"""
    return {
        "service": "Iaminfinity Engine C",
        "version": "1.1.0",
        "status": "operational",
        "description": "Trade Execution Engine via DhanHQ SDK",
        "capabilities": [
            "Live Trade Execution",
            "Order Placement & Management",
            "DhanHQ Integration",
            "Real-time Order Status",
            "Multi-exchange Support (NSE/BSE)"
        ],
        "endpoints": {
            "place_order": "/api/dhan/place-order - Execute trades via DhanHQ",
            "health": "/healthz - Service health check",
            "docs": "/docs - Interactive API documentation"
        },
        "supported_exchanges": ["NSE_EQ", "BSE_EQ", "NSE_FNO", "BSE_FNO", "MCX", "CDS"],
        "order_types": ["MARKET", "LIMIT", "STOP_LOSS", "STOP_LOSS_MARKET"]
    }

@app.get("/healthz", tags=["System"])
async def healthz():
    """Provides a simple health check for the service."""
    return {"status": "healthy", "service": "engine-c-execution"}

@app.post("/api/dhan/place-order", tags=["Trading"], response_model=OrderResponse)
async def place_order(
    order: PlaceOrderRequest,
    dhan_client: dhanhq = Depends(get_dhan_client)
):
    """
    Receives an order request and places it using the DhanHQ Python SDK.
    """
    try:
        # The SDK maps the function arguments to the API payload.
        response = dhan_client.place_order(
            security_id=order.security_id,
            exchange_segment=order.exchange_segment,
            transaction_type=order.transaction_type,
            quantity=order.quantity,
            order_type=order.order_type,
            product_type=order.product_type,
            price=order.price,
            validity=order.validity
        )

        # Check the response from the SDK
        if response and response.get('status') == 'success' and response.get('order_id'):
            return OrderResponse(
                status="success", 
                order_id=response['order_id']
            )
        else:
            # If the status is not success or order_id is missing
            error_message = response.get("remarks", "Unknown error from DhanHQ SDK")
            return OrderResponse(status="error", message=error_message)

    except Exception as e:
        # Log the exception for debugging
        print(f"An unexpected error occurred during order placement: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An internal error occurred: {str(e)}"
        )
