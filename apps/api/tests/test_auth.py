"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestSignup:
    def test_signup_success(self, client: TestClient):
        resp = client.post("/api/v1/auth/signup", json={
            "email": "new@example.com",
            "password": "StrongPass123!",
            "full_name": "New User",
            "organization_name": "New Org",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_signup_duplicate_email(self, client: TestClient, test_user):
        resp = client.post("/api/v1/auth/signup", json={
            "email": "owner@testcorp.com",
            "password": "StrongPass123!",
            "full_name": "Duplicate",
            "organization_name": "Dup Org",
        })
        assert resp.status_code == 409
        assert resp.json()["detail"]["error"] == "email_taken"

    def test_signup_weak_password(self, client: TestClient):
        resp = client.post("/api/v1/auth/signup", json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "Weak",
            "organization_name": "Weak Org",
        })
        assert resp.status_code == 422

    def test_signup_invalid_email(self, client: TestClient):
        resp = client.post("/api/v1/auth/signup", json={
            "email": "not-an-email",
            "password": "StrongPass123!",
            "full_name": "Bad",
            "organization_name": "Bad Org",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient, test_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "owner@testcorp.com",
            "password": "TestPass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["expires_in"] == 1800

    def test_login_wrong_password(self, client: TestClient, test_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "owner@testcorp.com",
            "password": "WrongPassword!",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"]["error"] == "invalid_credentials"

    def test_login_nonexistent_email(self, client: TestClient):
        resp = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "SomePassword!",
        })
        assert resp.status_code == 401


class TestTokenRefresh:
    def test_refresh_success(self, client: TestClient, test_user):
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "owner@testcorp.com",
            "password": "TestPass123!",
        })
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_invalid_token(self, client: TestClient):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert resp.status_code == 401


class TestProfile:
    def test_get_profile(self, client: TestClient, auth_headers, test_user):
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "owner@testcorp.com"
        assert data["role"] == "owner"

    def test_profile_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestAPIKeyManagement:
    def test_create_api_key(self, client: TestClient, auth_headers):
        resp = client.post("/api/v1/auth/api-keys", headers=auth_headers, json={
            "name": "Test Key",
            "scopes": "read,write",
            "expires_in_days": 30,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Key"
        assert data["key"].startswith("fs_")
        assert data["scopes"] == "read,write"

    def test_list_api_keys(self, client: TestClient, auth_headers):
        client.post("/api/v1/auth/api-keys", headers=auth_headers, json={
            "name": "Key 1", "scopes": "read",
        })
        resp = client.get("/api/v1/auth/api-keys", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_revoke_api_key(self, client: TestClient, auth_headers):
        create_resp = client.post("/api/v1/auth/api-keys", headers=auth_headers, json={
            "name": "Revokable", "scopes": "read",
        })
        key_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_viewer_cannot_create_api_key(self, client: TestClient, viewer_headers):
        resp = client.post("/api/v1/auth/api-keys", headers=viewer_headers, json={
            "name": "Denied", "scopes": "read",
        })
        assert resp.status_code == 403
