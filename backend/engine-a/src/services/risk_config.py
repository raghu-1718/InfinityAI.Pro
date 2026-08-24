"""
InfinityAI.Pro — Dynamic Risk Configuration & State Schemas
============================================================
Pydantic v2 schemas enforcing strict type safety for multi-regime risk layers,
live telemetry payloads, and cross-worker position state management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class RiskRegimeThresholds(BaseModel):
    """Immutable baseline constraints for multi-regime dynamic risk layers."""
    min_alpha_confidence_threshold: float = Field(default=0.48, ge=0.0, le=1.0)
    max_order_book_imbalance_limit: float = Field(default=-0.70, ge=-1.0, le=1.0)
    absolute_emergency_floor_pct: float = Field(default=0.15, ge=0.05, le=0.30)
    cool_down_duration_minutes: int = Field(default=45, ge=5, le=120)
    consecutive_loss_limit: int = Field(default=3, ge=2, le=10)

class LiveMarketState(BaseModel):
    """Real-time data telemetry payload fetched from DhanHQ, Pub/Sub, and Vertex AI pipelines."""
    timestamp: datetime
    current_premium: float = Field(..., gt=0.0)
    entry_premium: float = Field(..., gt=0.0)
    ml_confidence: float = Field(..., ge=0.0, le=1.0)
    order_book_imbalance: float = Field(default=0.0, ge=-1.0, le=1.0)  # (Bid Qty - Ask Qty) / Total Qty
    live_greeks: Dict[str, float] = Field(default_factory=lambda: {"IV": 0.1717, "Gamma": 0.00084, "Delta": 0.54, "Theta": -45.26})
    spot_price: Optional[float] = None
    symbol: Optional[str] = "NIFTY"

class PositionState(BaseModel):
    """Maintains active internal state metrics for the institutional state machine."""
    position_id: str
    is_active: bool = False
    consecutive_losses: int = 0
    last_exit_timestamp: Optional[datetime] = None
    cool_down_active: bool = False
    highest_observed_premium: Optional[float] = None
    entry_timestamp: Optional[datetime] = None
