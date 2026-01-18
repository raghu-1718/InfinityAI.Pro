
import pytest
import sys
import os
import numpy as np

# Ensure src and repo root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add backend/engine-a to path
sys.path.append(os.path.join(current_dir, '..'))
# Add repo root to path
sys.path.append(os.path.join(current_dir, '..', '..', '..'))

from src.services.risk_manager import RiskManager, RiskException
from src.safety_limits import MAX_TRADE_CAPITAL, MAX_SESSION_CAPITAL

@pytest.fixture
def risk_manager():
    return RiskManager()

def test_validate_hard_capital_limit(risk_manager):
    """Test hard capital limits are enforced"""
    # Should pass
    assert risk_manager.validate_hard_capital_limit(1000) is True
    
    # Should fail if trade > MAX_TRADE_CAPITAL (assume 10Cr or similar large number defined in safety_limits)
    # Since we import MAX_TRADE_CAPITAL, we can test boundary + 1
    with pytest.raises(RiskException) as excinfo:
        risk_manager.validate_hard_capital_limit(MAX_TRADE_CAPITAL + 1)
    assert "MAX_TRADE_CAPITAL_EXCEEDED" in str(excinfo.value)
    
    # Should fail if session exposure > MAX_SESSION_CAPITAL
    with pytest.raises(RiskException) as excinfo:
        risk_manager.validate_hard_capital_limit(1000, current_session_exposure=MAX_SESSION_CAPITAL + 1)
    assert "MAX_SESSION_CAPITAL_EXCEEDED" in str(excinfo.value)

def test_calculate_var(risk_manager):
    """Test Value at Risk calculation"""
    returns = np.array([-0.02, -0.01, 0.0, 0.01, 0.02])
    
    # Historical method
    var_res = risk_manager.calculate_var(returns, confidence=0.95, method="historical")
    assert "var" in var_res
    assert var_res["method"] == "historical"
    
    # Parametric
    var_res_p = risk_manager.calculate_var(returns, confidence=0.95, method="parametric")
    assert "var" in var_res_p
    assert var_res_p["method"] == "parametric"

def test_calculate_cvar(risk_manager):
    """Test CVaR calculation"""
    returns = np.array([-0.05, -0.02, -0.01, 0.0, 0.01, 0.02])
    cvar_res = risk_manager.calculate_cvar(returns, confidence=0.95)
    
    assert "cvar" in cvar_res
    assert "var" in cvar_res
    # CVaR should be <= VaR (more negative)
    assert cvar_res["cvar"] <= cvar_res["var"]

def test_calculate_sharpe_ratio(risk_manager):
    """Test Sharpe Ratio"""
    # Flat returns -> 0 std dev -> 0 sharpe
    returns_flat = np.array([0.01, 0.01, 0.01])
    assert risk_manager.calculate_sharpe_ratio(returns_flat) == 0.0
    
    # Positive returns
    returns_pos = np.array([0.01, 0.02, 0.03])
    sharpe = risk_manager.calculate_sharpe_ratio(returns_pos, risk_free_rate=0.0)
    assert sharpe > 0

def test_calculate_sortino_ratio(risk_manager):
    """Test Sortino Ratio"""
    returns = np.array([-0.01, -0.02, 0.04, 0.05])
    sortino = risk_manager.calculate_sortino_ratio(returns)
    assert "sortino_ratio" in sortino
    assert sortino["downside_deviation"] > 0

def test_calculate_kelly_criterion(risk_manager):
    """Test Kelly Criterion"""
    # Win rate 50%, Win = 2, Loss = 1 (Ratio=2)
    # Kelly = 0.5 - (0.5 / 2) = 0.25 (25%)
    kelly = risk_manager.calculate_kelly_criterion(0.5, 200, 100)
    assert 0.24 <= kelly["kelly_fraction"] <= 0.26
    
    # Loss only
    kelly_loss = risk_manager.calculate_kelly_criterion(0.0, 0, 100)
    assert kelly_loss["kelly_fraction"] == 0.0

def test_score_risk(risk_manager):
    """Test Risk Scoring"""
    # Low risk
    score_low = risk_manager.score_risk(1000, 0.1, 0.01)
    assert score_low["risk_level"] == "LOW"
    
    # High risk
    score_high = risk_manager.score_risk(1000000, 0.8, 0.5)
    assert score_high["risk_level"] == "HIGH"
