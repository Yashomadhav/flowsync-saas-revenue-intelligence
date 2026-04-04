"""
Pydantic schemas for the FlowSync data ingestion API.
All ingest endpoints accept arrays of these models (batch upsert).
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator
import uuid


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _uuid_str() -> str:
    return str(uuid.uuid4())


class IngestResponse(BaseModel):
    inserted: int = 0
    updated: int = 0
    error_count: int = 0          # number of records that failed (not a list — use logs for details)
    message: str = "OK"


# ─── Account ──────────────────────────────────────────────────────────────────

class AccountIngest(BaseModel):
    account_id: str = Field(..., description="Unique account identifier (your CRM/billing ID)")
    company_name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = None
    company_size: Optional[Literal["startup", "smb", "mid_market", "enterprise"]] = None
    region: Optional[str] = None
    country: Optional[str] = None
    acquisition_channel: Optional[str] = None
    account_owner: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("account_id")
    @classmethod
    def strip_account_id(cls, v: str) -> str:
        return v.strip()


class AccountBatch(BaseModel):
    records: List[AccountIngest] = Field(..., min_length=1, max_length=1000)


# ─── Subscription ─────────────────────────────────────────────────────────────

class SubscriptionIngest(BaseModel):
    subscription_id: str = Field(..., description="Unique subscription ID from billing system")
    account_id: str = Field(..., description="Must match an existing account_id")
    plan_name: str = Field(..., description="e.g. Starter, Growth, Enterprise")
    plan_id: Optional[str] = None
    mrr: float = Field(..., ge=0, description="Monthly recurring revenue in USD")
    arr: Optional[float] = Field(None, ge=0)
    status: Literal["active", "trialing", "past_due", "canceled", "paused"] = "active"
    billing_interval: Optional[Literal["monthly", "quarterly", "annual"]] = "monthly"
    seats: Optional[int] = Field(None, ge=0)
    started_at: Optional[datetime] = None
    trial_started_at: Optional[datetime] = None
    trial_ended_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("mrr")
    @classmethod
    def normalize_mrr(cls, v: float, info) -> float:
        """Normalize annual/quarterly billing to monthly MRR."""
        # Caller should pass already-normalized MRR, but we validate it's reasonable
        if v > 1_000_000:
            raise ValueError("MRR exceeds $1M — did you pass ARR instead of MRR?")
        return round(v, 2)


class SubscriptionBatch(BaseModel):
    records: List[SubscriptionIngest] = Field(..., min_length=1, max_length=1000)


# ─── Invoice ──────────────────────────────────────────────────────────────────

class InvoiceIngest(BaseModel):
    invoice_id: str = Field(..., description="Unique invoice ID from billing system")
    account_id: str
    subscription_id: Optional[str] = None
    amount: float = Field(..., ge=0, description="Invoice amount in USD")
    currency: str = Field(default="USD", max_length=3)
    status: Literal["paid", "open", "void", "uncollectible", "draft"] = "paid"
    payment_method: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    attempt_count: Optional[int] = Field(None, ge=0)
    created_at: Optional[datetime] = None


class InvoiceBatch(BaseModel):
    records: List[InvoiceIngest] = Field(..., min_length=1, max_length=5000)


# ─── Usage Event ──────────────────────────────────────────────────────────────

class UsageEventIngest(BaseModel):
    event_id: Optional[str] = Field(default_factory=_uuid_str)
    account_id: str
    user_id: Optional[str] = None
    feature_name: str = Field(..., description="e.g. workflow_run, api_call, report_export")
    event_type: Optional[str] = None
    event_count: int = Field(default=1, ge=0)
    session_duration_seconds: Optional[int] = Field(None, ge=0)
    occurred_at: datetime = Field(..., description="When the event occurred (UTC)")
    properties: Optional[dict] = Field(default_factory=dict)

    @field_validator("feature_name")
    @classmethod
    def lowercase_feature(cls, v: str) -> str:
        return v.lower().strip().replace(" ", "_")


class UsageEventBatch(BaseModel):
    records: List[UsageEventIngest] = Field(..., min_length=1, max_length=10000)


# ─── Support Ticket ───────────────────────────────────────────────────────────

class TicketIngest(BaseModel):
    ticket_id: str = Field(..., description="Unique ticket ID from support system")
    account_id: str
    user_id: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = "medium"
    status: Optional[Literal["open", "pending", "resolved", "closed"]] = "open"
    csat_score: Optional[float] = Field(None, ge=1, le=5, description="Customer satisfaction 1-5")
    resolution_time_hours: Optional[float] = Field(None, ge=0)
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TicketBatch(BaseModel):
    records: List[TicketIngest] = Field(..., min_length=1, max_length=5000)


# ─── Lead / Opportunity ───────────────────────────────────────────────────────

class LeadIngest(BaseModel):
    lead_id: str = Field(..., description="Unique lead/opportunity ID from CRM")
    company_name: Optional[str] = None
    contact_email: Optional[str] = None
    acquisition_channel: Optional[str] = None
    lead_source: Optional[str] = None
    funnel_stage: Optional[Literal["lead", "mql", "sql", "trial", "opportunity", "closed_won", "closed_lost"]] = "lead"
    is_trial: Optional[bool] = False
    is_paid_conversion: Optional[bool] = False
    converted_account_id: Optional[str] = None
    converted_mrr: Optional[float] = Field(None, ge=0)
    industry: Optional[str] = None
    company_size: Optional[str] = None
    region: Optional[str] = None
    lead_score: Optional[int] = Field(None, ge=0, le=100)
    days_lead_to_trial: Optional[int] = Field(None, ge=0)
    days_trial_to_paid: Optional[int] = Field(None, ge=0)
    days_lead_to_paid: Optional[int] = Field(None, ge=0)
    created_at: Optional[datetime] = None
    trial_started_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


class LeadBatch(BaseModel):
    records: List[LeadIngest] = Field(..., min_length=1, max_length=5000)


# ─── Stripe Webhook ───────────────────────────────────────────────────────────

class StripeWebhookPayload(BaseModel):
    """Raw Stripe webhook event envelope."""
    id: str
    type: str
    created: int
    data: dict
    livemode: bool = False
    api_version: Optional[str] = None


class WebhookResponse(BaseModel):
    received: bool = True
    event_type: str
    event_id: Optional[str] = None
    processed: bool = False
    message: str = ""
