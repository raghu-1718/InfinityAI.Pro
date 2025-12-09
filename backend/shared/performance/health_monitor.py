"""
Health Monitoring and Circuit Breaker for 24/7 Operation
Provides automatic failure detection and recovery.
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Callable, Any, List
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 3        # Successes to close from half-open
    timeout: float = 30.0             # Time in open state before half-open
    half_open_max_calls: int = 3      # Max calls allowed in half-open


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for service resilience.
    Prevents cascade failures and allows automatic recovery.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None, name: str = "default"):
        self.config = config or CircuitBreakerConfig()
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0

        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0,
            "state_changes": 0,
        }

        self._lock = asyncio.Lock()
        logger.info(f"✅ CircuitBreaker '{name}' initialized (threshold={self.config.failure_threshold})")

    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._stats["state_changes"] += 1
            logger.info(f"CircuitBreaker '{self.name}': {old_state.value} -> {new_state.value}")

            if new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
                self._success_count = 0

    async def can_execute(self) -> bool:
        """Check if request can be executed"""
        async with self._lock:
            self._stats["total_calls"] += 1

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if timeout has passed
                if time.monotonic() - self._last_failure_time >= self.config.timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True

                self._stats["rejected_calls"] += 1
                return False

            # Half-open state
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True

            self._stats["rejected_calls"] += 1
            return False

    async def record_success(self):
        """Record successful call"""
        async with self._lock:
            self._stats["successful_calls"] += 1

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    self._failure_count = 0
            else:
                self._failure_count = max(0, self._failure_count - 1)

    async def record_failure(self):
        """Record failed call"""
        async with self._lock:
            self._stats["failed_calls"] += 1
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    def get_stats(self) -> Dict:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            **self._stats,
        }


@dataclass
class ServiceHealth:
    """Service health status"""
    name: str
    healthy: bool
    latency_ms: float = 0.0
    last_check: float = field(default_factory=time.monotonic)
    error: Optional[str] = None
    consecutive_failures: int = 0


class HealthMonitor:
    """
    Monitors health of all services and provides automatic recovery.
    Essential for 24/7 operation.
    """

    _instance: Optional['HealthMonitor'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._services: Dict[str, ServiceHealth] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._health_checks: Dict[str, Callable] = {}
        self._check_interval = 30.0  # seconds
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable] = []
        self._lock = asyncio.Lock()
        self._initialized = True

        logger.info("✅ HealthMonitor initialized")

    def register_service(
        self,
        name: str,
        health_check: Callable,
        circuit_config: Optional[CircuitBreakerConfig] = None
    ):
        """Register a service for health monitoring"""
        self._services[name] = ServiceHealth(name=name, healthy=True)
        self._health_checks[name] = health_check
        self._circuit_breakers[name] = CircuitBreaker(circuit_config, name)
        logger.info(f"Registered service for monitoring: {name}")

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker for a service"""
        return self._circuit_breakers.get(name)

    async def check_service(self, name: str) -> ServiceHealth:
        """Check health of a specific service"""
        if name not in self._health_checks:
            return ServiceHealth(name=name, healthy=False, error="Service not registered")

        health_check = self._health_checks[name]
        start_time = time.monotonic()

        try:
            await asyncio.wait_for(health_check(), timeout=10.0)
            latency = (time.monotonic() - start_time) * 1000

            async with self._lock:
                self._services[name] = ServiceHealth(
                    name=name,
                    healthy=True,
                    latency_ms=latency,
                    consecutive_failures=0
                )

            # Record success in circuit breaker
            cb = self._circuit_breakers.get(name)
            if cb:
                await cb.record_success()

        except Exception as e:
            latency = (time.monotonic() - start_time) * 1000

            async with self._lock:
                prev = self._services.get(name, ServiceHealth(name=name, healthy=False))
                self._services[name] = ServiceHealth(
                    name=name,
                    healthy=False,
                    latency_ms=latency,
                    error=str(e),
                    consecutive_failures=prev.consecutive_failures + 1
                )

            # Record failure in circuit breaker
            cb = self._circuit_breakers.get(name)
            if cb:
                await cb.record_failure()

            logger.warning(f"Health check failed for {name}: {e}")

        return self._services[name]

    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all registered services"""
        tasks = [self.check_service(name) for name in self._health_checks.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)
        return self._services.copy()

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self._check_interval)
                await self.check_all_services()

                # Trigger callbacks for unhealthy services
                for name, health in self._services.items():
                    if not health.healthy:
                        for callback in self._callbacks:
                            try:
                                await callback(name, health)
                            except Exception as e:
                                logger.error(f"Health callback error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

    async def start_monitoring(self, interval: float = 30.0):
        """Start background health monitoring"""
        self._check_interval = interval
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            logger.info(f"Started health monitoring (interval={interval}s)")

    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped health monitoring")

    def on_unhealthy(self, callback: Callable):
        """Register callback for unhealthy service events"""
        self._callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        all_healthy = all(s.healthy for s in self._services.values())
        unhealthy = [n for n, s in self._services.items() if not s.healthy]

        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": {n: s.__dict__ for n, s in self._services.items()},
            "unhealthy_services": unhealthy,
            "circuit_breakers": {n: cb.get_stats() for n, cb in self._circuit_breakers.items()},
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton accessor
def get_health_monitor() -> HealthMonitor:
    """Get the singleton health monitor instance"""
    return HealthMonitor()


def with_circuit_breaker(service_name: str, fallback: Optional[Callable] = None):
    """
    Decorator that applies circuit breaker pattern to a function.

    Usage:
        @with_circuit_breaker("engine_b", fallback=get_cached_data)
        async def call_engine_b():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = get_health_monitor()
            cb = monitor.get_circuit_breaker(service_name)

            if cb is None:
                # No circuit breaker, execute directly
                return await func(*args, **kwargs)

            if not await cb.can_execute():
                if fallback:
                    logger.warning(f"Circuit open for {service_name}, using fallback")
                    return await fallback(*args, **kwargs)
                raise Exception(f"Service {service_name} is unavailable (circuit open)")

            try:
                result = await func(*args, **kwargs)
                await cb.record_success()
                return result
            except Exception as e:
                await cb.record_failure()
                raise

        return wrapper
    return decorator
