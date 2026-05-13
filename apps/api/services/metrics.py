"""MetricsService — combines all domain mixins into a single service class."""
from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from .metrics_exec_revenue import ExecRevenueMixin
from .metrics_cohorts import CohortsMixin
from .metrics_health import HealthMixin
from .metrics_funnel import FunnelMixin


class MetricsService(ExecRevenueMixin, CohortsMixin, HealthMixin, FunnelMixin):
    """
    Unified metrics service for all dashboard domains.
    Accepts an optional tenant_id for multi-tenant query scoping.
    """

    def __init__(self, db: Session, tenant_id: Optional[UUID] = None) -> None:
        self.db = db
        self.tenant_id = tenant_id
