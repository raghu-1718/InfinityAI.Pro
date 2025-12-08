# =====================================================================
# InfinityAI.Pro - Google Cloud Integrations
# =====================================================================
# This package provides unified Google Cloud service integrations:
# - GenAI SDK for Gemini model access (Gemini 3 Pro, 2.5 Flash, etc.)
# - Cloud Logging for structured trade signal logging
# - Cloud Storage for ML model and trading history persistence
# - ADK-inspired agent architecture for trading signals
#
# Available Credits: ₹89,272 Gen App Builder + ₹26,781 Trial = ₹1,16,054
# =====================================================================

from .genai_client import GenAIClient, TradingAnalysisAgent, GeminiModel, ModelTier, DEFAULT_MODELS
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
    "GeminiModel",
    "ModelTier",
    "DEFAULT_MODELS",
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
