"""
Pydantic schemas for Revenue Movements dashboard endpoints.
Covers: MRR bridge, account movements, new MRR by channel,
expansion by segment, churned by plan, payment trends.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class MRRBridgePoint(BaseModel):
    """Single month in the MRR bridge / waterfall time series."""
    month_key: str
    starting_mrr: float
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float = Field(..., description="Positive value representing loss")
    churned_mrr: float = Field(..., description="Positive value representing loss")
    reactivation_mrr: float
    net_new_mrr: float
    ending_mrr: float


class MRRBridgeResponse(BaseModel):
    data: list[MRRBridgePoint]
    months: int


class AccountMovementItem(BaseModel):
    """Account-level MRR movement for the movement table."""
    account_id: str
    company_name: str
    plan_name: str
    region: str
    industry: str
    company_size: str
    month_key: str
    mrr: float
    prev_mrr: Optional[float] = None
    mrr_delta: Optional[float] = None
    mrr_movement_type: str = Field(
        ...,
        description="new | expansion | contraction | retained | reactivation | churned"
    )
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    churned_mrr: float
    reactivation_mrr: float
    net_mrr_contribution: float
    acquisition_channel: Optional[str] = None


class AccountMovementResponse(BaseModel):
    month_key: str
    total_count: int
    page: int
    page_size: int
    data: list[AccountMovementItem]


class NewMRRByChannelItem(BaseModel):
    """New MRR breakdown by acquisition channel."""
    channel: str
    month_key: str
    new_mrr: float
    new_accounts: int
    avg_mrr_per_account: float
    pct_of_total_new_mrr: float


class NewMRRByChannelResponse(BaseModel):
    month_key: str
    total_new_mrr: float
    data: list[NewMRRByChannelItem]


class ExpansionBySegmentItem(BaseModel):
    """Expansion MRR breakdown by company size segment."""
    segment: str = Field(..., description="company_size or plan_name segment")
    month_key: str
    expansion_mrr: float
    expanding_accounts: int
    avg_expansion_per_account: float
    pct_of_total_expansion: float


class ExpansionBySegmentResponse(BaseModel):
    month_key: str
    dimension: str = Field(..., description="company_size | plan_name | region")
    total_expansion_mrr: float
    data: list[ExpansionBySegmentItem]


class ChurnedByPlanItem(BaseModel):
    """Churned MRR breakdown by plan."""
    plan_name: str
    month_key: str
    churned_mrr: float
    churned_accounts: int
    avg_churned_mrr: float
    pct_of_total_churned: float


class ChurnedByPlanResponse(BaseModel):
    month_key: str
    total_churned_mrr: float
    data: list[ChurnedByPlanItem]


class PaymentTrendPoint(BaseModel):
    """Monthly payment success / failure trend."""
    month_key: str
    total_invoices: int
    paid_invoices: int
    failed_invoices: int
    pending_invoices: int
    payment_success_rate: float = Field(..., description="Percentage 0-100")
    total_invoice_amount: float
    collected_amount: float
    failed_amount: float
    avg_days_to_pay: Optional[float] = None


class PaymentTrendResponse(BaseModel):
    data: list[PaymentTrendPoint]
    months: int
