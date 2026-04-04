"""Funnel & Growth Router — delegates to MetricsService."""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from services import MetricsService

router = APIRouter()


def _svc(db: Session) -> MetricsService:
    return MetricsService(db)


@router.get("/overview")
def get_funnel_overview(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_funnel_overview(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversion-by-channel")
def get_conversion_by_channel(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_conversion_by_channel(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales-cycle")
def get_sales_cycle(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_sales_cycle(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trial-usage")
def get_trial_usage(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_trial_usage(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expansion-by-segment")
def get_expansion_by_segment_funnel(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_expansion_by_segment_funnel(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
