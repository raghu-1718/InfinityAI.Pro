import pytest
from pydantic import ValidationError
from datetime import datetime

from backend.src.schemas import (
    MarketTickRequest,
    ModelInferenceRequest,
    BacktestRunRequest,
    CorrelationIdHeader,
    PortfolioStateResponse,
    OptionType
)

def test_valid_market_tick_request():
    """Verify that a well-formed market tick passes schema validation."""
    data = {
        "symbol": "NIFTY",
        "price": 24500.50,
        "volume": 1500,
        "strike_price": 24500,
        "option_type": "CE",
        "open_interest": 450000,
        "timestamp": datetime.utcnow().isoformat()
    }
    tick = MarketTickRequest(**data)
    assert tick.symbol == "NIFTY"
    assert tick.price == 24500.50
    assert tick.option_type == OptionType.CE

def test_invalid_market_tick_price():
    """Negative prices must fail validation."""
    with pytest.raises(ValidationError):
        MarketTickRequest(
            symbol="NIFTY",
            price=-10.0,
            volume=100,
            timestamp=datetime.utcnow()
        )

def test_invalid_option_type():
    """Invalid option types must be rejected."""
    with pytest.raises(ValidationError):
        MarketTickRequest(
            symbol="BANKNIFTY",
            price=51200.0,
            volume=500,
            option_type="INVALID_TYPE",
            timestamp=datetime.utcnow()
        )

def test_valid_model_inference_request():
    """Verify inference request with valid features and model weights."""
    req = ModelInferenceRequest(
        features={"close": 24500.0, "rsi_14": 52.3, "macd": 10.5, "iv": 14.2},
        models=["catboost", "lightgbm", "xgboost"],
        ensemble_weights={"catboost": 0.4, "lightgbm": 0.35, "xgboost": 0.25}
    )
    assert len(req.models) == 3
    assert req.features["rsi_14"] == 52.3

def test_empty_inference_features():
    """Inference request with empty features must be rejected."""
    with pytest.raises(ValidationError):
        ModelInferenceRequest(features={})

def test_invalid_ensemble_weights():
    """Ensemble weights not summing to 1.0 must be rejected."""
    with pytest.raises(ValidationError):
        ModelInferenceRequest(
            features={"close": 24500.0},
            models=["catboost", "xgboost"],
            ensemble_weights={"catboost": 0.5, "xgboost": 0.8}  # Sums to 1.3
        )

def test_valid_backtest_request():
    """Verify backtest configuration schema."""
    req = BacktestRunRequest(
        strategy="tri_model_ensemble",
        symbol="NIFTY",
        start_date="2025-01-01",
        end_date="2025-06-30",
        initial_capital=500000.0,
        slippage_pct=0.0005,
        include_sebi_taxes=True
    )
    assert req.initial_capital == 500000.0
    assert req.include_sebi_taxes is True

def test_invalid_backtest_dates():
    """Backtest where end_date is before start_date must fail validation."""
    with pytest.raises(ValidationError):
        BacktestRunRequest(
            strategy="momentum",
            symbol="NIFTY",
            start_date="2025-12-31",
            end_date="2025-01-01",
            initial_capital=100000.0
        )

def test_correlation_id_validation():
    """Correlation IDs must not exceed 30 characters."""
    valid = CorrelationIdHeader(correlation_id="corr-valid-12345")
    assert valid.correlation_id == "corr-valid-12345"

    with pytest.raises(ValidationError):
        CorrelationIdHeader(correlation_id="this-correlation-id-is-way-too-long-and-exceeds-thirty-chars")
