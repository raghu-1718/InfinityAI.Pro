"""
Minimal circuit breaker for Engine A
"""
import time
import threading
from dataclasses import dataclass
from enum import Enum


class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, half_open_max_calls: int = 3):
        self.config = CircuitBreakerConfig(failure_threshold, recovery_timeout, half_open_max_calls)
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = 0.0
        self._lock = threading.RLock()

    @property
    def status(self) -> str:
        return self._state.value

    def is_open(self) -> bool:
        return self._state == CircuitBreakerState.OPEN

    def record_success(self):
        with self._lock:
            if self._state == CircuitBreakerState.CLOSED:
                self._failure_count = 0
            elif self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= 1:
                    self._move_to_closed()

    def record_failure(self):
        with self._lock:
            if self._state == CircuitBreakerState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._move_to_open()
            elif self._state == CircuitBreakerState.HALF_OPEN:
                self._move_to_open()

    def reset(self):
        with self._lock:
            self._move_to_closed()

    def _move_to_open(self):
        self._state = CircuitBreakerState.OPEN
        self._last_failure_time = time.time()

    def _move_to_closed(self):
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
