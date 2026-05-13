"""Cohort Retention Router — delegates to MetricsService with tenant isolation."""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import CurrentUser, get_current_user
from db.database import get_db
from services import MetricsService

router = APIRouter()


def _svc(db: Session, user: CurrentUser) -> MetricsService:
    return MetricsService(db, tenant_id=user.tenant_id)


@router.get("/heatmap")
def get_cohort_heatmap(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    metric: str = Query(default="logo_retention", description="logo_retention|revenue_retention|nrr|grr"),
) -> dict:
    try:
        return _svc(db, user).get_cohort_heatmap(metric=metric)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch cohort heatmap.")


@router.get("/logo-churn-trend")
def get_logo_churn_trend(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=24, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_logo_churn_trend(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch logo churn trend.")


@router.get("/nrr-by-cohort")
def get_nrr_by_cohort(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    period_months: int = Query(default=12, ge=1, le=24),
) -> dict:
    try:
        return _svc(db, user).get_nrr_by_cohort(period_months=period_months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch NRR by cohort.")


@router.get("/retention-by-segment")
def get_retention_by_segment(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    dimension: str = Query(default="plan_name", description="plan_name|company_size|region"),
    period_months: int = Query(default=12, ge=1, le=24),
) -> dict:
    try:
        return _svc(db, user).get_retention_by_segment(dimension=dimension, period_months=period_months)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch retention by segment.")
