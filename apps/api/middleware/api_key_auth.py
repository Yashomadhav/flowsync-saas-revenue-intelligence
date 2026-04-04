"""
API Key authentication middleware for FlowSync ingest endpoints.

Usage:
    from middleware.api_key_auth import require_api_key, APIKeyScopes
    
    @router.post("/ingest/accounts")
    async def ingest_accounts(
        payload: AccountBatch,
        key_info: dict = Depends(require_api_key(APIKeyScopes.INGEST_WRITE)),
    ):
        ...

Key format:  fs_live_<random>  or  fs_test_<random>  or  fs_whk_<random>
Scopes:      ingest:write | ingest:read | webhook:receive | admin
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from enum import Enum
from typing import Optional

import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader

logger = structlog.get_logger(__name__)

# ─── Scope definitions ────────────────────────────────────────────────────────

class APIKeyScopes(str, Enum):
    INGEST_WRITE = "ingest:write"
    INGEST_READ  = "ingest:read"
    WEBHOOK      = "webhook:receive"
    ADMIN        = "admin"


# ─── In-memory key store (replace with DB lookup in production) ───────────────
# Format: { "hashed_key": { "name": str, "scopes": list[str], "active": bool } }
# Keys are SHA-256 hashed before storage — never store plaintext keys.

def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


# Demo keys — in production these come from the database (api_keys table)
_DEMO_KEYS: dict[str, dict] = {
    _hash_key("fs_live_demo_production_key_k9mX"): {
        "name": "Production Ingestion Key",
        "scopes": [APIKeyScopes.INGEST_WRITE, APIKeyScopes.INGEST_READ],
        "active": True,
        "prefix": "fs_live_",
    },
    _hash_key("fs_test_demo_staging_key_p2nQ"): {
        "name": "Staging / Test Key",
        "scopes": [APIKeyScopes.INGEST_WRITE, APIKeyScopes.INGEST_READ],
        "active": True,
        "prefix": "fs_test_",
    },
    _hash_key("fs_whk_demo_webhook_key_r7vL"): {
        "name": "Stripe Webhook Key",
        "scopes": [APIKeyScopes.WEBHOOK],
        "active": True,
        "prefix": "fs_whk_",
    },
    _hash_key("fs_live_admin_master_key_ADMIN"): {
        "name": "Admin Master Key",
        "scopes": [APIKeyScopes.INGEST_WRITE, APIKeyScopes.INGEST_READ, APIKeyScopes.WEBHOOK, APIKeyScopes.ADMIN],
        "active": True,
        "prefix": "fs_live_",
    },
}

# Also allow env-var override for CI/CD
_ENV_ADMIN_KEY = os.getenv("FLOWSYNC_ADMIN_API_KEY", "")
if _ENV_ADMIN_KEY:
    _DEMO_KEYS[_hash_key(_ENV_ADMIN_KEY)] = {
        "name": "Env Admin Key",
        "scopes": [APIKeyScopes.INGEST_WRITE, APIKeyScopes.INGEST_READ, APIKeyScopes.WEBHOOK, APIKeyScopes.ADMIN],
        "active": True,
        "prefix": "fs_live_",
    }

# ─── FastAPI security scheme ──────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _lookup_key(raw_key: str) -> Optional[dict]:
    """Hash the incoming key and look it up in the store."""
    hashed = _hash_key(raw_key)
    return _DEMO_KEYS.get(hashed)


def require_api_key(required_scope: Optional[APIKeyScopes] = None):
    """
    Dependency factory. Returns a FastAPI Depends-compatible function.
    
    Example:
        Depends(require_api_key(APIKeyScopes.INGEST_WRITE))
    """
    async def _check(
        request: Request,
        x_api_key: Optional[str] = Depends(_api_key_header),
    ) -> dict:
        # ── 1. Extract key ────────────────────────────────────────────────────
        raw_key = x_api_key or request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

        if not raw_key:
            logger.warning("api_key_missing", path=str(request.url.path))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "missing_api_key",
                    "message": "Include your API key in the X-API-Key header.",
                    "docs": "/docs#section/Authentication",
                },
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # ── 2. Validate format ────────────────────────────────────────────────
        if not (raw_key.startswith("fs_live_") or raw_key.startswith("fs_test_") or raw_key.startswith("fs_whk_")):
            logger.warning("api_key_invalid_format", path=str(request.url.path))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_key_format",
                    "message": "API keys must start with fs_live_, fs_test_, or fs_whk_.",
                },
            )

        # ── 3. Look up key ────────────────────────────────────────────────────
        key_info = _lookup_key(raw_key)
        if not key_info or not key_info.get("active"):
            logger.warning("api_key_not_found", path=str(request.url.path))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_api_key",
                    "message": "The provided API key is invalid or has been revoked.",
                },
            )

        # ── 4. Check scope ────────────────────────────────────────────────────
        if required_scope and required_scope not in key_info["scopes"]:
            logger.warning(
                "api_key_insufficient_scope",
                required=required_scope,
                has=key_info["scopes"],
                path=str(request.url.path),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_scope",
                    "message": f"This key does not have the '{required_scope}' scope.",
                    "required_scope": required_scope,
                    "key_scopes": key_info["scopes"],
                },
            )

        logger.info(
            "api_key_authenticated",
            key_name=key_info["name"],
            scope=required_scope,
            path=str(request.url.path),
        )
        return key_info

    return _check


# ─── Stripe webhook signature verification ────────────────────────────────────

def verify_stripe_signature(
    payload_bytes: bytes,
    stripe_signature: str,
    webhook_secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    """
    Verify Stripe webhook signature using HMAC-SHA256.
    Stripe sends: Stripe-Signature: t=<timestamp>,v1=<sig>
    """
    try:
        parts = dict(item.split("=", 1) for item in stripe_signature.split(","))
        timestamp = int(parts.get("t", 0))
        expected_sig = parts.get("v1", "")

        # Reject stale webhooks
        if abs(time.time() - timestamp) > tolerance_seconds:
            logger.warning("stripe_webhook_stale", age_seconds=abs(time.time() - timestamp))
            return False

        # Compute expected signature: HMAC-SHA256(secret, "{timestamp}.{payload}")
        signed_payload = f"{timestamp}.".encode() + payload_bytes
        mac = hmac.new(webhook_secret.encode(), signed_payload, hashlib.sha256)
        computed = mac.hexdigest()
        return hmac.compare_digest(computed, expected_sig)
    except Exception as exc:
        logger.error("stripe_signature_verification_error", error=str(exc))
        return False
