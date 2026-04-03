"""
Customer Health & Churn Risk Router
Endpoints: score-distribution, risk-quadrant, usage-trends,
           support-burden, risky-accounts
"""
from __future__ import annotations

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.database import get_db

router = APIRouter()


def _query(db: Session, sql: str, params: dict | None = None) -> list[dict]:
    result = db.execute(text(sql), params or {})
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


@router.get("/score-distribution", summary="Health score distribution histogram")
def get_score_distribution(db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    sql = (
        "SELECT "
        "CASE "
        "WHEN health_score >= 90 THEN '90-100' "
        "WHEN health_score >= 80 THEN '80-89' "
        "WHEN health_score >= 70 THEN '70-79' "
        "WHEN health_score >= 60 THEN '60-69' "
        "WHEN health_score >= 50 THEN '50-59' "
        "WHEN health_score >= 40 THEN '40-49' "
        "WHEN health_score >= 30 THEN '30-39' "
        "ELSE '0-29' END AS score_bucket, "
        "COUNT(*) AS account_count, "
        "SUM(current_mrr) AS total_mrr, "
        "AVG(health_score) AS avg_score "
        "FROM mart_customer_success_summary "
        "GROUP BY score_bucket "
        "ORDER BY score_bucket DESC"
    )
    return _query(db, sql)


@router.get("/risk-quadrant", summary="Churn risk quadrant: usage vs health score")
def get_risk_quadrant(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=100, ge=10, le=500),
) -> list[dict]:
    sql = (
        "SELECT account_id, company_name, plan_name, company_size, region, "
        "current_mrr, health_score, risk_level, "
        "usage_score, seat_utilization_score, "
        "flag_usage_drop, flag_no_login, flag_open_tickets, "
        "flag_payment_failure, flag_low_csat, flag_low_seat_util, "
        "risk_flag_count "
        "FROM mart_customer_success_summary "
        "ORDER BY current_mrr DESC LIMIT :limit"
    )
    return _query(db, sql, {"limit": limit})


@router.get("/usage-trends", summary="Usage drop trends for at-risk accounts")
def get_usage_trends(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=6, ge=2, le=12),
) -> list[dict]:
    sql = (
        "SELECT h.account_id, a.company_name, a.plan_name, "
        "h.month, h.usage_score, h.seat_utilization_score, "
        "h.feature_adoption_score, h.health_score, h.risk_level "
        "FROM fct_account_monthly_health h "
        "JOIN stg_accounts a ON a.account_id = h.account_id "
        "WHERE h.month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "AND h.risk_level IN ('at_risk', 'critical') "
        "ORDER BY h.account_id, h.month ASC"
    )
    return _query(db, sql, {"months": months})


@router.get("/support-burden", summary="Support ticket burden by account")
def get_support_burden(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=20, ge=5, le=100),
) -> list[dict]:
    sql = (
        "SELECT s.account_id, a.company_name, a.plan_name, "
        "COUNT(s.ticket_id) AS total_tickets, "
        "SUM(CASE WHEN s.is_high_priority THEN 1 ELSE 0 END) AS high_priority_tickets, "
        "SUM(CASE WHEN NOT s.is_resolved THEN 1 ELSE 0 END) AS open_tickets, "
        "AVG(s.csat_score) AS avg_csat, "
        "AVG(s.resolution_hours) AS avg_resolution_hours, "
        "MAX(s.created_at) AS last_ticket_date "
        "FROM stg_tickets s "
        "JOIN stg_accounts a ON a.account_id = s.account_id "
        "WHERE s.created_at >= CURRENT_DATE - INTERVAL '90 days' "
        "GROUP BY s.account_id, a.company_name, a.plan_name "
        "ORDER BY high_priority_tickets DESC, total_tickets DESC "
        "LIMIT :limit"
    )
    return _query(db, sql, {"limit": limit})


@router.get("/risky-accounts", summary="Accounts at churn risk with risk reasons")
def get_risky_accounts(
    db: Annotated[Session, Depends(get_db)],
    risk_level: Optional[str] = Query(default=None, description="critical|at_risk"),
    limit: int = Query(default=25, ge=5, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if risk_level:
        conditions.append("risk_level = :risk_level")
        params["risk_level"] = risk_level
    else:
        conditions.append("risk_level IN ('at_risk', 'critical')")

    where = " AND ".join(conditions)

    count_sql = "SELECT COUNT(*) AS total FROM mart_customer_success_summary WHERE " + where
    data_sql = (
        "SELECT account_id, company_name, plan_name, region, company_size, "
        "current_mrr, health_score, risk_level, risk_flag_count, "
        "flag_usage_drop, flag_no_login, flag_open_tickets, "
        "flag_payment_failure, flag_low_csat, flag_low_seat_util, "
        "usage_score, seat_utilization_score, support_score, csat_score "
        "FROM mart_customer_success_summary WHERE " + where +
        " ORDER BY health_score ASC, current_mrr DESC LIMIT :limit OFFSET :offset"
    )

    count_rows = _query(db, count_sql, params)
    total = count_rows[0]["total"] if count_rows else 0
    data = _query(db, data_sql, params)
    return {"total": total, "data": data}


@router.get("/health-over-time", summary="Health score trend for an account")
def get_health_over_time(
    db: Annotated[Session, Depends(get_db)],
    account_id: str = Query(..., description="Account UUID"),
    months: int = Query(default=6, ge=2, le=24),
) -> list[dict]:
    sql = (
        "SELECT h.month, h.health_score, h.risk_level, "
        "h.usage_score, h.seat_utilization_score, h.feature_adoption_score, "
        "h.support_score, h.csat_score, h.payment_score, "
        "h.flag_usage_drop, h.flag_no_login, h.flag_open_tickets, "
        "h.flag_payment_failure, h.flag_low_csat "
        "FROM fct_account_monthly_health h "
        "WHERE h.account_id = :account_id "
        "AND h.month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "ORDER BY h.month ASC"
    )
    return _query(db, sql, {"account_id": account_id, "months": months})


@router.get("/summary-stats", summary="Health summary statistics")
def get_health_summary_stats(db: Annotated[Session, Depends(get_db)]) -> dict:
    sql = (
        "SELECT "
        "COUNT(*) AS total_accounts, "
        "SUM(CASE WHEN risk_level = 'healthy' THEN 1 ELSE 0 END) AS healthy_count, "
        "SUM(CASE WHEN risk_level = 'at_risk' THEN 1 ELSE 0 END) AS at_risk_count, "
        "SUM(CASE WHEN risk_level = 'critical' THEN 1 ELSE 0 END) AS critical_count, "
        "AVG(health_score) AS avg_health_score, "
        "SUM(CASE WHEN risk_level IN ('at_risk', 'critical') THEN current_mrr ELSE 0 END) AS at_risk_mrr, "
        "SUM(current_mrr) AS total_mrr "
        "FROM mart_customer_success_summary"
    )
    rows = _query(db, sql)
    return rows[0] if rows else {}
