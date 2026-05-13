"""Executive Overview Router — delegates to MetricsService with tenant isolation."""
from __future__ import annotations
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import CurrentUser, get_current_user
from db.database import get_db
from services import MetricsService

router = APIRouter()


def _svc(db: Session, user: CurrentUser) -> MetricsService:
    return MetricsService(db, tenant_id=user.tenant_id)


@router.get("/summary")
def get_executive_summary(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None, description="YYYY-MM"),
) -> dict:
    try:
        return _svc(db, user).get_latest_exec_kpi(month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch executive summary.")


@router.get("/mrr-trend")
def get_mrr_trend(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=24, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_mrr_trend(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch MRR trend.")


@router.get("/waterfall")
def get_mrr_waterfall(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None, description="YYYY-MM"),
) -> dict:
    try:
        return _svc(db, user).get_waterfall(month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch waterfall data.")


@router.get("/by-plan")
def get_revenue_by_plan(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_revenue_by_dimension("plan_name", month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch revenue by plan.")


@router.get("/by-region")
def get_revenue_by_region(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_revenue_by_dimension("region", month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch revenue by region.")


@router.get("/by-industry")
def get_revenue_by_industry(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_revenue_by_dimension("industry", month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch revenue by industry.")


@router.get("/by-company-size")
def get_revenue_by_company_size(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_revenue_by_dimension("company_size", month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch revenue by company size.")


@router.get("/top-expanding")
def get_top_expanding(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_top_accounts(sort_by="expansion", limit=limit, month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch top expanding accounts.")


@router.get("/top-churn-risk")
def get_top_churn_risk(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_top_accounts(sort_by="churn_risk", limit=limit, month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch top churn risk accounts.")
