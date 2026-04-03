"""
Cohort Retention Router
Endpoints: customer-retention, revenue-retention, logo-churn-trend,
           nrr-by-cohort, retention-by-segment
"""
from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.database import get_db

router = APIRouter()


def _query(db: Session, sql: str, params: dict | None = None) -> list[dict]:
    result = db.execute(text(sql), params or {})
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


@router.get("/customer-retention", summary="Customer retention cohort heatmap data")
def get_customer_retention(
    db: Annotated[Session, Depends(get_db)],
    cohort_months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT cohort_month, period_number, cohort_size, "
        "active_customers, customer_retention_rate, "
        "logo_churn_rate "
        "FROM fct_customer_cohorts "
        "WHERE cohort_month >= DATE_TRUNC('month', CURRENT_DATE) - (:cohort_months - 1) * INTERVAL '1 month' "
        "ORDER BY cohort_month ASC, period_number ASC"
    )
    return _query(db, sql, {"cohort_months": cohort_months})


@router.get("/revenue-retention", summary="Revenue retention cohort heatmap data")
def get_revenue_retention(
    db: Annotated[Session, Depends(get_db)],
    cohort_months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT cohort_month, period_number, cohort_size, "
        "cohort_starting_mrr, active_mrr, "
        "revenue_retention_rate, nrr "
        "FROM fct_customer_cohorts "
        "WHERE cohort_month >= DATE_TRUNC('month', CURRENT_DATE) - (:cohort_months - 1) * INTERVAL '1 month' "
        "ORDER BY cohort_month ASC, period_number ASC"
    )
    return _query(db, sql, {"cohort_months": cohort_months})


@router.get("/logo-churn-trend", summary="Monthly logo churn rate trend")
def get_logo_churn_trend(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> list[dict]:
    sql = (
        "SELECT month, logo_churn_rate, revenue_churn_rate, "
        "churned_accounts, active_accounts "
        "FROM mart_exec_revenue_summary "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "ORDER BY month ASC"
    )
    return _query(db, sql, {"months": months})


@router.get("/nrr-by-cohort", summary="NRR by cohort month")
def get_nrr_by_cohort(
    db: Annotated[Session, Depends(get_db)],
    cohort_months: int = Query(default=12, ge=3, le=24),
    period: int = Query(default=12, ge=1, le=24, description="Period number to compare"),
) -> list[dict]:
    sql = (
        "SELECT cohort_month, period_number, nrr, "
        "revenue_retention_rate, cohort_starting_mrr, active_mrr "
        "FROM fct_customer_cohorts "
        "WHERE cohort_month >= DATE_TRUNC('month', CURRENT_DATE) - (:cohort_months - 1) * INTERVAL '1 month' "
        "AND period_number = :period "
        "ORDER BY cohort_month ASC"
    )
    return _query(db, sql, {"cohort_months": cohort_months, "period": period})


@router.get("/retention-by-plan", summary="Retention rates by subscription plan")
def get_retention_by_plan(
    db: Annotated[Session, Depends(get_db)],
    cohort_months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT m.plan_name, "
        "AVG(c.customer_retention_rate) AS avg_customer_retention, "
        "AVG(c.revenue_retention_rate) AS avg_revenue_retention, "
        "AVG(c.nrr) AS avg_nrr, "
        "COUNT(DISTINCT m.account_id) AS cohort_accounts "
        "FROM fct_customer_cohorts c "
        "JOIN fct_mrr_movements m ON m.account_id = c.account_id "
        "AND m.month = c.cohort_month "
        "WHERE c.cohort_month >= DATE_TRUNC('month', CURRENT_DATE) - (:cohort_months - 1) * INTERVAL '1 month' "
        "AND c.period_number = 12 "
        "GROUP BY m.plan_name ORDER BY avg_nrr DESC"
    )
    return _query(db, sql, {"cohort_months": cohort_months})


@router.get("/retention-by-size", summary="Retention rates by company size")
def get_retention_by_size(
    db: Annotated[Session, Depends(get_db)],
    cohort_months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT m.company_size, "
        "AVG(c.customer_retention_rate) AS avg_customer_retention, "
        "AVG(c.revenue_retention_rate) AS avg_revenue_retention, "
        "AVG(c.nrr) AS avg_nrr, "
        "COUNT(DISTINCT m.account_id) AS cohort_accounts "
        "FROM fct_customer_cohorts c "
        "JOIN fct_mrr_movements m ON m.account_id = c.account_id "
        "AND m.month = c.cohort_month "
        "WHERE c.cohort_month >= DATE_TRUNC('month', CURRENT_DATE) - (:cohort_months - 1) * INTERVAL '1 month' "
        "AND c.period_number = 12 "
        "GROUP BY m.company_size ORDER BY avg_nrr DESC"
    )
    return _query(db, sql, {"cohort_months": cohort_months})


@router.get("/retention-by-channel", summary="Retention rates by acquisition channel")
def get_retention_by_channel(
    db: Annotated[Session, Depends(get_db)],
    cohort_months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT m.acquisition_channel, "
        "AVG(c.customer_retention_rate) AS avg_customer_retention, "
        "AVG(c.revenue_retention_rate) AS avg_revenue_retention, "
        "AVG(c.nrr) AS avg_nrr, "
        "COUNT(DISTINCT m.account_id) AS cohort_accounts "
        "FROM fct_customer_cohorts c "
        "JOIN fct_mrr_movements m ON m.account_id = c.account_id "
        "AND m.month = c.cohort_month "
        "WHERE c.cohort_month >= DATE_TRUNC('month', CURRENT_DATE) - (:cohort_months - 1) * INTERVAL '1 month' "
        "AND c.period_number = 12 "
        "GROUP BY m.acquisition_channel ORDER BY avg_nrr DESC"
    )
    return _query(db, sql, {"cohort_months": cohort_months})
