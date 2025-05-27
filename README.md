# Rate Limiter with Token Bucket Algorithm 🚦

This project provides a **pluggable, async-compatible rate limiting system** built using the **Token Bucket algorithm**, with demonstraiton on both **Flask** and **FastAPI** backends.

---

## 🚀 Features

- ⚙️ Backend-agnostic: Both **Flask** and **FastAPI** demos
- 🪣 Efficient **Token Bucket Algorithm**
- 💾 Supports **in-memory** and **Redis** storage
- 🐳 **Docker & Docker Compose** ready
- 📈 Logging and custom headers for observability

---

### 📖 Algorithm Overview: Token Bucket with Greedy Refiller

This project uses the **Token Bucket algorithm** with a **greedy refill strategy**.

- Each client is assigned a **"bucket"** with a fixed capacity (e.g. 5 tokens).
- **Requests consume tokens** based on their "weight" (e.g. upload = 3 tokens).
- **Tokens refill instantly** based on elapsed time since the last request (greedy refill), at a fixed rate (e.g. 1 token/sec).
- If there aren’t enough tokens, the request is rejected with **HTTP 429**.
- After a short wait (as indicated by the `Retry-After` header), tokens will replenish.

This approach is **efficient** and **accurate** for APIs, allowing:
- 🟢 Short bursts within limits (burst tolerance)
- 🔴 Rejection of excessive or abusive traffic

> This is ideal for **real-time APIs** that require fairness while permitting some flexibility.



The core algorithmic approach implemented in this project is inspired by the following article:  
👉 [Implementing an Async Rate Limiter in Python](https://rdiachenko.com/posts/arch/rate-limiting/token-bucket-algorithm/#common-use-cases)

---

## 🛠 Installation (Manual)

### Clone and install with Poetry:
```bash
git clone https://github.com/SERGIUS276/rate_limiter.git
cd rate_limiter
poetry install
```

### Run FastAPI:
```bash
poetry run uvicorn demo.fastapi.app:app --host 127.0.0.1 --port 5000 --reload
```

### Run Flask:
```bash
poetry run python demo/flaskapp/app.py --use-redis
```

## 🧪 Test the Endpoints

### Ping:
```bash
curl http://localhost:5000/api/ping
```

### Upload (heavier weight)::
```bash
curl -X POST http://localhost:5000/api/upload
```

## 🔧 Integrating Into Your Own App

You can use the core AsyncTokenBucketRateLimiter or TokenBucketRateLimiter in your own app like this:

```bash
from rate_limiter.token_bucket_async import AsyncTokenBucketRateLimiter
from rate_limiter.redis_store_async import AsyncRedisStore
from rate_limiter.config import RateLimitConfig
import redis.asyncio as redis

# Initialize config
config = RateLimitConfig(capacity=10, refill_rate=1.0)

# Use Redis or in-memory store
redis_client = redis.Redis(host="localhost", port=6379)
store = AsyncRedisStore(redis_client)

# Initialize rate limiter
limiter = AsyncTokenBucketRateLimiter(config, store)

# Then use limiter.allow_request(client_id)
```

> **P.S.**: Unfortunately, Redis functionality currently does **not** work with `AsyncTokenBucketRateLimiter` due to issues with async Redis client integration. The rate limiter will fall back to in-memory storage when Redis is unavailable.
