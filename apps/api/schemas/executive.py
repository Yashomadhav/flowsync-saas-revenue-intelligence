"""
Pydantic schemas for Executive Overview dashboard endpoints.
Covers: KPI cards, MRR trend, revenue waterfall, revenue by dimension, top accounts.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# KPI Summary
# ---------------------------------------------------------------------------

class ExecKPIResponse(BaseModel):
    """Top-level KPI card data for the Executive Overview page."""
    month_key: str = Field(..., description="YYYY-MM of the reporting month")
    total_mrr: float = Field(..., description="Total MRR in USD")
    total_arr: float = Field(..., description="ARR = MRR * 12")
    active_accounts: int = Field(..., description="Accounts with MRR > 0")
    arpa: float = Field(..., description="Average Revenue Per Account (MRR / active accounts)")
    new_mrr: float = Field(..., description="MRR from new accounts this month")
    expansion_mrr: float = Field(..., description="MRR gained from expansion")
    contraction_mrr: float = Field(..., description="MRR lost from contraction (positive)")
    churned_mrr: float = Field(..., description="MRR lost from churn (positive)")
    reactivation_mrr: float = Field(..., description="MRR from reactivated accounts")
    net_new_mrr: float = Field(..., description="Net New MRR = new + expansion + reactivation - contraction - churn")
    nrr: float = Field(..., description="Net Revenue Retention as percentage (e.g. 112.4)")
    grr: float = Field(..., description="Gross Revenue Retention as percentage (e.g. 94.2)")
    logo_churn_rate: float = Field(..., description="Logo churn rate as percentage (e.g. 2.1)")
    revenue_churn_rate: float = Field(..., description="Revenue churn rate as percentage (e.g. 1.8)")
    mrr_mom_pct: float = Field(..., description="MRR month-over-month growth %")
    prev_month_mrr: Optional[float] = Field(None, description="Prior month MRR for delta calculation")
    prev_month_nrr: Optional[float] = Field(None, description="Prior month NRR for delta calculation")
    prev_month_logo_churn: Optional[float] = Field(None, description="Prior month logo churn for delta")

    class Config:
        json_schema_extra = {
            "example": {
                "month_key": "2024-11",
                "total_mrr": 487250.0,
                "total_arr": 5847000.0,
                "active_accounts": 298,
                "arpa": 1634.4,
                "new_mrr": 28400.0,
                "expansion_mrr": 14200.0,
                "contraction_mrr": 6800.0,
                "churned_mrr": 9100.0,
                "reactivation_mrr": 2100.0,
                "net_new_mrr": 28800.0,
                "nrr": 112.4,
                "grr": 94.2,
                "logo_churn_rate": 2.1,
                "revenue_churn_rate": 1.8,
                "mrr_mom_pct": 6.3,
            }
        }


# ---------------------------------------------------------------------------
# MRR Trend
# ---------------------------------------------------------------------------

class MRRTrendPoint(BaseModel):
    """Single data point in the MRR trend time series."""
    month_key: str = Field(..., description="YYYY-MM")
    total_mrr: float
    total_arr: float
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    churned_mrr: float
    reactivation_mrr: float
    net_new_mrr: float
    active_accounts: int
    nrr: float
    grr: float
    logo_churn_rate: float
    mrr_mom_pct: float


class MRRTrendResponse(BaseModel):
    """MRR trend time series for the trend chart."""
    data: list[MRRTrendPoint]
    months: int = Field(..., description="Number of months in the series")


# ---------------------------------------------------------------------------
# Revenue Waterfall
# ---------------------------------------------------------------------------

class WaterfallItem(BaseModel):
    """Single bar in the MRR waterfall / bridge chart."""
    label: str = Field(..., description="Bar label: Starting MRR, New, Expansion, etc.")
    value: float = Field(..., description="Absolute value of this movement")
    cumulative: float = Field(..., description="Running total after this bar")
    type: str = Field(..., description="bar type: start | positive | negative | end")
    color: str = Field(..., description="Hex color for this bar")


class WaterfallResponse(BaseModel):
    """Full waterfall data for a given month."""
    month_key: str
    items: list[WaterfallItem]
    starting_mrr: float
    ending_mrr: float
    net_change: float


# ---------------------------------------------------------------------------
# Revenue by Dimension
# ---------------------------------------------------------------------------

class RevenueByDimensionItem(BaseModel):
    """Revenue breakdown by a single dimension value (plan, region, industry, etc.)."""
    dimension: str = Field(..., description="Dimension name: plan_name, region, industry, company_size")
    value: str = Field(..., description="Dimension value: e.g. 'Enterprise', 'North America'")
    mrr: float
    arr: float
    account_count: int
    arpa: float
    pct_of_total: float = Field(..., description="Percentage of total MRR")


class RevenueByDimensionResponse(BaseModel):
    """Revenue breakdown by a dimension for a given month."""
    month_key: str
    dimension: str
    total_mrr: float
    items: list[RevenueByDimensionItem]


# ---------------------------------------------------------------------------
# Top Accounts
# ---------------------------------------------------------------------------

class TopAccountItem(BaseModel):
    """Single account in the top expanding / top churn-risk list."""
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
    mrr_change: Optional[float] = Field(None, description="MRR delta vs prior month")
    mrr_change_pct: Optional[float] = Field(None, description="MRR delta % vs prior month")
    risk_reasons: Optional[list[str]] = Field(default_factory=list)


class TopAccountsResponse(BaseModel):
    """Top N accounts by a given sort criterion."""
    month_key: str
    sort_by: str = Field(..., description="expanding | churn_risk | mrr")
    limit: int
    accounts: list[TopAccountItem]
