"""Customer Health & Churn Risk Router — delegates to MetricsService."""
from __future__ import annotations
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from services import MetricsService

router = APIRouter()


def _svc(db: Session) -> MetricsService:
    return MetricsService(db)


@router.get("/distribution")
def get_health_distribution(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None, description="YYYY-MM"),
) -> dict:
    try:
        return _svc(db).get_health_distribution(month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/churn-risk-quadrant")
def get_churn_risk_quadrant(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
) -> dict:
    try:
        return _svc(db).get_churn_risk_quadrant(month_key=month_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risky-accounts")
def get_risky_accounts(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None, description="high|critical"),
    plan_name: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=5, le=100),
) -> dict:
    try:
        return _svc(db).get_risky_accounts(
            month_key=month_key,
            risk_level=risk_level,
            plan_name=plan_name,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support-burden")
def get_support_burden(
    db: Annotated[Session, Depends(get_db)],
    month_key: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=5, le=100),
) -> dict:
    try:
        return _svc(db).get_support_burden(month_key=month_key, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
