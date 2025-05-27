import time
import redis
from threading import Lock


class RedisStore:
    def __init__(self, redis_client: redis.Redis, prefix: str = "ratelimit"):
        self.redis = redis_client
        self.prefix = prefix
        self.lock = Lock()

    def _make_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get_state(self, key: str):
        redis_key = self._make_key(key)
        pipe = self.redis.pipeline()
        pipe.hget(redis_key, "tokens")
        pipe.hget(redis_key, "last_refill")
        tokens, last_refill = pipe.execute()

        # Convert if exists, else set default
        tokens = float(tokens) if tokens is not None else None
        last_refill = float(last_refill) if last_refill is not None else time.time()

        return {
            "tokens": tokens,
            "last_refill": last_refill
        }

    def set_state(self, key: str, tokens: float, last_refill: float):
        redis_key = self._make_key(key)
        pipe = self.redis.pipeline()
        pipe.hset(redis_key, mapping={
            "tokens": tokens,
            "last_refill": last_refill
        })
        pipe.expire(redis_key, 3600)  # TTL of 1 hour
        pipe.execute()