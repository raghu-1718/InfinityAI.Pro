"""
Exponential backoff utility for Engine C
InfinityAI.Pro Trading Platform

Exponential backoff implementation with jitter to prevent thundering herd
problems when retrying failed operations like broker API calls.
"""

import asyncio
import random
import time
import logging
from typing import Optional, Callable, Any, Union
from dataclasses import dataclass
from enum import Enum
import functools

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Backoff strategy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    FIBONACCI = "fibonacci"


class JitterType(Enum):
    """Jitter types for randomization"""
    NONE = "none"
    FULL = "full"
    EQUAL = "equal"
    DECORRELATED = "decorrelated"


@dataclass
class BackoffConfig:
    """Configuration for backoff behavior"""
    base_delay: float = 1.0          # Base delay in seconds
    max_delay: float = 60.0          # Maximum delay in seconds
    max_retries: int = 5             # Maximum number of retries
    multiplier: float = 2.0          # Backoff multiplier
    jitter_type: JitterType = JitterType.FULL
    strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL


class ExponentialBackoff:
    """Exponential backoff with configurable jitter and strategies"""
    
    def __init__(self,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 max_retries: int = 5,
                 multiplier: float = 2.0,
                 jitter_type: JitterType = JitterType.FULL,
                 strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL):
        
        self.config = BackoffConfig(
            base_delay=base_delay,
            max_delay=max_delay,
            max_retries=max_retries,
            multiplier=multiplier,
            jitter_type=jitter_type,
            strategy=strategy
        )
        
        self._reset()
        
        logger.debug(f"ExponentialBackoff initialized with config: {self.config}")
    
    def _reset(self):
        """Reset internal state"""
        self._attempt = 0
        self._last_delay = 0
    
    @property
    def base_delay(self) -> float:
        return self.config.base_delay
    
    @property
    def max_delay(self) -> float:
        return self.config.max_delay
    
    @property
    def max_retries(self) -> int:
        return self.config.max_retries
    
    @property
    def multiplier(self) -> float:
        return self.config.multiplier
    
    @property
    def attempt(self) -> int:
        return self._attempt
    
    def calculate_delay(self, attempt: int = None) -> float:
        """
        Calculate delay for given attempt number
        
        Args:
            attempt: Attempt number (0-based). If None, uses internal counter.
            
        Returns:
            Delay in seconds
        """
        if attempt is None:
            attempt = self._attempt
            self._attempt += 1
        
        # Calculate base delay using selected strategy
        if self.config.strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.multiplier ** attempt)
            
        elif self.config.strategy == BackoffStrategy.LINEAR:
            delay = self.config.base_delay * (1 + attempt)
            
        elif self.config.strategy == BackoffStrategy.FIXED:
            delay = self.config.base_delay
            
        elif self.config.strategy == BackoffStrategy.FIBONACCI:
            delay = self.config.base_delay * self._fibonacci(attempt + 1)
            
        else:
            delay = self.config.base_delay * (self.config.multiplier ** attempt)
        
        # Apply maximum delay cap
        delay = min(delay, self.config.max_delay)
        
        # Apply jitter
        delay = self._apply_jitter(delay, attempt)
        
        self._last_delay = delay
        
        logger.debug(f"Calculated backoff delay: {delay:.2f}s for attempt {attempt}")
        
        return delay
    
    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number"""
        if n <= 1:
            return n
        
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        
        return b
    
    def _apply_jitter(self, delay: float, attempt: int) -> float:
        """Apply jitter to delay based on configured jitter type"""
        
        if self.config.jitter_type == JitterType.NONE:
            return delay
        
        elif self.config.jitter_type == JitterType.FULL:
            # Random delay between 0 and calculated delay
            return random.uniform(0, delay)
        
        elif self.config.jitter_type == JitterType.EQUAL:
            # Half the delay plus random half
            base = delay / 2
            return base + random.uniform(0, base)
        
        elif self.config.jitter_type == JitterType.DECORRELATED:
            # Decorrelated jitter based on previous delay
            if attempt == 0:
                return random.uniform(0, delay)
            else:
                # Use last delay for decorrelation
                return random.uniform(self.config.base_delay, self._last_delay * 3)
        
        return delay
    
    def reset(self):
        """Reset backoff state"""
        self._reset()
        logger.debug("ExponentialBackoff state reset")
    
    def should_retry(self, attempt: int = None) -> bool:
        """Check if we should retry based on max_retries"""
        check_attempt = attempt if attempt is not None else self._attempt
        return check_attempt < self.config.max_retries
    
    def get_stats(self) -> dict:
        """Get backoff statistics"""
        return {
            'attempt': self._attempt,
            'last_delay': self._last_delay,
            'config': {
                'base_delay': self.config.base_delay,
                'max_delay': self.config.max_delay,
                'max_retries': self.config.max_retries,
                'multiplier': self.config.multiplier,
                'jitter_type': self.config.jitter_type.value,
                'strategy': self.config.strategy.value
            }
        }


class RetryableError(Exception):
    """Base exception for retryable errors"""
    pass


class NonRetryableError(Exception):
    """Exception for non-retryable errors"""
    pass


def retry_with_backoff(
    backoff: ExponentialBackoff = None,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = (),
    on_retry: Optional[Callable] = None,
    on_failure: Optional[Callable] = None
):
    """
    Decorator to add retry with exponential backoff to a function
    
    Args:
        backoff: ExponentialBackoff instance. If None, uses default config.
        retryable_exceptions: Tuple of exceptions that should trigger retry
        non_retryable_exceptions: Tuple of exceptions that should not trigger retry
        on_retry: Callback called on each retry (attempt, exception, delay)
        on_failure: Callback called when all retries are exhausted (exception)
    """
    
    if backoff is None:
        backoff = ExponentialBackoff()
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            backoff.reset()
            last_exception = None
            
            for attempt in range(backoff.max_retries + 1):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                    
                except non_retryable_exceptions as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == backoff.max_retries:
                        # Final attempt failed
                        logger.error(f"All retry attempts exhausted for {func.__name__}")
                        if on_failure:
                            on_failure(e)
                        raise
                    
                    # Calculate delay and sleep
                    delay = backoff.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    if on_retry:
                        on_retry(attempt, e, delay)
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


def async_retry_with_backoff(
    backoff: ExponentialBackoff = None,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = (),
    on_retry: Optional[Callable] = None,
    on_failure: Optional[Callable] = None
):
    """
    Decorator to add retry with exponential backoff to an async function
    
    Args:
        backoff: ExponentialBackoff instance. If None, uses default config.
        retryable_exceptions: Tuple of exceptions that should trigger retry
        non_retryable_exceptions: Tuple of exceptions that should not trigger retry
        on_retry: Callback called on each retry (attempt, exception, delay)
        on_failure: Callback called when all retries are exhausted (exception)
    """
    
    if backoff is None:
        backoff = ExponentialBackoff()
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            backoff.reset()
            last_exception = None
            
            for attempt in range(backoff.max_retries + 1):  # +1 for initial attempt
                try:
                    return await func(*args, **kwargs)
                    
                except non_retryable_exceptions as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == backoff.max_retries:
                        # Final attempt failed
                        logger.error(f"All retry attempts exhausted for {func.__name__}")
                        if on_failure:
                            if asyncio.iscoroutinefunction(on_failure):
                                await on_failure(e)
                            else:
                                on_failure(e)
                        raise
                    
                    # Calculate delay and sleep
                    delay = backoff.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    if on_retry:
                        if asyncio.iscoroutinefunction(on_retry):
                            await on_retry(attempt, e, delay)
                        else:
                            on_retry(attempt, e, delay)
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


class RetryManager:
    """Manager for retry operations with different backoff strategies"""
    
    def __init__(self):
        self._backoffs: dict[str, ExponentialBackoff] = {}
    
    def get_or_create_backoff(self, name: str, **config) -> ExponentialBackoff:
        """Get existing backoff or create new one"""
        if name not in self._backoffs:
            self._backoffs[name] = ExponentialBackoff(**config)
        return self._backoffs[name]
    
    def reset_backoff(self, name: str):
        """Reset specific backoff"""
        if name in self._backoffs:
            self._backoffs[name].reset()
    
    def reset_all(self):
        """Reset all backoffs"""
        for backoff in self._backoffs.values():
            backoff.reset()
    
    def get_stats(self) -> dict:
        """Get stats for all backoffs"""
        return {
            name: backoff.get_stats()
            for name, backoff in self._backoffs.items()
        }


# Global retry manager
_global_retry_manager = RetryManager()


def get_backoff(name: str, **config) -> ExponentialBackoff:
    """Get or create a named backoff instance"""
    return _global_retry_manager.get_or_create_backoff(name, **config)


def reset_backoff(name: str):
    """Reset a named backoff instance"""
    _global_retry_manager.reset_backoff(name)


def reset_all_backoffs():
    """Reset all backoff instances"""
    _global_retry_manager.reset_all()


def get_retry_stats() -> dict:
    """Get stats for all backoff instances"""
    return _global_retry_manager.get_stats()


# Convenience functions for common retry patterns
def broker_api_backoff() -> ExponentialBackoff:
    """Get backoff configuration optimized for broker API calls"""
    return ExponentialBackoff(
        base_delay=1.0,
        max_delay=30.0,
        max_retries=5,
        multiplier=2.0,
        jitter_type=JitterType.EQUAL,
        strategy=BackoffStrategy.EXPONENTIAL
    )


def database_backoff() -> ExponentialBackoff:
    """Get backoff configuration optimized for database operations"""
    return ExponentialBackoff(
        base_delay=0.5,
        max_delay=10.0,
        max_retries=3,
        multiplier=2.0,
        jitter_type=JitterType.FULL,
        strategy=BackoffStrategy.EXPONENTIAL
    )


def kafka_backoff() -> ExponentialBackoff:
    """Get backoff configuration optimized for Kafka operations"""
    return ExponentialBackoff(
        base_delay=2.0,
        max_delay=60.0,
        max_retries=10,
        multiplier=1.5,
        jitter_type=JitterType.DECORRELATED,
        strategy=BackoffStrategy.EXPONENTIAL
    )


# Export commonly used classes and functions
__all__ = [
    "ExponentialBackoff",
    "BackoffConfig",
    "BackoffStrategy",
    "JitterType",
    "RetryableError",
    "NonRetryableError",
    "retry_with_backoff",
    "async_retry_with_backoff",
    "RetryManager",
    "get_backoff",
    "reset_backoff",
    "reset_all_backoffs",
    "get_retry_stats",
    "broker_api_backoff",
    "database_backoff",
    "kafka_backoff"
]