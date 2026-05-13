"""Tests for rate limiting middleware."""
import pytest
from fastapi.testclient import TestClient


class TestRateLimiter:
    def test_health_exempt_from_rate_limit(self, client: TestClient):
        for _ in range(100):
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_rate_limit_headers_present(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/executive/summary", headers=auth_headers)
        if resp.status_code != 429:
            assert "X-RateLimit-Limit" in resp.headers
            assert "X-RateLimit-Remaining" in resp.headers

    def test_root_exempt_from_rate_limit(self, client: TestClient):
        for _ in range(100):
            resp = client.get("/")
            assert resp.status_code == 200
