"""Funnel & Growth Router — delegates to MetricsService with tenant isolation."""
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


@router.get("/overview")
def get_funnel_overview(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_funnel_overview(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch funnel overview.")


@router.get("/conversion-by-channel")
def get_conversion_by_channel(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_conversion_by_channel(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch conversion by channel.")


@router.get("/sales-cycle")
def get_sales_cycle(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_sales_cycle(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch sales cycle.")


@router.get("/trial-usage")
def get_trial_usage(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_trial_usage(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch trial usage.")


@router.get("/expansion-by-segment")
def get_expansion_by_segment_funnel(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_expansion_by_segment_funnel(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch expansion by segment.")
