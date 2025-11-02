import os
import hmac
import hashlib
from fastapi import APIRouter, Request, Header, HTTPException, status

router = APIRouter(tags=["Webhooks"]) 

# Secret for Dhan webhook signature verification
DHAN_WEBHOOK_SECRET = os.environ.get("DHAN_WEBHOOK_SECRET")


def verify_dhan_signature(request_data: bytes, signature: str) -> bool:
    """Verifies the incoming webhook signature from Dhan using HMAC-SHA256."""
    if not DHAN_WEBHOOK_SECRET:
        # Fail closed if not configured
        return False

    digest = hmac.new(
        DHAN_WEBHOOK_SECRET.encode("utf-8"),
        request_data,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature or "")


@router.post("/webhook/dhan")
async def handle_dhan_webhook(
    request: Request,
    x_dhan_signature: str | None = Header(default=None),
):
    """
    Receives and validates webhooks from Dhan.
    Next step (optional): forward payload to Engine C/D (internal URL or Pub/Sub).
    """
    if not x_dhan_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="x-dhan-signature header missing.",
        )

    # Read raw body (limit size in production if desired)
    raw_body = await request.body()

    if not verify_dhan_signature(raw_body, x_dhan_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature.",
        )

    # Signature valid: parse payload
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Example: forward to Engine C/D or enqueue
    # import aiohttp
    # engine_c_url = os.getenv("ENGINE_C_INTERNAL_URL", "")
    # if engine_c_url:
    #     async with aiohttp.ClientSession() as session:
    #         await session.post(engine_c_url, json=payload, timeout=5)

    return {"status": "received"}
