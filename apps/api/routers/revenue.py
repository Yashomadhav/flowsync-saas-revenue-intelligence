"""
Revenue Movements Router
Endpoints: mrr-bridge, account-movements, new-mrr-by-channel,
           expansion-by-segment, churned-by-plan, payment-trends
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


@router.get("/mrr-bridge", summary="Monthly MRR bridge by movement type")
def get_mrr_bridge(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT month, "
        "SUM(new_mrr) AS new_mrr, "
        "SUM(expansion_mrr) AS expansion_mrr, "
        "SUM(reactivation_mrr) AS reactivation_mrr, "
        "SUM(contraction_mrr) AS contraction_mrr, "
        "SUM(churned_mrr) AS churned_mrr, "
        "SUM(net_new_mrr) AS net_new_mrr, "
        "SUM(current_mrr) AS total_mrr "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "GROUP BY month ORDER BY month ASC"
    )
    return _query(db, sql, {"months": months})


@router.get("/account-movements", summary="Account-level MRR movements")
def get_account_movements(
    db: Annotated[Session, Depends(get_db)],
    month: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    movement_type: Optional[str] = Query(default=None, description="new|expansion|contraction|churn|reactivation"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if month:
        conditions.append("month = :month")
        params["month"] = month
    else:
        conditions.append("month = DATE_TRUNC('month', CURRENT_DATE)")

    if movement_type:
        conditions.append("movement_type = :movement_type")
        params["movement_type"] = movement_type

    where = " AND ".join(conditions)

    count_sql = "SELECT COUNT(*) AS total FROM fct_mrr_movements WHERE " + where
    data_sql = (
        "SELECT account_id, company_name, plan_name, region, company_size, "
        "acquisition_channel, month, movement_type, current_mrr, previous_mrr, "
        "mrr_delta, mrr_growth_pct, new_mrr, expansion_mrr, contraction_mrr, "
        "churned_mrr, reactivation_mrr "
        "FROM fct_mrr_movements WHERE " + where +
        " ORDER BY ABS(mrr_delta) DESC LIMIT :limit OFFSET :offset"
    )

    count_rows = _query(db, count_sql, params)
    total = count_rows[0]["total"] if count_rows else 0
    data = _query(db, data_sql, params)
    return {"total": total, "data": data}


@router.get("/new-mrr-by-channel", summary="New MRR by acquisition channel")
def get_new_mrr_by_channel(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict]:
    sql = (
        "SELECT month, acquisition_channel, "
        "SUM(new_mrr) AS new_mrr, "
        "COUNT(DISTINCT CASE WHEN movement_type = 'new' THEN account_id END) AS new_accounts "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "AND new_mrr > 0 "
        "GROUP BY month, acquisition_channel "
        "ORDER BY month ASC, new_mrr DESC"
    )
    return _query(db, sql, {"months": months})


@router.get("/expansion-by-segment", summary="Expansion MRR by company segment")
def get_expansion_by_segment(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict]:
    sql = (
        "SELECT month, company_size, plan_name, "
        "SUM(expansion_mrr) AS expansion_mrr, "
        "COUNT(DISTINCT CASE WHEN expansion_mrr > 0 THEN account_id END) AS expanding_accounts "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "AND expansion_mrr > 0 "
        "GROUP BY month, company_size, plan_name "
        "ORDER BY month ASC, expansion_mrr DESC"
    )
    return _query(db, sql, {"months": months})


@router.get("/churned-by-plan", summary="Churned MRR by plan")
def get_churned_by_plan(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict]:
    sql = (
        "SELECT month, plan_name, "
        "SUM(churned_mrr) AS churned_mrr, "
        "COUNT(DISTINCT CASE WHEN churned_mrr > 0 THEN account_id END) AS churned_accounts "
        "FROM fct_mrr_movements "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "AND churned_mrr > 0 "
        "GROUP BY month, plan_name "
        "ORDER BY month ASC, churned_mrr DESC"
    )
    return _query(db, sql, {"months": months})


@router.get("/payment-trends", summary="Invoice payment failure trends")
def get_payment_trends(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=24),
) -> list[dict]:
    sql = (
        "SELECT invoice_month AS month, "
        "COUNT(invoice_id) AS total_invoices, "
        "SUM(CASE WHEN is_paid THEN 1 ELSE 0 END) AS paid_invoices, "
        "SUM(CASE WHEN is_failed THEN 1 ELSE 0 END) AS failed_invoices, "
        "SUM(CASE WHEN is_pending THEN 1 ELSE 0 END) AS pending_invoices, "
        "SUM(CASE WHEN is_paid THEN amount ELSE 0 END) AS paid_amount, "
        "SUM(CASE WHEN is_failed THEN amount ELSE 0 END) AS failed_amount, "
        "ROUND(SUM(CASE WHEN is_failed THEN 1 ELSE 0 END)::NUMERIC / "
        "NULLIF(COUNT(invoice_id), 0) * 100, 2) AS failure_rate_pct "
        "FROM stg_invoices "
        "WHERE invoice_month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "GROUP BY invoice_month ORDER BY invoice_month ASC"
    )
    return _query(db, sql, {"months": months})


@router.get("/summary-by-month", summary="Full revenue summary by month")
def get_revenue_summary_by_month(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> list[dict]:
    sql = (
        "SELECT month, total_mrr, arr, new_mrr, expansion_mrr, "
        "contraction_mrr, churned_mrr, reactivation_mrr, net_new_mrr, "
        "active_accounts, new_accounts, churned_accounts, "
        "mrr_growth_pct, arpa, logo_churn_rate, revenue_churn_rate, nrr, grr "
        "FROM mart_exec_revenue_summary "
        "WHERE month >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month' "
        "ORDER BY month ASC"
    )
    return _query(db, sql, {"months": months})
