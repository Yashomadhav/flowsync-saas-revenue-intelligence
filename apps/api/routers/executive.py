"""
Executive Overview Router
Endpoints: summary, mrr-trend, waterfall, by-plan, by-region, top-accounts
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


@router.get("/summary", summary="Executive KPI summary")
def get_executive_summary(db: Annotated[Session, Depends(get_db)]) -> dict:
    sql = (
        "WITH latest AS ("
        "  SELECT * FROM mart_exec_revenue_summary ORDER BY month DESC LIMIT 1"
        "), prev AS ("
        "  SELECT * FROM mart_exec_revenue_summary ORDER BY month DESC LIMIT 1 OFFSET 1"
        ") "
        "SELECT l.month, l.total_mrr, l.arr, l.new_mrr, l.expansion_mrr, "
        "l.contraction_mrr, l.churned_mrr, l.reactivation_mrr, l.net_new_mrr, "
        "l.active_accounts, l.new_accounts, l.churned_accounts, l.mrr_growth_pct, "
        "l.arpa, l.logo_churn_rate, l.revenue_churn_rate, l.nrr, l.grr, "
        "p.total_mrr AS prev_mrr, p.active_accounts AS prev_active_accounts "
        "FROM latest l LEFT JOIN prev p ON TRUE"
    )
    rows = _query(db, sql)
    return rows[0] if rows else {}


@router.get("/mrr-trend", summary="MRR trend last N months")
def get_mrr_trend(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> list[dict]:
    sql = (
        "SELECT month, total_mrr, arr, net_new_mrr, new_mrr, expansion_mrr, "
        "contraction_mrr, churned_mrr, reactivation_mrr, active_accounts, "
        "mrr_growth_pct, nrr, arpa "
        "FROM mart_exec_revenue_summary "
        "ORDER BY month DESC LIMIT :months"
    )
    rows = _query(db, sql, {"months": months})
    return list(reversed(rows))


@router.get("/waterfall", summary="MRR waterfall bridge")
def get_mrr_waterfall(
    db: Annotated[Session, Depends(get_db)],
    month: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
) -> dict:
    if month:
        sql = (
            "SELECT month, "
            "COALESCE(LAG(total_mrr) OVER (ORDER BY month), 0) AS starting_mrr, "
            "new_mrr, expansion_mrr, reactivation_mrr, contraction_mrr, "
            "churned_mrr, net_new_mrr, total_mrr AS ending_mrr "
            "FROM mart_exec_revenue_summary WHERE month = :month"
        )
        rows = _query(db, sql, {"month": month})
    else:
        sql = (
            "SELECT month, "
            "COALESCE(LAG(total_mrr) OVER (ORDER BY month), 0) AS starting_mrr, "
            "new_mrr, expansion_mrr, reactivation_mrr, contraction_mrr, "
            "churned_mrr, net_new_mrr, total_mrr AS ending_mrr "
            "FROM mart_exec_revenue_summary ORDER BY month DESC LIMIT 1"
        )
        rows = _query(db, sql)
    if not rows:
        return {}
    r = rows[0]
    return {
        "month": str(r["month"]),
        "waterfall": [
            {"label": "Starting MRR",  "value": float(r["starting_mrr"] or 0),    "type": "start"},
            {"label": "New",           "value": float(r["new_mrr"] or 0),          "type": "positive"},
            {"label": "Expansion",     "value": float(r["expansion_mrr"] or 0),    "type": "positive"},
            {"label": "Reactivation",  "value": float(r["reactivation_mrr"] or 0), "type": "positive"},
            {"label": "Contraction",   "value": -float(r["contraction_mrr"] or 0), "type": "negative"},
            {"label": "Churn",         "value": -float(r["churned_mrr"] or 0),     "type": "negative"},
            {"label": "Ending MRR",    "value": float(r["ending_mrr"] or 0),       "type": "end"},
        ],
        "net_new_mrr": float(r["net_new_mrr"] or 0),
    }


@router.get("/by-plan", summary="Revenue by plan")
def get_revenue_by_plan(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=1, ge=1, le=12),
) -> list[dict]:
    sql = (
        "SELECT plan_name, SUM(current_mrr) AS total_mrr, "
        "COUNT(DISTINCT account_id) AS account_count, "
        "AVG(current_mrr) AS avg_mrr_per_account, "
        "SUM(expansion_mrr) AS expansion_mrr, SUM(churned_mrr) AS churned_mrr "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "AND current_mrr > 0 "
        "GROUP BY plan_name ORDER BY total_mrr DESC"
    )
    return _query(db, sql, {"months": months})


@router.get("/by-region", summary="Revenue by region")
def get_revenue_by_region(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=1, ge=1, le=12),
) -> list[dict]:
    sql = (
        "SELECT region, SUM(current_mrr) AS total_mrr, "
        "COUNT(DISTINCT account_id) AS account_count, "
        "AVG(current_mrr) AS avg_mrr, "
        "SUM(new_mrr) AS new_mrr, SUM(churned_mrr) AS churned_mrr "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "AND current_mrr > 0 "
        "GROUP BY region ORDER BY total_mrr DESC"
    )
    return _query(db, sql, {"months": months})


@router.get("/by-industry", summary="Revenue by industry")
def get_revenue_by_industry(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=1, ge=1, le=12),
) -> list[dict]:
    sql = (
        "SELECT industry, SUM(current_mrr) AS total_mrr, "
        "COUNT(DISTINCT account_id) AS account_count, "
        "AVG(current_mrr) AS avg_mrr "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "AND current_mrr > 0 "
        "GROUP BY industry ORDER BY total_mrr DESC"
    )
    return _query(db, sql, {"months": months})


@router.get("/top-expanding", summary="Top expanding accounts")
def get_top_expanding(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    sql = (
        "SELECT account_id, company_name, plan_name, region, company_size, "
        "current_mrr, previous_mrr, expansion_mrr, mrr_growth_pct "
        "FROM fct_mrr_movements "
        "WHERE month = DATE_TRUNC('month', CURRENT_DATE) AND expansion_mrr > 0 "
        "ORDER BY expansion_mrr DESC LIMIT :limit"
    )
    return _query(db, sql, {"limit": limit})


@router.get("/top-churn-risk", summary="Top churn-risk accounts")
def get_top_churn_risk(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    sql = (
        "SELECT account_id, company_name, plan_name, region, company_size, "
        "current_mrr, health_score, risk_level, risk_flag_count, "
        "flag_usage_drop, flag_no_login, flag_open_tickets, "
        "flag_payment_failure, flag_low_csat, flag_low_seat_util "
        "FROM mart_customer_success_summary "
        "WHERE risk_level IN ('at_risk', 'critical') "
        "ORDER BY health_score ASC, current_mrr DESC LIMIT :limit"
    )
    return _query(db, sql, {"limit": limit})
