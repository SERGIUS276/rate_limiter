import argparse
import time
from flask import Flask, request, jsonify

from rate_limiter.token_bucket import TokenBucketRateLimiter
from rate_limiter.memory_store import InMemoryStore
from rate_limiter.redis_store import RedisStore
from rate_limiter.config import RateLimitConfig
import redis

ROUTE_WEIGHTS = {
    ("GET", "/api/ping"): 1.0,
    ("POST", "/api/upload"): 3.0,
    ("GET", "/api/heavy-report"): 5.0,
}

app = Flask(__name__)

# Returns the weight of specified request from ROUTE_WEIGHTS dict
def get_request_weight(path: str, method: str) -> float:
    return ROUTE_WEIGHTS.get((method.upper(), path), 1.0)

@app.route("/api/ping")
def ping():
    client_ip = request.remote_addr
    limiter = app.config["rate_limiter"]
    storage_type = app.config["storage_type"]

    weight = get_request_weight(request.path, request.method)
    headers = limiter.get_headers(client_ip)

    if limiter.allow_request(client_ip, weight=weight):
        response = jsonify({
            "message": "pong",
            "remaining_tokens": float(headers["X-RateLimit-Remaining"]),
            "storage": storage_type,
            "used_weight": weight
        })
        response.status_code = 200
    else:
        response = jsonify({
            "error": "Too many requests",
            "retry_after": "wait a moment and try again",
            "storage": storage_type,
            "used_weight": weight
        })
        response.status_code = 429
        response.headers["Retry-After"] = "1"

    # Attach rate limit headers to the response
    for key, value in headers.items():
        response.headers[key] = value

    return response

@app.route("/api/upload", methods=["POST"])
def upload():
    client_ip = request.remote_addr
    limiter = app.config["rate_limiter"]
    storage_type = app.config["storage_type"]

    weight = get_request_weight(request.path, request.method)
    headers = limiter.get_headers(client_ip)

    if limiter.allow_request(client_ip, weight=weight):
        response = jsonify({
            "message": "upload accepted",
            "storage": storage_type,
            "used_weight": weight
        })
        response.status_code = 200
    else:
        response = jsonify({
            "error": "Too many requests",
            "storage": storage_type,
            "used_weight": weight
        })
        response.status_code = 429
        response.headers["Retry-After"] = "1"

    for key, value in headers.items():
        response.headers[key] = value

    return response


def main():
    parser = argparse.ArgumentParser(description="Rate Limiting Demo App")
    parser.add_argument("--use-redis", action="store_true", help="Enable Redis backend for rate limiting")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    config = RateLimitConfig(capacity=5, refill_rate=1.0)

    if args.use_redis:
        try:
            redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
            redis_client.ping()
            store = RedisStore(redis_client)
            print("✅ Using RedisStore backend.", flush=True)
            storage_type = "redis"
        except redis.ConnectionError:
            print("⚠️ Redis connection failed, falling back to InMemoryStore.", flush=True)
            store = InMemoryStore()
            storage_type = "regular"
    else:
        print("✅ Using InMemoryStore backend.", flush=True)
        store = InMemoryStore()
        storage_type = "regular"

    app.config["rate_limiter"] = TokenBucketRateLimiter(config=config, store=store)
    app.config["storage_type"] = storage_type

    app.run(debug=True, host=args.host, port=args.port)


if __name__ == "__main__":
    main()