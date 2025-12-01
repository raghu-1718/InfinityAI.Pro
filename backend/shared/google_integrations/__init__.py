# =====================================================================
# InfinityAI.Pro - Google Cloud Integrations
# =====================================================================
# This package provides unified Google Cloud service integrations:
# - GenAI SDK for Gemini model access
# - Cloud Logging for structured trade signal logging
# - Cloud Storage for ML model and trading history persistence
# - ADK-inspired agent architecture for trading signals
# =====================================================================

from .genai_client import GenAIClient, TradingAnalysisAgent, TradingPrompt, TradingAnalysis
from .cloud_logging import TradingLogger, LogLevel, TradingEventType
from .cloud_storage import ModelStorage, TradingHistoryStorage
from .trading_agents import (
    TradingSignalAgent,
    RiskAssessmentAgent,
    MarketAnalysisAgent,
    AgentOrchestrator,
    create_trading_workflow
)

__all__ = [
    # GenAI
    "GenAIClient",
    "TradingAnalysisAgent",
    "TradingPrompt",
    "TradingAnalysis",
    # Logging
    "TradingLogger",
    "LogLevel",
    "TradingEventType",
    # Storage
    "ModelStorage",
    "TradingHistoryStorage",
    # Agents
    "TradingSignalAgent",
    "RiskAssessmentAgent",
    "MarketAnalysisAgent",
    "AgentOrchestrator",
    "create_trading_workflow",
]
