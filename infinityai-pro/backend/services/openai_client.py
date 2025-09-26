# openai_client.py
import openai
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TradeStrategy:
    """AI-generated trading strategy"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    risk_level: str  # low, medium, high
    position_size: float  # percentage of capital
    stop_loss: float
    take_profit: float
    time_horizon: str  # short, medium, long
    market_context: str

@dataclass
class RiskAssessment:
    """Risk assessment for portfolio/trade"""
    overall_risk: str
    risk_factors: List[str]
    mitigation_strategies: List[str]
    portfolio_diversification: str
    market_volatility: str
    liquidity_assessment: str

@dataclass
class PortfolioInsights:
    """Portfolio analysis and recommendations"""
    performance_summary: str
    key_strengths: List[str]
    areas_for_improvement: List[str]
    rebalancing_suggestions: List[str]
    risk_adjustments: List[str]

class OpenAIClient:
    """OpenAI API client for trading strategy narration and risk analysis"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

        # System prompts for different use cases
        self.system_prompts = {
            "strategy_narration": """You are an expert quantitative trading strategist. Analyze trading signals and market data to provide clear, actionable trading strategies.
            Focus on risk management, position sizing, and market timing. Provide specific entry/exit points and reasoning.""",

            "risk_analysis": """You are a professional risk manager specializing in algorithmic trading. Assess portfolio risk, identify potential vulnerabilities,
            and recommend risk mitigation strategies. Consider market volatility, correlation, and liquidity factors.""",

            "portfolio_insights": """You are a portfolio manager and financial analyst. Provide insights on portfolio performance, diversification,
            and optimization opportunities. Give actionable recommendations for improvement.""",

            "market_context": """You are a market analyst providing context and interpretation of quantitative signals.
            Explain market conditions, sentiment, and how they influence trading decisions."""
        }

    async def generate_trade_strategy(self, signal_data: Dict, market_context: Dict = None) -> Optional[TradeStrategy]:
        """Generate a narrated trading strategy from signal data"""
        try:
            prompt = self._build_strategy_prompt(signal_data, market_context)

            response = await self._call_openai_api(prompt, "strategy_narration")

            if response:
                strategy_data = self._parse_strategy_response(response, signal_data.get('symbol', 'UNKNOWN'))
                return strategy_data

            return None

        except Exception as e:
            logger.error(f"Error generating trade strategy: {e}")
            return None

    async def assess_portfolio_risk(self, portfolio_data: Dict, market_conditions: Dict = None) -> Optional[RiskAssessment]:
        """Assess portfolio risk and provide mitigation strategies"""
        try:
            prompt = self._build_risk_prompt(portfolio_data, market_conditions)

            response = await self._call_openai_api(prompt, "risk_analysis")

            if response:
                risk_data = self._parse_risk_response(response)
                return risk_data

            return None

        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return None

    async def generate_portfolio_insights(self, portfolio_data: Dict, performance_data: Dict = None) -> Optional[PortfolioInsights]:
        """Generate portfolio insights and recommendations"""
        try:
            prompt = self._build_portfolio_prompt(portfolio_data, performance_data)

            response = await self._call_openai_api(prompt, "portfolio_insights")

            if response:
                insights_data = self._parse_portfolio_response(response)
                return insights_data

            return None

        except Exception as e:
            logger.error(f"Error generating portfolio insights: {e}")
            return None

    async def narrate_market_context(self, market_data: Dict, news_sentiment: Dict = None) -> str:
        """Provide narrative context for market conditions"""
        try:
            prompt = self._build_market_context_prompt(market_data, news_sentiment)

            response = await self._call_openai_api(prompt, "market_context")

            return response if response else "Market context analysis unavailable."

        except Exception as e:
            logger.error(f"Error narrating market context: {e}")
            return "Error analyzing market context."

    async def _call_openai_api(self, prompt: str, prompt_type: str) -> Optional[str]:
        """Make API call to OpenAI"""
        try:
            system_prompt = self.system_prompts.get(prompt_type, "")

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # Balanced creativity and consistency
                    max_tokens=1000
                )
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _build_strategy_prompt(self, signal_data: Dict, market_context: Dict = None) -> str:
        """Build prompt for strategy generation"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        action = signal_data.get('direction', 'HOLD')
        score = signal_data.get('score', 0.0)
        ml_prob = signal_data.get('ml_prob', 0.0)
        rule_score = signal_data.get('rule_score', 0.0)

        prompt = f"""
        Analyze this trading signal and provide a detailed trading strategy:

        Signal Details:
        - Symbol: {symbol}
        - Recommended Action: {action}
        - Total Score: {score:.3f}
        - ML Probability: {ml_prob:.3f}
        - Rule-based Score: {rule_score:.3f}

        Market Context:
        {json.dumps(market_context, indent=2) if market_context else "No additional market context provided"}

        Please provide:
        1. Strategy rationale and confidence level
        2. Recommended position size (as % of capital)
        3. Entry price considerations
        4. Stop loss and take profit levels
        5. Time horizon for the trade
        6. Key risk factors to monitor
        7. Alternative scenarios to consider

        Format your response as a structured trading plan.
        """

        return prompt

    def _build_risk_prompt(self, portfolio_data: Dict, market_conditions: Dict = None) -> str:
        """Build prompt for risk assessment"""
        prompt = f"""
        Assess the risk profile of this trading portfolio:

        Portfolio Data:
        {json.dumps(portfolio_data, indent=2)}

        Market Conditions:
        {json.dumps(market_conditions, indent=2) if market_conditions else "Standard market conditions"}

        Please analyze:
        1. Overall portfolio risk level
        2. Key risk factors and concentrations
        3. Correlation and diversification assessment
        4. Liquidity and volatility considerations
        5. Specific mitigation strategies
        6. Recommended risk limits and adjustments

        Provide actionable risk management recommendations.
        """

        return prompt

    def _build_portfolio_prompt(self, portfolio_data: Dict, performance_data: Dict = None) -> str:
        """Build prompt for portfolio insights"""
        prompt = f"""
        Analyze this trading portfolio and provide insights:

        Current Portfolio:
        {json.dumps(portfolio_data, indent=2)}

        Performance Data:
        {json.dumps(performance_data, indent=2) if performance_data else "No performance data available"}

        Please provide:
        1. Portfolio performance summary
        2. Key strengths and competitive advantages
        3. Areas for improvement
        4. Rebalancing recommendations
        5. Risk management adjustments
        6. Long-term strategic suggestions

        Focus on actionable insights for portfolio optimization.
        """

        return prompt

    def _build_market_context_prompt(self, market_data: Dict, news_sentiment: Dict = None) -> str:
        """Build prompt for market context narration"""
        prompt = f"""
        Provide market context and analysis for these conditions:

        Market Data:
        {json.dumps(market_data, indent=2)}

        News & Sentiment:
        {json.dumps(news_sentiment, indent=2) if news_sentiment else "No news sentiment data"}

        Please explain:
        1. Current market environment and key drivers
        2. How these conditions affect trading strategies
        3. Notable trends or patterns
        4. Potential opportunities or risks
        5. Recommended trading approach given current context

        Provide clear, actionable market intelligence.
        """

        return prompt

    def _parse_strategy_response(self, response: str, symbol: str) -> TradeStrategy:
        """Parse strategy response into structured data"""
        # Simple parsing - in production, use more sophisticated NLP
        lines = response.split('\n')

        # Default values
        action = "HOLD"
        confidence = 0.5
        reasoning = response
        risk_level = "medium"
        position_size = 0.02  # 2% default
        stop_loss = 0.03
        take_profit = 0.06
        time_horizon = "medium"

        # Extract key information
        for line in lines:
            line_lower = line.lower()
            if 'buy' in line_lower and 'sell' not in line_lower:
                action = "BUY"
            elif 'sell' in line_lower:
                action = "SELL"

            if 'confidence' in line_lower or 'certain' in line_lower:
                if any(word in line_lower for word in ['high', 'strong', 'very']):
                    confidence = 0.8
                elif any(word in line_lower for word in ['low', 'weak']):
                    confidence = 0.3

            if 'position size' in line_lower or 'allocation' in line_lower:
                # Extract percentage
                import re
                percent_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                if percent_match:
                    position_size = float(percent_match.group(1)) / 100

            if 'stop loss' in line_lower:
                # Extract stop loss percentage
                import re
                sl_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                if sl_match:
                    stop_loss = float(sl_match.group(1)) / 100

        return TradeStrategy(
            symbol=symbol,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            risk_level=risk_level,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            time_horizon=time_horizon,
            market_context="Analyzed via OpenAI"
        )

    def _parse_risk_response(self, response: str) -> RiskAssessment:
        """Parse risk assessment response"""
        # Simplified parsing
        risk_factors = []
        mitigation_strategies = []

        lines = response.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['risk', 'concern', 'vulnerable']):
                risk_factors.append(line.strip())
            elif any(word in line.lower() for word in ['mitigate', 'reduce', 'hedge', 'diversify']):
                mitigation_strategies.append(line.strip())

        return RiskAssessment(
            overall_risk="medium",  # Would be determined by analysis
            risk_factors=risk_factors[:5],
            mitigation_strategies=mitigation_strategies[:5],
            portfolio_diversification="moderate",  # Would analyze
            market_volatility="normal",  # Would assess
            liquidity_assessment="adequate"  # Would evaluate
        )

    def _parse_portfolio_response(self, response: str) -> PortfolioInsights:
        """Parse portfolio insights response"""
        # Simplified parsing
        strengths = []
        improvements = []
        suggestions = []

        lines = response.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['strength', 'good', 'strong', 'advantage']):
                strengths.append(line.strip())
            elif any(word in line_lower for word in ['improve', 'weak', 'concern', 'better']):
                improvements.append(line.strip())
            elif any(word in line_lower for word in ['recommend', 'suggest', 'consider']):
                suggestions.append(line.strip())

        return PortfolioInsights(
            performance_summary="Portfolio analysis completed",
            key_strengths=strengths[:3],
            areas_for_improvement=improvements[:3],
            rebalancing_suggestions=suggestions[:3],
            risk_adjustments=["Monitor volatility", "Consider diversification"]
        )