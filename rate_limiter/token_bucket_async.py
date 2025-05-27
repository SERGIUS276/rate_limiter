import time
from rate_limiter.config import RateLimitConfig
from rate_limiter.interfaces import IAsyncRateLimitStore


class AsyncTokenBucketRateLimiter:
    def __init__(self, config: RateLimitConfig, store: IAsyncRateLimitStore):
        self.config = config
        self.store = store

    async def allow_request(self, key: str, weight: float = 1.0) -> bool:
        state = await self.store.get_state(key)
        now = time.time()

        tokens = state["tokens"]
        last_refill = state["last_refill"]

        if tokens is None:
            tokens = self.config.capacity
            last_refill = now

        # refill logic
        elapsed = now - last_refill
        refill = elapsed * self.config.refill_rate
        tokens = min(self.config.capacity, tokens + refill)

        if tokens >= weight:
            tokens -= weight
            await self.store.set_state(key, tokens, now)
            return True
        else:
            await self.store.set_state(key, tokens, now)
            return False

    async def get_remaining_tokens(self, key: str) -> float:
        state = await self.store.get_state(key)
        now = time.time()

        tokens = state["tokens"]
        last_refill = state["last_refill"]

        if tokens is None:
            tokens = self.config.capacity
            last_refill = now

        elapsed = now - last_refill
        refill = elapsed * self.config.refill_rate
        tokens = min(self.config.capacity, tokens + refill)
        return tokens

    async def get_headers(self, key: str) -> dict:
        remaining = await self.get_remaining_tokens(key)
        return {
            "X-RateLimit-Limit": str(self.config.capacity),
            "X-RateLimit-Remaining": str(round(remaining, 2)),
            "X-RateLimit-Reset": str(round((self.config.capacity - remaining) / self.config.refill_rate, 2))
        }