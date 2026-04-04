"""
Pydantic schemas for Funnel & Growth dashboard endpoints.
Covers: funnel overview, conversion by channel, sales cycle,
trial engagement, expansion by segment.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class FunnelOverviewResponse(BaseModel):
    """Top-level funnel conversion summary for a given period."""
    period_months: int = Field(..., description="Number of months in the analysis window")
    total_leads: int
    qualified_leads: int
    demo_requested: int
    demo_completed: int
    trial_starts: int
    paid_conversions: int
    lead_to_qualified_rate: float = Field(..., description="Percentage 0-100")
    qualified_to_demo_rate: float
    demo_to_trial_rate: float
    trial_to_paid_rate: float
    lead_to_trial_rate: float
    overall_conversion_rate: float = Field(..., description="Lead to paid %")
    avg_days_lead_to_paid: float
    avg_days_lead_to_trial: float
    avg_days_trial_to_paid: float
    avg_trial_engagement_score: float = Field(..., description="0-100 engagement during trial")
    total_converted_mrr: float = Field(..., description="Total MRR from converted accounts")
    avg_first_month_mrr: float


class ConversionByChannelItem(BaseModel):
    """Funnel conversion metrics broken down by acquisition channel."""
    channel: str
    total_leads: int
    trial_starts: int
    paid_conversions: int
    lead_to_trial_rate: float = Field(..., description="Percentage 0-100")
    trial_to_paid_rate: float = Field(..., description="Percentage 0-100")
    overall_conversion_rate: float
    avg_days_to_convert: float
    avg_first_month_mrr: float
    total_converted_mrr: float
    pct_of_total_leads: float
    pct_of_total_conversions: float


class ConversionByChannelResponse(BaseModel):
    period_months: int
    total_leads: int
    total_conversions: int
    data: list[ConversionByChannelItem]
    best_channel_by_conversion: Optional[str] = None
    best_channel_by_mrr: Optional[str] = None


class SalesCycleItem(BaseModel):
    """Sales cycle duration statistics by channel and plan."""
    channel: str
    plan_name: str
    avg_days: float
    median_days: float
    min_days: float
    max_days: float
    conversions: int
    avg_mrr: float


class SalesCycleResponse(BaseModel):
    period_months: int
    data: list[SalesCycleItem]
    overall_avg_days: float
    overall_median_days: float


class TrialEngagementItem(BaseModel):
    """Trial engagement vs paid conversion correlation."""
    engagement_bucket: str = Field(
        ...,
        description="Engagement tier: very_low | low | medium | high | very_high"
    )
    trial_count: int
    paid_conversions: int
    conversion_rate: float = Field(..., description="Percentage 0-100")
    avg_engagement_score: float
    avg_converted_mrr: float
    avg_days_to_convert: Optional[float] = None


class TrialEngagementResponse(BaseModel):
    period_months: int
    total_trials: int
    data: list[TrialEngagementItem]
    correlation_insight: str = Field(
        ...,
        description="Human-readable insight about engagement vs conversion correlation"
    )


class ExpansionBySegmentFunnelItem(BaseModel):
    """Expansion MRR breakdown by segment for the Funnel page."""
    company_size: str
    acquisition_channel: str
    plan_name: str
    total_expansion_mrr: float
    expanding_accounts: int
    avg_expansion_per_account: float
    pct_of_total_expansion: float
    months_to_first_expansion: Optional[float] = Field(
        None,
        description="Average months from acquisition to first expansion"
    )


class ExpansionBySegmentFunnelResponse(BaseModel):
    period_months: int
    total_expansion_mrr: float
    total_expanding_accounts: int
    data: list[ExpansionBySegmentFunnelItem]
    top_expansion_segment: Optional[str] = None
