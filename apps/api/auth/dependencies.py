"""FastAPI dependencies for authentication and tenant isolation."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from db.database import get_db
from auth.jwt_handler import TokenError, decode_token
from auth.models import APIKey, AuthUser, Tenant, UserRole, ROLE_HIERARCHY

logger = structlog.get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """Represents the authenticated user context for a request."""

    def __init__(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role: str,
        email: Optional[str] = None,
        auth_method: str = "jwt",
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.email = email
        self.auth_method = auth_method

    def has_role(self, required: UserRole) -> bool:
        user_level = ROLE_HIERARCHY.get(UserRole(self.role), 0)
        required_level = ROLE_HIERARCHY.get(required, 999)
        return user_level >= required_level


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Extract and validate the user from JWT or API key."""

    # Try JWT Bearer token first
    if credentials and credentials.credentials:
        return _authenticate_jwt(credentials.credentials, db)

    # Fall back to X-API-Key header
    api_key = request.headers.get("X-API-Key", "").strip()
    if api_key:
        return _authenticate_api_key(api_key, db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "not_authenticated", "message": "Provide a Bearer token or X-API-Key header."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _authenticate_jwt(token: str, db: Session) -> CurrentUser:
    try:
        payload = decode_token(token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": str(e)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token_type", "message": "Expected an access token."},
        )

    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tid"])

    user = db.query(AuthUser).filter(
        AuthUser.id == user_id,
        AuthUser.tenant_id == tenant_id,
        AuthUser.is_active.is_(True),
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "user_not_found", "message": "User account is inactive or deleted."},
        )

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_active.is_(True)).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "tenant_inactive", "message": "Organization is inactive."},
        )

    return CurrentUser(
        user_id=user.id,
        tenant_id=tenant.id,
        role=user.role,
        email=user.email,
        auth_method="jwt",
    )


def _authenticate_api_key(raw_key: str, db: Session) -> CurrentUser:
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active.is_(True),
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_api_key", "message": "API key is invalid or revoked."},
        )

    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "api_key_expired", "message": "API key has expired."},
        )

    tenant = db.query(Tenant).filter(Tenant.id == api_key.tenant_id, Tenant.is_active.is_(True)).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "tenant_inactive", "message": "Organization is inactive."},
        )

    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return CurrentUser(
        user_id=api_key.created_by,
        tenant_id=api_key.tenant_id,
        role=UserRole.ANALYST.value,
        auth_method="api_key",
    )


async def get_current_tenant(user: CurrentUser = Depends(get_current_user)) -> UUID:
    """Returns just the tenant_id for query scoping."""
    return user.tenant_id


def require_role(minimum_role: UserRole):
    """Dependency factory that enforces a minimum role level."""
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_role(minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_permissions",
                    "message": f"Requires '{minimum_role.value}' role or higher.",
                    "your_role": user.role,
                },
            )
        return user
    return _check
