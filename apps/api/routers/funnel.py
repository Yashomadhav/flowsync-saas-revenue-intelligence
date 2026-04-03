"""
Funnel & Growth Router
Endpoints: conversion, by-channel, sales-cycle, trial-usage, expansion-by-segment
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


@router.get("/conversion", summary="Lead to trial to paid funnel")
def get_funnel_conversion(db: Annotated[Session, Depends(get_db)]) -> dict:
    sql = (
        "SELECT "
        "COUNT(*) AS total_leads, "
        "SUM(CASE WHEN funnel_stage IN ('trial', 'paid', 'churned') THEN 1 ELSE 0 END) AS trial_starts, "
        "SUM(CASE WHEN trial_converted THEN 1 ELSE 0 END) AS paid_conversions, "
        "ROUND(SUM(CASE WHEN funnel_stage IN ('trial', 'paid', 'churned') THEN 1 ELSE 0 END)::NUMERIC "
        "/ NULLIF(COUNT(*), 0) * 100, 2) AS lead_to_trial_rate, "
        "ROUND(SUM(CASE WHEN trial_converted THEN 1 ELSE 0 END)::NUMERIC "
        "/ NULLIF(SUM(CASE WHEN funnel_stage IN ('trial', 'paid', 'churned') THEN 1 ELSE 0 END), 0) * 100, 2) AS trial_to_paid_rate, "
        "ROUND(SUM(CASE WHEN trial_converted THEN 1 ELSE 0 END)::NUMERIC "
        "/ NULLIF(COUNT(*), 0) * 100, 2) AS overall_conversion_rate, "
        "AVG(CASE WHEN trial_converted THEN days_to_convert END) AS avg_days_to_convert, "
        "AVG(CASE WHEN trial_converted THEN trial_engagement_score END) AS avg_trial_engagement "
        "FROM fct_sales_conversion"
    )
    rows = _query(db, sql)
    return rows[0] if rows else {}


@router.get("/by-channel", summary="Funnel conversion rates by acquisition channel")
def get_conversion_by_channel(db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    sql = (
        "SELECT channel, "
        "COUNT(*) AS total_leads, "
        "SUM(CASE WHEN funnel_stage IN ('trial', 'paid', 'churned') THEN 1 ELSE 0 END) AS trial_starts, "
        "SUM(CASE WHEN trial_converted THEN 1 ELSE 0 END) AS paid_conversions, "
        "ROUND(SUM(CASE WHEN trial_converted THEN 1 ELSE 0 END)::NUMERIC "
        "/ NULLIF(SUM(CASE WHEN funnel_stage IN ('trial', 'paid', 'churned') THEN 1 ELSE 0 END), 0) * 100, 2) AS trial_to_paid_rate, "
        "AVG(CASE WHEN trial_converted THEN days_to_convert END) AS avg_days_to_convert, "
        "AVG(CASE WHEN trial_converted THEN first_month_mrr END) AS avg_first_month_mrr "
        "FROM fct_sales_conversion "
        "GROUP BY channel ORDER BY paid_conversions DESC"
    )
    return _query(db, sql)


@router.get("/sales-cycle", summary="Sales cycle duration distribution")
def get_sales_cycle(db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    sql = (
        "SELECT channel, plan_name, "
        "AVG(days_to_convert) AS avg_days, "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_to_convert) AS median_days, "
        "MIN(days_to_convert) AS min_days, "
        "MAX(days_to_convert) AS max_days, "
        "COUNT(*) AS conversions "
        "FROM fct_sales_conversion "
        "WHERE trial_converted = TRUE "
        "GROUP BY channel, plan_name "
        "ORDER BY avg_days ASC"
    )
    return _query(db, sql)


@router.get("/trial-usage", summary="Trial engagement vs paid conversion scatter data")
def get_trial_usage(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=200, ge=50, le=500),
) -> list[dict]:
    sql = (
        "SELECT lead_id, channel, plan_name, "
        "trial_engagement_score, trial_converted, "
        "days_to_convert, first_month_mrr, trial_duration_days "
        "FROM fct_sales_conversion "
        "WHERE funnel_stage IN ('trial', 'paid', 'churned') "
        "ORDER BY trial_engagement_score DESC LIMIT :limit"
    )
    return _query(db, sql, {"limit": limit})


@router.get("/expansion-by-segment", summary="Expansion revenue by segment and source")
def get_expansion_by_segment(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict]:
    sql = (
        "SELECT company_size, acquisition_channel, plan_name, "
        "SUM(expansion_mrr) AS total_expansion_mrr, "
        "COUNT(DISTINCT CASE WHEN expansion_mrr > 0 THEN account_id END) AS expanding_accounts, "
        "AVG(CASE WHEN expansion_mrr > 0 THEN expansion_mrr END) AS avg_expansion_per_account "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "GROUP BY company_size, acquisition_channel, plan_name "
        "ORDER BY total_expansion_mrr DESC"
    )
    return _query(db, sql, {"months": months})


@router.get("/monthly-trend", summary="Monthly funnel metrics trend")
def get_funnel_monthly_trend(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT DATE_TRUNC('month', created_at) AS month, "
        "COUNT(*) AS new_leads, "
        "SUM(CASE WHEN funnel_stage IN ('trial', 'paid', 'churned') THEN 1 ELSE 0 END) AS trial_starts, "
        "SUM(CASE WHEN trial_converted THEN 1 ELSE 0 END) AS paid_conversions, "
        "SUM(CASE WHEN trial_converted THEN first_month_mrr ELSE 0 END) AS new_mrr_from_trials "
        "FROM fct_sales_conversion "
        "WHERE created_at >= CURRENT_DATE - (:months * 30) "
        "GROUP BY DATE_TRUNC('month', created_at) "
        "ORDER BY month ASC"
    )
    return _query(db, sql, {"months": months})
