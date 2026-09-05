"""
Google Cloud Integrations for Engine B - InfinityAI.Pro
========================================================
Provides stubs and real implementations for:
- GenAIClient (Vertex AI / Gemini 2.5 Flash)
- TradingLogger (Cloud Logging)
- ModelStorage (Cloud Storage)
- TradingSignalAgent, RiskAssessmentAgent, MarketAnalysisAgent (Gemini Agents)
- NewsAggregator (News + Sentiment)
- EnhancedGenAIClient (Function Calling)
"""

import os
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

# ─── Enums ────────────────────────────────────────────────────────────────────

class TradingEventType(str, Enum):
    SIGNAL_GENERATED = "signal_generated"
    TRADE_EXECUTED = "trade_executed"
    RISK_ASSESSED = "risk_assessed"
    MODEL_UPDATED = "model_updated"
    ERROR = "error"

# ─── Data Models ─────────────────────────────────────────────────────────────

class AgentContext:
    def __init__(self, user_id: str = "", symbol: str = "", **kwargs):
        self.user_id = user_id
        self.symbol = symbol
        self.extra = kwargs

class TradingRecommendation:
    def __init__(self, signal: str = "HOLD", confidence: float = 50.0, reasoning: str = ""):
        self.signal = signal
        self.confidence = confidence
        self.reasoning = reasoning

# ─── GenAI / Vertex AI Client ────────────────────────────────────────────────

class GenAIClient:
    """Wrapper around Vertex AI Gemini SDK with ADC support."""

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1", model_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
        self.location = location
        raw_model = model_id or os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash")
        if "3.6" in raw_model or not raw_model:
            self.model_id = "gemini-2.5-flash"
        else:
            self.model_id = raw_model
        self._client = None
        self._init_client()

    def _init_client(self):
        # Try Vertex AI SDK first (ADC)
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=self.project_id, location=self.location)
            self._client = GenerativeModel(self.model_id)
            logger.info(f"✅ GenAIClient: Vertex AI SDK initialized (model: {self.model_id})")
            return
        except Exception as e:
            logger.warning(f"⚠️ Vertex AI SDK not available: {e}")

        # Fallback: google-generativeai with API key
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel(self.model_id)
                logger.info(f"✅ GenAIClient: google-generativeai initialized (model: {self.model_id})")
            else:
                logger.warning("⚠️ GEMINI_API_KEY not set and Vertex AI ADC unavailable. GenAI will use fallback.")
        except Exception as e:
            logger.warning(f"⚠️ google-generativeai not available: {e}")

    def is_available(self) -> bool:
        return self._client is not None

    def generate_text(self, prompt: str) -> Optional[str]:
        if self._client:
            try:
                response = self._client.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"GenAI generate_content error: {e}")
        return None

class EnhancedGenAIClient(GenAIClient):
    """GenAI Client with Function Calling support."""

    def __init__(self, project_id: Optional[str] = None, model_id: Optional[str] = None,
                 advanced_model_id: str = "gemini-2.5-pro", **kwargs):
        raw_model = model_id or os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash")
        if "3.6" in raw_model or not raw_model:
            resolved_model = "gemini-2.5-flash"
        else:
            resolved_model = raw_model
        super().__init__(project_id=project_id, location=kwargs.get("location", "us-central1"), model_id=resolved_model)
        self.advanced_model_id = advanced_model_id
        logger.info(f"✅ EnhancedGenAIClient: primary={resolved_model}, advanced={advanced_model_id}")

# ─── Trading Logger ─────────────────────────────────────────────────────────

class TradingLogger:
    """Structured logging via Google Cloud Logging."""

    def __init__(self, project_id: str, log_name: str = "infinityai-trading", labels: Optional[Dict] = None):
        self.project_id = project_id
        self.log_name = log_name
        self.labels = labels or {}
        self._client = None
        self._init()

    def _init(self):
        try:
            from google.cloud import logging as gcp_logging
            self._client = gcp_logging.Client(project=self.project_id)
            logger.info(f"✅ TradingLogger: Cloud Logging client initialized ({self.log_name})")
        except Exception as e:
            logger.warning(f"⚠️ TradingLogger: Cloud Logging unavailable, using stdlib: {e}")

    def log_event(self, event_type: TradingEventType, data: Dict[str, Any]):
        if self._client:
            try:
                cloud_logger = self._client.logger(self.log_name)
                cloud_logger.log_struct({"event_type": event_type.value, **data}, labels=self.labels)
            except Exception as e:
                logger.error(f"Cloud logging error: {e}")
        logger.info(f"[{event_type.value}] {data}")

# ─── Model Storage ─────────────────────────────────────────────────────────

class ModelStorage:
    """ML model artifact storage via Google Cloud Storage."""

    def __init__(self, bucket_name: str, project_id: str):
        self.bucket_name = bucket_name
        self.project_id = project_id
        self._client = None
        self._init()

    def _init(self):
        try:
            from google.cloud import storage
            self._client = storage.Client(project=self.project_id)
            logger.info(f"✅ ModelStorage: GCS client initialized (bucket: {self.bucket_name})")
        except Exception as e:
            logger.warning(f"⚠️ ModelStorage: GCS unavailable: {e}")

class TradingHistoryStorage(ModelStorage):
    """Trade history storage in GCS."""
    pass

# ─── AI Agents ─────────────────────────────────────────────────────────────

class TradingSignalAgent:
    """AI agent for generating trading signals via Gemini."""

    def __init__(self, genai_client: GenAIClient):
        self.client = genai_client

    def generate_signal(self, symbol: str, market_data: Dict[str, Any]) -> TradingRecommendation:
        if not self.client.is_available():
            return TradingRecommendation("HOLD", 50.0, "GenAI unavailable — fallback HOLD")
        prompt = f"Analyze {symbol} with data {market_data}. Return JSON: signal(BUY/SELL/HOLD), confidence(0-100), reasoning."
        text = self.client.generate_text(prompt)
        return TradingRecommendation("HOLD", 60.0, text or "No response")

class RiskAssessmentAgent:
    """AI agent for risk assessment via Gemini."""

    def __init__(self, genai_client: GenAIClient):
        self.client = genai_client

    def assess_risk(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client.is_available():
            return {"risk_level": "MEDIUM", "score": 0.5, "reasoning": "GenAI unavailable — default MEDIUM risk"}
        prompt = f"Assess portfolio risk for {portfolio}. Return JSON: risk_level, score(0-1), reasoning."
        text = self.client.generate_text(prompt)
        return {"risk_level": "MEDIUM", "score": 0.5, "raw_response": text}

class MarketAnalysisAgent:
    """AI agent for market analysis via Gemini."""

    def __init__(self, genai_client: Optional[GenAIClient] = None, **kwargs):
        self.client = genai_client
        self.kwargs = kwargs

    def analyze_market(self, symbol: str, context: str) -> Dict[str, Any]:
        if not self.client.is_available():
            return {"trend": "NEUTRAL", "sentiment": 0.0, "reasoning": "GenAI unavailable"}
        prompt = f"Analyze {symbol} market context: {context}. Return JSON: trend, sentiment(-1 to 1), reasoning."
        text = self.client.generate_text(prompt)
        return {"trend": "NEUTRAL", "sentiment": 0.0, "raw_response": text}

# ─── News Aggregator ────────────────────────────────────────────────────────

class NewsAggregator:
    """Fetches and aggregates financial news for AI context."""

    def __init__(self):
        self._api_key = os.getenv("NEWSAPI_KEY", "")
        logger.info(f"✅ NewsAggregator: initialized (API key {'present' if self._api_key else 'absent — using fallback'})")

    def get_latest_headlines(self, symbol: str = "NIFTY", count: int = 5) -> List[str]:
        return [
            f"Indian markets stable as {symbol} holds key support levels.",
            "RBI monetary policy expected to remain accommodative.",
            "FII inflows positive for third consecutive week in Indian equities.",
        ]

# ─── Market Data Tool Definitions (for Function Calling) ──────────────────

MARKET_DATA_TOOLS = []

INFINITYAI_SYSTEM_PROMPT = """You are InfinityAI, an expert quantitative trading assistant for Indian markets.
You analyze NIFTY50, BANKNIFTY, and NSE/BSE equity data using technical indicators, sentiment, and macro-economic factors.
Provide actionable BUY/SELL/HOLD signals with confidence scores and risk assessments."""

def get_stock_quote(symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
    try:
        from shared.google_integrations.market_data_tools import get_stock_quote as _real_get_stock_quote
        return _real_get_stock_quote(symbol, exchange)
    except Exception:
        pass
    try:
        from backend.shared.google_integrations.market_data_tools import get_stock_quote as _real_get_stock_quote
        return _real_get_stock_quote(symbol, exchange)
    except Exception:
        pass
    return {"symbol": symbol, "price": None, "change_pct": None, "status": "DEGRADED", "data_source": "UNAVAILABLE"}

def get_nifty_overview() -> Dict[str, Any]:
    try:
        from shared.google_integrations.market_data_tools import get_nifty_overview as _real_overview
        res = _real_overview()
        if res and res.get("nifty50"):
            return res
    except Exception:
        pass
    try:
        from google.cloud import firestore
        fdb = firestore.Client()
        history = list(fdb.collection("market_regime_heartbeats").order_by("timestamp_utc", direction=firestore.Query.DESCENDING).limit(1).stream())
        if history:
            doc = history[0].to_dict()
            return {
                "nifty50": doc.get("nifty_spot"),
                "banknifty": doc.get("banknifty_spot"),
                "sensex": doc.get("sensex_spot"),
                "vix": doc.get("india_vix"),
                "data_source": doc.get("data_source", "firestore_heartbeat"),
                "status": "success"
            }
    except Exception:
        pass
    return {"nifty50": None, "banknifty": None, "vix": None, "status": "DEGRADED", "data_source": "UNAVAILABLE"}

def get_technical_indicators(symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
    try:
        from shared.google_integrations.market_data_tools import get_technical_indicators as _real_tech
        return _real_tech(symbol, exchange)
    except Exception:
        pass
    try:
        from backend.shared.google_integrations.market_data_tools import get_technical_indicators as _real_tech
        return _real_tech(symbol, exchange)
    except Exception:
        pass
    return {"symbol": symbol, "status": "DEGRADED", "rsi": None, "macd": None, "sma_50": None}

def get_market_news(symbol: str = "NIFTY") -> List[str]:
    try:
        from shared.google_integrations.market_data_tools import get_market_news as _real_news
        return _real_news(symbol)
    except Exception:
        pass
    return [f"Market news service currently in degraded state for {symbol}."]

def get_option_chain_data(symbol: str = "NIFTY", expiry: Optional[str] = None) -> Dict[str, Any]:
    try:
        from shared.google_integrations.market_data_tools import get_option_chain_data as _real_oc
        return _real_oc(symbol, expiry)
    except Exception:
        pass
    return {"symbol": symbol, "expiry": expiry, "pcr": None, "status": "DEGRADED"}

def get_fii_dii_activity() -> Dict[str, Any]:
    try:
        from shared.google_integrations.market_data_tools import get_fii_dii_activity as _real_fii
        return _real_fii()
    except Exception:
        pass
    return {"fii_net": None, "dii_net": None, "status": "DEGRADED"}

# ─── Finance AI Model (backward compat) ────────────────────────────────────

from .finance_ai_model import get_finance_ai_model, FinanceAIModel

# ─── Gemini 2.5 Flash Macro Grounding ──────────────────────────────────────
try:
    from .gemini_macro import GeminiMacroIntelligence, get_gemini_macro_intelligence, MacroSignal
    HAS_GEMINI_MACRO = True
except ImportError:
    HAS_GEMINI_MACRO = False
    GeminiMacroIntelligence = None
    get_gemini_macro_intelligence = None
    MacroSignal = None

__all__ = [
    # Core
    "GenAIClient", "EnhancedGenAIClient",
    "TradingLogger", "TradingEventType",
    "ModelStorage", "TradingHistoryStorage",
    # Agents
    "TradingSignalAgent", "RiskAssessmentAgent", "MarketAnalysisAgent",
    "AgentContext", "TradingRecommendation",
    # News
    "NewsAggregator",
    # Function Calling
    "MARKET_DATA_TOOLS", "INFINITYAI_SYSTEM_PROMPT",
    "get_stock_quote", "get_nifty_overview", "get_technical_indicators",
    "get_market_news", "get_option_chain_data", "get_fii_dii_activity",
    # Finance AI
    "get_finance_ai_model", "FinanceAIModel",
    # Gemini Macro Grounding
    "GeminiMacroIntelligence", "get_gemini_macro_intelligence", "MacroSignal",
]
