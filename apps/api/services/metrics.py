"""MetricsService — combines all domain mixins into a single service class."""
from __future__ import annotations
from sqlalchemy.orm import Session
from .metrics_exec_revenue import ExecRevenueMixin
from .metrics_cohorts import CohortsMixin
from .metrics_health import HealthMixin
from .metrics_funnel import FunnelMixin


class MetricsService(ExecRevenueMixin, CohortsMixin, HealthMixin, FunnelMixin):
    """
    Unified metrics service for all dashboard domains.

    Domains:
    - Executive: KPI summary, MRR trend, waterfall, revenue by dimension, top accounts
    - Revenue: MRR bridge, account movements, new MRR by channel, expansion, churn, payments
    - Cohorts: cohort heatmap, logo churn trend, NRR by cohort, retention by segment
    - Health: health distribution, churn risk quadrant, risky accounts, support burden
    - Funnel: funnel overview, conversion by channel, sales cycle, expansion by segment
    """

    def __init__(self, db: Session) -> None:
        self.db = db
