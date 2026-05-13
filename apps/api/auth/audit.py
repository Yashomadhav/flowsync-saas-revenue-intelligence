"""Audit logging service."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

import structlog
from fastapi import Request
from sqlalchemy.orm import Session

from auth.models import AuditLog

logger = structlog.get_logger(__name__)


def log_action(
    db: Session,
    tenant_id: UUID,
    action: str,
    user_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    request: Optional[Request] = None,
    details: Optional[str] = None,
) -> None:
    ip_address = None
    user_agent = None
    if request:
        forwarded = request.headers.get("X-Forwarded-For", "")
        ip_address = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
        user_agent = request.headers.get("User-Agent", "")[:500]

    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
    )
    db.add(entry)
    db.commit()

    logger.info(
        "audit",
        action=action,
        tenant_id=str(tenant_id),
        user_id=str(user_id) if user_id else None,
        resource=f"{resource_type}:{resource_id}" if resource_type else None,
    )
