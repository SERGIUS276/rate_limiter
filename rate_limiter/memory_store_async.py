import time
from asyncio import Lock
from rate_limiter.interfaces import IAsyncRateLimitStore


class AsyncInMemoryStore(IAsyncRateLimitStore):
    def __init__(self):
        self._store = {}
        self._lock = Lock()

    def _make_key(self, key: str) -> str:
        return f"ratelimit:{key}"

    async def get_state(self, key: str):
        async with self._lock:
            redis_key = self._make_key(key)
            state = self._store.get(redis_key)

            if state is None:
                return {"tokens": None, "last_refill": time.time()}

            return state

    async def set_state(self, key: str, tokens: float, last_refill: float):
        async with self._lock:
            redis_key = self._make_key(key)
            self._store[redis_key] = {
                "tokens": tokens,
                "last_refill": last_refill
            }