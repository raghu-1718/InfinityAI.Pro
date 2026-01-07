"""
Evaluation Framework for InfinityAI.Pro
========================================

This module provides evaluation runners for testing AI signals, trade decisions,
and end-to-end platform functionality against test datasets.

Project: galvanic-pulsar-482815-h0 (I Am Infinity)
Status: Production Grade
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging

# Configure logging with trace ID support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [TRACE_ID: %(trace_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Represents a single test case for evaluation."""
    id: str
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationResult:
    """Represents the result of a single test case evaluation."""
    test_case_id: str
    test_case_name: str
    status: str  # "PASS", "FAIL", "ERROR"
    actual_output: Dict[str, Any]
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    latency_ms: float = 0.0
    timestamp: str = None
    trace_id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvaluationMetric(ABC):
    """Base class for custom evaluation metrics."""

    @abstractmethod
    def calculate(self, result: EvaluationResult) -> float:
        """Calculate metric value for a test result."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Return metric name."""
        pass


class SignalAccuracyMetric(EvaluationMetric):
    """Evaluates accuracy of AI signals (BUY/SELL/HOLD predictions)."""

    def calculate(self, result: EvaluationResult) -> float:
        if result.status == "ERROR":
            return 0.0

        actual_signal = result.actual_output.get("signal", None)
        expected_signal = result.actual_output.get("expected_signal", None)

        if actual_signal and expected_signal:
            return 1.0 if actual_signal == expected_signal else 0.0
        return 0.0

    def name(self) -> str:
        return "signal_accuracy"


class ConfidenceScoreMetric(EvaluationMetric):
    """Evaluates if confidence scores are within expected ranges."""

    def calculate(self, result: EvaluationResult) -> float:
        if result.status == "ERROR":
            return 0.0

        confidence = result.actual_output.get("confidence", 0.0)
        return confidence  # Raw confidence score (0.0-1.0)

    def name(self) -> str:
        return "confidence_score"


class LatencyMetric(EvaluationMetric):
    """Evaluates if response latency meets SLA requirements."""

    def __init__(self, sla_ms: float = 1000.0):
        self.sla_ms = sla_ms

    def calculate(self, result: EvaluationResult) -> float:
        if result.latency_ms <= self.sla_ms:
            return 1.0
        else:
            return max(0.0, 1.0 - (result.latency_ms - self.sla_ms) / self.sla_ms)

    def name(self) -> str:
        return f"latency_sla_{self.sla_ms}ms"


class EvaluationRunner:
    """
    Main evaluation runner for executing test datasets and collecting metrics.

    Usage:
        runner = EvaluationRunner(
            name="AI Signal Evaluation",
            test_cases=test_cases,
            metrics=[SignalAccuracyMetric(), ConfidenceScoreMetric()]
        )
        results = runner.run()
        runner.save_results("evaluation_results.json")
    """

    def __init__(
        self,
        name: str,
        test_cases: List[TestCase],
        metrics: List[EvaluationMetric],
        trace_id: Optional[str] = None
    ):
        self.name = name
        self.test_cases = test_cases
        self.metrics = metrics
        self.trace_id = trace_id or f"eval-{datetime.utcnow().isoformat()}"
        self.results: List[EvaluationResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def run(self, handler_func=None) -> List[EvaluationResult]:
        """
        Execute all test cases.

        Args:
            handler_func: Optional function(test_case) -> EvaluationResult
                         If not provided, returns mock results for framework validation.

        Returns:
            List of EvaluationResult objects
        """
        self.start_time = datetime.utcnow()
        logger.info(
            f"Starting evaluation: {self.name}",
            extra={"trace_id": self.trace_id}
        )

        for test_case in self.test_cases:
            try:
                if handler_func:
                    result = handler_func(test_case)
                else:
                    # Mock result for demonstration
                    result = self._create_mock_result(test_case)

                # Enrich with metrics
                result.trace_id = self.trace_id
                metrics_dict = {}
                for metric in self.metrics:
                    metrics_dict[metric.name()] = metric.calculate(result)
                result.metrics = metrics_dict

                self.results.append(result)
                logger.info(
                    f"Completed test: {test_case.name} - {result.status}",
                    extra={"trace_id": self.trace_id}
                )

            except Exception as e:
                logger.error(
                    f"Error running test {test_case.name}: {str(e)}",
                    extra={"trace_id": self.trace_id}
                )
                result = EvaluationResult(
                    test_case_id=test_case.id,
                    test_case_name=test_case.name,
                    status="ERROR",
                    actual_output={},
                    error_message=str(e),
                    trace_id=self.trace_id
                )
                self.results.append(result)

        self.end_time = datetime.utcnow()
        return self.results

    def _create_mock_result(self, test_case: TestCase) -> EvaluationResult:
        """Create a mock result for testing framework."""
        return EvaluationResult(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            status="PASS",
            actual_output={
                "signal": test_case.input_data.get("expected_signal", "HOLD"),
                "confidence": 0.75,
                "expected_signal": test_case.input_data.get("expected_signal", "HOLD")
            },
            latency_ms=150.0
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get evaluation summary statistics."""
        if not self.results:
            return {}

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")

        # Aggregate metrics
        metric_averages = {}
        for metric in self.metrics:
            values = [r.metrics.get(metric.name(), 0.0) for r in self.results if r.metrics]
            if values:
                metric_averages[metric.name()] = sum(values) / len(values)

        avg_latency = sum(r.latency_ms for r in self.results) / total if total > 0 else 0.0

        return {
            "evaluation_name": self.name,
            "trace_id": self.trace_id,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": (passed / total * 100) if total > 0 else 0.0,
            "metrics": metric_averages,
            "average_latency_ms": avg_latency,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None
        }

    def save_results(self, filepath: str):
        """Save evaluation results to JSON file."""
        output = {
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results]
        }

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(
            f"Results saved to {filepath}",
            extra={"trace_id": self.trace_id}
        )

    def upload_to_firestore(self, firestore_client, collection: str = "evaluation_results"):
        """Upload evaluation results to Firestore for tracking."""
        summary = self.get_summary()
        doc_id = f"{self.trace_id}_{datetime.utcnow().isoformat()}"

        firestore_client.collection(collection).document(doc_id).set({
            "summary": summary,
            "timestamp": datetime.utcnow(),
            "result_count": len(self.results),
            "trace_id": self.trace_id
        })

        logger.info(
            f"Results uploaded to Firestore: {collection}/{doc_id}",
            extra={"trace_id": self.trace_id}
        )


# Example usage for testing
if __name__ == "__main__":
    # Create sample test cases
    test_cases = [
        TestCase(
            id="signal-test-001",
            name="NIFTY 50 Bull Signal",
            description="Test AI signal for NIFTY 50 in bullish market",
            input_data={
                "symbol": "NIFTY50",
                "price": 20500.0,
                "expected_signal": "BUY"
            }
        ),
        TestCase(
            id="signal-test-002",
            name="BANKNIFTY Bear Signal",
            description="Test AI signal for BANKNIFTY in bearish market",
            input_data={
                "symbol": "BANKNIFTY",
                "price": 45000.0,
                "expected_signal": "SELL"
            }
        ),
    ]

    # Create evaluation runner
    runner = EvaluationRunner(
        name="AI Signal Evaluation - Smoke Test",
        test_cases=test_cases,
        metrics=[SignalAccuracyMetric(), ConfidenceScoreMetric(), LatencyMetric(sla_ms=1000)]
    )

    # Run evaluation
    results = runner.run()

    # Print summary
    summary = runner.get_summary()
    print("\n=== Evaluation Summary ===")
    print(json.dumps(summary, indent=2))

    # Save results
    os.makedirs("backend/tests/evaluation/results", exist_ok=True)
    runner.save_results("backend/tests/evaluation/results/evaluation_results.json")
    print("✅ Evaluation framework ready for production")
