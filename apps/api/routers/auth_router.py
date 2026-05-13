"""Authentication router — signup, login, token refresh, API key management."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from auth.audit import log_action
from auth.dependencies import CurrentUser, get_current_user, require_role
from auth.jwt_handler import create_access_token, create_refresh_token, decode_token, TokenError
from auth.models import APIKey, AuthUser, Tenant, UserRole
from auth.password import hash_password, verify_password
from db.database import get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Request/Response schemas ────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    organization_name: str = Field(min_length=1, max_length=200)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshRequest(BaseModel):
    refresh_token: str

class CreateAPIKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: str = Field(default="read", description="Comma-separated: read,write,ingest,webhook")
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    prefix: str
    scopes: str
    expires_at: Optional[str]

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: str
    tenant_name: str
    created_at: str


# ─── Signup ──────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.query(AuthUser).filter(AuthUser.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "email_taken", "message": "An account with this email already exists."},
        )

    slug = body.organization_name.lower().replace(" ", "-")[:80]
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    existing_tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if existing_tenant:
        slug = slug + "-" + secrets.token_hex(3)

    tenant = Tenant(name=body.organization_name, slug=slug, plan="free")
    db.add(tenant)
    db.flush()

    user = AuthUser(
        tenant_id=tenant.id,
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole.OWNER.value,
        is_active=True,
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(tenant)

    log_action(db, tenant.id, "user.signup", user_id=user.id, request=request)

    access_token = create_access_token(user.id, tenant.id, user.role)
    refresh_token = create_refresh_token(user.id, tenant.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
    )


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(AuthUser).filter(AuthUser.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Invalid email or password."},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "account_disabled", "message": "Account has been disabled."},
        )

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id, Tenant.is_active.is_(True)).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "tenant_inactive", "message": "Organization is inactive."},
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    log_action(db, tenant.id, "user.login", user_id=user.id, request=request)

    access_token = create_access_token(user.id, tenant.id, user.role)
    refresh_token = create_refresh_token(user.id, tenant.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
    )


# ─── Token Refresh ───────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_refresh_token", "message": str(e)},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token_type", "message": "Expected a refresh token."},
        )

    from uuid import UUID
    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tid"])

    user = db.query(AuthUser).filter(AuthUser.id == user_id, AuthUser.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "user_not_found"})

    access_token = create_access_token(user.id, tenant_id, user.role)
    refresh_token = create_refresh_token(user.id, tenant_id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800)


# ─── Profile ─────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfileResponse)
def get_profile(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    db_user = db.query(AuthUser).filter(AuthUser.id == user.user_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    return UserProfileResponse(
        id=str(db_user.id),
        email=db_user.email,
        full_name=db_user.full_name,
        role=db_user.role,
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        created_at=db_user.created_at.isoformat(),
    )


# ─── API Key Management ─────────────────────────────────────────────────────

@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    body: CreateAPIKeyRequest,
    request: Request,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    key_count = db.query(APIKey).filter(
        APIKey.tenant_id == user.tenant_id,
        APIKey.is_active.is_(True),
    ).count()

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if key_count >= tenant.max_api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "api_key_limit", "message": f"Maximum {tenant.max_api_keys} active keys allowed."},
        )

    raw_key = "fs_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:12]

    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    api_key = APIKey(
        tenant_id=user.tenant_id,
        created_by=user.user_id,
        name=body.name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=body.scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    log_action(
        db, user.tenant_id, "api_key.created",
        user_id=user.user_id, resource_type="api_key", resource_id=str(api_key.id), request=request,
    )

    return APIKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        key=raw_key,
        prefix=prefix,
        scopes=api_key.scopes,
        expires_at=expires_at.isoformat() if expires_at else None,
    )


@router.get("/api-keys")
def list_api_keys(
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> list[dict]:
    keys = db.query(APIKey).filter(
        APIKey.tenant_id == user.tenant_id,
        APIKey.is_active.is_(True),
    ).all()
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "prefix": k.key_prefix,
            "scopes": k.scopes,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: str,
    request: Request,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    from uuid import UUID
    api_key = db.query(APIKey).filter(
        APIKey.id == UUID(key_id),
        APIKey.tenant_id == user.tenant_id,
    ).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not_found"})
    api_key.is_active = False
    db.commit()
    log_action(
        db, user.tenant_id, "api_key.revoked",
        user_id=user.user_id, resource_type="api_key", resource_id=key_id, request=request,
    )
