#!/usr/bin/env python3
"""
Dhan Webhook Handler for InfinityAI.Pro
Handles real-time trading updates from Dhan API
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - WEBHOOK - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DhanWebhookHandler:
    def __init__(self):
        self.webhook_secret = os.getenv('DHAN_WEBHOOK_SECRET', 'default_secret')
        self.client_id = os.getenv('DHAN_CLIENT_ID')
        
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    async def handle_order_update(self, order_data: Dict[str, Any]):
        """Handle order status updates"""
        try:
            order_id = order_data.get('orderId')
            status = order_data.get('orderStatus')
            
            logger.info(f"Order Update: {order_id} -> {status}")
            
            # TODO: Update order status in your system
            # await self.update_order_status(order_id, status)
            
            return {"status": "processed", "order_id": order_id}
            
        except Exception as e:
            logger.error(f"Error handling order update: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def handle_position_update(self, position_data: Dict[str, Any]):
        """Handle position updates"""
        try:
            symbol = position_data.get('tradingSymbol')
            quantity = position_data.get('netQty')
            
            logger.info(f"Position Update: {symbol} -> {quantity}")
            
            # TODO: Update position in your system
            # await self.update_position(symbol, position_data)
            
            return {"status": "processed", "symbol": symbol}
            
        except Exception as e:
            logger.error(f"Error handling position update: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Global webhook handler
webhook_handler = DhanWebhookHandler()

# Add webhook routes to your existing engines
async def setup_webhook_routes(app: FastAPI):
    """Add webhook routes to FastAPI app"""
    
    @app.post("/api/webhooks/dhan")
    async def dhan_webhook(request: Request, background_tasks: BackgroundTasks):
        """Handle Dhan webhook notifications"""
        try:
            # Get request body and signature
            body = await request.body()
            signature = request.headers.get("X-Dhan-Signature", "")
            
            # Verify signature (in production)
            if os.getenv('ENVIRONMENT') == 'production':
                if not webhook_handler.verify_webhook_signature(body, signature):
                    raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Parse webhook data
            webhook_data = json.loads(body)
            webhook_type = webhook_data.get('type', 'unknown')
            
            logger.info(f"Received webhook: {webhook_type}")
            
            # Handle different webhook types
            if webhook_type == 'order':
                result = await webhook_handler.handle_order_update(webhook_data.get('data', {}))
            elif webhook_type == 'position':
                result = await webhook_handler.handle_position_update(webhook_data.get('data', {}))
            else:
                logger.warning(f"Unknown webhook type: {webhook_type}")
                result = {"status": "ignored", "type": webhook_type}
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/auth/dhan/callback")
    async def dhan_auth_callback(code: str = None, state: str = None):
        """Handle Dhan OAuth callback"""
        try:
            if not code:
                raise HTTPException(status_code=400, detail="Authorization code required")
            
            logger.info(f"Dhan auth callback received: code={code}, state={state}")
            
            # TODO: Exchange code for access token
            # token_response = await exchange_code_for_token(code)
            
            return {
                "status": "success",
                "message": "Authorization successful",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Auth callback error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # This file provides webhook handlers that can be imported into your engines
    print("Dhan webhook handlers ready for integration")