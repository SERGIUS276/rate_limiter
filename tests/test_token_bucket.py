import time
import unittest
from rate_limiter.token_bucket import TokenBucketRateLimiter
from rate_limiter.config import RateLimitConfig
from rate_limiter.memory_store import InMemoryStore


class TestTokenBucketRateLimiter(unittest.TestCase):
    def setUp(self):
        self.config = RateLimitConfig(capacity=5, refill_rate=1.0)  # 1 token/sec, 5 max
        self.store = InMemoryStore()
        self.limiter = TokenBucketRateLimiter(config=self.config, store=self.store)
        self.key = "test_user"

    def test_initial_allow(self):
        # Should allow up to 5 requests immediately
        for _ in range(5):
            self.assertTrue(self.limiter.allow_request(self.key))
        # 6th should be blocked
        self.assertFalse(self.limiter.allow_request(self.key))

    def test_refill_after_wait(self):
        # Exhaust tokens
        for _ in range(5):
            self.limiter.allow_request(self.key)
        self.assertFalse(self.limiter.allow_request(self.key))

        # Wait enough to refill one token
        time.sleep(1.1)
        self.assertTrue(self.limiter.allow_request(self.key))
        self.assertFalse(self.limiter.allow_request(self.key))  # Only one refilled

    def test_token_recovery_is_capped(self):
        # Exhaust tokens
        for _ in range(5):
            self.limiter.allow_request(self.key)
        time.sleep(10)  # Should refill > capacity
        self.assertTrue(self.limiter.allow_request(self.key))  # Should succeed
        # Still only max 5 tokens — cannot exceed capacity
        for _ in range(4):
            self.assertTrue(self.limiter.allow_request(self.key))
        self.assertFalse(self.limiter.allow_request(self.key))  # 6th blocked

    def test_get_remaining_tokens(self):
        self.assertEqual(self.limiter.get_remaining_tokens(self.key), 5)
        self.limiter.allow_request(self.key)
        remaining = self.limiter.get_remaining_tokens(self.key)
        self.assertTrue(remaining < 5)

    def test_get_headers_contains_correct_values(self):
        # Initially full
        headers = self.limiter.get_headers(self.key)

        self.assertIn("X-RateLimit-Limit", headers)
        self.assertIn("X-RateLimit-Remaining", headers)
        self.assertIn("X-RateLimit-Reset", headers)

        self.assertEqual(headers["X-RateLimit-Limit"], str(self.config.capacity))
        self.assertEqual(float(headers["X-RateLimit-Remaining"]), self.config.capacity)

        # Spend 1 token
        self.limiter.allow_request(self.key)

        headers_after = self.limiter.get_headers(self.key)
        remaining_after = float(headers_after["X-RateLimit-Remaining"])

        self.assertTrue(remaining_after < self.config.capacity)
        self.assertGreaterEqual(float(headers_after["X-RateLimit-Reset"]), 0)

if __name__ == "__main__":
    unittest.main()