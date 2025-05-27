import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from rate_limiter.config import RateLimitConfig
from rate_limiter.token_bucket_async import AsyncTokenBucketRateLimiter
from rate_limiter.memory_store_async import AsyncInMemoryStore
from rate_limiter.redis_store_async import AsyncRedisStore
import logging

logging.basicConfig(
    filename="ratelimit.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    filemode="a"
)
logger = logging.getLogger("ratelimiter")
app = FastAPI()
limiter = None
storage_type = "unknown"

@app.on_event("startup")
async def setup_rate_limiter():
    global limiter, storage_type
    config = RateLimitConfig(capacity=5, refill_rate=1.0)

    try:
        redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        await redis_client.ping()
        limiter = AsyncTokenBucketRateLimiter(config, AsyncRedisStore(redis_client))
        storage_type = "redis"
        print("✅ Using AsyncRedisStore backend.")
    except Exception as e:
        limiter = AsyncTokenBucketRateLimiter(config, AsyncInMemoryStore())
        storage_type = "memory"
        print(f"⚠️ Redis unavailable: {e}. Using AsyncInMemoryStore.")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    global limiter, storage_type

    if limiter is None:
        return JSONResponse(status_code=500, content={"error": "Rate limiter not initialized"})

    client_ip = request.client.host
    path = request.url.path
    method = request.method

    weight = 1.0
    if path == "/api/upload" and method == "POST":
        weight = 3.0

    headers = await limiter.get_headers(client_ip)

    if not await limiter.allow_request(client_ip, weight=weight):
        headers["Retry-After"] = "1"
        logger.info(f"[BLOCKED] {client_ip} on {path} | remaining={headers.get('X-RateLimit-Remaining')}")

        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests",
                "retry_after": "wait a moment and try again",
                "storage": storage_type
            },
            headers=headers
        )

    logger.info(f"[ALLOWED] {client_ip} on {path} | remaining={headers.get('X-RateLimit-Remaining')}")

    response = await call_next(request)
    for key, value in headers.items():
        response.headers[key] = value
    response.headers["X-Storage-Type"] = storage_type

    return response

@app.get("/api/stats")
async def get_stats(ip: str):
    if limiter is None:
        return JSONResponse(status_code=500, content={"error": "Limiter not initialized"})

    headers = await limiter.get_headers(ip)
    return {
        "ip": ip,
        "remaining_tokens": headers["X-RateLimit-Remaining"],
        "limit": headers["X-RateLimit-Limit"],
        "reset": headers["X-RateLimit-Reset"]
    }

@app.get("/api/ping")
async def ping():
    return {"message": "pong"}


@app.post("/api/upload")
async def upload():
    return {"message": "upload accepted"}


