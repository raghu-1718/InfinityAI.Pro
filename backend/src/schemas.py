"""
Pydantic v2 schemas for InfinityAI.Pro Backend API
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class OptionType(str, Enum):
    CE = "CE"
    PE = "PE"
    FUT = "FUT"
    EQ = "EQ"


class CorrelationIdHeader(BaseModel):
    """Enforces max 30-character alphanumeric correlation ID for idempotency."""
    correlation_id: str = Field(..., max_length=30, description="Idempotency tracking ID (max 30 chars)")


class MarketTickRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading instrument ticker")
    price: float = Field(..., gt=0, description="Last traded price (must be positive)")
    volume: int = Field(..., ge=0, description="Cumulative volume")
    strike_price: Optional[float] = Field(None, description="Option strike price")
    option_type: Optional[OptionType] = Field(None, description="CE, PE, or FUT")
    open_interest: Optional[int] = Field(None, ge=0, description="Open interest")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Tick ISO timestamp")


class MarketTickResponse(BaseModel):
    tick_id: str
    status: str = "ingested"
    correlation_id: Optional[str] = None
    symbol: str
    price: float
    volume: int
    timestamp: datetime


class ModelInferenceRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Map of technical/market features")
    models: List[str] = Field(default=["catboost", "lightgbm", "xgboost"], description="Models to run")
    ensemble_weights: Optional[Dict[str, float]] = Field(None, description="Optional custom weights")

    @field_validator("features")
    @classmethod
    def validate_features_not_empty(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise ValueError("Features map must not be empty.")
        return v

    @field_validator("ensemble_weights")
    @classmethod
    def validate_weights(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is not None:
            total = sum(v.values())
            if not (0.95 <= total <= 1.05):
                raise ValueError(f"Ensemble weights must sum to approximately 1.0 (got {total:.3f})")
        return v


class ModelInferenceResponse(BaseModel):
    predictions: Dict[str, float]
    consensus_signal: str  # BULLISH, BEARISH, NEUTRAL
    consensus_score: float
    confidence: float
    latency_ms: float
    correlation_id: Optional[str] = None


class BacktestRunRequest(BaseModel):
    strategy: str = Field(..., min_length=1, description="Strategy name or identifier")
    symbol: str = Field(..., min_length=1, description="Target instrument")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(..., gt=0, description="Initial capital in INR")
    slippage_pct: float = Field(default=0.0005, ge=0, description="Execution slippage (0.05%)")
    include_sebi_taxes: bool = Field(default=True, description="Include SEBI 2026 statutory taxes")

    @model_validator(mode="after")
    def validate_date_range(self) -> "BacktestRunRequest":
        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            if end < start:
                raise ValueError("end_date must be on or after start_date")
        except ValueError as e:
            if "end_date must be on or after" in str(e):
                raise
            raise ValueError(f"Invalid date format: {e}")
        return self


class BacktestMetrics(BaseModel):
    sharpe_ratio: float
    deflated_sharpe_ratio: float
    probabilistic_sharpe_ratio: float
    max_drawdown: float
    total_pnl: float
    total_return_pct: float
    win_rate: float
    total_trades: int


class BacktestRunResponse(BaseModel):
    run_id: str
    strategy: str
    symbol: str
    status: str  # running, completed, failed
    metrics: Optional[BacktestMetrics] = None
    execution_time_sec: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PortfolioPosition(BaseModel):
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    pnl: float
    pnl_pct: float


class PortfolioStateResponse(BaseModel):
    total_equity: float
    cash_balance: float
    margin_used: float
    dynamic_var_99: float
    unrealized_pnl: float
    realized_pnl: float
    positions: List[PortfolioPosition] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OrderRequest(BaseModel):
    symbol: str
    action: str  # BUY or SELL
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    order_type: str = "LIMIT"
    correlation_id: Optional[str] = Field(None, max_length=30)
