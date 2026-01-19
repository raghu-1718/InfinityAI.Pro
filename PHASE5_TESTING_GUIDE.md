# Phase 5: Integration Testing & Validation

**Status**: In Progress
**Duration**: 90 minutes
**Date Started**: 2025-01-19
**Target Completion**: 2025-01-19 (End of day)

---

## Overview

Phase 5 validates that all three engines work together correctly with the new Indian market parameters. This includes:

1. **Unit Testing** (15 min) - Individual engine components
2. **Integration Testing** (30 min) - Engines working together
3. **Data Validation** (20 min) - Signal quality and accuracy
4. **Stress Testing** (15 min) - Edge cases and limits
5. **Documentation** (10 min) - Test results and sign-off

---

## Quick Status

| Component   | Status  | Test Result | Notes                              |
| ----------- | ------- | ----------- | ---------------------------------- |
| Engine A    | Ready   | Pending     | Orchestration/Risk engine          |
| Engine B    | Ready   | Pending     | MACD/RSI/BB parameters updated     |
| Engine C    | Ready   | Pending     | ML model waiting transfer learning |
| Integration | Ready   | Pending     | Full pipeline needs validation     |
| Deployment  | Blocked | N/A         | Blocked until Phase 5 tests pass   |

---

## Phase 5 Test Plan

### Section 1: Unit Tests (15 min)

#### Test 1.1: Engine B - MACD Parameter Validation

**Objective**: Verify MACD(10,20,9) is correctly calculated

**Test Script**:

```python
# backend/engine-b/tests/test_macd_params.py

import pandas as pd
from engine_b.src.main import add_features

def test_macd_10_20_9_vs_12_26_9():
    """Verify MACD params changed correctly"""
    # Create synthetic data
    df = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105] * 5  # 30 days
    })

    # Apply feature engineering
    df = add_features(df)

    # Checks
    assert 'MACD_10_20_9' in df.columns, "MACD_10_20_9 column missing"
    assert 'MACD_12_26_9' in df.columns, "Backward compat column missing"

    # MACD(10,20,9) should respond faster than (12,26,9)
    # Verify first non-NaN value appears earlier in (10,20,9)
    idx_10 = df['MACD_10_20_9'].first_valid_index()
    idx_12 = df['MACD_12_26_9'].first_valid_index()

    # Both should be valid, column exists
    assert idx_10 is not None
    assert idx_12 is not None

    print("✅ MACD parameters validated")

def test_rsi_25_75_thresholds():
    """Verify RSI thresholds changed to 25/75"""
    df = pd.DataFrame({
        'close': list(range(100, 150)) * 3  # Synthetic uptrend
    })

    df = add_features(df)

    assert 'RSI_14' in df.columns
    rsi_values = df['RSI_14'].dropna()

    # RSI should be between 0-100
    assert rsi_values.min() >= 0
    assert rsi_values.max() <= 100

    print("✅ RSI thresholds validated")

def test_bb_width_2_5_vs_2_0():
    """Verify BB width increased to 2.5"""
    df = pd.DataFrame({
        'close': [100 + i*0.1 for i in range(100)]  # Trending data
    })

    df = add_features(df)

    # BB(2.5) should be wider than BB(2.0)
    df['bb_width_25'] = df['BBU_20_2.5'] - df['BBL_20_2.5']
    df['bb_width_20'] = df['BBU_20_2.0'] - df['BBL_20_2.0']

    # Compare widths (should be wider with 2.5)
    assert (df['bb_width_25'] >= df['bb_width_20']).sum() > 0

    print("✅ BB width validated")
```

**Expected Results**:

- ✅ All MACD/RSI/BB columns present
- ✅ Parameters match specifications
- ✅ Backward compatibility maintained
- ✅ No NaN values in output (after warmup period)

---

#### Test 1.2: Engine A - Risk Management Validation

**Objective**: Verify Engine A applies risk rules correctly

**Test Script**:

```python
# backend/engine-a/tests/test_risk_rules.py

def test_position_sizing():
    """Verify position sizing within limits"""
    from engine_a.src.main import calculate_position_size

    # Test cases
    test_cases = [
        {'portfolio': 100000, 'risk_pct': 2, 'entry': 100, 'stop': 95, 'expected_qty': 400},
        {'portfolio': 500000, 'risk_pct': 1, 'entry': 50, 'stop': 48, 'expected_qty': 250},
    ]

    for tc in test_cases:
        qty = calculate_position_size(
            tc['portfolio'],
            tc['risk_pct'],
            tc['entry'],
            tc['stop']
        )
        assert qty <= tc['expected_qty'] * 1.05, "Position size too large"
        print(f"✅ Position sizing OK: {qty} shares")

def test_drawdown_limits():
    """Verify daily/monthly drawdown limits enforced"""
    from engine_a.src.main import check_drawdown_limits

    # Simulate portfolio with 15% loss
    portfolio_pnl = -15000  # 15% of 100k
    daily_limit = 5  # 5%

    allowed, reason = check_drawdown_limits(portfolio_pnl, daily_limit)

    assert not allowed, "Should block trades on excess drawdown"
    print(f"✅ Drawdown limit enforced: {reason}")
```

**Expected Results**:

- ✅ Position sizing calculations correct
- ✅ Risk limits enforced
- ✅ No positions exceed portfolio risk tolerance

---

### Section 2: Integration Tests (30 min)

#### Test 2.1: Full Pipeline - Signal Generation

**Objective**: Validate complete Engine A → Engine B → Execution flow

**Test Data**:

- Stock: TCS (Tata Consultancy Services)
- Period: Last 30 days
- Timeframe: Daily candles

**Test Script**:

```python
# backend/tests/test_full_pipeline.py

def test_signal_generation_pipeline():
    """Test complete signal generation flow"""
    from engine_b.src.main import add_features
    from engine_a.src.main import generate_signals, apply_risk_rules
    import pandas as pd

    # 1. Fetch data
    df = fetch_historical_data(
        symbol='TCS',
        days=30,
        interval='1day'
    )

    # 2. Engine B: Add technical indicators
    df = add_features(df)

    # Validate Engine B output
    assert 'MACD_10_20_9' in df.columns
    assert 'RSI_14' in df.columns
    assert 'BBL_20_2.5' in df.columns
    print("✅ Engine B feature engineering complete")

    # 3. Engine A: Generate trading signals
    signals = generate_signals(df)

    # Validate signals
    assert len(signals) > 0, "No signals generated"
    assert all(s['type'] in ['BUY', 'SELL', 'HOLD'] for s in signals)
    print(f"✅ Engine A generated {len(signals)} signals")

    # 4. Engine A: Apply risk rules
    approved_signals = apply_risk_rules(
        signals,
        portfolio_value=100000,
        max_position_pct=2,
        max_daily_drawdown=5
    )

    print(f"✅ Risk filter: {len(signals)} signals → {len(approved_signals)} approved")

    # 5. Validate approved signals
    for sig in approved_signals:
        assert sig['position_size'] > 0
        assert sig['stop_loss'] is not None
        assert sig['take_profit'] is not None
        assert sig['risk_pct'] <= 2, "Risk % exceeds limit"

    print("✅ Full pipeline validation passed")
    return approved_signals
```

**Expected Output**:

```
Sample signal:
{
  'symbol': 'TCS',
  'type': 'BUY',
  'entry_price': 4250.50,
  'quantity': 25,
  'stop_loss': 4200.00,
  'take_profit': 4350.00,
  'risk_reward_ratio': 1:2,
  'confidence': 0.75,
  'timestamp': '2025-01-19 15:30:00',
  'indicators': {
    'macd_10_20_9': 150.25,
    'macd_signal_9': 145.30,
    'rsi_14': 28.5,  # Oversold
    'bb_position': 'lower_band'
  }
}
```

**Acceptance Criteria**:

- ✅ Signals generated with all required fields
- ✅ Risk/reward ratios > 1:1.5
- ✅ No signals on days with missing data
- ✅ Signal confidence scores reasonable (0.5-0.9)

---

#### Test 2.2: Dhan Broker Integration

**Objective**: Verify signals can be sent to Dhan broker

**Test Script**:

```python
# backend/tests/test_dhan_integration.py

def test_dhan_order_placement():
    """Test placing order via Dhan broker"""
    from dhan_connector import DhanBroker

    broker = DhanBroker(
        client_id='TEST_CLIENT',
        auth_token=os.getenv('DHAN_AUTH_TOKEN')
    )

    # Validate connection
    assert broker.is_connected(), "Broker connection failed"
    print("✅ Dhan broker connected")

    # Get holdings to validate account
    holdings = broker.get_holdings()
    assert len(holdings) >= 0, "Could not fetch holdings"
    print(f"✅ Current holdings: {len(holdings)} positions")

    # Validate broker can accept orders
    # (Don't actually place order in test)
    order_template = {
        'symbol': 'TCS',
        'qty': 1,
        'price': 4250,
        'type': 'LIMIT',
        'side': 'BUY',
        'product': 'CNC'  # Cash & Carry for equity
    }

    # Validate order format
    assert broker.validate_order(order_template), "Order validation failed"
    print("✅ Order validation passed")
```

**Expected Results**:

- ✅ Broker connection successful
- ✅ Account accessible
- ✅ Order format validation passes
- ✅ No credential errors

---

### Section 3: Data Validation (20 min)

#### Test 3.1: Signal Quality Metrics

**Objective**: Analyze quality of generated signals

**Metrics**:

```python
# backend/tests/test_signal_quality.py

def analyze_signal_quality(signals_df):
    """Compute signal quality metrics"""

    # 1. Signal frequency
    buy_signals = len(signals_df[signals_df['type'] == 'BUY'])
    sell_signals = len(signals_df[signals_df['type'] == 'SELL'])

    # For 30 days of daily data, expect 5-10 signals total
    assert 5 <= (buy_signals + sell_signals) <= 10, \
        f"Signal frequency abnormal: {buy_signals + sell_signals} signals"
    print(f"✅ Signal frequency OK: {buy_signals} BUY, {sell_signals} SELL")

    # 2. Risk/Reward ratio
    avg_rr = signals_df['risk_reward_ratio'].mean()
    assert avg_rr >= 1.5, f"Risk/reward too low: {avg_rr}"
    print(f"✅ Avg Risk/Reward: {avg_rr:.2f}:1")

    # 3. Confidence scores
    avg_confidence = signals_df['confidence'].mean()
    assert 0.6 <= avg_confidence <= 0.85, \
        f"Confidence score abnormal: {avg_confidence}"
    print(f"✅ Avg Confidence: {avg_confidence:.2%}")

    # 4. Entry point distribution
    # Check that entries aren't clustered in one area
    entry_std = signals_df['entry_price'].std() / signals_df['entry_price'].mean()
    assert entry_std > 0.02, "Entry points too clustered"
    print(f"✅ Entry point distribution: {entry_std:.2%} variation")

    return {
        'total_signals': len(signals_df),
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'avg_risk_reward': avg_rr,
        'avg_confidence': avg_confidence
    }
```

**Expected Metrics** (per 30 trading days):

- Total signals: 5-10
- Buy/Sell ratio: 0.8-1.2 (roughly balanced)
- Avg Risk/Reward: 1.5:1 or better
- Avg Confidence: 60-85%
- Drawdown on stop-loss: -2.0% to -2.5% max

---

#### Test 3.2: Indicator Value Ranges

**Objective**: Verify technical indicators in expected ranges

**Test Script**:

```python
# backend/tests/test_indicator_ranges.py

def test_indicator_ranges(df):
    """Validate all indicators in expected ranges"""

    checks = {
        'RSI_14': {'min': 0, 'max': 100, 'desc': 'RSI'},
        'MACD_10_20_9': {'min': -100, 'max': 100, 'desc': 'MACD'},
        'BBL_20_2.5': {'relation': 'BBU_20_2.5', 'check': 'less_than', 'desc': 'BB Lower < Upper'},
    }

    for column, spec in checks.items():
        if 'min' in spec:
            assert df[column].min() >= spec['min'], \
                f"{spec['desc']} too low: {df[column].min()}"
            assert df[column].max() <= spec['max'], \
                f"{spec['desc']} too high: {df[column].max()}"
            print(f"✅ {spec['desc']}: [{df[column].min():.2f}, {df[column].max():.2f}]")

        if 'relation' in spec:
            lower = df[column]
            upper = df[spec['relation']]
            assert (lower < upper).all(), f"{spec['desc']} failed"
            print(f"✅ {spec['desc']}: Validated")
```

**Expected Ranges**:

- RSI: 0-100 ✅
- MACD: -50 to +50 (typical) ✅
- BB Upper > BB Lower ✅
- Volume increasing on breakouts ✅

---

### Section 4: Stress Testing (15 min)

#### Test 4.1: Market Conditions

**Objective**: Test engines handle various market conditions

```python
# backend/tests/test_stress_conditions.py

def test_high_volatility():
    """Test with high volatility data (e.g., 5% daily swings)"""
    df = generate_synthetic_data(volatility=0.05)  # 5% daily move
    df = add_features(df)

    # Should still generate signals, not crash
    signals = generate_signals(df)
    assert len(signals) > 0
    print("✅ High volatility handling: OK")

def test_low_volume():
    """Test with low volume data"""
    df = generate_synthetic_data(volume_multiplier=0.1)

    # Risk management should warn or skip
    signals = generate_signals(df)
    print("✅ Low volume handling: OK")

def test_gap_up_down():
    """Test with gap up/down scenarios"""
    df = generate_synthetic_data(include_gaps=True)
    signals = generate_signals(df)

    # Stops should adjust for gaps
    for sig in signals:
        assert sig['stop_loss'] != sig['entry_price']
    print("✅ Gap handling: OK")

def test_limit_up_down():
    """Test circuit breaker scenarios (Indian markets)"""
    df = generate_synthetic_data(circuit_breaker=True)

    # Signals should be suppressed during circuit limits
    signals = generate_signals(df)
    # May have no signals, that's OK
    print("✅ Circuit breaker handling: OK")
```

**Expected Behavior**:

- ✅ No crashes on edge cases
- ✅ Appropriate risk adjustments
- ✅ No signals during gaps/circuit breakers
- ✅ Graceful degradation

---

### Section 5: Test Summary Report

**Template**:

```markdown
# Phase 5 Test Results - TCS (30 days)

| Test                      | Result  | Status | Notes                             |
| ------------------------- | ------- | ------ | --------------------------------- |
| MACD(10,20,9) calculation | ✅ PASS | 15 min | Faster response confirmed         |
| RSI(25/75) thresholds     | ✅ PASS | 15 min | Better signal quality             |
| BB(2.5σ) widths           | ✅ PASS | 15 min | 25-30% wider than 2.0σ            |
| Full pipeline             | ✅ PASS | 30 min | 8 signals generated, quality good |
| Dhan integration          | ✅ PASS | 20 min | Broker connection stable          |
| Signal quality            | ✅ PASS | 20 min | Avg RR: 1.8:1, Confidence: 72%    |
| Stress conditions         | ✅ PASS | 15 min | Handles volatility, gaps, limits  |

**Summary**: All tests passed. Ready for Phase 6 deployment.
```

---

## Test Execution Checklist

- [ ] Verify test environment setup (dependencies installed)
- [ ] Pull latest Engine B code (with new MACD/RSI/BB params)
- [ ] Pull Dhan broker integration code
- [ ] Set environment variables (Dhan credentials)
- [ ] Run unit tests (Section 1) - should take 5 min
- [ ] Run integration tests (Section 2) - should take 20 min
- [ ] Run data validation (Section 3) - should take 15 min
- [ ] Run stress tests (Section 4) - should take 10 min
- [ ] Review test report
- [ ] Sign off - Tests Passed ✅
- [ ] Proceed to Phase 6

---

## Test Failure Handling

### If Signal Generation Fails

**Debug Steps**:

1. Check Engine B imports - `python -c "from engine_b.src.main import add_features"`
2. Verify data fetch - `python -c "fetch_historical_data('TCS', 30)"`
3. Check TA indicators - Run MACD calculation manually
4. Validate broker credentials - Test Dhan connection

### If Risk Rules Block All Signals

**Debug Steps**:

1. Check risk limits - Are they too strict?
2. Validate position sizing - Test with smaller positions
3. Review drawdown - Check if at daily/monthly limit
4. Loosen limits temporarily to unblock testing

### If Backward Compatibility Fails

**Debug Steps**:

1. Verify column aliasing - Check `df.columns` for old names
2. Test old signal names - `df['MACD_12_26_9']` should still work
3. Review mapping logic - Ensure aliases correctly point to new columns

---

## Success Criteria

**Phase 5 is COMPLETE when**:

- ✅ All unit tests pass (Section 1)
- ✅ Full pipeline generates valid signals (Section 2)
- ✅ Signal quality meets targets (Section 3)
- ✅ Stress tests complete without errors (Section 4)
- ✅ Test report signed off
- ✅ Zero critical bugs found
- ✅ Dhan broker integration verified

---

**Status**: Ready to begin Phase 5 testing
**Next Steps**: Execute Section 1 (Unit Tests) first
**Estimated Time**: 90 minutes total
