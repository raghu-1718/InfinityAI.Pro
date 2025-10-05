"""
Circuit breaker implementation for Engine C
InfinityAI.Pro Trading Platform

Circuit breaker pattern implementation to prevent cascade failures
and provide graceful degradation when external services fail.
"""

import asyncio
import time
import logging
from typing import Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass
from contextlib import asynccontextmanager
import threading

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"           # Circuit is open, requests fail fast
    HALF_OPEN = "HALF_OPEN" # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5      # Number of failures to trigger open state
    recovery_timeout: int = 60      # Seconds before trying half-open state
    half_open_max_calls: int = 3    # Max calls allowed in half-open state
    success_threshold: int = 3      # Successes needed in half-open to close
    timeout: float = 30.0           # Request timeout in seconds


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker implementation with thread safety"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 half_open_max_calls: int = 3,
                 success_threshold: int = 3,
                 timeout: float = 30.0,
                 name: str = "CircuitBreaker"):
        
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
            success_threshold=success_threshold,
            timeout=timeout
        )
        
        self.name = name
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = 0
        self._lock = threading.RLock()
        
        logger.info(f"Circuit breaker '{self.name}' initialized with config: {self.config}")
    
    @property
    def state(self) -> CircuitBreakerState:
        """Get current state"""
        with self._lock:
            return self._state
    
    @property
    def status(self) -> str:
        """Get status string"""
        return self.state.value
    
    @property
    def failure_count(self) -> int:
        """Get current failure count"""
        with self._lock:
            return self._failure_count
    
    @property
    def success_count(self) -> int:
        """Get current success count"""
        with self._lock:
            return self._success_count
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed (normal operation)"""
        return self.state == CircuitBreakerState.CLOSED
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open (failing fast)"""
        return self.state == CircuitBreakerState.OPEN
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open (testing recovery)"""
        return self.state == CircuitBreakerState.HALF_OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from open to half-open"""
        if self._state != CircuitBreakerState.OPEN:
            return False
        
        time_since_failure = time.time() - self._last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _move_to_half_open(self):
        """Move circuit breaker to half-open state"""
        with self._lock:
            self._state = CircuitBreakerState.HALF_OPEN
            self._half_open_calls = 0
            self._success_count = 0
            
        logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN state")
    
    def _move_to_open(self):
        """Move circuit breaker to open state"""
        with self._lock:
            self._state = CircuitBreakerState.OPEN
            self._last_failure_time = time.time()
            
        logger.warning(f"Circuit breaker '{self.name}' moved to OPEN state after {self._failure_count} failures")
    
    def _move_to_closed(self):
        """Move circuit breaker to closed state"""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            
        logger.info(f"Circuit breaker '{self.name}' moved to CLOSED state")
    
    def _can_execute(self) -> bool:
        """Check if execution is allowed"""
        with self._lock:
            if self._state == CircuitBreakerState.CLOSED:
                return True
            
            elif self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._move_to_half_open()
                    return True
                return False
            
            elif self._state == CircuitBreakerState.HALF_OPEN:
                return self._half_open_calls < self.config.half_open_max_calls
            
            return False
    
    def record_success(self):
        """Record a successful operation"""
        with self._lock:
            if self._state == CircuitBreakerState.CLOSED:
                # Reset failure count on success in closed state
                self._failure_count = 0
                
            elif self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                
                # Check if we have enough successes to close
                if self._success_count >= self.config.success_threshold:
                    self._move_to_closed()
                    logger.info(f"Circuit breaker '{self.name}' recovered - moved to CLOSED")
        
        logger.debug(f"Circuit breaker '{self.name}' recorded success (failures: {self._failure_count}, successes: {self._success_count})")
    
    def record_failure(self):
        """Record a failed operation"""
        with self._lock:
            if self._state == CircuitBreakerState.CLOSED:
                self._failure_count += 1
                
                # Check if we should open
                if self._failure_count >= self.config.failure_threshold:
                    self._move_to_open()
                    
            elif self._state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open state moves back to open
                self._move_to_open()
                
        logger.debug(f"Circuit breaker '{self.name}' recorded failure (failures: {self._failure_count})")
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        with self._lock:
            old_state = self._state
            self._move_to_closed()
            
        logger.info(f"Circuit breaker '{self.name}' manually reset from {old_state.value} to CLOSED")
    
    def force_open(self):
        """Manually force circuit breaker to open state"""
        with self._lock:
            old_state = self._state
            self._move_to_open()
            
        logger.warning(f"Circuit breaker '{self.name}' manually forced from {old_state.value} to OPEN")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        with self._lock:
            return {
                'name': self.name,
                'state': self._state.value,
                'failure_count': self._failure_count,
                'success_count': self._success_count,
                'half_open_calls': self._half_open_calls,
                'last_failure_time': self._last_failure_time,
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout': self.config.recovery_timeout,
                    'half_open_max_calls': self.config.half_open_max_calls,
                    'success_threshold': self.config.success_threshold,
                    'timeout': self.config.timeout
                }
            }
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker"""
        
        def wrapper(*args, **kwargs):
            if not self._can_execute():
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is {self._state.value}")
            
            # Track half-open calls
            if self._state == CircuitBreakerState.HALF_OPEN:
                with self._lock:
                    self._half_open_calls += 1
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
                
            except Exception as e:
                self.record_failure()
                raise
        
        return wrapper
    
    @asynccontextmanager
    async def async_call(self):
        """Async context manager for circuit breaker protection"""
        if not self._can_execute():
            raise CircuitBreakerError(f"Circuit breaker '{self.name}' is {self._state.value}")
        
        # Track half-open calls
        if self._state == CircuitBreakerState.HALF_OPEN:
            with self._lock:
                self._half_open_calls += 1
        
        try:
            yield
            self.record_success()
            
        except Exception as e:
            self.record_failure()
            raise
    
    async def execute_async(self, coro):
        """Execute async coroutine with circuit breaker protection"""
        async with self.async_call():
            return await coro


class CircuitBreakerManager:
    """Manager for multiple circuit breakers"""
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_or_create(self, name: str, **config) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name=name, **config)
            return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        with self._lock:
            return self._breakers.get(name)
    
    def reset_all(self):
        """Reset all circuit breakers"""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
        
        logger.info("All circuit breakers reset")
    
    def get_all_stats(self) -> dict:
        """Get stats for all circuit breakers"""
        with self._lock:
            return {
                name: breaker.get_stats() 
                for name, breaker in self._breakers.items()
            }
    
    def get_health_status(self) -> dict:
        """Get health status summary"""
        with self._lock:
            total_breakers = len(self._breakers)
            open_breakers = sum(1 for b in self._breakers.values() if b.is_open())
            half_open_breakers = sum(1 for b in self._breakers.values() if b.is_half_open())
            
            return {
                'total_breakers': total_breakers,
                'open_breakers': open_breakers,
                'half_open_breakers': half_open_breakers,
                'closed_breakers': total_breakers - open_breakers - half_open_breakers,
                'overall_health': 'healthy' if open_breakers == 0 else 'degraded' if open_breakers < total_breakers else 'unhealthy'
            }


# Global circuit breaker manager
_global_manager = CircuitBreakerManager()


def get_circuit_breaker(name: str, **config) -> CircuitBreaker:
    """Get or create a circuit breaker with given name and configuration"""
    return _global_manager.get_or_create(name, **config)


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager"""
    return _global_manager


# Decorator functions
def circuit_breaker(name: str = None, **config):
    """Decorator to apply circuit breaker to a function"""
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        breaker = get_circuit_breaker(breaker_name, **config)
        return breaker(func)
    
    return decorator


def async_circuit_breaker(name: str = None, **config):
    """Decorator to apply circuit breaker to an async function"""
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        breaker = get_circuit_breaker(breaker_name, **config)
        
        async def wrapper(*args, **kwargs):
            async with breaker.async_call():
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Export commonly used classes and functions
__all__ = [
    "CircuitBreaker",
    "CircuitBreakerState", 
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerManager",
    "get_circuit_breaker",
    "get_circuit_breaker_manager",
    "circuit_breaker",
    "async_circuit_breaker"
]