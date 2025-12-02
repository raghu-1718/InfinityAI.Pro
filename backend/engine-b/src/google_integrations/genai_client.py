"""
InfinityAI.Pro - Google GenAI SDK Integration
==============================================
Official Google GenAI SDK integration for Gemini model access.
Replaces raw REST API calls with the official Python SDK.

Based on: https://github.com/googleapis/python-genai
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger("InfinityAI.GenAI")


class GeminiModel(Enum):
    """Available Gemini models for trading analysis."""
    FLASH = "gemini-2.0-flash"
    FLASH_LITE = "gemini-2.0-flash-lite"
    PRO = "gemini-1.5-pro"
    PRO_LATEST = "gemini-1.5-pro-latest"


@dataclass
class TradingPrompt:
    """Structured prompt for trading analysis."""
    symbol: str
    market: str = "NSE"
    analysis_type: str = "signal"  # signal, risk, sentiment, technical
    context: Dict[str, Any] = field(default_factory=dict)
    historical_data: Optional[str] = None
    news_context: Optional[str] = None


@dataclass
class TradingAnalysis:
    """Structured response from Gemini trading analysis."""
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    risk_level: str  # LOW, MEDIUM, HIGH
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    timeframe: str = "INTRADAY"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_response: Optional[str] = None


class GenAIClient:
    """
    Official Google GenAI SDK client for InfinityAI.Pro trading platform.

    Features:
    - Async and sync API support
    - Structured trading prompts
    - Response parsing for trading signals
    - Rate limiting and retry logic
    - Caching for repeated queries
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: GeminiModel = GeminiModel.FLASH,
        project_id: Optional[str] = None,
        location: str = "us-central1"
    ):
        """
        Initialize the GenAI client.

        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            model: Gemini model to use
            project_id: GCP project ID for Vertex AI
            location: GCP region for Vertex AI
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model = model
        self._client = None
        self._initialized = False

        if not HAS_GENAI:
            logger.warning("google-genai SDK not installed. Install with: pip install google-genai")

    def _ensure_client(self):
        """Lazy initialization of the GenAI client."""
        if self._initialized:
            return

        if not HAS_GENAI:
            raise RuntimeError("google-genai SDK not installed")

        try:
            # Prefer Vertex AI with Application Default Credentials for Cloud Run
            # This works better with GCP service accounts
            if self.project_id:
                self._client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location
                )
                logger.info(f"✅ GenAI client initialized with Vertex AI (project: {self.project_id})")
            elif self.api_key:
                # Fallback to API key if no project
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"✅ GenAI client initialized with API key")
            else:
                raise RuntimeError("No project_id or api_key configured for GenAI")
            self._initialized = True
            logger.info(f"✅ Using model: {self.model.value}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GenAI client: {e}")
            raise

    async def generate_trading_signal(
        self,
        prompt: TradingPrompt,
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> TradingAnalysis:
        """
        Generate a trading signal using Gemini.

        Args:
            prompt: Structured trading prompt
            temperature: Model temperature (lower = more deterministic)
            max_tokens: Maximum response tokens

        Returns:
            TradingAnalysis with signal and reasoning
        """
        self._ensure_client()

        system_instruction = self._build_trading_system_prompt()
        user_prompt = self._build_trading_user_prompt(prompt)

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model.value,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )

            return self._parse_trading_response(prompt.symbol, response.text)

        except Exception as e:
            logger.error(f"❌ GenAI trading signal generation failed: {e}")
            return TradingAnalysis(
                symbol=prompt.symbol,
                signal="HOLD",
                confidence=0.0,
                reasoning=f"Error generating signal: {str(e)}",
                risk_level="HIGH",
                raw_response=None
            )

    async def analyze_market_sentiment(
        self,
        news_items: List[str],
        symbol: str
    ) -> Dict[str, Any]:
        """
        Analyze market sentiment from news items.

        Args:
            news_items: List of news headlines/articles
            symbol: Stock symbol for context

        Returns:
            Sentiment analysis results
        """
        self._ensure_client()

        prompt = f"""Analyze the market sentiment for {symbol} based on these news items:

{chr(10).join(f'- {item}' for item in news_items)}

Provide:
1. Overall sentiment (BULLISH/BEARISH/NEUTRAL)
2. Sentiment score (-1.0 to 1.0)
3. Key factors affecting the stock
4. Short-term outlook (1-5 days)
5. Risk factors to consider

Respond in JSON format:
{{
    "sentiment": "BULLISH|BEARISH|NEUTRAL",
    "score": 0.0,
    "key_factors": [],
    "outlook": "",
    "risks": []
}}"""

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model.value,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=512,
                )
            )

            import json
            try:
                # Try to parse JSON from response
                text = response.text
                # Find JSON in response
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

            return {
                "sentiment": "NEUTRAL",
                "score": 0.0,
                "key_factors": [],
                "outlook": response.text,
                "risks": []
            }

        except Exception as e:
            logger.error(f"❌ Sentiment analysis failed: {e}")
            return {
                "sentiment": "NEUTRAL",
                "score": 0.0,
                "error": str(e)
            }

    async def generate_risk_assessment(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        portfolio_value: float,
        volatility: float
    ) -> Dict[str, Any]:
        """
        Generate AI-powered risk assessment for a trade.

        Args:
            symbol: Stock symbol
            position_size: Number of shares
            entry_price: Entry price per share
            portfolio_value: Total portfolio value
            volatility: Current volatility (e.g., from ATR)

        Returns:
            Risk assessment with recommendations
        """
        self._ensure_client()

        position_value = position_size * entry_price
        position_pct = (position_value / portfolio_value) * 100

        prompt = f"""Assess the risk for this trade:

Symbol: {symbol}
Position Size: {position_size} shares
Entry Price: ₹{entry_price:.2f}
Position Value: ₹{position_value:.2f}
Portfolio Value: ₹{portfolio_value:.2f}
Position % of Portfolio: {position_pct:.2f}%
Current Volatility: {volatility:.2f}%

Provide risk assessment in JSON:
{{
    "risk_score": 0-100,
    "risk_level": "LOW|MEDIUM|HIGH|EXTREME",
    "max_loss_pct": 0.0,
    "recommended_stop_loss": 0.0,
    "recommended_position_size": 0,
    "warnings": [],
    "sebi_compliance": true,
    "recommendations": []
}}"""

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model.value,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=512,
                )
            )

            import json
            try:
                text = response.text
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

            return {
                "risk_score": 50,
                "risk_level": "MEDIUM",
                "raw_response": response.text
            }

        except Exception as e:
            logger.error(f"❌ Risk assessment failed: {e}")
            return {
                "risk_score": 100,
                "risk_level": "EXTREME",
                "error": str(e)
            }

    def _build_trading_system_prompt(self) -> str:
        """Build the system prompt for trading analysis."""
        return """You are an expert algorithmic trading analyst for the Indian stock market (NSE/BSE).
Your role is to analyze market data and provide trading signals with clear reasoning.

Guidelines:
1. Always consider SEBI regulations for algorithmic trading
2. Focus on risk management - never recommend positions exceeding 5% of portfolio
3. Consider market hours (9:15 AM - 3:30 PM IST) and volatility patterns
4. Account for FII/DII activity and market sentiment
5. Use technical analysis (RSI, MACD, Bollinger Bands, Volume) when data is provided
6. Consider fundamental factors for swing trades
7. Always provide stop-loss and target levels
8. Express confidence as a percentage (0-100)

Response Format:
- Signal: BUY, SELL, or HOLD
- Confidence: 0-100%
- Risk Level: LOW, MEDIUM, or HIGH
- Entry Price: specific price or range
- Stop Loss: specific price
- Target: specific price
- Timeframe: INTRADAY, SWING, or POSITIONAL
- Reasoning: clear explanation"""

    def _build_trading_user_prompt(self, prompt: TradingPrompt) -> str:
        """Build the user prompt from TradingPrompt."""
        parts = [f"Analyze {prompt.symbol} on {prompt.market} for {prompt.analysis_type} analysis."]

        if prompt.context:
            parts.append(f"\nCurrent Market Context:\n{prompt.context}")

        if prompt.historical_data:
            parts.append(f"\nHistorical Data:\n{prompt.historical_data}")

        if prompt.news_context:
            parts.append(f"\nRecent News:\n{prompt.news_context}")

        parts.append("\nProvide your analysis with signal, confidence, and reasoning.")

        return "\n".join(parts)

    def _parse_trading_response(self, symbol: str, response_text: str) -> TradingAnalysis:
        """Parse Gemini response into TradingAnalysis."""
        import re

        # Default values
        signal = "HOLD"
        confidence = 50.0
        risk_level = "MEDIUM"
        entry_price = None
        stop_loss = None
        target_price = None

        text_upper = response_text.upper()

        # Extract signal
        if "BUY" in text_upper and "SELL" not in text_upper:
            signal = "BUY"
        elif "SELL" in text_upper and "BUY" not in text_upper:
            signal = "SELL"
        elif "STRONG BUY" in text_upper:
            signal = "BUY"
        elif "STRONG SELL" in text_upper:
            signal = "SELL"

        # Extract confidence
        conf_match = re.search(r'confidence[:\s]+(\d+(?:\.\d+)?)\s*%?', response_text, re.IGNORECASE)
        if conf_match:
            confidence = float(conf_match.group(1))

        # Extract risk level
        if "HIGH RISK" in text_upper or "RISK: HIGH" in text_upper:
            risk_level = "HIGH"
        elif "LOW RISK" in text_upper or "RISK: LOW" in text_upper:
            risk_level = "LOW"

        # Extract prices
        price_patterns = [
            (r'entry[:\s]+₹?\s*(\d+(?:\.\d+)?)', 'entry'),
            (r'stop[- ]?loss[:\s]+₹?\s*(\d+(?:\.\d+)?)', 'stop'),
            (r'target[:\s]+₹?\s*(\d+(?:\.\d+)?)', 'target'),
        ]

        for pattern, price_type in price_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if price_type == 'entry':
                    entry_price = value
                elif price_type == 'stop':
                    stop_loss = value
                elif price_type == 'target':
                    target_price = value

        return TradingAnalysis(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            reasoning=response_text,
            risk_level=risk_level,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            raw_response=response_text
        )


class TradingAnalysisAgent:
    """
    ADK-inspired trading analysis agent.
    Wraps GenAI client with agent-like capabilities.
    """

    def __init__(self, client: Optional[GenAIClient] = None):
        """Initialize the trading analysis agent."""
        self.client = client or GenAIClient()
        self.name = "TradingAnalysisAgent"
        self.capabilities = ["signal_generation", "sentiment_analysis", "risk_assessment"]
        logger.info(f"✅ {self.name} initialized with capabilities: {self.capabilities}")

    async def run(
        self,
        task: str,
        symbol: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the agent with a specific task.

        Args:
            task: Task type (generate_signal, analyze_sentiment, assess_risk)
            symbol: Stock symbol
            **kwargs: Additional task-specific arguments

        Returns:
            Task results
        """
        if task == "generate_signal":
            prompt = TradingPrompt(
                symbol=symbol,
                market=kwargs.get("market", "NSE"),
                analysis_type=kwargs.get("analysis_type", "signal"),
                context=kwargs.get("context", {}),
                historical_data=kwargs.get("historical_data"),
                news_context=kwargs.get("news_context")
            )
            analysis = await self.client.generate_trading_signal(prompt)
            return {
                "task": task,
                "symbol": symbol,
                "signal": analysis.signal,
                "confidence": analysis.confidence,
                "risk_level": analysis.risk_level,
                "entry_price": analysis.entry_price,
                "stop_loss": analysis.stop_loss,
                "target_price": analysis.target_price,
                "reasoning": analysis.reasoning,
                "timestamp": analysis.timestamp.isoformat()
            }

        elif task == "analyze_sentiment":
            news_items = kwargs.get("news_items", [])
            return await self.client.analyze_market_sentiment(news_items, symbol)

        elif task == "assess_risk":
            return await self.client.generate_risk_assessment(
                symbol=symbol,
                position_size=kwargs.get("position_size", 0),
                entry_price=kwargs.get("entry_price", 0),
                portfolio_value=kwargs.get("portfolio_value", 100000),
                volatility=kwargs.get("volatility", 2.0)
            )

        else:
            return {"error": f"Unknown task: {task}"}
