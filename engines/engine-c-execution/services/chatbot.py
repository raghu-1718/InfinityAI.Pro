from typing import Tuple, Dict, Any, Optional
import os
import time
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from google.cloud import secretmanager
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', os.getenv('PROJECT_ID', ''))

def get_gemini_api_key() -> str:
    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{PROJECT_ID}/secrets/gemini-api-key-primary/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode('UTF-8')
    except Exception:
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{PROJECT_ID}/secrets/gemini-api-key-secondary/versions/latest"
            response = client.access_secret_version(request={"name": secret_name})
            return response.payload.data.decode('UTF-8')
        except Exception:
            key = os.getenv('GEMINI_API_KEY_PRIMARY') or os.getenv('GEMINI_API_KEY')
            if key:
                return key
            raise RuntimeError('Gemini API key not configured')

def classify_intent(message: str) -> Tuple[str, float]:
    msg = message.lower()
    if any(w in msg for w in ["status", "health", "system", "running"]):
        return ("status", 0.9)
    if any(w in msg for w in ["market", "price", "signal", "data"]):
        return ("market_data", 0.8)
    if any(w in msg for w in ["ai", "predict", "forecast", "analysis"]):
        return ("ai_prediction", 0.8)
    if any(w in msg for w in ["trade", "buy", "sell", "order"]):
        return ("trade_execution", 0.7)
    if any(w in msg for w in ["portfolio", "balance", "holdings"]):
        return ("portfolio", 0.8)
    if any(w in msg for w in ["dhan", "oauth", "connect", "account"]):
        return ("account_management", 0.7)
    return ("general", 0.5)

async def generate_response(intent: str, message: str, confidence: float) -> str:
    # Use Gemini when available
    if not HAS_GENAI:
        return f"Assistant not configured: Gemini unavailable (intent={intent})"

    try:
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        gemini_prompt = f"""
        You are InfinityAI.Pro's expert chatbot.
        User message: {message}
        Detected intent: {intent}
        Confidence: {confidence}

        Provide a concise, helpful response.
        """
        response = model.generate_content(gemini_prompt)
        return response.text
    except Exception as e:
        logger.warning(f"Gemini generation failed: {e}")
        return f"Assistant error: {str(e)[:200]}"
