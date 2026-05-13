"""
FlowSync Ingest Router — POST endpoints for all 6 entity types.

All endpoints require authentication with write scope.
Batch size is capped at 1000 records per request.
"""
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.dependencies import CurrentUser, get_current_user, require_role
from auth.models import UserRole
from db.database import get_db
from schemas.ingest import (
    AccountBatch,
    IngestResponse,
    InvoiceBatch,
    LeadBatch,
    SubscriptionBatch,
    TicketBatch,
    UsageEventBatch,
)
from services.ingest_service import (
    upsert_accounts,
    upsert_invoices,
    upsert_leads,
    upsert_subscriptions,
    upsert_tickets,
    upsert_usage_events,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/ingest",
    tags=["Ingest"],
    responses={
        401: {"description": "Missing or invalid credentials"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Validation error in payload"},
    },
)

WriteAuth = Annotated[CurrentUser, Depends(require_role(UserRole.ANALYST))]

MAX_BATCH = 1000


def _check_batch_size(count: int, entity: str) -> None:
    if count > MAX_BATCH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "batch_too_large",
                "message": f"Maximum {MAX_BATCH} {entity} per request. Got {count}.",
                "max_batch_size": MAX_BATCH,
                "received": count,
            },
        )


@router.get("/status", summary="Ingest API status")
async def ingest_status(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    return {
        "status": "operational",
        "version": "2.0.0",
        "max_batch_size": MAX_BATCH,
        "supported_entities": ["accounts", "subscriptions", "invoices", "usage-events", "tickets", "leads"],
        "tenant_id": str(user.tenant_id),
        "role": user.role,
    }


@router.post("/accounts", response_model=IngestResponse, status_code=status.HTTP_200_OK, summary="Upsert accounts")
async def ingest_accounts(
    payload: AccountBatch,
    user: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "accounts")
    logger.info("ingest_accounts_start", count=len(payload.records), tenant_id=str(user.tenant_id))
    return upsert_accounts(db, payload.records, tenant_id=user.tenant_id)


@router.post("/subscriptions", response_model=IngestResponse, status_code=status.HTTP_200_OK, summary="Upsert subscriptions")
async def ingest_subscriptions(
    payload: SubscriptionBatch,
    user: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "subscriptions")
    logger.info("ingest_subscriptions_start", count=len(payload.records), tenant_id=str(user.tenant_id))
    return upsert_subscriptions(db, payload.records, tenant_id=user.tenant_id)


@router.post("/invoices", response_model=IngestResponse, status_code=status.HTTP_200_OK, summary="Upsert invoices")
async def ingest_invoices(
    payload: InvoiceBatch,
    user: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "invoices")
    logger.info("ingest_invoices_start", count=len(payload.records), tenant_id=str(user.tenant_id))
    return upsert_invoices(db, payload.records, tenant_id=user.tenant_id)


@router.post("/usage-events", response_model=IngestResponse, status_code=status.HTTP_200_OK, summary="Upsert usage events")
async def ingest_usage_events(
    payload: UsageEventBatch,
    user: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "usage events")
    logger.info("ingest_usage_events_start", count=len(payload.records), tenant_id=str(user.tenant_id))
    return upsert_usage_events(db, payload.records, tenant_id=user.tenant_id)


@router.post("/tickets", response_model=IngestResponse, status_code=status.HTTP_200_OK, summary="Upsert support tickets")
async def ingest_tickets(
    payload: TicketBatch,
    user: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "tickets")
    logger.info("ingest_tickets_start", count=len(payload.records), tenant_id=str(user.tenant_id))
    return upsert_tickets(db, payload.records, tenant_id=user.tenant_id)


@router.post("/leads", response_model=IngestResponse, status_code=status.HTTP_200_OK, summary="Upsert leads")
async def ingest_leads(
    payload: LeadBatch,
    user: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "leads")
    logger.info("ingest_leads_start", count=len(payload.records), tenant_id=str(user.tenant_id))
    return upsert_leads(db, payload.records, tenant_id=user.tenant_id)
