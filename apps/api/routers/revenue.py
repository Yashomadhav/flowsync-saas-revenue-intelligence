"""Revenue Movements Router — delegates to MetricsService with tenant isolation."""
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


@router.get("/mrr-bridge")
def get_mrr_bridge(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_mrr_bridge(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch MRR bridge.")


@router.get("/account-movements")
def get_account_movements(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None, description="YYYY-MM"),
    movement_type: Optional[str] = Query(default=None, description="new|expansion|contraction|churn|reactivation"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=10, le=200),
) -> dict:
    try:
        return _svc(db, user).get_account_movements(
            month_key=month_key,
            movement_type=movement_type,
            page=page,
            page_size=page_size,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch account movements.")


@router.get("/new-mrr-by-channel")
def get_new_mrr_by_channel(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_new_mrr_by_channel(month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch new MRR by channel.")


@router.get("/expansion-by-segment")
def get_expansion_by_segment(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    dimension: str = Query(default="company_size", description="company_size|plan_name|region"),
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_expansion_by_segment(dimension=dimension, month_key=month_key)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch expansion by segment.")


@router.get("/churned-by-plan")
def get_churned_by_plan(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db, user).get_churned_by_plan(month_key=month_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch churned by plan.")


@router.get("/payment-trend")
def get_payment_trend(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    months: int = Query(default=12, ge=3, le=36),
) -> dict:
    try:
        return _svc(db, user).get_payment_trend(months=months)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch payment trend.")
