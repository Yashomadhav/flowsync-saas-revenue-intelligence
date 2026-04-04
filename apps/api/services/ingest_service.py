"""
FlowSync Ingest Service — upsert logic for all 6 entity types.

Each function accepts a list of validated Pydantic models and performs
INSERT ... ON CONFLICT DO UPDATE (upsert) into the raw.* tables.

Key design decisions:
- Schema field names ≠ DB column names in several cases; we build params
  explicitly rather than using model_dump() directly.
- DB columns not present in the schema receive safe defaults (None / 'USD' etc.)
- IngestResponse.error_count is an int (not a list) — details go to logs.
- xmax trick: xmax=0 → inserted, xmax>0 → updated.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from schemas.ingest import (
    AccountIngest,
    IngestResponse,
    InvoiceIngest,
    LeadIngest,
    SubscriptionIngest,
    TicketIngest,
    UsageEventIngest,
)

logger = structlog.get_logger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(val) -> Optional[str]:
    """Convert datetime/date to ISO string, or return None."""
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def _safe_upsert(db: Session, sql: str, params: dict, entity_id: str) -> str:
    """
    Execute a single upsert. Returns 'inserted', 'updated', or 'error'.
    Uses PostgreSQL xmax trick: xmax=0 → inserted, xmax>0 → updated.
    """
    try:
        result = db.execute(text(sql), params)
        row = result.fetchone()
        if row and row[0] == 0:
            return "inserted"
        return "updated"
    except Exception as exc:
        logger.error("upsert_error", entity_id=entity_id, error=str(exc))
        return "error"


def _make_response(entity: str, total: int, inserted: int, updated: int, errors: int) -> IngestResponse:
    return IngestResponse(
        inserted=inserted,
        updated=updated,
        error_count=errors,
        message=(
            f"Processed {total} {entity}: "
            f"{inserted} new, {updated} updated, {errors} errors."
        ),
    )


# ─── Accounts ─────────────────────────────────────────────────────────────────

_ACCOUNT_UPSERT = """
INSERT INTO raw.raw_accounts (
    account_id, company_name, industry, region, company_size,
    acquisition_channel, account_status, created_at, updated_at,
    website, employee_count, annual_revenue_usd, country, city,
    primary_contact_email, primary_contact_name, _ingested_at
)
VALUES (
    :account_id, :company_name, :industry, :region, :company_size,
    :acquisition_channel, :account_status, :created_at, :updated_at,
    :website, :employee_count, :annual_revenue_usd, :country, :city,
    :primary_contact_email, :primary_contact_name, :_ingested_at
)
ON CONFLICT (account_id) DO UPDATE SET
    company_name          = EXCLUDED.company_name,
    industry              = EXCLUDED.industry,
    region                = EXCLUDED.region,
    company_size          = EXCLUDED.company_size,
    acquisition_channel   = EXCLUDED.acquisition_channel,
    account_status        = EXCLUDED.account_status,
    updated_at            = EXCLUDED.updated_at,
    website               = EXCLUDED.website,
    employee_count        = EXCLUDED.employee_count,
    annual_revenue_usd    = EXCLUDED.annual_revenue_usd,
    country               = EXCLUDED.country,
    city                  = EXCLUDED.city,
    primary_contact_email = EXCLUDED.primary_contact_email,
    primary_contact_name  = EXCLUDED.primary_contact_name,
    _ingested_at          = EXCLUDED._ingested_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_accounts(db: Session, records: List[AccountIngest]) -> IngestResponse:
    inserted = updated = errors = 0
    ingested_at = _now_utc()

    for rec in records:
        params = {
            "account_id":           rec.account_id,
            "company_name":         rec.company_name,
            "industry":             rec.industry,
            "region":               rec.region,
            "company_size":         rec.company_size,
            "acquisition_channel":  rec.acquisition_channel,
            "account_status":       "active",           # not in schema → default
            "created_at":           _iso(rec.created_at),
            "updated_at":           _iso(rec.updated_at),
            "website":              rec.website,
            "employee_count":       None,               # not in schema → NULL
            "annual_revenue_usd":   None,               # not in schema → NULL
            "country":              rec.country,
            "city":                 None,               # not in schema → NULL
            "primary_contact_email": None,              # not in schema → NULL
            "primary_contact_name":  rec.account_owner, # closest mapping
            "_ingested_at":         ingested_at,
        }
        outcome = _safe_upsert(db, _ACCOUNT_UPSERT, params, rec.account_id)
        if outcome == "inserted":
            inserted += 1
        elif outcome == "updated":
            updated += 1
        else:
            errors += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("accounts_commit_error", error=str(exc))
        return IngestResponse(inserted=0, updated=0, error_count=len(records), message=str(exc))

    logger.info("accounts_upserted", inserted=inserted, updated=updated, errors=errors)
    return _make_response("accounts", len(records), inserted, updated, errors)


# ─── Subscriptions ────────────────────────────────────────────────────────────

_SUBSCRIPTION_UPSERT = """
INSERT INTO raw.raw_subscriptions (
    subscription_id, account_id, plan_id, plan_name, status,
    mrr, arr, seats, start_date, end_date, trial_start, trial_end,
    billing_cycle, currency, discount_pct, created_at, updated_at, _ingested_at
)
VALUES (
    :subscription_id, :account_id, :plan_id, :plan_name, :status,
    :mrr, :arr, :seats, :start_date, :end_date, :trial_start, :trial_end,
    :billing_cycle, :currency, :discount_pct, :created_at, :updated_at, :_ingested_at
)
ON CONFLICT (subscription_id) DO UPDATE SET
    account_id    = EXCLUDED.account_id,
    plan_id       = EXCLUDED.plan_id,
    plan_name     = EXCLUDED.plan_name,
    status        = EXCLUDED.status,
    mrr           = EXCLUDED.mrr,
    arr           = EXCLUDED.arr,
    seats         = EXCLUDED.seats,
    start_date    = EXCLUDED.start_date,
    end_date      = EXCLUDED.end_date,
    trial_start   = EXCLUDED.trial_start,
    trial_end     = EXCLUDED.trial_end,
    billing_cycle = EXCLUDED.billing_cycle,
    currency      = EXCLUDED.currency,
    discount_pct  = EXCLUDED.discount_pct,
    updated_at    = EXCLUDED.updated_at,
    _ingested_at  = EXCLUDED._ingested_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_subscriptions(db: Session, records: List[SubscriptionIngest]) -> IngestResponse:
    inserted = updated = errors = 0
    ingested_at = _now_utc()

    for rec in records:
        arr = rec.arr if rec.arr is not None else round(rec.mrr * 12, 2)
        params = {
            "subscription_id": rec.subscription_id,
            "account_id":      rec.account_id,
            "plan_id":         rec.plan_id,
            "plan_name":       rec.plan_name,
            "status":          rec.status,
            "mrr":             rec.mrr,
            "arr":             arr,
            "seats":           rec.seats,
            # field name mapping: schema → DB column
            "start_date":      _iso(rec.started_at),
            "end_date":        _iso(rec.canceled_at),   # canceled_at → end_date
            "trial_start":     _iso(rec.trial_started_at),
            "trial_end":       _iso(rec.trial_ended_at),
            "billing_cycle":   rec.billing_interval,    # billing_interval → billing_cycle
            "currency":        "USD",                   # not in schema → default
            "discount_pct":    0.0,                     # not in schema → default
            "created_at":      _iso(rec.started_at),    # use started_at as created_at
            "updated_at":      _iso(rec.updated_at),
            "_ingested_at":    ingested_at,
        }
        outcome = _safe_upsert(db, _SUBSCRIPTION_UPSERT, params, rec.subscription_id)
        if outcome == "inserted":
            inserted += 1
        elif outcome == "updated":
            updated += 1
        else:
            errors += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("subscriptions_commit_error", error=str(exc))
        return IngestResponse(inserted=0, updated=0, error_count=len(records), message=str(exc))

    logger.info("subscriptions_upserted", inserted=inserted, updated=updated, errors=errors)
    return _make_response("subscriptions", len(records), inserted, updated, errors)


# ─── Invoices ─────────────────────────────────────────────────────────────────

_INVOICE_UPSERT = """
INSERT INTO raw.raw_invoices (
    invoice_id, account_id, subscription_id, invoice_date, due_date,
    amount, currency, status, payment_method, payment_attempts,
    paid_at, voided_at, created_at, _ingested_at
)
VALUES (
    :invoice_id, :account_id, :subscription_id, :invoice_date, :due_date,
    :amount, :currency, :status, :payment_method, :payment_attempts,
    :paid_at, :voided_at, :created_at, :_ingested_at
)
ON CONFLICT (invoice_id) DO UPDATE SET
    account_id       = EXCLUDED.account_id,
    subscription_id  = EXCLUDED.subscription_id,
    invoice_date     = EXCLUDED.invoice_date,
    due_date         = EXCLUDED.due_date,
    amount           = EXCLUDED.amount,
    currency         = EXCLUDED.currency,
    status           = EXCLUDED.status,
    payment_method   = EXCLUDED.payment_method,
    payment_attempts = EXCLUDED.payment_attempts,
    paid_at          = EXCLUDED.paid_at,
    voided_at        = EXCLUDED.voided_at,
    _ingested_at     = EXCLUDED._ingested_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_invoices(db: Session, records: List[InvoiceIngest]) -> IngestResponse:
    inserted = updated = errors = 0
    ingested_at = _now_utc()

    for rec in records:
        # Map void status → voided_at timestamp
        voided_at = _iso(rec.failed_at) if rec.status == "void" else None
        params = {
            "invoice_id":       rec.invoice_id,
            "account_id":       rec.account_id,
            "subscription_id":  rec.subscription_id,
            "invoice_date":     _iso(rec.invoice_date),
            "due_date":         _iso(rec.due_date),
            "amount":           rec.amount,
            "currency":         rec.currency,
            "status":           rec.status,
            "payment_method":   rec.payment_method,
            "payment_attempts": rec.attempt_count,       # attempt_count → payment_attempts
            "paid_at":          _iso(rec.paid_at),
            "voided_at":        voided_at,               # not in schema → derive from status
            "created_at":       _iso(rec.created_at),
            "_ingested_at":     ingested_at,
        }
        outcome = _safe_upsert(db, _INVOICE_UPSERT, params, rec.invoice_id)
        if outcome == "inserted":
            inserted += 1
        elif outcome == "updated":
            updated += 1
        else:
            errors += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("invoices_commit_error", error=str(exc))
        return IngestResponse(inserted=0, updated=0, error_count=len(records), message=str(exc))

    logger.info("invoices_upserted", inserted=inserted, updated=updated, errors=errors)
    return _make_response("invoices", len(records), inserted, updated, errors)


# ─── Usage Events ─────────────────────────────────────────────────────────────

_USAGE_UPSERT = """
INSERT INTO raw.raw_usage_events (
    event_id, account_id, user_id, event_type, feature_name,
    event_timestamp, session_id, duration_seconds, metadata, _ingested_at
)
VALUES (
    :event_id, :account_id, :user_id, :event_type, :feature_name,
    :event_timestamp, :session_id, :duration_seconds, :metadata::jsonb, :_ingested_at
)
ON CONFLICT (event_id) DO UPDATE SET
    account_id       = EXCLUDED.account_id,
    user_id          = EXCLUDED.user_id,
    event_type       = EXCLUDED.event_type,
    feature_name     = EXCLUDED.feature_name,
    event_timestamp  = EXCLUDED.event_timestamp,
    session_id       = EXCLUDED.session_id,
    duration_seconds = EXCLUDED.duration_seconds,
    metadata         = EXCLUDED.metadata,
    _ingested_at     = EXCLUDED._ingested_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_usage_events(db: Session, records: List[UsageEventIngest]) -> IngestResponse:
    inserted = updated = errors = 0
    ingested_at = _now_utc()

    for rec in records:
        # Build metadata: merge properties + event_count
        meta = dict(rec.properties or {})
        meta["event_count"] = rec.event_count
        params = {
            "event_id":         rec.event_id,
            "account_id":       rec.account_id,
            "user_id":          rec.user_id,
            "event_type":       rec.event_type or rec.feature_name,
            "feature_name":     rec.feature_name,
            "event_timestamp":  _iso(rec.occurred_at),          # occurred_at → event_timestamp
            "session_id":       None,                            # not in schema → NULL
            "duration_seconds": rec.session_duration_seconds,   # session_duration_seconds → duration_seconds
            "metadata":         json.dumps(meta),               # properties → metadata (jsonb)
            "_ingested_at":     ingested_at,
        }
        outcome = _safe_upsert(db, _USAGE_UPSERT, params, rec.event_id or "unknown")
        if outcome == "inserted":
            inserted += 1
        elif outcome == "updated":
            updated += 1
        else:
            errors += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("usage_events_commit_error", error=str(exc))
        return IngestResponse(inserted=0, updated=0, error_count=len(records), message=str(exc))

    logger.info("usage_events_upserted", inserted=inserted, updated=updated, errors=errors)
    return _make_response("usage_events", len(records), inserted, updated, errors)


# ─── Support Tickets ──────────────────────────────────────────────────────────

_TICKET_UPSERT = """
INSERT INTO raw.raw_tickets (
    ticket_id, account_id, user_id, subject, category, priority,
    status, channel, created_at, resolved_at, first_response_at,
    csat_score, agent_id, tags, _ingested_at
)
VALUES (
    :ticket_id, :account_id, :user_id, :subject, :category, :priority,
    :status, :channel, :created_at, :resolved_at, :first_response_at,
    :csat_score, :agent_id, :tags, :_ingested_at
)
ON CONFLICT (ticket_id) DO UPDATE SET
    account_id        = EXCLUDED.account_id,
    user_id           = EXCLUDED.user_id,
    subject           = EXCLUDED.subject,
    category          = EXCLUDED.category,
    priority          = EXCLUDED.priority,
    status            = EXCLUDED.status,
    channel           = EXCLUDED.channel,
    resolved_at       = EXCLUDED.resolved_at,
    first_response_at = EXCLUDED.first_response_at,
    csat_score        = EXCLUDED.csat_score,
    agent_id          = EXCLUDED.agent_id,
    tags              = EXCLUDED.tags,
    _ingested_at      = EXCLUDED._ingested_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_tickets(db: Session, records: List[TicketIngest]) -> IngestResponse:
    inserted = updated = errors = 0
    ingested_at = _now_utc()

    for rec in records:
        params = {
            "ticket_id":         rec.ticket_id,
            "account_id":        rec.account_id,
            "user_id":           rec.user_id,
            "subject":           rec.subject,
            "category":          rec.category,
            "priority":          rec.priority,
            "status":            rec.status,
            "channel":           None,               # not in schema → NULL
            "created_at":        _iso(rec.created_at),
            "resolved_at":       _iso(rec.resolved_at),
            "first_response_at": None,               # not in schema → NULL
            "csat_score":        rec.csat_score,
            "agent_id":          None,               # not in schema → NULL
            "tags":              None,               # not in schema → NULL
            "_ingested_at":      ingested_at,
        }
        outcome = _safe_upsert(db, _TICKET_UPSERT, params, rec.ticket_id)
        if outcome == "inserted":
            inserted += 1
        elif outcome == "updated":
            updated += 1
        else:
            errors += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("tickets_commit_error", error=str(exc))
        return IngestResponse(inserted=0, updated=0, error_count=len(records), message=str(exc))

    logger.info("tickets_upserted", inserted=inserted, updated=updated, errors=errors)
    return _make_response("tickets", len(records), inserted, updated, errors)


# ─── Leads ────────────────────────────────────────────────────────────────────

_LEAD_UPSERT = """
INSERT INTO raw.raw_leads (
    lead_id, company_name, contact_name, contact_email, phone,
    acquisition_channel, lead_source, industry, company_size, region,
    lead_status, funnel_stage, lead_score, estimated_mrr,
    created_at, qualified_at, trial_started_at, converted_at,
    lost_at, lost_reason, owner_id, _ingested_at
)
VALUES (
    :lead_id, :company_name, :contact_name, :contact_email, :phone,
    :acquisition_channel, :lead_source, :industry, :company_size, :region,
    :lead_status, :funnel_stage, :lead_score, :estimated_mrr,
    :created_at, :qualified_at, :trial_started_at, :converted_at,
    :lost_at, :lost_reason, :owner_id, :_ingested_at
)
ON CONFLICT (lead_id) DO UPDATE SET
    company_name        = EXCLUDED.company_name,
    contact_name        = EXCLUDED.contact_name,
    contact_email       = EXCLUDED.contact_email,
    phone               = EXCLUDED.phone,
    acquisition_channel = EXCLUDED.acquisition_channel,
    lead_source         = EXCLUDED.lead_source,
    industry            = EXCLUDED.industry,
    company_size        = EXCLUDED.company_size,
    region              = EXCLUDED.region,
    lead_status         = EXCLUDED.lead_status,
    funnel_stage        = EXCLUDED.funnel_stage,
    lead_score          = EXCLUDED.lead_score,
    estimated_mrr       = EXCLUDED.estimated_mrr,
    qualified_at        = EXCLUDED.qualified_at,
    trial_started_at    = EXCLUDED.trial_started_at,
    converted_at        = EXCLUDED.converted_at,
    lost_at             = EXCLUDED.lost_at,
    lost_reason         = EXCLUDED.lost_reason,
    owner_id            = EXCLUDED.owner_id,
    _ingested_at        = EXCLUDED._ingested_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_leads(db: Session, records: List[LeadIngest]) -> IngestResponse:
    inserted = updated = errors = 0
    ingested_at = _now_utc()

    for rec in records:
        # Derive lead_status from funnel_stage
        stage = rec.funnel_stage or "lead"
        if stage in ("closed_won",):
            lead_status = "converted"
        elif stage in ("closed_lost",):
            lead_status = "lost"
        elif stage in ("trial", "opportunity"):
            lead_status = "active"
        else:
            lead_status = "new"

        # lost_at: use closed_at when stage is closed_lost
        lost_at = _iso(rec.closed_at) if stage == "closed_lost" else None

        params = {
            "lead_id":            rec.lead_id,
            "company_name":       rec.company_name,
            "contact_name":       None,                      # not in schema → NULL
            "contact_email":      rec.contact_email,
            "phone":              None,                      # not in schema → NULL
            "acquisition_channel": rec.acquisition_channel,
            "lead_source":        rec.lead_source,
            "industry":           rec.industry,
            "company_size":       rec.company_size,
            "region":             rec.region,
            "lead_status":        lead_status,               # derived from funnel_stage
            "funnel_stage":       stage,
            "lead_score":         rec.lead_score,
            "estimated_mrr":      rec.converted_mrr,         # converted_mrr → estimated_mrr
            "created_at":         _iso(rec.created_at),
            "qualified_at":       None,                      # not in schema → NULL
            "trial_started_at":   _iso(rec.trial_started_at),
            "converted_at":       _iso(rec.converted_at),
            "lost_at":            lost_at,
            "lost_reason":        None,                      # not in schema → NULL
            "owner_id":           None,                      # not in schema → NULL
            "_ingested_at":       ingested_at,
        }
        outcome = _safe_upsert(db, _LEAD_UPSERT, params, rec.lead_id)
        if outcome == "inserted":
            inserted += 1
        elif outcome == "updated":
            updated += 1
        else:
            errors += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("leads_commit_error", error=str(exc))
        return IngestResponse(inserted=0, updated=0, error_count=len(records), message=str(exc))

    logger.info("leads_upserted", inserted=inserted, updated=updated, errors=errors)
    return _make_response("leads", len(records), inserted, updated, errors)
