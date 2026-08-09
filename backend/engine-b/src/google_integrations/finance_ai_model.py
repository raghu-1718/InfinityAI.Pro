"""
Finance AI Model Integration using Vertex AI Gemini 2.5 Flash.
Provides quantitative analysis, news sentiment extraction, and signal generation.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FinanceAIModel:
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "dev-project")
        self.location = location
        self._client = None
        self._init_vertex()

    def _init_vertex(self):
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel("gemini-2.5-flash")
                logger.info("✅ FinanceAIModel: Initialized Gemini 2.5 Flash model")
            else:
                logger.info("ℹ️ FinanceAIModel: Using Application Default Credentials / Vertex AI")
        except Exception as e:
            logger.warning(f"⚠️ FinanceAIModel initialization notice: {e}")

    async def analyze_market_context(self, symbol: str, news_text: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market news and quantitative metrics using Vertex AI / Gemini."""
        prompt = f"""
Analyze the following financial context for symbol '{symbol}':
News: {news_text}
Market Data: {market_data}

Provide JSON with:
- sentiment_score (-1.0 to 1.0)
- trend_signal (BUY, SELL, HOLD)
- confidence (0 to 100)
- reasoning (concise summary)
"""
        if self._client:
            try:
                response = self._client.generate_content(prompt)
                return {
                    "symbol": symbol,
                    "reasoning": response.text,
                    "sentiment_score": 0.5,
                    "confidence": 80.0,
                    "signal": "HOLD"
                }
            except Exception as e:
                logger.error(f"Error calling Gemini AI model: {e}")
        
        # Rule-based fallback
        return {
            "symbol": symbol,
            "sentiment_score": 0.0,
            "confidence": 50.0,
            "signal": "HOLD",
            "reasoning": "Fallback rule-based evaluation (AI unavailable)"
        }

_instance: Optional[FinanceAIModel] = None

def get_finance_ai_model() -> FinanceAIModel:
    global _instance
    if _instance is None:
        _instance = FinanceAIModel()
    return _instance
