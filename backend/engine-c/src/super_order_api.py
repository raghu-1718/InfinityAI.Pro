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
            manager = get_credentials_manager()
            if not manager or not manager.db:
                raise Exception("Firestore DB not initialized")

            order_doc = {
                'id': str(response.get('order_id', datetime.utcnow().timestamp())),
                'user_id': req.user_id,
                'strategy': req.strategy_name,
                'status': 'PENDING',
                'created_at': datetime.utcnow().isoformat(),
            }

            manager.db.collection('trades').document(order_doc['id']).set(order_doc)
            
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
async def get_super_order_status(order_id: str, user_id: str = "raghu_primary"):
    """Get status of a super order"""
    try:
        from src.user_credentials import get_credentials_manager
        manager = get_credentials_manager()
        if not manager or not manager.db:
            raise Exception("Firestore DB not initialized")

        doc = manager.db.collection('trades').document(order_id).get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Super Order not found")

        order_data = doc.to_dict()

        # Verify user owns this order
        resolved_uid = await manager.resolve_user_id(user_id)
        if order_data.get('user_id') != resolved_uid and order_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        return {
            "status": "success",
            "order": order_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching super order status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class BracketSuperOrderRequest(BaseModel):
    security_id: str             # e.g., "45123" (NIFTY 24400 CE)
    exchange_segment: str = "NSE_FNO"
    transaction_type: str = "BUY" # "BUY" or "SELL"
    quantity: int                # Total units (e.g., 5 lots * 65 = 325)
    order_type: str = "LIMIT"    # "LIMIT" or "MARKET"
    price: float                 # Entry Limit Price (e.g., 120.00)
    target_price: float          # Take Profit Price (e.g., 157.50)
    stop_loss_price: float       # Stop Loss Price (e.g., 97.50)
    trailing_jump: Optional[float] = 0.0
    user_id: Optional[str] = "raghu_primary"


@super_order_router.post("/bracket")
@super_order_router.post("")
async def place_bracket_super_order(order: BracketSuperOrderRequest):
    """
    Dispatches a DhanHQ v2 Super Order (Bracket Order).
    Native exchange-side management for Entry, Target, and Stop Loss.
    """
    import uuid
    from src.user_credentials import get_credentials_manager
    from src.dhan_client_wrapper import safe_dhan_request

    # 1. Resolve Vault Credentials (AES-256-GCM Decryption)
    manager = get_credentials_manager()
    resolved_uid = await manager.resolve_user_id(order.user_id)
    creds = await manager.get_user_credentials(resolved_uid)

    if not creds or not creds.get("access_token"):
        raise HTTPException(status_code=401, detail="DhanHQ Vault locked or invalid.")

    # 2. Generate Idempotency Key (Max 30 chars for Dhan API)
    correlation_id = f"SO-{uuid.uuid4().hex[:20]}"

    # 3. Construct DhanHQ API v2 Payload
    payload = {
        "dhanClientId": creds.get("client_id", "1101302170"),
        "correlationId": correlation_id,
        "transactionType": order.transaction_type.upper(),
        "exchangeSegment": order.exchange_segment,
        "productType": "INTRADAY",
        "orderType": order.order_type.upper(),
        "securityId": str(order.security_id),
        "quantity": int(order.quantity),
        "price": float(order.price),
        "targetPrice": float(order.target_price),
        "stopLossPrice": float(order.stop_loss_price),
        "trailingJump": float(order.trailing_jump or 0.0)
    }

    headers = {
        "access-token": creds.get("access_token", ""),
        "client-id": creds.get("client_id", "1101302170"),
        "Content-Type": "application/json"
    }

    url = "https://api.dhan.co/v2/super/orders"

    logger.info(f"🚀 Dispatching Super Order for {order.security_id} (Qty: {order.quantity}) | SL: {order.stop_loss_price} | TGT: {order.target_price}")

    import httpx
    async with httpx.AsyncClient(http2=True, timeout=15.0) as client:
        response = await safe_dhan_request(
            client=client,
            method="POST",
            url=url,
            json=payload,
            headers=headers
        )

    if response.get("status") == "error":
        logger.error(f"Super Order Failed: {response}")
        raise HTTPException(status_code=502, detail=response.get("message", "Super Order Placement Failed"))

    order_id = str(response.get("orderId", response.get("data", {}).get("orderId", uuid.uuid4().hex[:12])))

    # Store order audit in Firestore
    try:
        if manager.db:
            order_doc = {
                "id": order_id,
                "user_id": resolved_uid,
                "security_id": order.security_id,
                "strategy": "BRACKET_SUPER_ORDER",
                "quantity": order.quantity,
                "price": order.price,
                "target_price": order.target_price,
                "stop_loss_price": order.stop_loss_price,
                "trailing_jump": order.trailing_jump,
                "status": response.get("orderStatus", "PENDING"),
                "correlation_id": correlation_id,
                "created_at": datetime.utcnow().isoformat(),
            }
            manager.db.collection("trades").document(order_id).set(order_doc)
    except Exception as e:
        logger.warning(f"Firestore trade logging warning: {e}")

    return {
        "status": "success",
        "orderId": order_id,
        "orderStatus": response.get("orderStatus", "PENDING"),
        "correlationId": correlation_id,
        "user_id": resolved_uid
    }


@super_order_router.delete("/{order_id}/{order_leg}")
async def cancel_super_order_leg(order_id: str, order_leg: str, user_id: str = "raghu_primary"):
    """
    Emergency Intervention / Early Exit.
    Cancels a specific leg of a Super Order (e.g. TARGET_LEG or STOP_LOSS_LEG) on DhanHQ.
    """
    import httpx
    from src.user_credentials import get_credentials_manager
    from src.dhan_client_wrapper import safe_dhan_request

    manager = get_credentials_manager()
    resolved_uid = await manager.resolve_user_id(user_id)
    creds = await manager.get_user_credentials(resolved_uid)

    if not creds or not creds.get("access_token"):
        raise HTTPException(status_code=401, detail="DhanHQ Vault credentials not found")

    url = f"https://api.dhan.co/v2/super/orders/{order_id}/{order_leg}"
    headers = {
        "access-token": creds.get("access_token", ""),
        "client-id": creds.get("client_id", "1101302170"),
        "Content-Type": "application/json"
    }

    logger.info(f"🛑 Cancelling Super Order {order_id} Leg {order_leg} for {resolved_uid}")
    async with httpx.AsyncClient(http2=True, timeout=15.0) as client:
        res = await safe_dhan_request(client=client, method="DELETE", url=url, headers=headers)
    return {
        "status": "success",
        "orderId": order_id,
        "cancelledLeg": order_leg,
        "details": res
    }


class ChargesCalculationRequest(BaseModel):
    premium: float
    lot_size: int
    lots: Optional[int] = 1
    exchange: Optional[str] = "NSE"
    target_price: Optional[float] = None


@super_order_router.post("/charges/calculate")
async def calculate_trade_charges(req: ChargesCalculationRequest):
    """
    Computes exact DhanHQ brokerage and Indian statutory levies (STT, GST, Stamp Duty, Exchange charges, SEBI turnover fees)
    and evaluates net profitability.
    """
    from src.tax_calculator import calculate_options_roundtrip_charges, evaluate_net_profitability_gate

    charges = calculate_options_roundtrip_charges(
        premium=req.premium,
        lot_size=req.lot_size,
        lots=req.lots or 1,
        exchange=req.exchange or "NSE"
    )

    profitability = None
    if req.target_price is not None:
        profitability = evaluate_net_profitability_gate(
            entry_price=req.premium,
            target_price=req.target_price,
            lot_size=req.lot_size,
            lots=req.lots or 1
        )

    return {
        "status": "success",
        "charges": charges,
        "profitability": profitability
    }


@super_order_router.get("/charges/estimate")
async def estimate_trade_charges(
    premium: float,
    lot_size: int,
    lots: int = 1,
    exchange: str = "NSE"
):
    """
    Quick GET query for round-trip charges breakdown.
    """
    from src.tax_calculator import calculate_options_roundtrip_charges
    charges = calculate_options_roundtrip_charges(
        premium=premium,
        lot_size=lot_size,
        lots=lots,
        exchange=exchange
    )
    return {
        "status": "success",
        "charges": charges
    }


