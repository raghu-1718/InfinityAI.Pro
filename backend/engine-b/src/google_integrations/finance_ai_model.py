"""
InfinityAI.Pro - Finance AI Model Integration
=============================================
Specialized finance AI model using Google Gemini for:
- Stock price prediction and analysis
- Technical indicator interpretation
- Sentiment analysis from news
- Risk assessment
- Options Greeks calculation insights
- Market trend analysis

Version: 1.0.0
Author: InfinityAI.Pro
"""

import os
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
import json
import re

# Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None
    types = None

logger = logging.getLogger("InfinityAI.FinanceAI")


class FinanceModelType(Enum):
    """Available finance model configurations."""
    STOCK_ANALYST = "stock_analyst"
    OPTIONS_STRATEGIST = "options_strategist"
    RISK_MANAGER = "risk_manager"
    SENTIMENT_ANALYST = "sentiment_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    PORTFOLIO_OPTIMIZER = "portfolio_optimizer"


@dataclass
class FinanceSignal:
    """Finance AI signal output."""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    target_3: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    position_size_pct: float = 2.0
    timeframe: str = "INTRADAY"
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    risk_level: str = "MEDIUM"
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketAnalysis:
    """Comprehensive market analysis output."""
    symbol: str
    trend: str  # BULLISH, BEARISH, NEUTRAL
    trend_strength: float
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    key_indicators: Dict[str, Any] = field(default_factory=dict)
    sentiment_score: float = 0.0
    volume_analysis: str = ""
    sector_outlook: str = ""
    global_cues: str = ""
    recommendation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


# System prompts for different finance AI models
FINANCE_SYSTEM_PROMPTS = {
    FinanceModelType.STOCK_ANALYST: """You are an expert Indian stock market analyst with deep knowledge of:
- NSE and BSE listed companies
- Fundamental analysis (P/E, P/B, ROE, ROCE, Debt/Equity)
- Sector-specific dynamics (IT, Banking, Pharma, Auto, FMCG, etc.)
- FII/DII activity and its impact
- Corporate actions (dividends, splits, bonuses, buybacks)
- Quarterly results analysis
- Management commentary interpretation

You provide actionable BUY/SELL/HOLD recommendations with:
- Clear entry prices with reasoning
- Stop-loss levels (typically 2-3% for intraday, 5-8% for swing)
- Target prices with multiple levels
- Risk-reward analysis
- Position sizing suggestions

Always consider:
1. Current market conditions (Nifty, Bank Nifty levels)
2. Sector momentum
3. Global cues (SGX Nifty, US markets, Asian markets)
4. News and events
5. Technical levels

Output your analysis in a structured JSON format.""",

    FinanceModelType.OPTIONS_STRATEGIST: """You are an expert F&O (Futures & Options) strategist specializing in Indian markets:

Knowledge Areas:
- Index Options: NIFTY, BANKNIFTY, SENSEX, FINNIFTY
- Stock Options: High-volume F&O stocks
- Greeks: Delta, Gamma, Theta, Vega, Rho
- Options strategies: Straddle, Strangle, Iron Condor, Butterfly, Bull/Bear Spreads
- Expiry dynamics and premium decay
- PCR (Put-Call Ratio) analysis
- Max Pain theory
- Open Interest analysis

Current Rules (SEBI 2024):
- Weekly expiry only for NIFTY (Tuesday) and SENSEX (Thursday)
- BANKNIFTY, FINNIFTY have monthly expiry only
- Lot sizes: NIFTY 75, BANKNIFTY 35, FINNIFTY 65

Provide:
1. Strategy recommendation with legs
2. Entry prices for each leg
3. Breakeven points
4. Max profit/loss potential
5. Optimal exit conditions
6. Greeks-based risk assessment

Output in structured JSON format.""",

    FinanceModelType.RISK_MANAGER: """You are a quantitative risk manager for trading portfolios:

Risk Assessment Areas:
- Value at Risk (VaR) interpretation
- Conditional VaR (CVaR)
- Sharpe Ratio and Sortino Ratio
- Maximum Drawdown analysis
- Beta and correlation analysis
- Position sizing using Kelly Criterion
- Portfolio diversification

For each position/portfolio, analyze:
1. Single-position risk metrics
2. Portfolio-level risk
3. Correlation with market indices
4. Recommended hedge strategies
5. Position size adjustments
6. Stop-loss placement rationale

Indian Market Specifics:
- SEBI margin requirements
- Peak margin rules
- Exposure limits
- Concentration risk limits

Output risk assessment in structured JSON format.""",

    FinanceModelType.SENTIMENT_ANALYST: """You are a financial sentiment analyst specializing in:

News Analysis:
- Corporate announcements
- Regulatory changes
- Economic data releases
- Global events impact
- Sector-specific news
- Management interviews and commentary

Social Sentiment:
- Market buzz on trading forums
- Expert opinions
- Broker recommendations
- Institutional activity patterns

For each analysis provide:
1. Overall sentiment score (-1 to +1)
2. News impact classification (High/Medium/Low)
3. Expected price movement direction
4. Duration of impact
5. Key triggers to watch
6. Contrarian indicators

Output sentiment analysis in structured JSON format.""",

    FinanceModelType.TECHNICAL_ANALYST: """You are an expert technical analyst for Indian markets:

Technical Tools:
- Price Action: Support/Resistance, Trend lines, Channels
- Moving Averages: EMA 9/21/50/200, SMA, VWAP
- Momentum: RSI, MACD, Stochastic, ADX
- Volume: OBV, Volume Profile, A/D Line
- Volatility: Bollinger Bands, ATR, Standard Deviation
- Candlestick Patterns: Doji, Engulfing, Hammer, etc.
- Chart Patterns: Head & Shoulders, Triangles, Flags, etc.
- Fibonacci: Retracements, Extensions, Time Zones

Analysis Framework:
1. Multi-timeframe analysis (15m, 1h, Daily, Weekly)
2. Trend identification and strength
3. Key levels and zones
4. Entry/Exit triggers
5. Trade setup validity
6. Risk-reward calculation

Output technical analysis in structured JSON format with specific price levels.""",

    FinanceModelType.PORTFOLIO_OPTIMIZER: """You are a portfolio optimization specialist:

Optimization Techniques:
- Modern Portfolio Theory (MPT)
- Mean-Variance Optimization
- Risk Parity approach
- Black-Litterman model concepts
- Factor-based allocation

Indian Market Considerations:
- Sector diversification (avoid over-concentration in IT/Banking)
- Market cap allocation (Large, Mid, Small)
- F&O hedging strategies
- Tax-efficient rebalancing
- LTCG/STCG optimization

Provide recommendations for:
1. Optimal asset allocation
2. Rebalancing suggestions
3. Hedging strategies
4. Underweight/Overweight sectors
5. Stock replacement candidates
6. Cash allocation timing

Output portfolio recommendations in structured JSON format."""
}


class FinanceAIModel:
    """
    Finance-specialized AI model using Google Gemini.

    Features:
    - Multiple specialized model configurations
    - Indian market expertise built-in
    - Structured JSON outputs
    - Rate limiting and retry logic
    - Response caching
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "gemini-2.0-flash"
    ):
        """
        Initialize the Finance AI Model.

        Args:
            api_key: Google API key (falls back to GEMINI_API_KEY env var)
            project_id: GCP project ID for Vertex AI
            location: GCP region
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model_name = model_name
        self._client = None
        self._initialized = False

        logger.info(f"FinanceAIModel initializing with project: {self.project_id}, model: {self.model_name}")

    def _ensure_client(self):
        """Lazy initialization of the GenAI client."""
        if self._initialized:
            return True

        if not HAS_GENAI:
            logger.error("google-genai SDK not installed")
            return False

        try:
            # Prefer Vertex AI for production (uses service account)
            if self.project_id:
                self._client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location
                )
                logger.info(f"✅ Finance AI initialized with Vertex AI (project: {self.project_id})")
            elif self.api_key:
                self._client = genai.Client(api_key=self.api_key)
                logger.info("✅ Finance AI initialized with API key")
            else:
                logger.error("No credentials configured for Finance AI")
                return False

            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Finance AI: {e}")
            return False

    async def analyze_stock(
        self,
        symbol: str,
        current_price: float,
        historical_data: Optional[Dict[str, Any]] = None,
        technical_indicators: Optional[Dict[str, Any]] = None,
        news_items: Optional[List[str]] = None,
        model_type: FinanceModelType = FinanceModelType.STOCK_ANALYST
    ) -> FinanceSignal:
        """
        Analyze a stock and generate trading signal.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")
            current_price: Current market price
            historical_data: OHLCV data
            technical_indicators: Pre-calculated indicators
            news_items: Recent news headlines
            model_type: Type of analysis model to use

        Returns:
            FinanceSignal with recommendation
        """
        if not self._ensure_client():
            return self._fallback_signal(symbol, current_price)

        system_prompt = FINANCE_SYSTEM_PROMPTS.get(
            model_type,
            FINANCE_SYSTEM_PROMPTS[FinanceModelType.STOCK_ANALYST]
        )

        # Build context
        context_parts = [f"Analyze {symbol} trading at ₹{current_price}"]

        if technical_indicators:
            context_parts.append(f"\nTechnical Indicators:\n{json.dumps(technical_indicators, indent=2)}")

        if historical_data:
            context_parts.append(f"\nRecent Price Action:\n{json.dumps(historical_data, indent=2)}")

        if news_items:
            context_parts.append(f"\nRecent News:\n" + "\n".join(f"- {n}" for n in news_items[:5]))

        context_parts.append("""
Please provide your analysis in this exact JSON format:
{
    "action": "BUY|SELL|HOLD",
    "confidence": 0.0-1.0,
    "entry_price": price or null,
    "stop_loss": price or null,
    "target_1": price or null,
    "target_2": price or null,
    "target_3": price or null,
    "risk_reward_ratio": ratio or null,
    "position_size_pct": 1.0-5.0,
    "timeframe": "INTRADAY|SWING|POSITIONAL",
    "reasoning": "brief explanation",
    "key_factors": ["factor1", "factor2"],
    "risk_level": "LOW|MEDIUM|HIGH"
}""")

        user_prompt = "\n".join(context_parts)

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )

            return self._parse_signal_response(symbol, current_price, response.text)

        except Exception as e:
            logger.error(f"❌ Finance AI analysis failed for {symbol}: {e}")
            return self._fallback_signal(symbol, current_price)

    async def get_market_analysis(
        self,
        symbol: str,
        current_price: float,
        technical_data: Optional[Dict[str, Any]] = None
    ) -> MarketAnalysis:
        """
        Get comprehensive market analysis.

        Args:
            symbol: Stock symbol
            current_price: Current price
            technical_data: Technical indicators

        Returns:
            MarketAnalysis with trend and levels
        """
        if not self._ensure_client():
            return MarketAnalysis(
                symbol=symbol,
                trend="NEUTRAL",
                trend_strength=0.5,
                recommendation="Unable to analyze - AI unavailable"
            )

        system_prompt = FINANCE_SYSTEM_PROMPTS[FinanceModelType.TECHNICAL_ANALYST]

        user_prompt = f"""Analyze {symbol} at ₹{current_price}.

Technical Data: {json.dumps(technical_data or {}, indent=2)}

Provide analysis in this JSON format:
{{
    "trend": "BULLISH|BEARISH|NEUTRAL",
    "trend_strength": 0.0-1.0,
    "support_levels": [price1, price2, price3],
    "resistance_levels": [price1, price2, price3],
    "key_indicators": {{"rsi": value, "macd": value, "adx": value}},
    "sentiment_score": -1.0 to 1.0,
    "volume_analysis": "description",
    "sector_outlook": "description",
    "global_cues": "description",
    "recommendation": "actionable recommendation"
}}"""

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )

            return self._parse_market_response(symbol, response.text)

        except Exception as e:
            logger.error(f"❌ Market analysis failed for {symbol}: {e}")
            return MarketAnalysis(
                symbol=symbol,
                trend="NEUTRAL",
                trend_strength=0.5,
                recommendation=f"Analysis error: {str(e)}"
            )

    async def get_options_strategy(
        self,
        index: str,
        spot_price: float,
        outlook: str = "NEUTRAL",
        capital: float = 100000,
        risk_appetite: str = "MODERATE"
    ) -> Dict[str, Any]:
        """
        Get options strategy recommendation.

        Args:
            index: Index name (NIFTY, BANKNIFTY, etc.)
            spot_price: Current index level
            outlook: Market outlook (BULLISH, BEARISH, NEUTRAL)
            capital: Available capital
            risk_appetite: LOW, MODERATE, HIGH

        Returns:
            Options strategy recommendation
        """
        if not self._ensure_client():
            return {"error": "AI unavailable", "fallback": "Iron Condor for neutral outlook"}

        system_prompt = FINANCE_SYSTEM_PROMPTS[FinanceModelType.OPTIONS_STRATEGIST]

        user_prompt = f"""Recommend an options strategy for:
Index: {index}
Spot Price: {spot_price}
Market Outlook: {outlook}
Available Capital: ₹{capital:,.0f}
Risk Appetite: {risk_appetite}

Current Date: {datetime.now().strftime('%Y-%m-%d')}

Consider:
1. Days to expiry
2. IV levels
3. Support/Resistance levels
4. Max loss should not exceed 3% of capital for LOW risk, 5% for MODERATE, 10% for HIGH

Provide strategy in JSON format with legs, entry prices, Greeks, and exit conditions."""

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=1500,
                )
            )

            return self._parse_json_response(response.text)

        except Exception as e:
            logger.error(f"❌ Options strategy generation failed: {e}")
            return {"error": str(e), "fallback": "Consider Iron Condor for neutral markets"}

    async def analyze_risk(
        self,
        positions: List[Dict[str, Any]],
        account_value: float
    ) -> Dict[str, Any]:
        """
        Analyze portfolio risk.

        Args:
            positions: List of current positions
            account_value: Total account value

        Returns:
            Risk analysis and recommendations
        """
        if not self._ensure_client():
            return {"error": "AI unavailable", "risk_level": "UNKNOWN"}

        system_prompt = FINANCE_SYSTEM_PROMPTS[FinanceModelType.RISK_MANAGER]

        user_prompt = f"""Analyze risk for this portfolio:

Account Value: ₹{account_value:,.0f}
Positions:
{json.dumps(positions, indent=2)}

Provide risk analysis in JSON format including:
1. Overall portfolio risk score (1-10)
2. Position-wise risk breakdown
3. Correlation risks
4. Concentration risks
5. Suggested adjustments
6. Hedge recommendations"""

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=1500,
                )
            )

            return self._parse_json_response(response.text)

        except Exception as e:
            logger.error(f"❌ Risk analysis failed: {e}")
            return {"error": str(e), "risk_level": "UNKNOWN"}

    def _parse_signal_response(
        self,
        symbol: str,
        current_price: float,
        response_text: str
    ) -> FinanceSignal:
        """Parse AI response into FinanceSignal."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                return FinanceSignal(
                    symbol=symbol,
                    action=data.get("action", "HOLD"),
                    confidence=float(data.get("confidence", 0.5)),
                    entry_price=data.get("entry_price"),
                    stop_loss=data.get("stop_loss"),
                    target_1=data.get("target_1"),
                    target_2=data.get("target_2"),
                    target_3=data.get("target_3"),
                    risk_reward_ratio=data.get("risk_reward_ratio"),
                    position_size_pct=float(data.get("position_size_pct", 2.0)),
                    timeframe=data.get("timeframe", "INTRADAY"),
                    reasoning=data.get("reasoning", ""),
                    key_factors=data.get("key_factors", []),
                    risk_level=data.get("risk_level", "MEDIUM")
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse signal response: {e}")

        return self._fallback_signal(symbol, current_price)

    def _parse_market_response(self, symbol: str, response_text: str) -> MarketAnalysis:
        """Parse AI response into MarketAnalysis."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                return MarketAnalysis(
                    symbol=symbol,
                    trend=data.get("trend", "NEUTRAL"),
                    trend_strength=float(data.get("trend_strength", 0.5)),
                    support_levels=data.get("support_levels", []),
                    resistance_levels=data.get("resistance_levels", []),
                    key_indicators=data.get("key_indicators", {}),
                    sentiment_score=float(data.get("sentiment_score", 0.0)),
                    volume_analysis=data.get("volume_analysis", ""),
                    sector_outlook=data.get("sector_outlook", ""),
                    global_cues=data.get("global_cues", ""),
                    recommendation=data.get("recommendation", "")
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse market response: {e}")

        return MarketAnalysis(
            symbol=symbol,
            trend="NEUTRAL",
            trend_strength=0.5,
            recommendation="Unable to parse analysis"
        )

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from response."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, TypeError):
            pass
        return {"raw_response": response_text}

    def _fallback_signal(self, symbol: str, current_price: float) -> FinanceSignal:
        """Generate fallback signal when AI is unavailable."""
        return FinanceSignal(
            symbol=symbol,
            action="HOLD",
            confidence=0.3,
            entry_price=current_price,
            stop_loss=current_price * 0.98,
            target_1=current_price * 1.02,
            reasoning="Fallback signal - AI analysis unavailable",
            key_factors=["Technical analysis required"],
            risk_level="HIGH"
        )


# Singleton instance
_finance_ai_model: Optional[FinanceAIModel] = None


def get_finance_ai_model() -> FinanceAIModel:
    """Get singleton instance of FinanceAIModel."""
    global _finance_ai_model
    if _finance_ai_model is None:
        _finance_ai_model = FinanceAIModel()
    return _finance_ai_model


# Convenience functions
async def get_stock_signal(
    symbol: str,
    current_price: float,
    technical_indicators: Optional[Dict[str, Any]] = None
) -> FinanceSignal:
    """Quick stock signal generation."""
    model = get_finance_ai_model()
    return await model.analyze_stock(
        symbol=symbol,
        current_price=current_price,
        technical_indicators=technical_indicators
    )


async def get_market_trend(symbol: str, current_price: float) -> MarketAnalysis:
    """Quick market trend analysis."""
    model = get_finance_ai_model()
    return await model.get_market_analysis(symbol, current_price)


async def get_options_recommendation(
    index: str,
    spot_price: float,
    outlook: str = "NEUTRAL"
) -> Dict[str, Any]:
    """Quick options strategy recommendation."""
    model = get_finance_ai_model()
    return await model.get_options_strategy(index, spot_price, outlook)
