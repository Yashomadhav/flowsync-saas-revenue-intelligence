"""Shared helpers for MetricsService query layer."""
from __future__ import annotations
import json
import logging
from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _q(db: Session, sql: str, params: dict | None = None) -> list[dict[str, Any]]:
    try:
        result = db.execute(text(sql), params or {})
        cols = list(result.keys())
        return [dict(zip(cols, row)) for row in result.fetchall()]
    except Exception as exc:
        logger.error("Query failed: %s | error=%s", sql[:100], exc)
        raise


def _div(n: float, d: float, default: float = 0.0) -> float:
    return n / d if d else default


def _pct(raw: Any) -> float:
    return round(float(raw or 0) * 100, 2)


def _f(raw: Any) -> float:
    return float(raw or 0)


def _i(raw: Any) -> int:
    return int(raw or 0)


def _s(raw: Any) -> str:
    return str(raw or "")


def _risks(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return [str(raw)]


def _latest(db: Session, table: str = "marts.mart_exec_revenue_summary", col: str = "month_key") -> Optional[str]:
    rows = _q(db, f"SELECT MAX({col}) AS mk FROM {table}")
    return rows[0]["mk"] if rows else None
