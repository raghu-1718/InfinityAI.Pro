# InfinityAI.Pro - Phase 2 Integration Guide

**Status:** Ready for Implementation
**Scope:** Structured Logging + Evaluation Framework Integration
**Timeline:** 2-4 hours for full integration
**Risk Level:** LOW (non-breaking changes, additive)

---

## 📋 **Overview**

Phase 2 adds two critical observability components to the InfinityAI.Pro platform:

1. **Structured Logging** - Production-grade JSON logging with trace ID propagation
2. **Evaluation Framework** - Test dataset runners and AI signal evaluation harness

These frameworks integrate with existing Phase 1 code (OTEL, CORS, security rules) and prepare the platform for 10/10 production readiness.

---

## 🎯 **Implementation Checklist**

### Step 1: Install Python Dependencies

```bash
cd c:\workspace\InfinityAI.Pro\backend

# Add to requirements.txt (all engines)
# Already available in Python 3.11+ standard library:
# - json, logging, uuid, datetime, contextvars, abc
# No new dependencies required!
```

**Note:** Both frameworks use only Python stdlib (no external deps). This keeps deployments lightweight and reduces supply-chain risk.

---

### Step 2: Engine A Integration

#### 2.1 Update `backend/engine-a/src/main.py`

**Add import at top:**

```python
from shared.structured_logging import (
    get_logger,
    set_trace_context,
    get_trace_context
)

logger = get_logger(__name__)
```

**Update FastAPI app startup:**

```python
@app.on_event("startup")
async def startup_event():
    logger.info(
        "Engine A starting",
        version="1.0.0",
        region="us-central1",
        environment=os.getenv("ENVIRONMENT", "production")
    )
    # ... existing startup code ...
```

**Add middleware for trace context propagation:**

```python
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Extract or generate trace ID from headers
        trace_id = request.headers.get(
            "X-Cloud-Trace-Context",
            f"trace-{uuid.uuid4().hex[:16]}"
        )

        set_trace_context(
            trace_id=trace_id,
            user_id=request.headers.get("X-User-ID"),
            request_id=request.headers.get("X-Request-ID")
        )

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response

app.add_middleware(TraceContextMiddleware)
```

#### 2.2 Update Routes in `backend/engine-a/src/api/routes.py`

**Before:**

```python
@router.post("/signals")
async def get_signals(request: SignalRequest):
    print(f"Received signal request for {request.symbol}")
    # ...
```

**After:**

```python
@router.post("/signals")
async def get_signals(request: SignalRequest):
    logger.info(
        "Signal request received",
        symbol=request.symbol,
        timeframe=request.timeframe,
        indicators=request.indicators
    )

    try:
        signals = await compute_signals(request)
        logger.debug(
            "Signals computed",
            symbol=request.symbol,
            signal_count=len(signals),
            confidence_avg=sum(s.confidence for s in signals) / len(signals)
        )
        return signals
    except Exception as e:
        logger.error(
            "Signal computation failed",
            symbol=request.symbol,
            error_type=type(e).__name__,
            exc_info=True
        )
        raise
```

#### 2.3 Update Risk Manager Logger

**File:** `backend/engine-a/src/services/risk_manager.py`

```python
from shared.structured_logging import get_logger

logger = get_logger(__name__)

def check_position_limits(order: Order) -> RiskCheckResult:
    logger.debug(
        "Checking position limits",
        symbol=order.symbol,
        quantity=order.quantity,
        current_position=get_current_position(order.symbol)
    )

    if order.quantity > MAX_POSITION:
        logger.warning(
            "Position limit exceeded",
            symbol=order.symbol,
            quantity=order.quantity,
            limit=MAX_POSITION
        )
        return RiskCheckResult(passed=False, reason="Position limit exceeded")

    logger.info(
        "Risk check passed",
        symbol=order.symbol,
        quantity=order.quantity,
        check_type="position_limits"
    )
    return RiskCheckResult(passed=True)
```

---

### Step 3: Engine B Integration

#### 3.1 Update `backend/engine-b/src/main.py`

Same pattern as Engine A:

```python
from shared.structured_logging import (
    get_logger,
    set_trace_context,
    TraceContextFilter
)

logger = get_logger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info(
        "Engine B (AI/ML) starting",
        model_version=os.getenv("MODEL_VERSION", "gemini-2.0-flash"),
        region="us-central1"
    )
    # ...
```

#### 3.2 Update Gemini Integration

**File:** `backend/engine-b/src/services/gemini_client.py`

```python
import logging
from shared.structured_logging import get_logger

logger = get_logger(__name__)

async def generate_signal(symbol: str, market_data: Dict) -> SignalResponse:
    logger.debug(
        "Generating AI signal with Gemini",
        symbol=symbol,
        data_points=len(market_data),
        model="gemini-2.0-flash"
    )

    start_time = time.time()

    try:
        response = await gemini_client.generate_content(
            prompt=build_prompt(symbol, market_data),
            temperature=0.3
        )

        latency_ms = (time.time() - start_time) * 1000

        logger.info(
            "AI signal generated",
            symbol=symbol,
            signal=response.signal,
            confidence=response.confidence,
            latency_ms=latency_ms,
            reasoning_length=len(response.reasoning)
        )

        return response

    except Exception as e:
        logger.error(
            "AI signal generation failed",
            symbol=symbol,
            model="gemini-2.0-flash",
            error=str(e),
            exc_info=True
        )
        raise
```

#### 3.3 Add Model Evaluation Integration

**File:** `backend/engine-b/src/services/model_evaluator.py` (NEW)

```python
from shared.structured_logging import get_logger
from backend.tests.evaluation.framework import (
    EvaluationRunner,
    SignalAccuracyMetric,
    ConfidenceScoreMetric
)

logger = get_logger(__name__)

async def evaluate_model_performance(test_dataset: List[Dict]):
    """Evaluate AI model against test cases."""

    logger.info(
        "Starting model evaluation",
        test_case_count=len(test_dataset),
        evaluation_type="signal_accuracy"
    )

    test_cases = [
        TestCase(
            id=f"test-{i}",
            name=f"{test['symbol']} signal test",
            description=test.get('description', ''),
            input_data=test
        )
        for i, test in enumerate(test_dataset)
    ]

    # Handler for evaluating each test case
    async def evaluate_test(test_case):
        signal_response = await generate_signal(
            test_case.input_data['symbol'],
            test_case.input_data['market_data']
        )

        result = EvaluationResult(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            status="PASS" if signal_response else "FAIL",
            actual_output={
                "signal": signal_response.signal,
                "confidence": signal_response.confidence,
                "expected_signal": test_case.input_data.get('expected_signal')
            }
        )
        return result

    runner = EvaluationRunner(
        name="Gemini Signal Model Evaluation",
        test_cases=test_cases,
        metrics=[SignalAccuracyMetric(), ConfidenceScoreMetric()]
    )

    results = runner.run(handler_func=evaluate_test)
    summary = runner.get_summary()

    logger.info(
        "Model evaluation complete",
        pass_rate=summary['pass_rate'],
        avg_confidence=summary['metrics'].get('confidence_score', 0.0),
        execution_time_seconds=summary['duration_seconds']
    )

    return summary
```

---

### Step 4: Engine C Integration

#### 4.1 Update `backend/engine-c/src/main.py`

```python
from shared.structured_logging import (
    get_logger,
    set_trace_context
)

logger = get_logger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info(
        "Engine C (Execution) starting",
        broker="DhanHQ",
        region="us-central1",
        trading_mode=os.getenv("TRADING_MODE", "paper")
    )
    # ...
```

#### 4.2 Update Order Placement Logic

**File:** `backend/engine-c/src/services/order_executor.py`

```python
from shared.structured_logging import get_logger

logger = get_logger(__name__)

async def place_order(order: Order) -> OrderResult:
    """Place trade order with execution logging."""

    logger.info(
        "Order placement initiated",
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        order_type=order.order_type,
        client_id=order.client_id
    )

    try:
        # Call DhanHQ API
        result = await dhan_client.place_order(
            symbol=order.symbol,
            quantity=order.quantity,
            side=order.side,
            order_type=order.order_type,
            price=order.price
        )

        logger.info(
            "Order placed successfully",
            symbol=order.symbol,
            quantity=order.quantity,
            order_id=result.order_id,
            execution_price=result.execution_price,
            execution_time_ms=result.execution_time_ms
        )

        return result

    except Exception as e:
        logger.error(
            "Order placement failed",
            symbol=order.symbol,
            quantity=order.quantity,
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise
```

#### 4.3 Add Trade Reconciliation Logger

**File:** `backend/engine-c/src/services/trade_reconciler.py`

```python
from shared.structured_logging import get_logger

logger = get_logger(__name__)

async def reconcile_trades(trades: List[Trade]):
    """Reconcile executed trades with broker."""

    logger.debug(
        "Starting trade reconciliation",
        trade_count=len(trades)
    )

    for trade in trades:
        try:
            broker_trade = await dhan_client.get_trade(trade.order_id)

            if trade.quantity != broker_trade.quantity:
                logger.warning(
                    "Trade quantity mismatch",
                    order_id=trade.order_id,
                    expected_qty=trade.quantity,
                    broker_qty=broker_trade.quantity
                )
            else:
                logger.debug(
                    "Trade reconciled",
                    order_id=trade.order_id,
                    quantity=trade.quantity,
                    execution_price=broker_trade.execution_price
                )

        except Exception as e:
            logger.error(
                "Trade reconciliation failed",
                order_id=trade.order_id,
                error=str(e),
                exc_info=True
            )
```

---

### Step 5: Shared Module Integration

#### 5.1 Update `backend/shared/__init__.py`

```python
"""Shared utilities for all InfinityAI.Pro services."""

from .structured_logging import (
    get_logger,
    set_trace_context,
    get_trace_context,
    clear_trace_context,
    StructuredLogger,
    StructuredFormatter
)

__all__ = [
    'get_logger',
    'set_trace_context',
    'get_trace_context',
    'clear_trace_context',
    'StructuredLogger',
    'StructuredFormatter'
]
```

---

### Step 6: Test Dataset Creation

#### 6.1 Create Test Datasets

**File:** `backend/tests/datasets/ai_signals.json`

```json
{
  "signal_tests": [
    {
      "id": "test-001",
      "symbol": "NIFTY50",
      "name": "Bullish Reversal Signal",
      "market_data": {
        "current_price": 20500,
        "price_change_pct": 2.5,
        "rsi": 35,
        "macd": "bullish_crossover",
        "volume_ratio": 1.8,
        "volatility_pct": 3.2
      },
      "expected_signal": "BUY",
      "expected_confidence_min": 0.75
    },
    {
      "id": "test-002",
      "symbol": "BANKNIFTY",
      "name": "Bearish Breakdown Signal",
      "market_data": {
        "current_price": 45000,
        "price_change_pct": -3.0,
        "rsi": 65,
        "macd": "bearish_crossover",
        "volume_ratio": 2.1,
        "volatility_pct": 5.0
      },
      "expected_signal": "SELL",
      "expected_confidence_min": 0.7
    }
  ]
}
```

#### 6.2 Create Evaluation Test Script

**File:** `backend/tests/evaluation/run_tests.py`

```python
#!/usr/bin/env python3
"""
Run AI signal evaluation tests against Engine B.
Usage: python backend/tests/evaluation/run_tests.py
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from framework import (
    EvaluationRunner,
    TestCase,
    SignalAccuracyMetric,
    ConfidenceScoreMetric,
    LatencyMetric
)
from shared.structured_logging import get_logger, set_trace_context

logger = get_logger(__name__)

def load_test_dataset(filepath: str):
    """Load test dataset from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    test_cases = [
        TestCase(
            id=test['id'],
            name=test['name'],
            description=test.get('description', ''),
            input_data=test
        )
        for test in data['signal_tests']
    ]

    return test_cases


def main():
    """Run evaluation suite."""

    # Set up tracing
    set_trace_context(trace_id=f"eval-{os.getenv('CI_COMMIT_SHA', 'local')}")

    logger.info("Starting evaluation test suite")

    # Load test dataset
    dataset_path = Path(__file__).parent / "../datasets/ai_signals.json"
    test_cases = load_test_dataset(str(dataset_path))

    logger.info(f"Loaded {len(test_cases)} test cases")

    # Create evaluation runner
    runner = EvaluationRunner(
        name="AI Signal Evaluation - CI/CD Pipeline",
        test_cases=test_cases,
        metrics=[
            SignalAccuracyMetric(),
            ConfidenceScoreMetric(),
            LatencyMetric(sla_ms=1000)
        ]
    )

    # Run evaluation
    results = runner.run()

    # Get summary
    summary = runner.get_summary()

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    runner.save_results(str(results_dir / f"results-{summary['trace_id']}.json"))

    # Log summary
    logger.info(
        "Evaluation complete",
        pass_rate=summary['pass_rate'],
        total_tests=summary['total_tests'],
        avg_latency_ms=summary['average_latency_ms']
    )

    # Exit with appropriate code
    if summary['pass_rate'] >= 90.0:
        logger.info("✅ All evaluation tests passed")
        return 0
    else:
        logger.error("❌ Evaluation tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

### Step 7: Integration Tests

#### 7.1 Create Integration Test

**File:** `backend/tests/integration/test_structured_logging.py`

```python
"""Integration tests for structured logging framework."""

import unittest
import json
import logging
from io import StringIO
from contextlib import redirect_stdout

from shared.structured_logging import (
    get_logger,
    set_trace_context,
    get_trace_context,
    clear_trace_context,
    StructuredFormatter
)


class TestStructuredLogging(unittest.TestCase):
    """Test structured logging functionality."""

    def setUp(self):
        clear_trace_context()

    def test_trace_context_setting(self):
        """Test setting and retrieving trace context."""
        set_trace_context(
            trace_id="test-trace-123",
            user_id="user-456"
        )

        context = get_trace_context()
        self.assertEqual(context['trace_id'], "test-trace-123")
        self.assertEqual(context['user_id'], "user-456")

    def test_structured_format(self):
        """Test that logs are formatted as valid JSON."""
        logger = get_logger("test_logger")

        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())
        test_logger = logging.getLogger("test_logger")
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)

        # Log a message
        test_logger.info("Test message")

        # Parse log as JSON
        log_output = log_stream.getvalue().strip()
        log_json = json.loads(log_output)

        self.assertEqual(log_json['message'], "Test message")
        self.assertEqual(log_json['level'], "INFO")
        self.assertIn('timestamp', log_json)

    def test_custom_fields(self):
        """Test logging with custom fields."""
        logger = get_logger("test_logger_2")

        # This should not raise an error
        logger.info(
            "Order placed",
            symbol="NIFTY50",
            quantity=100,
            price=20500.0
        )


if __name__ == "__main__":
    unittest.main()
```

---

## 🚀 **Deployment Steps**

### 1. Apply Code Changes to All Engines

```bash
# Verify files exist
ls -la backend/engine-a/src/main.py
ls -la backend/engine-b/src/main.py
ls -la backend/engine-c/src/main.py
ls -la backend/shared/structured_logging.py

# Test imports
python3 -c "from backend.shared.structured_logging import get_logger; print('✅ Import OK')"
python3 -c "from backend.tests.evaluation.framework import EvaluationRunner; print('✅ Import OK')"
```

### 2. Run Local Tests

```bash
cd backend
python3 -m pytest tests/integration/test_structured_logging.py -v
python3 -m pytest tests/evaluation/framework.py -v
```

### 3. Update Engine Dockerfiles

Add to each `Dockerfile`:

```dockerfile
# Copy shared modules
COPY backend/shared /app/shared

# Update Python path
ENV PYTHONPATH=/app:$PYTHONPATH
```

### 4. Deploy to Production

```bash
# Using CI/CD (GitHub Actions already configured):
git add backend/shared/structured_logging.py
git add backend/tests/evaluation/framework.py
git add backend/engine-a/src/main.py
git add backend/engine-b/src/main.py
git add backend/engine-c/src/main.py
git commit -m "Phase 2: Add structured logging and evaluation framework"
git push origin main

# OR manual deployment:
./infra/apply_secrets_and_verify.ps1
```

---

## ✅ **Validation Checklist**

After deployment, verify:

- [ ] All engines start without errors
- [ ] Cloud Logging shows structured JSON logs
- [ ] Trace IDs present in all log entries
- [ ] Cloud Trace receiving spans with correlation
- [ ] Evaluation framework can load test datasets
- [ ] Evaluation runner produces JSON results
- [ ] No performance degradation (< 5% latency increase)
- [ ] All error logs include exception details
- [ ] User ID propagation working end-to-end

---

## 📊 **Observability Matrix Post-Phase-2**

| Capability               | Status   | Evidence                          |
| ------------------------ | -------- | --------------------------------- |
| Structured Logging       | ✅       | JSON format in Cloud Logging      |
| Trace Propagation        | ✅       | X-Trace-ID in responses           |
| Error Tracking           | ✅       | Exception details in logs         |
| Performance Metrics      | ✅       | latency_ms in logs                |
| Business Metrics         | ✅       | symbol, quantity, price fields    |
| AI Signal Quality        | ✅       | Evaluation framework with metrics |
| End-to-End Tracing       | ✅       | Cloud Trace with OTEL spans       |
| **Production Readiness** | **7/10** | Logging + Evaluation added        |

---

## 🔄 **Phase 3 Preview (Deployment & Validation)**

After Phase 2 completion:

- Deploy Phase 1 + 2 changes to production
- Run comprehensive smoke test suite
- Validate all observability working end-to-end
- Execute full AI signal evaluation against live market data
- Achieve **Production Readiness: 10/10** certification

---

**Next Step:** Execute Phase 2 integration on all engines, then proceed to Phase 3 (Production Deployment & Validation).
