import time
from redis.asyncio import Redis
from rate_limiter.interfaces import IAsyncRateLimitStore


class AsyncRedisStore(IAsyncRateLimitStore):
    def __init__(self, redis_url="redis://localhost", prefix: str = "ratelimit"):
        self.redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get_state(self, key: str):
        redis_key = self._make_key(key)
        pipe = self.redis.pipeline()
        pipe.hget(redis_key, "tokens")
        pipe.hget(redis_key, "last_refill")
        tokens, last_refill = await pipe.execute()

        tokens = float(tokens) if tokens else None
        last_refill = float(last_refill) if last_refill else time.time()

        return {
            "tokens": tokens,
            "last_refill": last_refill
        }

    async def set_state(self, key: str, tokens: float, last_refill: float):
        redis_key = self._make_key(key)
        pipe = self.redis.pipeline()
        pipe.hset(redis_key, mapping={
            "tokens": tokens,
            "last_refill": last_refill
        })
        pipe.expire(redis_key, 3600)
        await pipe.execute()