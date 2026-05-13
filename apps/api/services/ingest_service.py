"""
FlowSync Ingest Service — bulk upsert logic for all 6 entity types.

Uses batched multi-row INSERT ... ON CONFLICT for ~100x throughput vs row-by-row.
Each function accepts a list of validated Pydantic models and performs bulk upsert
into the raw.* tables with tenant isolation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import UUID

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

BATCH_CHUNK_SIZE = 500


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(val: Any) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def _bulk_upsert(
    db: Session,
    sql_template: str,
    all_params: List[dict],
    entity_name: str,
) -> IngestResponse:
    """
    Execute bulk upserts in chunks. Uses executemany for efficiency.
    Returns aggregate counts.
    """
    total = len(all_params)
    inserted = 0
    updated = 0
    errors = 0

    for chunk_start in range(0, total, BATCH_CHUNK_SIZE):
        chunk = all_params[chunk_start:chunk_start + BATCH_CHUNK_SIZE]
        try:
            result = db.execute(text(sql_template), chunk)
            rows = result.fetchall()
            for row in rows:
                if row[0] == 1:
                    inserted += 1
                else:
                    updated += 1
        except Exception as exc:
            db.rollback()
            logger.error(
                "bulk_upsert_chunk_error",
                entity=entity_name,
                chunk_start=chunk_start,
                chunk_size=len(chunk),
                error=str(exc)[:200],
            )
            errors += len(chunk)

    if errors == 0:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("commit_error", entity=entity_name, error=str(exc)[:200])
            return IngestResponse(
                inserted=0, updated=0, error_count=total,
                message=f"Commit failed for {entity_name}: database error.",
            )

    logger.info(f"{entity_name}_upserted", inserted=inserted, updated=updated, errors=errors)
    return IngestResponse(
        inserted=inserted,
        updated=updated,
        error_count=errors,
        message=f"Processed {total} {entity_name}: {inserted} new, {updated} updated, {errors} errors.",
    )


# ─── Accounts ────────────────────────────────────────────────────────────────

_ACCOUNT_UPSERT = """
INSERT INTO raw.raw_accounts (
    tenant_id, account_id, company_name, industry, region, company_size,
    country, acquisition_channel, account_owner, created_at, website,
    annual_revenue_usd, employee_count, _loaded_at
)
VALUES (
    :tenant_id, :account_id, :company_name, :industry, :region, :company_size,
    :country, :acquisition_channel, :account_owner, :created_at, :website,
    :annual_revenue_usd, :employee_count, :_loaded_at
)
ON CONFLICT (account_id) WHERE tenant_id = :tenant_id DO UPDATE SET
    company_name        = EXCLUDED.company_name,
    industry            = EXCLUDED.industry,
    region              = EXCLUDED.region,
    company_size        = EXCLUDED.company_size,
    country             = EXCLUDED.country,
    acquisition_channel = EXCLUDED.acquisition_channel,
    account_owner       = EXCLUDED.account_owner,
    website             = EXCLUDED.website,
    annual_revenue_usd  = EXCLUDED.annual_revenue_usd,
    employee_count      = EXCLUDED.employee_count,
    _loaded_at          = EXCLUDED._loaded_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_accounts(db: Session, records: List[AccountIngest], tenant_id: Optional[UUID] = None) -> IngestResponse:
    loaded_at = _now_utc()
    params_list = []
    for rec in records:
        params_list.append({
            "tenant_id":           str(tenant_id) if tenant_id else None,
            "account_id":          rec.account_id,
            "company_name":        rec.company_name,
            "industry":            rec.industry,
            "region":              rec.region,
            "company_size":        rec.company_size,
            "country":             rec.country,
            "acquisition_channel": rec.acquisition_channel,
            "account_owner":       rec.account_owner,
            "created_at":          _iso(rec.created_at),
            "website":             rec.website,
            "annual_revenue_usd":  None,
            "employee_count":      None,
            "_loaded_at":          loaded_at,
        })
    return _bulk_upsert(db, _ACCOUNT_UPSERT, params_list, "accounts")


# ─── Subscriptions ───────────────────────────────────────────────────────────

_SUBSCRIPTION_UPSERT = """
INSERT INTO raw.raw_subscriptions (
    tenant_id, subscription_id, account_id, plan_id, status,
    billing_cycle, mrr, arr, seats, start_date, end_date,
    trial_start, trial_end, cancelled_at, cancellation_reason,
    discount_pct, _loaded_at
)
VALUES (
    :tenant_id, :subscription_id, :account_id, :plan_id, :status,
    :billing_cycle, :mrr, :arr, :seats, :start_date, :end_date,
    :trial_start, :trial_end, :cancelled_at, :cancellation_reason,
    :discount_pct, :_loaded_at
)
ON CONFLICT (subscription_id) WHERE tenant_id = :tenant_id DO UPDATE SET
    account_id          = EXCLUDED.account_id,
    plan_id             = EXCLUDED.plan_id,
    status              = EXCLUDED.status,
    billing_cycle       = EXCLUDED.billing_cycle,
    mrr                 = EXCLUDED.mrr,
    arr                 = EXCLUDED.arr,
    seats               = EXCLUDED.seats,
    start_date          = EXCLUDED.start_date,
    end_date            = EXCLUDED.end_date,
    trial_start         = EXCLUDED.trial_start,
    trial_end           = EXCLUDED.trial_end,
    cancelled_at        = EXCLUDED.cancelled_at,
    cancellation_reason = EXCLUDED.cancellation_reason,
    discount_pct        = EXCLUDED.discount_pct,
    _loaded_at          = EXCLUDED._loaded_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_subscriptions(db: Session, records: List[SubscriptionIngest], tenant_id: Optional[UUID] = None) -> IngestResponse:
    loaded_at = _now_utc()
    params_list = []
    for rec in records:
        arr = rec.arr if hasattr(rec, 'arr') and rec.arr is not None else round(rec.mrr * 12, 2)
        params_list.append({
            "tenant_id":           str(tenant_id) if tenant_id else None,
            "subscription_id":     rec.subscription_id,
            "account_id":          rec.account_id,
            "plan_id":             rec.plan_id,
            "status":              rec.status,
            "billing_cycle":       getattr(rec, 'billing_interval', None) or getattr(rec, 'billing_cycle', 'monthly'),
            "mrr":                 rec.mrr,
            "arr":                 arr,
            "seats":               rec.seats,
            "start_date":          _iso(getattr(rec, 'started_at', None) or getattr(rec, 'start_date', None)),
            "end_date":            _iso(getattr(rec, 'canceled_at', None) or getattr(rec, 'end_date', None)),
            "trial_start":         _iso(getattr(rec, 'trial_started_at', None) or getattr(rec, 'trial_start', None)),
            "trial_end":           _iso(getattr(rec, 'trial_ended_at', None) or getattr(rec, 'trial_end', None)),
            "cancelled_at":        _iso(getattr(rec, 'canceled_at', None)),
            "cancellation_reason": getattr(rec, 'cancellation_reason', None),
            "discount_pct":        getattr(rec, 'discount_pct', 0.0),
            "_loaded_at":          loaded_at,
        })
    return _bulk_upsert(db, _SUBSCRIPTION_UPSERT, params_list, "subscriptions")


# ─── Invoices ────────────────────────────────────────────────────────────────

_INVOICE_UPSERT = """
INSERT INTO raw.raw_invoices (
    tenant_id, invoice_id, account_id, subscription_id, invoice_date,
    due_date, amount, currency, status, payment_method,
    paid_at, failure_reason, retry_count, _loaded_at
)
VALUES (
    :tenant_id, :invoice_id, :account_id, :subscription_id, :invoice_date,
    :due_date, :amount, :currency, :status, :payment_method,
    :paid_at, :failure_reason, :retry_count, :_loaded_at
)
ON CONFLICT (invoice_id) WHERE tenant_id = :tenant_id DO UPDATE SET
    account_id      = EXCLUDED.account_id,
    subscription_id = EXCLUDED.subscription_id,
    invoice_date    = EXCLUDED.invoice_date,
    due_date        = EXCLUDED.due_date,
    amount          = EXCLUDED.amount,
    currency        = EXCLUDED.currency,
    status          = EXCLUDED.status,
    payment_method  = EXCLUDED.payment_method,
    paid_at         = EXCLUDED.paid_at,
    failure_reason  = EXCLUDED.failure_reason,
    retry_count     = EXCLUDED.retry_count,
    _loaded_at      = EXCLUDED._loaded_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_invoices(db: Session, records: List[InvoiceIngest], tenant_id: Optional[UUID] = None) -> IngestResponse:
    loaded_at = _now_utc()
    params_list = []
    for rec in records:
        params_list.append({
            "tenant_id":       str(tenant_id) if tenant_id else None,
            "invoice_id":      rec.invoice_id,
            "account_id":      rec.account_id,
            "subscription_id": rec.subscription_id,
            "invoice_date":    _iso(rec.invoice_date),
            "due_date":        _iso(rec.due_date),
            "amount":          rec.amount,
            "currency":        getattr(rec, 'currency', 'USD'),
            "status":          rec.status,
            "payment_method":  rec.payment_method,
            "paid_at":         _iso(rec.paid_at),
            "failure_reason":  getattr(rec, 'failure_reason', None),
            "retry_count":     getattr(rec, 'attempt_count', 0) or 0,
            "_loaded_at":      loaded_at,
        })
    return _bulk_upsert(db, _INVOICE_UPSERT, params_list, "invoices")


# ─── Usage Events ────────────────────────────────────────────────────────────

_USAGE_UPSERT = """
INSERT INTO raw.raw_usage_events (
    tenant_id, event_id, account_id, user_id, feature_id,
    event_type, event_date, session_duration_min, actions_count, _loaded_at
)
VALUES (
    :tenant_id, :event_id, :account_id, :user_id, :feature_id,
    :event_type, :event_date, :session_duration_min, :actions_count, :_loaded_at
)
ON CONFLICT (event_id) WHERE tenant_id = :tenant_id DO UPDATE SET
    account_id          = EXCLUDED.account_id,
    user_id             = EXCLUDED.user_id,
    feature_id          = EXCLUDED.feature_id,
    event_type          = EXCLUDED.event_type,
    event_date          = EXCLUDED.event_date,
    session_duration_min = EXCLUDED.session_duration_min,
    actions_count       = EXCLUDED.actions_count,
    _loaded_at          = EXCLUDED._loaded_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_usage_events(db: Session, records: List[UsageEventIngest], tenant_id: Optional[UUID] = None) -> IngestResponse:
    loaded_at = _now_utc()
    params_list = []
    for rec in records:
        params_list.append({
            "tenant_id":           str(tenant_id) if tenant_id else None,
            "event_id":            rec.event_id,
            "account_id":          rec.account_id,
            "user_id":             rec.user_id,
            "feature_id":          getattr(rec, 'feature_id', None) or getattr(rec, 'feature_name', None),
            "event_type":          rec.event_type or getattr(rec, 'feature_name', 'unknown'),
            "event_date":          _iso(getattr(rec, 'occurred_at', None) or getattr(rec, 'event_date', None)),
            "session_duration_min": getattr(rec, 'session_duration_seconds', None),
            "actions_count":       getattr(rec, 'event_count', 1),
            "_loaded_at":          loaded_at,
        })
    return _bulk_upsert(db, _USAGE_UPSERT, params_list, "usage_events")


# ─── Support Tickets ─────────────────────────────────────────────────────────

_TICKET_UPSERT = """
INSERT INTO raw.raw_tickets (
    tenant_id, ticket_id, account_id, subject, category, priority,
    status, created_at, resolved_at, csat_score, agent_id, _loaded_at
)
VALUES (
    :tenant_id, :ticket_id, :account_id, :subject, :category, :priority,
    :status, :created_at, :resolved_at, :csat_score, :agent_id, :_loaded_at
)
ON CONFLICT (ticket_id) WHERE tenant_id = :tenant_id DO UPDATE SET
    account_id  = EXCLUDED.account_id,
    subject     = EXCLUDED.subject,
    category    = EXCLUDED.category,
    priority    = EXCLUDED.priority,
    status      = EXCLUDED.status,
    resolved_at = EXCLUDED.resolved_at,
    csat_score  = EXCLUDED.csat_score,
    agent_id    = EXCLUDED.agent_id,
    _loaded_at  = EXCLUDED._loaded_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_tickets(db: Session, records: List[TicketIngest], tenant_id: Optional[UUID] = None) -> IngestResponse:
    loaded_at = _now_utc()
    params_list = []
    for rec in records:
        params_list.append({
            "tenant_id":   str(tenant_id) if tenant_id else None,
            "ticket_id":   rec.ticket_id,
            "account_id":  rec.account_id,
            "subject":     rec.subject,
            "category":    rec.category,
            "priority":    rec.priority,
            "status":      rec.status,
            "created_at":  _iso(rec.created_at),
            "resolved_at": _iso(rec.resolved_at),
            "csat_score":  rec.csat_score,
            "agent_id":    getattr(rec, 'agent_id', None),
            "_loaded_at":  loaded_at,
        })
    return _bulk_upsert(db, _TICKET_UPSERT, params_list, "tickets")


# ─── Leads ───────────────────────────────────────────────────────────────────

_LEAD_UPSERT = """
INSERT INTO raw.raw_leads (
    tenant_id, lead_id, company_name, industry, company_size, region,
    acquisition_channel, lead_source, lead_date, trial_start_date,
    trial_end_date, converted_at, account_id, plan_id, first_mrr,
    lost_reason, _loaded_at
)
VALUES (
    :tenant_id, :lead_id, :company_name, :industry, :company_size, :region,
    :acquisition_channel, :lead_source, :lead_date, :trial_start_date,
    :trial_end_date, :converted_at, :account_id, :plan_id, :first_mrr,
    :lost_reason, :_loaded_at
)
ON CONFLICT (lead_id) WHERE tenant_id = :tenant_id DO UPDATE SET
    company_name        = EXCLUDED.company_name,
    industry            = EXCLUDED.industry,
    company_size        = EXCLUDED.company_size,
    region              = EXCLUDED.region,
    acquisition_channel = EXCLUDED.acquisition_channel,
    lead_source         = EXCLUDED.lead_source,
    lead_date           = EXCLUDED.lead_date,
    trial_start_date    = EXCLUDED.trial_start_date,
    trial_end_date      = EXCLUDED.trial_end_date,
    converted_at        = EXCLUDED.converted_at,
    account_id          = EXCLUDED.account_id,
    plan_id             = EXCLUDED.plan_id,
    first_mrr           = EXCLUDED.first_mrr,
    lost_reason         = EXCLUDED.lost_reason,
    _loaded_at          = EXCLUDED._loaded_at
RETURNING (xmax = 0)::int AS is_insert
"""


def upsert_leads(db: Session, records: List[LeadIngest], tenant_id: Optional[UUID] = None) -> IngestResponse:
    loaded_at = _now_utc()
    params_list = []
    for rec in records:
        params_list.append({
            "tenant_id":           str(tenant_id) if tenant_id else None,
            "lead_id":             rec.lead_id,
            "company_name":        rec.company_name,
            "industry":            getattr(rec, 'industry', None),
            "company_size":        getattr(rec, 'company_size', None),
            "region":              getattr(rec, 'region', None),
            "acquisition_channel": getattr(rec, 'acquisition_channel', None),
            "lead_source":         rec.lead_source,
            "lead_date":           _iso(rec.created_at),
            "trial_start_date":    _iso(getattr(rec, 'trial_started_at', None)),
            "trial_end_date":      None,
            "converted_at":        _iso(getattr(rec, 'converted_at', None)),
            "account_id":          getattr(rec, 'account_id', None),
            "plan_id":             None,
            "first_mrr":           getattr(rec, 'converted_mrr', None),
            "lost_reason":         None,
            "_loaded_at":          loaded_at,
        })
    return _bulk_upsert(db, _LEAD_UPSERT, params_list, "leads")
