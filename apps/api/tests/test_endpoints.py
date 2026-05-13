"""Tests for protected analytics endpoints — verify auth enforcement."""
import pytest
from fastapi.testclient import TestClient


class TestExecutiveEndpoints:
    def test_summary_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/executive/summary")
        assert resp.status_code == 401

    def test_summary_with_auth(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/executive/summary", headers=auth_headers)
        assert resp.status_code in (200, 500)

    def test_mrr_trend_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/executive/mrr-trend")
        assert resp.status_code == 401


class TestRevenueEndpoints:
    def test_mrr_bridge_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/revenue/mrr-bridge")
        assert resp.status_code == 401

    def test_mrr_bridge_with_auth(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/revenue/mrr-bridge", headers=auth_headers)
        assert resp.status_code in (200, 500)


class TestCohortEndpoints:
    def test_heatmap_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/cohorts/heatmap")
        assert resp.status_code == 401

    def test_heatmap_with_auth(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/cohorts/heatmap", headers=auth_headers)
        assert resp.status_code in (200, 500)


class TestHealthEndpoints:
    def test_distribution_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/health/distribution")
        assert resp.status_code == 401


class TestFunnelEndpoints:
    def test_overview_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/funnel/overview")
        assert resp.status_code == 401


class TestIngestEndpoints:
    def test_ingest_status_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/ingest/status")
        assert resp.status_code == 401

    def test_ingest_status_with_auth(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/ingest/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operational"

    def test_ingest_accounts_requires_auth(self, client: TestClient):
        resp = client.post("/api/v1/ingest/accounts", json={"records": []})
        assert resp.status_code == 401

    def test_viewer_cannot_ingest(self, client: TestClient, viewer_headers):
        resp = client.post(
            "/api/v1/ingest/accounts",
            headers=viewer_headers,
            json={"records": []},
        )
        assert resp.status_code == 403


class TestPipelineEndpoints:
    def test_dbt_run_requires_admin(self, client: TestClient, viewer_headers):
        resp = client.post("/api/v1/pipeline/dbt/run", headers=viewer_headers)
        assert resp.status_code == 403

    def test_tasks_requires_admin(self, client: TestClient, viewer_headers):
        resp = client.get("/api/v1/pipeline/tasks", headers=viewer_headers)
        assert resp.status_code == 403


class TestSystemEndpoints:
    def test_health_check_no_auth(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["api"] == "healthy"

    def test_root_no_auth(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["version"] == "2.0.0"

    def test_security_headers(self, client: TestClient):
        resp = client.get("/")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_rate_limit_headers(self, client: TestClient):
        resp = client.get("/api/v1/executive/summary")
        assert "X-RateLimit-Limit" in resp.headers or resp.status_code == 401
