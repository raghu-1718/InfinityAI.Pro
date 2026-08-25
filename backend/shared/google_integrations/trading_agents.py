"""
InfinityAI.Pro - ADK-Inspired Trading Agents
=============================================
Agent-based architecture for trading signal generation.
Inspired by Google ADK (Agent Development Kit) patterns.

Based on: https://github.com/google/adk-go (patterns adapted for Python)
"""

import os
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger("InfinityAI.Agents")


class AgentCapability(Enum):
    """Capabilities that agents can have."""
    SIGNAL_GENERATION = "signal_generation"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_ANALYSIS = "market_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    ORDER_EXECUTION = "order_execution"
    TECHNICAL_ANALYSIS = "technical_analysis"


class AgentStatus(Enum):
    """Agent operational status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class AgentContext:
    """Context passed between agents during execution."""
    session_id: str
    user_id: Optional[str] = None
    symbol: Optional[str] = None
    market: str = "NSE"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def add_to_history(self, event_type: str, data: Dict[str, Any]):
        """Add an event to context history."""
        self.history.append({
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    agent_name: str
    capability: AgentCapability
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    """
    Base class for all trading agents.
    Implements ADK-style agent patterns.
    """

    def __init__(
        self,
        name: str,
        capabilities: List[AgentCapability],
        description: str = ""
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name
            capabilities: List of agent capabilities
            description: Agent description
        """
        self.name = name
        self.capabilities = capabilities
        self.description = description
        self.status = AgentStatus.IDLE
        self._tools: Dict[str, Callable] = {}

        logger.info(f"🤖 Agent initialized: {name} with capabilities {[c.value for c in capabilities]}")

    def register_tool(self, name: str, tool: Callable):
        """
        Register a tool for the agent to use.

        Args:
            name: Tool name
            tool: Tool function
        """
        self._tools[name] = tool
        logger.debug(f"Tool registered: {name}")

    async def use_tool(self, name: str, **kwargs) -> Any:
        """
        Use a registered tool.

        Args:
            name: Tool name
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")

        tool = self._tools[name]
        if asyncio.iscoroutinefunction(tool):
            return await tool(**kwargs)
        return tool(**kwargs)

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent's main task.

        Args:
            context: Execution context

        Returns:
            Agent result
        """
        pass

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute agent with timing and error handling.

        Args:
            context: Execution context

        Returns:
            Agent result
        """
        import time
        start_time = time.perf_counter()

        self.status = AgentStatus.RUNNING

        try:
            result = await self.run(context)
            result.execution_time_ms = (time.perf_counter() - start_time) * 1000
            self.status = AgentStatus.COMPLETED

            context.add_to_history(f"{self.name}_completed", {
                "result": result.data,
                "execution_time_ms": result.execution_time_ms
            })

            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            execution_time = (time.perf_counter() - start_time) * 1000

            logger.error(f"❌ Agent {self.name} failed: {e}")

            return AgentResult(
                success=False,
                agent_name=self.name,
                capability=self.capabilities[0] if self.capabilities else AgentCapability.SIGNAL_GENERATION,
                data={},
                error=str(e),
                execution_time_ms=execution_time
            )


class TradingSignalAgent(BaseAgent):
    """
    Agent for generating trading signals.
    Combines multiple data sources and ML models.
    """

    def __init__(self, genai_client=None, ml_models: Optional[Dict] = None):
        """
        Initialize trading signal agent.

        Args:
            genai_client: GenAI client for AI-powered analysis
            ml_models: Dictionary of ML models to use
        """
        super().__init__(
            name="TradingSignalAgent",
            capabilities=[
                AgentCapability.SIGNAL_GENERATION,
                AgentCapability.TECHNICAL_ANALYSIS
            ],
            description="Generates trading signals using ML and AI analysis"
        )
        self.genai_client = genai_client
        self.ml_models = ml_models or {}

    async def run(self, context: AgentContext) -> AgentResult:
        """Generate trading signal for the given context."""
        symbol = context.symbol
        if not symbol:
            return AgentResult(
                success=False,
                agent_name=self.name,
                capability=AgentCapability.SIGNAL_GENERATION,
                data={},
                error="Symbol is required"
            )

        # Collect signals from various sources
        signals = []

        # 1. Technical Analysis Signal
        if "technical_data" in context.data:
            tech_signal = self._analyze_technical(context.data["technical_data"])
            signals.append(("technical", tech_signal))

        # 2. ML Model Predictions
        for model_name, model in self.ml_models.items():
            if "features" in context.data:
                try:
                    prediction = await self._get_ml_prediction(model, context.data["features"])
                    signals.append((f"ml_{model_name}", prediction))
                except Exception as e:
                    logger.warning(f"ML prediction failed for {model_name}: {e}")

        # 3. AI Analysis (if GenAI client available)
        if self.genai_client:
            try:
                from .genai_client import TradingPrompt
                prompt = TradingPrompt(
                    symbol=symbol,
                    market=context.market,
                    context=context.data.get("market_context", {})
                )
                ai_analysis = await self.genai_client.generate_trading_signal(prompt)
                signals.append(("ai", {
                    "signal": ai_analysis.signal,
                    "confidence": ai_analysis.confidence / 100,
                    "reasoning": ai_analysis.reasoning
                }))
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")

        # Combine signals using weighted voting
        final_signal = self._combine_signals(signals)

        return AgentResult(
            success=True,
            agent_name=self.name,
            capability=AgentCapability.SIGNAL_GENERATION,
            data={
                "symbol": symbol,
                "signal": final_signal["signal"],
                "confidence": final_signal["confidence"],
                "components": signals,
                "entry_price": final_signal.get("entry_price"),
                "stop_loss": final_signal.get("stop_loss"),
                "target_price": final_signal.get("target_price")
            }
        )

    def _analyze_technical(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical indicators."""
        rsi = data.get("rsi", 50)
        macd = data.get("macd", 0)
        macd_signal = data.get("macd_signal", 0)

        signal = "HOLD"
        confidence = 0.5

        # RSI-based signal
        if rsi < 30:
            signal = "BUY"
            confidence = 0.7
        elif rsi > 70:
            signal = "SELL"
            confidence = 0.7

        # MACD confirmation
        if macd > macd_signal and signal == "BUY":
            confidence += 0.1
        elif macd < macd_signal and signal == "SELL":
            confidence += 0.1

        return {
            "signal": signal,
            "confidence": min(confidence, 1.0),
            "indicators": {"rsi": rsi, "macd": macd}
        }

    async def _get_ml_prediction(self, model: Any, features: Any) -> Dict[str, Any]:
        """Get prediction from ML model."""
        import numpy as np

        prediction = model.predict(np.array([features]))[0]

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(np.array([features]))[0]
            confidence = max(probabilities)
        else:
            confidence = 0.6

        signal = "BUY" if prediction == 1 else "SELL" if prediction == -1 else "HOLD"

        return {
            "signal": signal,
            "confidence": confidence
        }

    def _combine_signals(self, signals: List[tuple]) -> Dict[str, Any]:
        """Combine signals using weighted voting."""
        weights = {
            "technical": 0.3,
            "ml_xgboost": 0.3,
            "ml_lightgbm": 0.2,
            "ai": 0.2
        }

        if not signals:
            return {"signal": "HOLD", "confidence": 0.0}

        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0

        for source, signal_data in signals:
            weight = weights.get(source, 0.1)
            confidence = signal_data.get("confidence", 0.5)
            signal = signal_data.get("signal", "HOLD")

            if signal == "BUY":
                buy_score += weight * confidence
            elif signal == "SELL":
                sell_score += weight * confidence

            total_weight += weight

        if total_weight == 0:
            return {"signal": "HOLD", "confidence": 0.0}

        buy_score /= total_weight
        sell_score /= total_weight

        if buy_score > sell_score and buy_score > 0.5:
            return {"signal": "BUY", "confidence": buy_score}
        elif sell_score > buy_score and sell_score > 0.5:
            return {"signal": "SELL", "confidence": sell_score}
        else:
            return {"signal": "HOLD", "confidence": 1 - abs(buy_score - sell_score)}


class RiskAssessmentAgent(BaseAgent):
    """
    Agent for assessing trade and portfolio risk.
    Implements SEBI 2025 compliance checks.
    """

    def __init__(self, max_position_pct: float = 5.0, max_drawdown_pct: float = 3.0):
        """
        Initialize risk assessment agent.

        Args:
            max_position_pct: Maximum position size as % of portfolio
            max_drawdown_pct: Maximum allowed drawdown %
        """
        super().__init__(
            name="RiskAssessmentAgent",
            capabilities=[AgentCapability.RISK_ASSESSMENT],
            description="Assesses risk for trades and portfolios with SEBI compliance"
        )
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct

    async def run(self, context: AgentContext) -> AgentResult:
        """Assess risk for the given context."""
        trade_data = context.data.get("trade", {})
        portfolio_data = context.data.get("portfolio", {})

        # Calculate risk metrics
        position_size = trade_data.get("quantity", 0) * trade_data.get("price", 0)
        portfolio_value = portfolio_data.get("total_value", 100000)

        position_pct = (position_size / portfolio_value) * 100

        # Risk scoring
        risk_score = 0
        warnings = []

        # Position size check
        if position_pct > self.max_position_pct:
            risk_score += 30
            warnings.append(f"Position exceeds {self.max_position_pct}% of portfolio")

        # Volatility check
        volatility = trade_data.get("volatility", 2.0)
        if volatility > 3.0:
            risk_score += 20
            warnings.append("High volatility detected")

        # Stop loss check
        if not trade_data.get("stop_loss"):
            risk_score += 20
            warnings.append("No stop loss defined")

        # Drawdown check
        current_drawdown = portfolio_data.get("current_drawdown", 0)
        if current_drawdown > self.max_drawdown_pct:
            risk_score += 30
            warnings.append(f"Portfolio drawdown exceeds {self.max_drawdown_pct}%")

        # Determine risk level
        if risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # SEBI compliance
        sebi_compliant = risk_score < 60 and position_pct <= 10

        return AgentResult(
            success=True,
            agent_name=self.name,
            capability=AgentCapability.RISK_ASSESSMENT,
            data={
                "risk_score": risk_score,
                "risk_level": risk_level,
                "position_pct": position_pct,
                "warnings": warnings,
                "sebi_compliant": sebi_compliant,
                "recommended_position_size": min(
                    position_size,
                    portfolio_value * (self.max_position_pct / 100)
                ),
                "max_loss": position_size * (trade_data.get("stop_loss_pct", 2) / 100)
            }
        )


class MarketAnalysisAgent(BaseAgent):
    """
    Agent for analyzing market conditions.
    Provides macro and micro market insights.
    """

    def __init__(self, genai_client=None, ml_models: Optional[Dict] = None):
        """Initialize market analysis agent."""
        super().__init__(
            name="MarketAnalysisAgent",
            capabilities=[
                AgentCapability.MARKET_ANALYSIS,
                AgentCapability.SENTIMENT_ANALYSIS
            ],
            description="Analyzes market conditions and sentiment"
        )
        self.genai_client = genai_client
        self.ml_models = ml_models or {}

    async def run(self, context: AgentContext) -> AgentResult:
        """Analyze market conditions."""
        market_data = context.data.get("market", {})

        # Analyze market regime
        nifty_change = market_data.get("nifty_change_pct", 0)
        vix = market_data.get("india_vix", 15)
        fii_activity = market_data.get("fii_net", 0)
        dii_activity = market_data.get("dii_net", 0)

        # Market regime detection
        if vix > 25:
            regime = "HIGH_VOLATILITY"
        elif vix < 12:
            regime = "LOW_VOLATILITY"
        elif nifty_change > 1:
            regime = "BULLISH"
        elif nifty_change < -1:
            regime = "BEARISH"
        else:
            regime = "NEUTRAL"

        # Sentiment based on FII/DII
        if fii_activity > 0 and dii_activity > 0:
            sentiment = "BULLISH"
        elif fii_activity < 0 and dii_activity < 0:
            sentiment = "BEARISH"
        else:
            sentiment = "MIXED"

        # Trading recommendations
        recommendations = []

        if regime == "HIGH_VOLATILITY":
            recommendations.append("Reduce position sizes due to high volatility")
            recommendations.append("Consider hedging with options")

        if sentiment == "BEARISH":
            recommendations.append("Focus on defensive sectors")
            recommendations.append("Consider short-term trades only")

        return AgentResult(
            success=True,
            agent_name=self.name,
            capability=AgentCapability.MARKET_ANALYSIS,
            data={
                "regime": regime,
                "sentiment": sentiment,
                "vix": vix,
                "fii_activity": fii_activity,
                "dii_activity": dii_activity,
                "recommendations": recommendations,
                "is_favorable": regime not in ["HIGH_VOLATILITY"] and sentiment != "BEARISH"
            }
        )


class AgentOrchestrator:
    """
    Orchestrates multiple agents for complex trading workflows.
    Implements ADK-style multi-agent coordination.
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, List[str]] = {}

        logger.info("🎭 Agent Orchestrator initialized")

    def register_agent(self, agent: BaseAgent):
        """
        Register an agent.

        Args:
            agent: Agent to register
        """
        self.agents[agent.name] = agent
        logger.info(f"Agent registered: {agent.name}")

    def define_workflow(self, name: str, agent_sequence: List[str]):
        """
        Define a workflow as a sequence of agents.

        Args:
            name: Workflow name
            agent_sequence: List of agent names in execution order
        """
        self.workflows[name] = agent_sequence
        logger.info(f"Workflow defined: {name} -> {agent_sequence}")

    async def execute_workflow(
        self,
        workflow_name: str,
        context: AgentContext
    ) -> List[AgentResult]:
        """
        Execute a defined workflow.

        Args:
            workflow_name: Name of the workflow
            context: Initial context

        Returns:
            List of results from each agent
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_name}")

        results = []

        for agent_name in self.workflows[workflow_name]:
            if agent_name not in self.agents:
                logger.warning(f"Agent not found: {agent_name}")
                continue

            agent = self.agents[agent_name]
            result = await agent.execute(context)
            results.append(result)

            # Add result to context for next agent
            context.data[f"{agent_name}_result"] = result.data

            # Stop workflow on failure if needed
            if not result.success:
                logger.warning(f"Workflow stopped due to agent failure: {agent_name}")
                break

        return results

    async def run_parallel(
        self,
        agent_names: List[str],
        context: AgentContext
    ) -> List[AgentResult]:
        """
        Run multiple agents in parallel.

        Args:
            agent_names: List of agent names to run
            context: Shared context

        Returns:
            List of results
        """
        tasks = []

        for name in agent_names:
            if name in self.agents:
                tasks.append(self.agents[name].execute(context))

        return await asyncio.gather(*tasks)


# Pre-configured workflow for trading signal generation
def create_trading_workflow(
    genai_client=None,
    ml_models: Optional[Dict] = None
) -> AgentOrchestrator:
    """
    Create a pre-configured trading workflow.

    Args:
        genai_client: GenAI client for AI analysis
        ml_models: ML models for signal generation

    Returns:
        Configured orchestrator with trading workflow
    """
    orchestrator = AgentOrchestrator()

    # Register agents
    orchestrator.register_agent(MarketAnalysisAgent())
    orchestrator.register_agent(TradingSignalAgent(genai_client, ml_models))
    orchestrator.register_agent(RiskAssessmentAgent())

    # Define trading workflow
    orchestrator.define_workflow(
        "generate_signal",
        ["MarketAnalysisAgent", "TradingSignalAgent", "RiskAssessmentAgent"]
    )

    return orchestrator
