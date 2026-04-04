"""
FlowSync Ingest Router — POST endpoints for all 6 entity types.

All endpoints require X-API-Key header with ingest:write scope.
Batch size is capped at 1000 records per request.

Routes:
  POST /api/v1/ingest/accounts
  POST /api/v1/ingest/subscriptions
  POST /api/v1/ingest/invoices
  POST /api/v1/ingest/usage-events
  POST /api/v1/ingest/tickets
  POST /api/v1/ingest/leads
  GET  /api/v1/ingest/status
"""
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from middleware.api_key_auth import APIKeyScopes, require_api_key
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
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient scope"},
        422: {"description": "Validation error in payload"},
    },
)

# ─── Shared dependency aliases ─────────────────────────────────────────────────

WriteAuth = Annotated[dict, Depends(require_api_key(APIKeyScopes.INGEST_WRITE))]
ReadAuth  = Annotated[dict, Depends(require_api_key(APIKeyScopes.INGEST_READ))]

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


# ─── Status endpoint (read scope) ─────────────────────────────────────────────

@router.get(
    "/status",
    summary="Ingest API status",
    description="Returns ingest API health and configuration.",
)
async def ingest_status(key_info: ReadAuth) -> dict:
    return {
        "status": "operational",
        "version": "1.0.0",
        "max_batch_size": MAX_BATCH,
        "supported_entities": [
            "accounts",
            "subscriptions",
            "invoices",
            "usage-events",
            "tickets",
            "leads",
        ],
        "authenticated_as": key_info.get("name"),
        "scopes": [str(s) for s in key_info.get("scopes", [])],
    }


# ─── Accounts ─────────────────────────────────────────────────────────────────

@router.post(
    "/accounts",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert accounts",
    description=(
        "Upsert up to 1,000 accounts per request into `raw.raw_accounts`. "
        "Uses `account_id` as the conflict key. Existing records are updated."
    ),
)
async def ingest_accounts(
    payload: AccountBatch,
    key_info: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "accounts")
    logger.info("ingest_accounts_start", count=len(payload.records), key=key_info.get("name"))
    return upsert_accounts(db, payload.records)


# ─── Subscriptions ────────────────────────────────────────────────────────────

@router.post(
    "/subscriptions",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert subscriptions",
    description=(
        "Upsert up to 1,000 subscriptions per request into `raw.raw_subscriptions`. "
        "Uses `subscription_id` as the conflict key."
    ),
)
async def ingest_subscriptions(
    payload: SubscriptionBatch,
    key_info: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "subscriptions")
    logger.info("ingest_subscriptions_start", count=len(payload.records), key=key_info.get("name"))
    return upsert_subscriptions(db, payload.records)


# ─── Invoices ─────────────────────────────────────────────────────────────────

@router.post(
    "/invoices",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert invoices",
    description=(
        "Upsert up to 1,000 invoices per request into `raw.raw_invoices`. "
        "Uses `invoice_id` as the conflict key."
    ),
)
async def ingest_invoices(
    payload: InvoiceBatch,
    key_info: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "invoices")
    logger.info("ingest_invoices_start", count=len(payload.records), key=key_info.get("name"))
    return upsert_invoices(db, payload.records)


# ─── Usage Events ─────────────────────────────────────────────────────────────

@router.post(
    "/usage-events",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert usage events",
    description=(
        "Upsert up to 1,000 usage events per request into `raw.raw_usage_events`. "
        "Uses `event_id` as the conflict key."
    ),
)
async def ingest_usage_events(
    payload: UsageEventBatch,
    key_info: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "usage events")
    logger.info("ingest_usage_events_start", count=len(payload.records), key=key_info.get("name"))
    return upsert_usage_events(db, payload.records)


# ─── Support Tickets ──────────────────────────────────────────────────────────

@router.post(
    "/tickets",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert support tickets",
    description=(
        "Upsert up to 1,000 support tickets per request into `raw.raw_tickets`. "
        "Uses `ticket_id` as the conflict key."
    ),
)
async def ingest_tickets(
    payload: TicketBatch,
    key_info: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "tickets")
    logger.info("ingest_tickets_start", count=len(payload.records), key=key_info.get("name"))
    return upsert_tickets(db, payload.records)


# ─── Leads ────────────────────────────────────────────────────────────────────

@router.post(
    "/leads",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert leads",
    description=(
        "Upsert up to 1,000 leads per request into `raw.raw_leads`. "
        "Uses `lead_id` as the conflict key."
    ),
)
async def ingest_leads(
    payload: LeadBatch,
    key_info: WriteAuth,
    db: Session = Depends(get_db),
) -> IngestResponse:
    _check_batch_size(len(payload.records), "leads")
    logger.info("ingest_leads_start", count=len(payload.records), key=key_info.get("name"))
    return upsert_leads(db, payload.records)
