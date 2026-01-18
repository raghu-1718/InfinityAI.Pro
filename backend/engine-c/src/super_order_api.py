"""
Super Order API for Multi-Leg Options Strategies
Integrates with DhanHQ Super Order endpoint for complex options trades
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

super_order_router = APIRouter(prefix="/api/dhan/super-order", tags=["Super Orders"])


class OrderLeg(BaseModel):
    """Single leg of a multi-leg order"""
    security_id: str
    exchange_segment: str
    transaction_type: str  # BUY or SELL
    order_type: str  # LIMIT or MARKET
    quantity: int
    price: Optional[float] = 0
    product_type: str = "INTRADAY"  # INTRADAY, CNC, MARGIN
    validity: str = "DAY"


class SuperOrderRequest(BaseModel):
    """Multi-leg order request"""
    legs: List[OrderLeg]
    strategy_name: Optional[str] = None  # e.g., Iron Condor, Butterfly
    user_id: str


@super_order_router.post("/place")
async def place_super_order(req: SuperOrderRequest):
    """
    Place a multi-leg options order (Super Order)
    
    Use Cases:
    - Iron Condor (4 legs)
    - Butterfly (3 legs)
    - Spreads (2 legs)
    
    Request Body:
    {
        "user_id": "2508215064",
        "strategy_name": "Iron Condor",
        "legs": [
            {
                "security_id": "12345",
                "exchange_segment": "NSE_FNO",
                "transaction_type": "SELL",
                "order_type": "LIMIT",
                "quantity": 50,
                "price": 20,
                "product_type": "INTRADAY"
            },
            ...
        ]
    }
    """
    try:
        from src.user_credentials import get_credentials_manager
        from src.dhan_client_wrapper import create_dhan_client
        
        # Get user credentials
        credentials_manager = get_credentials_manager()
        creds_response = await credentials_manager.get_user_credentials(req.user_id)
        
        if not creds_response or not creds_response.get("credentials"):
            raise HTTPException(status_code=401, detail="User credentials not found")
        
        creds = creds_response["credentials"]
        
        # Initialize Dhan client
        dhan = create_dhan_client(
            client_id=creds["client_id"],
            access_token=creds["access_token"]
        )
        
        # Prepare legs for DhanHQ
        dhan_legs = []
        for leg in req.legs:
            dhan_legs.append({
                "security_id": leg.security_id,
                "exchange_segment": leg.exchange_segment,
                "transaction_type": leg.transaction_type,
                "order_type": leg.order_type,
                "quantity": leg.quantity,
                "price": leg.price,
                "product_type": leg.product_type,
                "validity": leg.validity
            })
        
        # Place Super Order via DhanHQ API
        # Note: This requires DhanHQ's Super Order API endpoint
        # Format: POST /v2/superorder
        response = dhan.place_super_order(data=dhan_legs)
        
        if response.get('status') == 'success':
            # Store in Firestore
            from google.cloud import firestore
            db = firestore.Client()
            
            order_doc = {
                'user_id': req.user_id,
                'strategy_name': req.strategy_name,
                'legs': req.legs,
                'dhan_response': response,
                'status': 'PENDING',
                'created_at': datetime.utcnow(),
                'order_type': 'SUPER_ORDER'
            }
            
            db.collection('super_orders').document(response.get('order_id', str(datetime.utcnow().timestamp()))).set(order_doc)
            
            return {
                "status": "success",
                "message": "Super Order placed successfully",
                "order_id": response.get('order_id'),
                "dhan_response": response,
                "strategy_name": req.strategy_name,
                "legs_count": len(req.legs),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=f"DhanHQ error: {response.get('remarks')}")
    
    except Exception as e:
        logger.error(f"Error placing super order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@super_order_router.post("/strategy/iron-condor")
async def place_iron_condor(
    user_id: str,
    underlying_spot: float,
    lot_size: int = 50,
    wing_width: int = 100
):
    """
    Quick Iron Condor strategy builder
    
    Args:
        underlying_spot: Current spot price (e.g., 18000)
        lot_size: Quantity per leg (e.g., 50)
        wing_width: Distance between strikes (e.g., 100)
    
    Creates:
        Sell Put @ spot - 100
        Buy Put @ spot - 200
        Sell Call @ spot + 100
        Buy Call @ spot + 200
    """
    try:
        sell_put_strike = underlying_spot - wing_width
        buy_put_strike = underlying_spot - (wing_width * 2)
        sell_call_strike = underlying_spot + wing_width
        buy_call_strike = underlying_spot + (wing_width * 2)
        
        # TODO: Fetch actual security IDs for these strikes
        # For now, return structure
        
        return {
            "status": "success",
            "strategy": "Iron Condor",
            "strikes": {
                "sell_put": sell_put_strike,
                "buy_put": buy_put_strike,
                "sell_call": sell_call_strike,
                "buy_call": buy_call_strike
            },
            "lot_size": lot_size,
            "message": "Use /place endpoint with actual security IDs"
        }
    
    except Exception as e:
        logger.error(f"Error building Iron Condor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@super_order_router.get("/status/{order_id}")
async def get_super_order_status(order_id: str, user_id: str):
    """Get status of a super order"""
    try:
        from google.cloud import firestore
        db = firestore.Client()
        
        doc_ref = db.collection('super_orders').document(order_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Super Order not found")
        
        order_data = doc.to_dict()
        
        # Verify user owns this order
        if order_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        return {
            "status": "success",
            "order": order_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching super order status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
