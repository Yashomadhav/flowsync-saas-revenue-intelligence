"""Revenue Movements Router — delegates to MetricsService."""
from __future__ import annotations
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from services import MetricsService

router = APIRouter()


def _svc(db: Session) -> MetricsService:
    return MetricsService(db)


@router.get("/mrr-bridge")
def get_mrr_bridge(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_mrr_bridge(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account-movements")
def get_account_movements(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None, description="YYYY-MM"),
    movement_type: Optional[str] = Query(default=None, description="new|expansion|contraction|churn|reactivation"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=10, le=200),
) -> dict:
    try:
        return _svc(db).get_account_movements(
            month_key=month_key,
            movement_type=movement_type,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new-mrr-by-channel")
def get_new_mrr_by_channel(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_new_mrr_by_channel(month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expansion-by-segment")
def get_expansion_by_segment(
    db: Annotated[Session, Depends(get_db)],
    dimension: str = Query(default="company_size", description="company_size|plan_name|region"),
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_expansion_by_segment(dimension=dimension, month_key=month_key)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/churned-by-plan")
def get_churned_by_plan(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_churned_by_plan(month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-trend")
def get_payment_trend(
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db).get_payment_trend(months=months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
