"""
Pydantic schemas for Cohort Retention dashboard endpoints.
Covers: cohort heatmap, logo churn trend, NRR by cohort, retention by segment.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class CohortHeatmapCell(BaseModel):
    """Single cell in the cohort retention heatmap."""
    cohort_month: str = Field(..., description="YYYY-MM acquisition cohort")
    months_since_created: int = Field(..., description="0 = cohort month, 1 = month+1, etc.")
    cohort_size: int = Field(..., description="Original accounts in cohort")
    active_accounts: int
    logo_retention_rate: float = Field(..., description="0.0 to 1.0")
    revenue_retention_rate: float = Field(..., description="Can exceed 1.0 with expansion")
    nrr: float = Field(..., description="Net Revenue Retention (same as revenue_retention_rate)")
    grr: float = Field(..., description="Gross Revenue Retention, capped at 1.0")
    cohort_mrr: float
    starting_mrr: float
    cohort_health: str = Field(..., description="excellent | good | fair | poor")


class CohortHeatmapResponse(BaseModel):
    """Full cohort heatmap data — list of cells for all cohort × period combinations."""
    cohorts: list[str] = Field(..., description="Sorted list of cohort months (YYYY-MM)")
    max_periods: int = Field(..., description="Maximum months_since_created in dataset")
    metric: str = Field(..., description="logo_retention | revenue_retention | nrr | grr")
    data: list[CohortHeatmapCell]
    total_cells: int


class LogoChurnTrendPoint(BaseModel):
    """Monthly logo churn trend data point."""
    month_key: str
    churned_accounts: int
    starting_accounts: int
    logo_churn_rate: float = Field(..., description="Percentage 0-100")
    revenue_churn_rate: float = Field(..., description="Percentage 0-100")
    churned_mrr: float
    starting_mrr: float
    rolling_3m_logo_churn: Optional[float] = Field(None, description="3-month rolling average")
    rolling_3m_revenue_churn: Optional[float] = None


class LogoChurnTrendResponse(BaseModel):
    data: list[LogoChurnTrendPoint]
    months: int
    avg_logo_churn_rate: float
    avg_revenue_churn_rate: float


class NRRByCohortItem(BaseModel):
    """NRR summary for a single cohort at a specific period."""
    cohort_month: str
    months_since_created: int
    nrr: float = Field(..., description="Net Revenue Retention as decimal (1.12 = 112%)")
    grr: float = Field(..., description="Gross Revenue Retention as decimal")
    cohort_size: int
    active_accounts: int
    logo_retention_rate: float
    cohort_health: str


class NRRByCohortResponse(BaseModel):
    """NRR by cohort at a specific period (e.g. month 3, 6, 12)."""
    period_months: int = Field(..., description="Months since cohort start: 3, 6, or 12")
    data: list[NRRByCohortItem]
    avg_nrr: float
    avg_grr: float
    best_cohort: Optional[str] = None
    worst_cohort: Optional[str] = None


class RetentionBySegmentItem(BaseModel):
    """Retention metrics broken down by a segment dimension."""
    segment_value: str = Field(..., description="e.g. 'Enterprise', 'North America', 'Organic'")
    dimension: str = Field(..., description="plan_name | company_size | region | channel")
    cohort_count: int = Field(..., description="Number of cohorts in this segment")
    avg_logo_retention_3m: Optional[float] = None
    avg_logo_retention_6m: Optional[float] = None
    avg_logo_retention_12m: Optional[float] = None
    avg_nrr_3m: Optional[float] = None
    avg_nrr_6m: Optional[float] = None
    avg_nrr_12m: Optional[float] = None
    avg_grr_12m: Optional[float] = None
    total_accounts: int


class RetentionBySegmentResponse(BaseModel):
    """Retention comparison across segments for a given dimension."""
    dimension: str
    period_months: int
    data: list[RetentionBySegmentItem]
