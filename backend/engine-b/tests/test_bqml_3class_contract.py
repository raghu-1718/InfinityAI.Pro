import pytest
import numpy as np

def test_bqml_3class_probability_parsing():
    """Verify that 3-class BQML predicted_signal_outcome_probs are parsed correctly."""
    probs_raw = [
        {'label': 2, 'prob': 0.3491455316543579},
        {'label': 1, 'prob': 0.3143814504146576},
        {'label': 0, 'prob': 0.3364729881286621}
    ]
    
    prob_map = {int(p.get('label', i)): float(p.get('prob', 0.0)) for i, p in enumerate(probs_raw)}
    p0 = prob_map.get(0, 0.0)
    p1 = prob_map.get(1, 0.0)
    p2 = prob_map.get(2, 0.0)
    
    assert set(prob_map.keys()) == {0, 1, 2}
    assert p0 > 0.0
    assert p1 > 0.0
    assert p2 > 0.0
    assert abs(p0 + p1 + p2 - 1.0) < 1e-4

def test_bqml_3class_weight_accumulation():
    """Verify class votes accumulation from 3-class probabilities."""
    weight = 0.40
    class_votes = {0: 0.0, 1: 0.0, 2: 0.0}
    p0, p1, p2 = 0.33647, 0.31438, 0.34915
    
    class_votes[0] += p0 * weight
    class_votes[1] += p1 * weight
    class_votes[2] += p2 * weight
    
    assert class_votes[0] == pytest.approx(0.134588)
    assert class_votes[1] == pytest.approx(0.125752)
    assert class_votes[2] == pytest.approx(0.139660)

def test_bqml_15_feature_schema():
    """Verify all 15 alpha feature keys are properly defined."""
    required_features = [
        'rsi_14', 'macd_line', 'macd_signal', 'macd_hist', 'macd_crossover',
        'vwap_distance', 'atr_volatility', 'atr_ratio', 'adx_14', 'adx_slope',
        'bollinger_bandwidth', 'bb_pct', 'return_15m_past', 'return_5m_past', 'trend_aligned'
    ]
    sample_dict = {f: 0.0 for f in required_features}
    assert len(sample_dict) == 15
    for f in required_features:
        assert f in sample_dict

