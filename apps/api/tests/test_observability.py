"""Tests for observability: metrics, error handling, logging."""
import pytest
from fastapi.testclient import TestClient

from observability.metrics import MetricsCollector


class TestMetricsCollector:
    def test_record_request(self):
        mc = MetricsCollector()
        mc.record_request("/api/v1/executive/summary", 45.2, 200)
        mc.record_request("/api/v1/executive/summary", 120.5, 200)
        mc.record_request("/api/v1/executive/summary", 500.0, 500)

        stats = mc.get_stats()
        assert stats["total_requests"] == 3
        assert stats["total_errors"] == 1
        assert stats["error_rate_pct"] == pytest.approx(33.33, rel=0.1)

    def test_path_normalization(self):
        mc = MetricsCollector()
        mc.record_request("/api/v1/auth/api-keys/12345678-1234-1234-1234-123456789012", 10, 200)
        stats = mc.get_stats()
        assert "/api/v1/auth/api-keys/:id" in stats["endpoints"]

    def test_percentiles(self):
        mc = MetricsCollector()
        for i in range(100):
            mc.record_request("/test", float(i), 200)
        stats = mc.get_stats()
        endpoint = stats["endpoints"]["/test"]
        assert endpoint["p50_ms"] == pytest.approx(50, abs=2)
        assert endpoint["p95_ms"] == pytest.approx(95, abs=2)

    def test_empty_stats(self):
        mc = MetricsCollector()
        stats = mc.get_stats()
        assert stats["total_requests"] == 0
        assert stats["error_rate_pct"] == 0


class TestErrorHandlers:
    def test_validation_error_format(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/executive/mrr-trend?months=0", headers=auth_headers)
        assert resp.status_code == 422
        data = resp.json()
        assert "details" in data or "detail" in data

    def test_404_returns_json(self, client: TestClient):
        resp = client.get("/nonexistent/path")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data


class TestMetricsEndpoint:
    def test_metrics_endpoint_accessible(self, client: TestClient):
        client.get("/health")
        client.get("/")
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "uptime_seconds" in data
        assert "endpoints" in data
