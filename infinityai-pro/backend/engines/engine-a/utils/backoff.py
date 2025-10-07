"""
Minimal exponential backoff for Engine A
"""
from dataclasses import dataclass


@dataclass
class BackoffConfig:
	base_delay: float = 1.0
	max_delay: float = 60.0
	max_retries: int = 5
	multiplier: float = 2.0


class ExponentialBackoff:
	def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, max_retries: int = 5, multiplier: float = 2.0):
		self.config = BackoffConfig(base_delay, max_delay, max_retries, multiplier)

	@property
	def base_delay(self) -> float:
		return self.config.base_delay

	@property
	def max_delay(self) -> float:
		return self.config.max_delay

	@property
	def max_retries(self) -> int:
		return self.config.max_retries

	def calculate_delay(self, attempt: int) -> float:
		delay = self.config.base_delay * (self.config.multiplier ** attempt)
		return min(delay, self.config.max_delay)