import time
from rate_limiter.interfaces import IRateLimiter
from rate_limiter.config import RateLimitConfig
from rate_limiter.memory_store import InMemoryStore


class TokenBucketRateLimiter(IRateLimiter):
    def __init__(self, config: RateLimitConfig, store: InMemoryStore):
        self.config = config
        self.store = store

    def allow_request(self, key: str, weight: float = 1.0) -> bool:
        state = self.store.get_state(key)
        now = time.time()

        tokens = state["tokens"]
        last_refill = state["last_refill"]

        if tokens is None:
            tokens = self.config.capacity
            last_refill = now

        # Refill based on elapsed time
        elapsed = now - last_refill
        refill = elapsed * self.config.refill_rate
        tokens = min(self.config.capacity, tokens + refill)

        if tokens >= weight:
            tokens -= weight
            self.store.set_state(key, tokens, now)
            return True
        else:
            self.store.set_state(key, tokens, now)
            return False

    def get_remaining_tokens(self, key: str) -> float:
        state = self.store.get_state(key)
        now = time.time()

        tokens = state["tokens"]
        last_refill = state["last_refill"]

        if tokens is None:
            return self.config.capacity

        elapsed = now - last_refill
        refill = elapsed * self.config.refill_rate
        tokens = min(self.config.capacity, tokens + refill)
        return tokens

    def get_headers(self, key: str) -> dict:
        state = self.store.get_state(key)
        tokens = state["tokens"]
        last_refill = state["last_refill"]

        now = time.time()
        elapsed = now - last_refill
        refill = elapsed * self.config.refill_rate

        #If tokens value wasn't set before calling the get_headers function, assume full capacity
        if tokens is None:
            tokens = self.config.capacity

        tokens = min(self.config.capacity, tokens + refill)
        remaining = max(0, tokens)

        if self.config.refill_rate > 0:
            reset_time = (self.config.capacity - tokens) / self.config.refill_rate
        else:
            reset_time = 0

        return {
            "X-RateLimit-Limit": str(self.config.capacity),
            "X-RateLimit-Remaining": str(round(remaining, 2)),
            "X-RateLimit-Reset": str(round(reset_time, 2))
        }