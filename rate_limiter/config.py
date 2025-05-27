from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    capacity: int
    refill_rate: float  # tokens per second
    tokens_per_request: float = 1.0
