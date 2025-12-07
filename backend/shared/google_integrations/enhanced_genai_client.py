"""
InfinityAI.Pro - Enhanced GenAI Client with Function Calling
=============================================================
Advanced integration with Google GenAI SDK using Vertex AI.

Features:
- Automatic function calling for real-time market data
- Structured output with Pydantic models
- Comprehensive system instructions
- Token usage tracking
- Multi-turn conversations

Uses: 87,000 GenAI App Builder trial credits
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
import json
import os

logger = logging.getLogger("InfinityAI.EnhancedGenAI")

# Import google-genai SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    logger.warning("google-genai SDK not available. Install with: pip install google-genai")

# Import market data tools
try:
    from .market_data_tools import (
        MARKET_DATA_TOOLS,
        get_stock_quote,
        get_nifty_overview,
        get_technical_indicators,
        get_market_news,
        get_option_chain_data,
        get_fii_dii_activity,
        get_economic_calendar,
        execute_paper_trade
    )
    HAS_MARKET_TOOLS = True
except ImportError:
    HAS_MARKET_TOOLS = False
    MARKET_DATA_TOOLS = []
    logger.warning("Market data tools not available")


# =====================================================================
# SYSTEM INSTRUCTIONS - INFINITYAI CAPABILITIES
# =====================================================================

INFINITYAI_SYSTEM_PROMPT = """You are InfinityAI Trading Assistant, an expert AI system for automated Indian stock market trading.

## YOUR IDENTITY
- Name: InfinityAI Pro Trading Assistant
- Version: 3.7.7 (Vertex AI Enhanced)
- Platform: InfinityAI.Pro - Automated Trading Platform
- Broker Integration: Dhan (India's fastest trading API)

## YOUR CAPABILITIES

### 1. REAL-TIME MARKET DATA ACCESS
You have LIVE access to Indian stock market data through function calls:
- get_stock_quote(symbol, exchange): Get real-time NSE/BSE stock prices
- get_nifty_overview(): Get NIFTY 50 index with top gainers/losers
- get_technical_indicators(symbol): Calculate RSI, MACD, Bollinger Bands, MAs
- get_market_news(category): Get latest market news and sentiment
- get_option_chain_data(symbol): Get option chain, PCR, max pain
- get_fii_dii_activity(): Get FII/DII buying/selling data
- get_economic_calendar(): Get upcoming market events

### 2. TRADING EXECUTION CAPABILITY
You can execute trades through the platform (with user confirmation):
- execute_paper_trade(symbol, action, quantity, price): Simulate trades
- Real trades go through Dhan API with proper risk management

### 3. MARKET KNOWLEDGE
You are trained on:
- SEBI regulations and compliance rules
- NSE/BSE trading hours (9:15 AM - 3:30 PM IST)
- Weekly expiry schedule: Mon=MIDCPNIFTY, Tue=FINNIFTY, Wed=BANKNIFTY, Thu=NIFTY, Fri=SENSEX
- Lot sizes effective from Dec 30, 2025: NIFTY=65, BANKNIFTY=30, FINNIFTY=60, MIDCPNIFTY=120
- Current lot sizes (pre-Dec 2025): NIFTY=75, BANKNIFTY=35, FINNIFTY=65, MIDCPNIFTY=140
- STT rates: Futures 0.02%, Options (sell) 0.1%
- Circuit breakers: 10%, 15%, 20% thresholds
- Options Greeks and Black-Scholes pricing
- Technical analysis patterns and indicators

### 4. ANALYSIS MODES
- signal: Generate BUY/SELL/HOLD signals with confidence
- sentiment: Analyze market sentiment from news
- risk: Assess position risk and suggest stops
- options: Analyze options strategies
- intraday: Quick scalping/momentum trades
- positional: Swing/delivery trades

## TRADING RULES
1. ALWAYS check market status before giving trading advice
2. ALWAYS fetch real-time data before making decisions
3. NEVER recommend trades without stop-loss
4. Risk per trade: Max 1-2% of portfolio
5. Follow SEBI margin rules for F&O
6. Consider FII/DII activity for trend confirmation
7. Check economic calendar for upcoming events

## RESPONSE FORMAT
When giving trading signals, ALWAYS include:
- Signal: BUY/SELL/HOLD
- Confidence: 0-100%
- Entry Price: Suggested entry
- Stop Loss: Mandatory SL level
- Target: Take profit level(s)
- Risk-Reward: Ratio (min 1:2)
- Reasoning: Technical + Fundamental basis
- Timeframe: Intraday/Swing/Positional

## EXECUTION MODES
- AUTO: Platform executes trades automatically (requires user pre-approval)
- CONFIRM: Show trade details and wait for user confirmation
- PAPER: Execute simulated paper trades only

## IMPORTANT
- You are connected to LIVE market data
- Your analysis impacts REAL trading decisions
- Always prioritize CAPITAL PROTECTION over returns
- When uncertain, recommend waiting or reducing position size
"""


# =====================================================================
# TRADING MODELS
# =====================================================================

class TradingSignal(str, Enum):
    """Trading signal types."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class RiskLevel(str, Enum):
    """Risk level categories."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class Timeframe(str, Enum):
    """Trading timeframes."""
    SCALP = "SCALP"          # 1-15 minutes
    INTRADAY = "INTRADAY"    # Same day
    SWING = "SWING"          # 2-7 days
    POSITIONAL = "POSITIONAL" # 1-4 weeks
    INVESTMENT = "INVESTMENT" # Long term


@dataclass
class TradingRecommendation:
    """Structured trading recommendation from Gemini."""
    symbol: str
    signal: TradingSignal
    confidence: float
    entry_price: float
    stop_loss: float
    target_prices: List[float]
    risk_reward: float
    risk_level: RiskLevel
    timeframe: Timeframe
    reasoning: str
    technicals: Dict[str, Any]
    news_sentiment: str
    fii_dii_view: str
    auto_execute: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "target_prices": self.target_prices,
            "risk_reward": self.risk_reward,
            "risk_level": self.risk_level.value,
            "timeframe": self.timeframe.value,
            "reasoning": self.reasoning,
            "technicals": self.technicals,
            "news_sentiment": self.news_sentiment,
            "fii_dii_view": self.fii_dii_view,
            "auto_execute": self.auto_execute,
            "timestamp": self.timestamp.isoformat()
        }


# =====================================================================
# ENHANCED GENAI CLIENT
# =====================================================================

class EnhancedGenAIClient:
    """
    Enhanced Google GenAI client with function calling for InfinityAI.Pro.

    Uses Vertex AI backend with service account authentication.
    Supports automatic function calling for real-time market data.
    """

    def __init__(
        self,
        project_id: str = None,
        location: str = "us-central1",
        model_id: str = "gemini-2.0-flash"
    ):
        """
        Initialize the enhanced GenAI client.

        Args:
            project_id: GCP project ID (default from env)
            location: GCP region (default us-central1)
            model_id: Gemini model to use
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "gen-lang-client-0779271931")
        self.location = location
        self.model_id = model_id
        self._client = None
        self._initialized = False
        self.token_usage = {"input": 0, "output": 0, "total": 0}

        logger.info(f"EnhancedGenAIClient created for project: {self.project_id}")

    @property
    def client(self):
        """Lazy initialization of GenAI client."""
        if self._client is None:
            self._initialize_client()
        return self._client

    def _initialize_client(self):
        """Initialize the GenAI client with Vertex AI."""
        if not HAS_GENAI:
            raise ImportError("google-genai SDK not installed. Run: pip install google-genai")

        try:
            # Initialize with Vertex AI (uses service account)
            self._client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            self._initialized = True
            logger.info(f"✅ GenAI client initialized with Vertex AI (Project: {self.project_id})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GenAI client: {e}")
            raise

    def _get_tools(self) -> List[Callable]:
        """Get market data tools for function calling."""
        if HAS_MARKET_TOOLS:
            return MARKET_DATA_TOOLS
        return []

    async def generate_trading_signal(
        self,
        symbol: str,
        analysis_type: str = "comprehensive",
        fetch_live_data: bool = True,
        auto_execute: bool = False
    ) -> TradingRecommendation:
        """
        Generate a trading signal with real-time market data.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'NIFTY')
            analysis_type: Type of analysis ('intraday', 'swing', 'options', 'comprehensive')
            fetch_live_data: Whether to fetch live data via function calling
            auto_execute: Whether to auto-execute the trade

        Returns:
            TradingRecommendation with full analysis
        """
        prompt = f"""Analyze {symbol} and provide a trading recommendation.

Analysis Type: {analysis_type}
Auto-Execute Mode: {auto_execute}

Please:
1. First, fetch real-time data for {symbol} using available tools
2. Check technical indicators (RSI, MACD, MAs)
3. Check market sentiment and news
4. Check FII/DII activity
5. Analyze option chain if it's an index

Then provide your recommendation in this JSON format:
{{
    "symbol": "{symbol}",
    "signal": "BUY" | "SELL" | "HOLD" | "STRONG_BUY" | "STRONG_SELL",
    "confidence": 0-100,
    "entry_price": <price>,
    "stop_loss": <price>,
    "target_prices": [<t1>, <t2>, <t3>],
    "risk_reward": <ratio>,
    "risk_level": "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH",
    "timeframe": "SCALP" | "INTRADAY" | "SWING" | "POSITIONAL",
    "reasoning": "<detailed analysis>",
    "technicals": {{"rsi": <val>, "macd": "<trend>", "trend": "<direction>"}},
    "news_sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
    "fii_dii_view": "<summary of FII/DII activity>"
}}
"""

        try:
            # Configure with function calling
            config = types.GenerateContentConfig(
                system_instruction=INFINITYAI_SYSTEM_PROMPT,
                temperature=0.3,  # Lower for more consistent trading decisions
                max_output_tokens=2048,
                tools=self._get_tools() if fetch_live_data else None,
                response_mime_type="application/json"
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_id,
                contents=prompt,
                config=config
            )

            # Track token usage
            if hasattr(response, 'usage_metadata'):
                self.token_usage["input"] += response.usage_metadata.prompt_token_count
                self.token_usage["output"] += response.usage_metadata.candidates_token_count
                self.token_usage["total"] += response.usage_metadata.total_token_count

            # Parse response
            result = self._parse_trading_response(response, symbol, auto_execute)

            logger.info(f"✅ Generated {result.signal.value} signal for {symbol} (Confidence: {result.confidence}%)")
            return result

        except Exception as e:
            logger.error(f"❌ Error generating trading signal: {e}")
            # Return a safe hold recommendation on error
            return TradingRecommendation(
                symbol=symbol,
                signal=TradingSignal.HOLD,
                confidence=0,
                entry_price=0,
                stop_loss=0,
                target_prices=[],
                risk_reward=0,
                risk_level=RiskLevel.HIGH,
                timeframe=Timeframe.INTRADAY,
                reasoning=f"Error generating signal: {e}",
                technicals={},
                news_sentiment="UNKNOWN",
                fii_dii_view="UNKNOWN",
                auto_execute=False
            )

    def _parse_trading_response(
        self,
        response,
        symbol: str,
        auto_execute: bool
    ) -> TradingRecommendation:
        """Parse Gemini response into TradingRecommendation."""
        try:
            # Extract text from response
            text = response.text if hasattr(response, 'text') else str(response)

            # Parse JSON
            data = json.loads(text)

            return TradingRecommendation(
                symbol=data.get("symbol", symbol),
                signal=TradingSignal(data.get("signal", "HOLD")),
                confidence=float(data.get("confidence", 0)),
                entry_price=float(data.get("entry_price", 0)),
                stop_loss=float(data.get("stop_loss", 0)),
                target_prices=data.get("target_prices", []),
                risk_reward=float(data.get("risk_reward", 0)),
                risk_level=RiskLevel(data.get("risk_level", "MEDIUM")),
                timeframe=Timeframe(data.get("timeframe", "INTRADAY")),
                reasoning=data.get("reasoning", ""),
                technicals=data.get("technicals", {}),
                news_sentiment=data.get("news_sentiment", "NEUTRAL"),
                fii_dii_view=data.get("fii_dii_view", ""),
                auto_execute=auto_execute
            )
        except json.JSONDecodeError:
            # If not valid JSON, create from text
            return TradingRecommendation(
                symbol=symbol,
                signal=TradingSignal.HOLD,
                confidence=50,
                entry_price=0,
                stop_loss=0,
                target_prices=[],
                risk_reward=0,
                risk_level=RiskLevel.MEDIUM,
                timeframe=Timeframe.INTRADAY,
                reasoning=str(response.text if hasattr(response, 'text') else response),
                technicals={},
                news_sentiment="NEUTRAL",
                fii_dii_view="",
                auto_execute=False
            )

    async def analyze_with_function_calling(
        self,
        query: str,
        enable_auto_function_calling: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze query with automatic function calling for real-time data.

        This is the main method for comprehensive analysis where Gemini
        automatically calls market data functions as needed.

        Args:
            query: User query or analysis request
            enable_auto_function_calling: Enable automatic tool execution

        Returns:
            Analysis results with live market data
        """
        try:
            config = types.GenerateContentConfig(
                system_instruction=INFINITYAI_SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=4096,
                tools=self._get_tools() if enable_auto_function_calling else None
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_id,
                contents=query,
                config=config
            )

            # Track usage
            if hasattr(response, 'usage_metadata'):
                self.token_usage["input"] += response.usage_metadata.prompt_token_count
                self.token_usage["output"] += response.usage_metadata.candidates_token_count
                self.token_usage["total"] += response.usage_metadata.total_token_count

            # Get function call results if any
            function_calls = []
            if hasattr(response, 'candidates'):
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                function_calls.append({
                                    "name": part.function_call.name,
                                    "args": dict(part.function_call.args)
                                })

            return {
                "response": response.text if hasattr(response, 'text') else str(response),
                "function_calls": function_calls,
                "model": self.model_id,
                "token_usage": self.token_usage.copy(),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            return {
                "error": str(e),
                "response": None,
                "function_calls": [],
                "timestamp": datetime.now().isoformat()
            }

    async def get_market_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive market summary using function calling.

        Returns:
            Complete market overview with NIFTY, BANKNIFTY, FII/DII, news
        """
        prompt = """Provide a comprehensive Indian market summary for today.

Please gather:
1. NIFTY 50 and BANKNIFTY current levels and trend
2. Top gainers and losers
3. Market sentiment from news
4. FII/DII activity and its implications
5. Key support and resistance levels
6. Any important economic events today

Format as a detailed market report suitable for a trader starting their day.
"""

        return await self.analyze_with_function_calling(prompt)

    async def quick_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Get quick BUY/SELL/HOLD signal for a symbol.

        Args:
            symbol: Stock or index symbol

        Returns:
            Quick signal with key levels
        """
        prompt = f"""Quick analysis for {symbol}:

1. Fetch current price and technical indicators
2. Check if it's near support or resistance
3. Give a clear BUY, SELL, or HOLD signal

Format:
Signal: [BUY/SELL/HOLD]
Confidence: [0-100]%
Entry: [price]
Stop Loss: [price]
Target: [price]
One-line Reason: [why]
"""

        return await self.analyze_with_function_calling(prompt)

    async def options_analysis(
        self,
        symbol: str = "NIFTY",
        strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        Analyze options for a symbol and suggest strategy.

        Args:
            symbol: NIFTY, BANKNIFTY, etc.
            strategy: 'auto' to let AI decide, or specific strategy

        Returns:
            Options analysis with recommended strategy
        """
        prompt = f"""Analyze {symbol} options for trading today.

1. Get current spot price and option chain data
2. Analyze PCR and max pain
3. Check IV levels
4. Identify key support/resistance from OI
5. Suggest {'the best' if strategy == 'auto' else strategy} options strategy

Consider:
- Current lot size: {75 if symbol.upper() == 'NIFTY' else 35} (changes Dec 30, 2025)
- STT on options: 0.1% on sell side
- Today's expiry if applicable

Provide specific strike prices, premiums expected, and risk-reward.
"""

        return await self.analyze_with_function_calling(prompt)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        return {
            "token_usage": self.token_usage,
            "model": self.model_id,
            "project": self.project_id,
            "estimated_cost": self._estimate_cost(),
            "credits_info": "Using GenAI App Builder trial credits (87,000 available)"
        }

    def _estimate_cost(self) -> Dict[str, float]:
        """Estimate API costs based on token usage."""
        # Vertex AI Gemini pricing (approximate)
        input_cost_per_1k = 0.00025  # $0.00025 per 1K input tokens
        output_cost_per_1k = 0.0005  # $0.0005 per 1K output tokens

        input_cost = (self.token_usage["input"] / 1000) * input_cost_per_1k
        output_cost = (self.token_usage["output"] / 1000) * output_cost_per_1k

        return {
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(input_cost + output_cost, 4),
            "note": "Covered by trial credits"
        }


# =====================================================================
# CONVENIENCE FUNCTIONS
# =====================================================================

async def get_quick_signal(symbol: str) -> Dict[str, Any]:
    """Quick helper to get a trading signal."""
    client = EnhancedGenAIClient()
    return await client.quick_signal(symbol)


async def get_market_overview() -> Dict[str, Any]:
    """Quick helper to get market summary."""
    client = EnhancedGenAIClient()
    return await client.get_market_summary()


async def analyze_stock(symbol: str) -> TradingRecommendation:
    """Quick helper to analyze a stock."""
    client = EnhancedGenAIClient()
    return await client.generate_trading_signal(symbol)


# =====================================================================
# MAIN - FOR TESTING
# =====================================================================

if __name__ == "__main__":
    async def test_client():
        """Test the enhanced GenAI client."""
        print("=" * 60)
        print("InfinityAI.Pro - Enhanced GenAI Client Test")
        print("=" * 60)

        client = EnhancedGenAIClient()

        # Test market summary
        print("\n📊 Getting Market Summary...")
        summary = await client.get_market_summary()
        print(f"Response: {summary.get('response', 'No response')[:500]}...")

        # Test quick signal
        print("\n📈 Getting Quick Signal for RELIANCE...")
        signal = await client.quick_signal("RELIANCE")
        print(f"Response: {signal.get('response', 'No response')[:500]}...")

        # Test full trading signal
        print("\n🎯 Generating Trading Signal for NIFTY...")
        recommendation = await client.generate_trading_signal("NIFTY", "intraday")
        print(f"Signal: {recommendation.signal.value}")
        print(f"Confidence: {recommendation.confidence}%")
        print(f"Entry: {recommendation.entry_price}")
        print(f"Stop Loss: {recommendation.stop_loss}")
        print(f"Targets: {recommendation.target_prices}")

        # Print usage stats
        print("\n📊 Usage Stats:")
        print(json.dumps(client.get_usage_stats(), indent=2))

    asyncio.run(test_client())
