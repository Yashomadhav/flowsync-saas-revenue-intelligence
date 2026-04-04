"""
Pydantic schemas for Customer Health & Churn Risk dashboard endpoints.
Covers: health distribution, churn risk quadrant, usage drop trends,
support burden, risky accounts table.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class HealthDistributionItem(BaseModel):
    """Count of accounts in each health tier for a given month."""
    health_tier: str = Field(..., description="healthy | at_risk | high_risk | critical")
    account_count: int
    total_mrr: float
    avg_health_score: float
    pct_of_accounts: float = Field(..., description="Percentage of total active accounts")
    pct_of_mrr: float = Field(..., description="Percentage of total MRR")


class HealthDistributionResponse(BaseModel):
    month_key: str
    total_accounts: int
    total_mrr: float
    data: list[HealthDistributionItem]


class ChurnRiskQuadrantItem(BaseModel):
    """Single account plotted in the churn risk quadrant (usage vs health)."""
    account_id: str
    company_name: str
    plan_name: str
    region: str
    company_size: str
    mrr: float
    health_score: float = Field(..., description="0-100, x-axis")
    churn_risk_score: float = Field(..., description="0-100, y-axis (higher = more risk)")
    churn_risk_level: str = Field(..., description="minimal | low | medium | high | critical")
    health_tier: str
    usage_score: float = Field(..., description="Usage component of health score 0-100")
    seat_utilization: float = Field(..., description="Seat utilization 0-100%")
    risk_flag_count: int
    risk_reasons: list[str]
    quadrant: str = Field(
        ...,
        description="safe | monitor | at_risk | critical — derived from health/risk scores"
    )


class ChurnRiskQuadrantResponse(BaseModel):
    month_key: str
    total_accounts: int
    data: list[ChurnRiskQuadrantItem]
    quadrant_counts: dict[str, int] = Field(
        ...,
        description="Count per quadrant: safe, monitor, at_risk, critical"
    )
    quadrant_mrr: dict[str, float] = Field(
        ...,
        description="Total MRR per quadrant"
    )


class UsageDropTrendPoint(BaseModel):
    """Monthly count of accounts with significant usage drops."""
    month_key: str
    accounts_with_usage_drop: int = Field(..., description="Accounts with >40% MoM usage drop")
    accounts_no_login_14d: int = Field(..., description="Accounts with no login in 14 days")
    avg_usage_drop_pct: float = Field(..., description="Average usage drop % among flagged accounts")
    total_active_accounts: int
    pct_accounts_at_usage_risk: float


class UsageDropTrendResponse(BaseModel):
    data: list[UsageDropTrendPoint]
    months: int


class SupportBurdenItem(BaseModel):
    """Support ticket burden per account."""
    account_id: str
    company_name: str
    plan_name: str
    mrr: float
    health_score: float
    health_tier: str
    open_tickets: int
    high_priority_tickets: int
    unresolved_high_priority: int
    avg_resolution_hours: Optional[float] = None
    csat_score: Optional[float] = None
    support_score: float = Field(..., description="Support health component 0-100 (lower = worse)")
    has_support_risk_flag: bool


class SupportBurdenResponse(BaseModel):
    month_key: str
    total_accounts: int
    data: list[SupportBurdenItem]


class RiskyAccountItem(BaseModel):
    """Account flagged as churn risk with detailed risk breakdown."""
    account_id: str
    company_name: str
    plan_name: str
    region: str
    industry: str
    company_size: str
    mrr: float
    arr: float
    health_score: float
    health_tier: str
    churn_risk_level: str
    churn_risk_score: float
    risk_priority_score: float = Field(..., description="Composite urgency score for sorting")
    risk_flag_count: int
    risk_reasons: list[str]
    health_trend: str = Field(..., description="improving | stable | declining")
    usage_score: float
    seat_utilization: float
    open_tickets: int
    days_since_last_login: Optional[int] = None
    payment_failed: bool
    csat_score: Optional[float] = None
    months_as_customer: int
    snapshot_month: str


class RiskyAccountsResponse(BaseModel):
    month_key: str
    total_at_risk: int
    total_at_risk_mrr: float
    page: int
    page_size: int
    total_count: int
    filters_applied: dict[str, str]
    data: list[RiskyAccountItem]
