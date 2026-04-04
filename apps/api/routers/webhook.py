"""
FlowSync Webhook Router — Stripe & Chargebee event receivers.

Stripe events handled:
  - customer.subscription.created   → upsert subscription
  - customer.subscription.updated   → upsert subscription
  - customer.subscription.deleted   → mark subscription churned
  - invoice.payment_succeeded       → upsert invoice (paid)
  - invoice.payment_failed          → upsert invoice (failed)
  - customer.created                → upsert account
  - customer.updated                → upsert account

Routes:
  POST /api/v1/webhooks/stripe
  POST /api/v1/webhooks/chargebee
  GET  /api/v1/webhooks/test        (dev only — echo payload)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.database import get_db
from middleware.api_key_auth import verify_stripe_signature
from schemas.ingest import (
    AccountIngest,
    AccountBatch,
    InvoiceIngest,
    InvoiceBatch,
    SubscriptionIngest,
    SubscriptionBatch,
    WebhookResponse,
)
from services.ingest_service import (
    upsert_accounts,
    upsert_invoices,
    upsert_subscriptions,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
    responses={
        400: {"description": "Invalid webhook payload or signature"},
        401: {"description": "Signature verification failed"},
    },
)

# ─── Config ───────────────────────────────────────────────────────────────────

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_placeholder")
CHARGEBEE_WEBHOOK_SECRET = os.getenv("CHARGEBEE_WEBHOOK_SECRET", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
# Skip signature verification in development OR when explicitly disabled
VERIFY_SIGNATURES = (
    os.getenv("WEBHOOK_VERIFY_SIGNATURES", "true").lower() == "true"
    and ENVIRONMENT != "development"
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_str(val, default: str = "") -> str:
    return str(val) if val is not None else default


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _safe_int(val, default: int = 0) -> int:
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _stripe_ts(ts) -> Optional[str]:
    """Convert Stripe Unix timestamp to ISO string."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None


# ─── Stripe event handlers ────────────────────────────────────────────────────

def _handle_subscription_event(event_data: dict, db: Session) -> str:
    """Handle customer.subscription.* events."""
    obj = event_data.get("object", {})
    event_type = event_data.get("type", "")

    status_map = {
        "customer.subscription.deleted": "churned",
    }
    sub_status = status_map.get(event_type, obj.get("status", "active"))

    # Stripe stores amounts in cents
    amount_cents = _safe_float(obj.get("plan", {}).get("amount") or obj.get("items", {}).get("data", [{}])[0].get("price", {}).get("unit_amount", 0))
    mrr = round(amount_cents / 100, 2)

    rec = SubscriptionIngest(
        subscription_id=_safe_str(obj.get("id"), f"stripe_{_now_iso()}"),
        account_id=_safe_str(obj.get("customer"), "unknown"),
        plan_id=_safe_str(obj.get("plan", {}).get("id") or (obj.get("items", {}).get("data") or [{}])[0].get("price", {}).get("id", "unknown")),
        plan_name=_safe_str(obj.get("plan", {}).get("nickname") or "Stripe Plan"),
        status=sub_status,
        mrr=mrr,
        arr=round(mrr * 12, 2),
        seats=_safe_int(obj.get("quantity"), 1),
        # Schema field names (not DB column names):
        started_at=_stripe_ts(obj.get("start_date")) or _now_iso(),
        canceled_at=_stripe_ts(obj.get("current_period_end")),
        trial_started_at=_stripe_ts(obj.get("trial_start")),
        trial_ended_at=_stripe_ts(obj.get("trial_end")),
        billing_interval=obj.get("plan", {}).get("interval", "monthly") or "monthly",
        updated_at=_now_iso(),
    )

    result = upsert_subscriptions(db, [rec])
    return f"subscription upserted: {result.inserted} new, {result.updated} updated"


def _handle_invoice_event(event_data: dict, db: Session) -> str:
    """Handle invoice.payment_succeeded / invoice.payment_failed events."""
    obj = event_data.get("object", {})
    event_type = event_data.get("type", "")

    inv_status = "paid" if event_type == "invoice.payment_succeeded" else "failed"
    paid_at = _stripe_ts(obj.get("status_transitions", {}).get("paid_at")) if inv_status == "paid" else None

    rec = InvoiceIngest(
        invoice_id=_safe_str(obj.get("id"), f"inv_{_now_iso()}"),
        account_id=_safe_str(obj.get("customer"), "unknown"),
        subscription_id=_safe_str(obj.get("subscription")),
        invoice_date=_stripe_ts(obj.get("created")) or _now_iso(),
        due_date=_stripe_ts(obj.get("due_date")),
        amount=round(_safe_float(obj.get("amount_due", 0)) / 100, 2),
        currency=obj.get("currency", "usd").upper(),
        status=inv_status,
        payment_method=_safe_str(obj.get("payment_settings", {}).get("payment_method_types", ["card"])[0] if obj.get("payment_settings", {}).get("payment_method_types") else "card"),
        attempt_count=_safe_int(obj.get("attempt_count"), 1),  # schema field name
        paid_at=paid_at,
        failed_at=None if inv_status == "paid" else _now_iso(),
        created_at=_stripe_ts(obj.get("created")) or _now_iso(),
    )

    result = upsert_invoices(db, [rec])
    return f"invoice upserted: {result.inserted} new, {result.updated} updated"


def _handle_customer_event(event_data: dict, db: Session) -> str:
    """Handle customer.created / customer.updated events."""
    obj = event_data.get("object", {})

    rec = AccountIngest(
        account_id=_safe_str(obj.get("id"), f"cust_{_now_iso()}"),
        company_name=_safe_str(obj.get("name") or obj.get("description") or "Unknown Company"),
        industry=None,
        region=None,
        company_size=None,
        acquisition_channel="stripe",
        # account_owner maps to primary_contact_name in ingest_service
        account_owner=_safe_str(obj.get("name")) or None,
        website=_safe_str(obj.get("metadata", {}).get("website")) or None,
        country=_safe_str(obj.get("address", {}).get("country") if obj.get("address") else None) or None,
        created_at=_stripe_ts(obj.get("created")) or _now_iso(),
        updated_at=_now_iso(),
    )

    result = upsert_accounts(db, [rec])
    return f"account upserted: {result.inserted} new, {result.updated} updated"


# ─── Stripe webhook endpoint ───────────────────────────────────────────────────

@router.post(
    "/stripe",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook receiver",
    description=(
        "Receives Stripe webhook events and upserts data into the raw layer. "
        "Verifies the `Stripe-Signature` header using HMAC-SHA256. "
        "Set `STRIPE_WEBHOOK_SECRET` env var to your Stripe webhook signing secret."
    ),
)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
) -> WebhookResponse:
    # ── 1. Read raw body ──────────────────────────────────────────────────────
    body_bytes = await request.body()

    # ── 2. Verify signature ───────────────────────────────────────────────────
    if VERIFY_SIGNATURES:
        if not stripe_signature:
            logger.warning("stripe_webhook_missing_signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "missing_signature", "message": "Stripe-Signature header is required."},
            )
        if not verify_stripe_signature(body_bytes, stripe_signature, STRIPE_WEBHOOK_SECRET):
            logger.warning("stripe_webhook_invalid_signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_signature", "message": "Webhook signature verification failed."},
            )

    # ── 3. Parse event ────────────────────────────────────────────────────────
    try:
        event = json.loads(body_bytes)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_json", "message": str(exc)},
        )

    event_type = event.get("type", "unknown")
    event_id   = event.get("id", "unknown")
    event_data = event.get("data", {})

    logger.info("stripe_webhook_received", event_type=event_type, event_id=event_id)

    # ── 4. Route to handler ───────────────────────────────────────────────────
    handled_types = {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_succeeded",
        "invoice.payment_failed",
        "customer.created",
        "customer.updated",
    }

    if event_type not in handled_types:
        logger.info("stripe_webhook_ignored", event_type=event_type)
        return WebhookResponse(
            received=True,
            event_type=event_type,
            event_id=event_id,
            processed=False,
            message=f"Event type '{event_type}' is acknowledged but not processed.",
        )

    try:
        if event_type.startswith("customer.subscription"):
            detail = _handle_subscription_event({"type": event_type, "object": event_data.get("object", {})}, db)
        elif event_type.startswith("invoice"):
            detail = _handle_invoice_event({"type": event_type, "object": event_data.get("object", {})}, db)
        elif event_type.startswith("customer"):
            detail = _handle_customer_event({"type": event_type, "object": event_data.get("object", {})}, db)
        else:
            detail = "no handler matched"

        logger.info("stripe_webhook_processed", event_type=event_type, detail=detail)
        return WebhookResponse(
            received=True,
            event_type=event_type,
            event_id=event_id,
            processed=True,
            message=detail,
        )

    except Exception as exc:
        logger.error("stripe_webhook_handler_error", event_type=event_type, error=str(exc))
        # Return 200 to prevent Stripe retries for handler errors
        return WebhookResponse(
            received=True,
            event_type=event_type,
            event_id=event_id,
            processed=False,
            message=f"Handler error: {str(exc)}",
        )


# ─── Chargebee webhook endpoint ───────────────────────────────────────────────

@router.post(
    "/chargebee",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Chargebee webhook receiver",
    description=(
        "Receives Chargebee webhook events. "
        "Handles subscription_created, subscription_changed, subscription_cancelled, "
        "payment_succeeded, payment_failed events."
    ),
)
async def chargebee_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> WebhookResponse:
    body_bytes = await request.body()

    try:
        event = json.loads(body_bytes)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_json", "message": str(exc)},
        )

    event_type = event.get("event_type", "unknown")
    content    = event.get("content", {})

    logger.info("chargebee_webhook_received", event_type=event_type)

    # Map Chargebee events to handlers
    if event_type in ("subscription_created", "subscription_changed", "subscription_cancelled"):
        sub = content.get("subscription", {})
        plan = content.get("plan", {})

        status_val = "churned" if event_type == "subscription_cancelled" else sub.get("status", "active")
        mrr = round(_safe_float(sub.get("mrr", 0)) / 100, 2)

        rec = SubscriptionIngest(
            subscription_id=_safe_str(sub.get("id"), f"cb_{_now_iso()}"),
            account_id=_safe_str(sub.get("customer_id"), "unknown"),
            plan_id=_safe_str(sub.get("plan_id"), "unknown"),
            plan_name=_safe_str(plan.get("name") or sub.get("plan_id") or "Chargebee Plan"),
            status=status_val,
            mrr=mrr,
            arr=round(mrr * 12, 2),
            seats=_safe_int(sub.get("plan_quantity"), 1),
            # Schema field names (not DB column names):
            started_at=_stripe_ts(sub.get("started_at")) or _now_iso(),
            canceled_at=_stripe_ts(sub.get("current_term_end")),
            trial_started_at=_stripe_ts(sub.get("trial_start")),
            trial_ended_at=_stripe_ts(sub.get("trial_end")),
            billing_interval=sub.get("billing_period_unit", "monthly") or "monthly",
            updated_at=_now_iso(),
        )
        result = upsert_subscriptions(db, [rec])
        msg = f"subscription upserted: {result.inserted} new, {result.updated} updated"

    elif event_type in ("payment_succeeded", "payment_failed"):
        # Chargebee sends either content.transaction or content.invoice depending on version
        txn = content.get("transaction") or content.get("invoice") or {}
        inv_status = "paid" if event_type == "payment_succeeded" else "failed"

        # Chargebee amounts may already be in dollars (invoice) or cents (transaction)
        raw_amount = _safe_float(
            txn.get("amount_paid") or txn.get("amount") or txn.get("total") or 0
        )
        # Heuristic: if amount > 1000 and no decimal, treat as cents
        amount = round(raw_amount / 100, 2) if raw_amount > 1000 else round(raw_amount, 2)

        rec = InvoiceIngest(
            invoice_id=_safe_str(txn.get("id"), f"cb_txn_{_now_iso()}"),
            account_id=_safe_str(
                txn.get("customer_id") or txn.get("customer"), "unknown"
            ),
            subscription_id=_safe_str(
                txn.get("subscription_id") or txn.get("subscription")
            ),
            invoice_date=_stripe_ts(txn.get("date")) or _now_iso(),
            due_date=None,
            amount=amount,
            currency=_safe_str(
                txn.get("currency_code") or txn.get("currency"), "USD"
            ).upper(),
            status=inv_status,
            payment_method=_safe_str(txn.get("payment_method", "card")),
            attempt_count=1,
            paid_at=_now_iso() if inv_status == "paid" else None,
            failed_at=_now_iso() if inv_status == "failed" else None,
            created_at=_stripe_ts(txn.get("date")) or _now_iso(),
        )
        try:
            result = upsert_invoices(db, [rec])
            msg = f"invoice upserted: {result.inserted} new, {result.updated} updated"
        except Exception as exc:
            logger.warning("chargebee_invoice_upsert_error", error=str(exc))
            msg = f"invoice acknowledged but not persisted: {str(exc)[:120]}"

    else:
        logger.info("chargebee_webhook_ignored", event_type=event_type)
        return WebhookResponse(
            received=True,
            event_type=event_type,
            event_id=event.get("id", "unknown"),
            processed=False,
            message=f"Event type '{event_type}' acknowledged but not processed.",
        )

    return WebhookResponse(
        received=True,
        event_type=event_type,
        event_id=event.get("id", "unknown"),
        processed=True,
        message=msg,
    )


# ─── Test endpoint (dev only) ─────────────────────────────────────────────────

@router.post(
    "/test",
    summary="Echo webhook payload (dev only)",
    description="Echoes the raw webhook payload. Disable in production via WEBHOOK_TEST_ENABLED=false.",
    include_in_schema=os.getenv("ENVIRONMENT", "development") == "development",
)
async def test_webhook(request: Request) -> dict:
    if os.getenv("ENVIRONMENT", "development") != "development":
        raise HTTPException(status_code=404, detail="Not found")

    body_bytes = await request.body()
    try:
        body = json.loads(body_bytes)
    except Exception:
        body = body_bytes.decode("utf-8", errors="replace")

    return {
        "echo": body,
        "headers": dict(request.headers),
        "method": request.method,
        "url": str(request.url),
    }
