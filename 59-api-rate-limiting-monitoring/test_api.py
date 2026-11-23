"""
Automated unit and integration tests for API Rate Limiting & Monitoring System.
"""
import unittest
import os
import tempfile
from fastapi.testclient import TestClient
import app as app_module
from database import init_db
from api_service import APIService
from rate_limiter import SlidingWindowRateLimiter


class TestAPIRateLimiter(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Wire up a fresh isolated service and rate limiter
        app_module.service = APIService(self.db_path)
        app_module.limiter = SlidingWindowRateLimiter(window_seconds=60)
        self.client = TestClient(app_module.app)

        # Register test user with 'free' tier (limit = 5 req/min)
        res = self.client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "email": "test@example.com", "tier": "free"}
        )
        self.assertEqual(res.status_code, 201)
        self.api_key = res.json()["data"]["api_key"]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_missing_api_key_header_unauthorized(self):
        res = self.client.get("/api/v1/data/ping")
        self.assertEqual(res.status_code, 401)
        self.assertIn("Missing required 'X-API-Key' header", res.json()["detail"])

    def test_invalid_api_key_forbidden(self):
        res = self.client.get("/api/v1/data/ping", headers={"X-API-Key": "ak_invalid_12345"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("Invalid or revoked API key", res.json()["detail"])

    def test_successful_request_with_rate_limit_headers(self):
        res = self.client.get("/api/v1/data/ping", headers={"X-API-Key": self.api_key})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"], "testuser")
        self.assertIn("X-RateLimit-Limit", res.headers)
        self.assertEqual(res.headers["X-RateLimit-Limit"], "5")
        self.assertEqual(res.headers["X-RateLimit-Remaining"], "4")

    def test_rate_limit_breach_returns_429_with_retry_after(self):
        headers = {"X-API-Key": self.api_key}

        # Exhaust 5 allowed requests
        for i in range(5):
            res = self.client.get("/api/v1/data/ping", headers=headers)
            self.assertEqual(res.status_code, 200)

        # 6th request must trigger HTTP 429
        res_throttled = self.client.get("/api/v1/data/ping", headers=headers)
        self.assertEqual(res_throttled.status_code, 429)
        self.assertIn("Rate limit exceeded", res_throttled.json()["detail"])
        self.assertIn("Retry-After", res_throttled.headers)
        self.assertGreaterEqual(int(res_throttled.headers["Retry-After"]), 1)

    def test_rate_limiter_reset(self):
        headers = {"X-API-Key": self.api_key}
        for _ in range(5):
            self.client.get("/api/v1/data/ping", headers=headers)

        res_throttled = self.client.get("/api/v1/data/ping", headers=headers)
        self.assertEqual(res_throttled.status_code, 429)

        # Reset limiter for this key
        app_module.limiter.reset_key(self.api_key)

        res_after_reset = self.client.get("/api/v1/data/ping", headers=headers)
        self.assertEqual(res_after_reset.status_code, 200)

    def test_usage_metrics_tracking(self):
        headers = {"X-API-Key": self.api_key}
        for _ in range(5):
            self.client.get("/api/v1/data/ping", headers=headers)
        self.client.get("/api/v1/data/ping", headers=headers)  # 6th is throttled

        # Reset in-memory window for this key so the metrics inquiry itself can be serviced
        app_module.limiter.reset_key(self.api_key)

        res = self.client.get("/api/v1/metrics/usage", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["tier"], "free")
        self.assertEqual(data["rate_limit_per_minute"], 5)
        self.assertGreaterEqual(data["successful_requests"], 5)
        self.assertGreaterEqual(data["throttled_requests"], 1)

    def test_admin_dashboard(self):
        headers = {"X-API-Key": self.api_key}
        self.client.get("/api/v1/data/ping", headers=headers)

        res = self.client.get("/api/v1/admin/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_users"], 1)
        self.assertGreaterEqual(data["total_keys"], 1)
        self.assertGreaterEqual(data["total_requests"], 1)


if __name__ == "__main__":
    unittest.main()
