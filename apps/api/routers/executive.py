"""Executive Overview Router — delegates to MetricsService."""
from __future__ import annotations
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from services import MetricsService

router = APIRouter()


def _svc(db: Session) -> MetricsService:
    return MetricsService(db)


@router.get("/summary")
def get_executive_summary(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None, description="YYYY-MM"),
) -> dict:
    try:
        return _svc(db).get_latest_exec_kpi(month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mrr-trend")
def get_mrr_trend(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=24, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_mrr_trend(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/waterfall")
def get_mrr_waterfall(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None, description="YYYY-MM"),
) -> dict:
    try:
        return _svc(db).get_waterfall(month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-plan")
def get_revenue_by_plan(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_revenue_by_dimension("plan_name", month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-region")
def get_revenue_by_region(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_revenue_by_dimension("region", month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-industry")
def get_revenue_by_industry(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_revenue_by_dimension("industry", month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-company-size")
def get_revenue_by_company_size(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_revenue_by_dimension("company_size", month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-expanding")
def get_top_expanding(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_top_accounts(sort_by="expansion", limit=limit, month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-churn-risk")
def get_top_churn_risk(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_top_accounts(sort_by="churn_risk", limit=limit, month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
