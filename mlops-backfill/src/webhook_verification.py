"""
Webhook Signature Verification

Validates incoming webhooks from DhanHQ using HMAC-SHA256.
Ensures webhook authenticity and integrity.

Reference: DhanHQ Webhook Documentation
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple
import os

logger = logging.getLogger(__name__)


class WebhookSignatureVerifier:
    """Verifies webhook signatures from DhanHQ"""

    # DhanHQ uses HMAC-SHA256 with the webhook secret
    ALGORITHM = "sha256"

    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize verifier

        Args:
            webhook_secret: Secret key for webhook verification
                          If None, loads from DHAN_WEBHOOK_SECRET env var
        """
        self.webhook_secret = webhook_secret or os.getenv("DHAN_WEBHOOK_SECRET", "")

        if not self.webhook_secret:
            logger.warning(
                "⚠️ DHAN_WEBHOOK_SECRET not configured. "
                "Webhook verification will be disabled."
            )

    def verify_signature(
        self,
        body: bytes,
        signature_header: str,
        webhook_secret: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Verify webhook signature

        Args:
            body: Raw request body (must be bytes)
            signature_header: Value of X-Dhan-Signature header
            webhook_secret: Override default secret

        Returns:
            Tuple of (is_valid, message)
        """
        secret = webhook_secret or self.webhook_secret

        if not secret:
            return False, "Webhook secret not configured"

        if not signature_header:
            return False, "X-Dhan-Signature header missing"

        # Calculate expected signature
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(signature_header, expected_signature)

            if is_valid:
                logger.info("✅ Webhook signature verified")
                return True, "Signature valid"
            else:
                logger.warning("❌ Webhook signature mismatch")
                return False, "Signature mismatch"

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False, f"Verification error: {str(e)}"

    def get_signature_for_body(
        self,
        body: bytes,
        webhook_secret: Optional[str] = None
    ) -> str:
        """
        Generate signature for a body (for testing)

        Args:
            body: Request body
            webhook_secret: Override default secret

        Returns:
            Hex-encoded signature
        """
        secret = webhook_secret or self.webhook_secret

        if not secret:
            raise ValueError("Webhook secret not configured")

        return hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()


class WebhookPayloadValidator:
    """Validates webhook payload structure and content"""

    @staticmethod
    def validate_order_update(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate order update payload

        Expected structure:
        {
            "orderId": "order_id",
            "clientId": "client_id",
            "orderStatus": "FILLED|REJECTED|CANCELLED|PENDING",
            "price": 100.5,
            "quantity": 10,
            "executedQuantity": 10,
            "tradedPrice": 100.5,
            "symbol": "NIFTY",
            "exchange": "NSE",
            "timestamp": "2024-01-20T10:30:00Z"
        }
        """
        required_fields = ["orderId", "clientId", "orderStatus"]

        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"

        # Validate order status
        valid_statuses = ["FILLED", "REJECTED", "CANCELLED", "PENDING", "PARTIAL"]
        if payload.get("orderStatus") not in valid_statuses:
            return False, f"Invalid order status: {payload.get('orderStatus')}"

        return True, None

    @staticmethod
    def validate_trade_update(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate trade update payload

        Expected structure:
        {
            "tradeId": "trade_id",
            "orderId": "order_id",
            "symbol": "NIFTY",
            "quantity": 10,
            "price": 100.5,
            "side": "BUY|SELL",
            "timestamp": "2024-01-20T10:30:00Z"
        }
        """
        required_fields = ["tradeId", "orderId", "symbol", "quantity", "price", "side"]

        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"

        # Validate side
        if payload.get("side") not in ["BUY", "SELL"]:
            return False, f"Invalid side: {payload.get('side')}"

        # Validate quantities
        if payload.get("quantity", 0) <= 0:
            return False, "Quantity must be positive"

        if payload.get("price", 0) <= 0:
            return False, "Price must be positive"

        return True, None

    @staticmethod
    def validate_postback(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate generic postback payload

        Can be order update or trade update
        """
        # Try order update validation
        is_valid, error = WebhookPayloadValidator.validate_order_update(payload)
        if is_valid:
            return True, None

        # Try trade update validation
        is_valid, error = WebhookPayloadValidator.validate_trade_update(payload)
        if is_valid:
            return True, None

        return False, error or "Invalid payload structure"


# Global verifier instance
_verifier: Optional[WebhookSignatureVerifier] = None


def get_webhook_verifier() -> WebhookSignatureVerifier:
    """Get or create global webhook verifier"""
    global _verifier
    if _verifier is None:
        _verifier = WebhookSignatureVerifier()
    return _verifier


def verify_dhan_webhook(
    body: bytes,
    signature_header: str
) -> Tuple[bool, str]:
    """
    Verify DhanHQ webhook signature

    Args:
        body: Raw request body
        signature_header: X-Dhan-Signature header value

    Returns:
        Tuple of (is_valid, message)
    """
    verifier = get_webhook_verifier()
    return verifier.verify_signature(body, signature_header)
