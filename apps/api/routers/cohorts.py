"""Cohort Retention Router — delegates to MetricsService."""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from services import MetricsService

router = APIRouter()


def _svc(db: Session) -> MetricsService:
    return MetricsService(db)


@router.get("/heatmap")
def get_cohort_heatmap(
    db: Annotated[Session, Depends(get_db)],
    metric: str = Query(default="logo_retention", description="logo_retention|revenue_retention|nrr|grr"),
) -> dict:
    try:
        return _svc(db).get_cohort_heatmap(metric=metric)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logo-churn-trend")
def get_logo_churn_trend(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=24, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_logo_churn_trend(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nrr-by-cohort")
def get_nrr_by_cohort(
    db: Annotated[Session, Depends(get_db)],
    period_months: int = Query(default=12, ge=1, le=24),
) -> dict:
    try:
        return _svc(db).get_nrr_by_cohort(period_months=period_months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention-by-segment")
def get_retention_by_segment(
    db: Annotated[Session, Depends(get_db)],
    dimension: str = Query(default="plan_name", description="plan_name|company_size|region"),
    period_months: int = Query(default=12, ge=1, le=24),
) -> dict:
    try:
        return _svc(db).get_retention_by_segment(dimension=dimension, period_months=period_months)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
