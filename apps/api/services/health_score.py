"""Rule-based account health score computation."""
from __future__ import annotations
from typing import Any
from .metrics_helpers import _q, _f, _i, _s, _risks, _latest


WEIGHTS = {
    "usage_frequency": 20,
    "seat_utilization": 15,
    "feature_adoption": 15,
    "support_burden": 15,
    "csat": 15,
    "payment_health": 10,
    "tenure_stability": 10,
}

RISK_FLAGS = {
    "usage_drop_40pct": "Usage dropped >40% month-over-month",
    "no_login_14d": "No login in 14+ days",
    "high_priority_tickets": "2+ unresolved high-priority tickets",
    "payment_failed": "Failed payment in current cycle",
    "low_csat": "CSAT score below 3.0",
    "low_seat_utilization": "Seat utilization below 25%",
}


class HealthScoreService:
    def __init__(self, db: Any) -> None:
        self.db = db

    def get_account_health_summary(self, month_key: str | None = None) -> dict[str, Any]:
        if not month_key:
            month_key = _latest(self.db, "marts.mart_customer_success_summary", "snapshot_month")
        rows = _q(self.db,
            "SELECT health_tier,COUNT(*) AS cnt,AVG(health_score) AS avg_score,"
            "SUM(mrr) AS total_mrr,AVG(churn_risk_score) AS avg_risk "
            "FROM marts.mart_customer_success_summary WHERE snapshot_month=:mk "
            "GROUP BY health_tier ORDER BY avg_score DESC",
            {"mk": month_key})
        return {
            "month_key": month_key,
            "tiers": [{
                "health_tier": _s(r.get("health_tier")),
                "account_count": _i(r.get("cnt")),
                "avg_health_score": round(_f(r.get("avg_score")), 1),
                "total_mrr": _f(r.get("total_mrr")),
                "avg_churn_risk_score": round(_f(r.get("avg_risk")), 1),
            } for r in rows],
        }

    def get_risk_flag_breakdown(self, month_key: str | None = None) -> dict[str, Any]:
        if not month_key:
            month_key = _latest(self.db, "marts.mart_customer_success_summary", "snapshot_month")
        rows = _q(self.db,
            "SELECT risk_reasons,COUNT(*) AS cnt,SUM(mrr) AS at_risk_mrr "
            "FROM marts.mart_customer_success_summary "
            "WHERE snapshot_month=:mk AND churn_risk_level IN ('high','critical') "
            "GROUP BY risk_reasons",
            {"mk": month_key})
        flag_counts: dict[str, int] = {}
        flag_mrr: dict[str, float] = {}
        for r in rows:
            reasons = _risks(r.get("risk_reasons"))
            cnt = _i(r.get("cnt"))
            mrr = _f(r.get("at_risk_mrr"))
            for reason in reasons:
                flag_counts[reason] = flag_counts.get(reason, 0) + cnt
                flag_mrr[reason] = flag_mrr.get(reason, 0.0) + mrr
        breakdown = [
            {"flag": flag, "account_count": flag_counts.get(flag, 0), "at_risk_mrr": flag_mrr.get(flag, 0.0)}
            for flag in RISK_FLAGS
        ]
        breakdown.sort(key=lambda x: x["account_count"], reverse=True)
        return {"month_key": month_key, "risk_flags": breakdown, "flag_definitions": RISK_FLAGS}

    def get_health_trend(self, account_id: str, months: int = 12) -> dict[str, Any]:
        rows = _q(self.db,
            "SELECT snapshot_month,health_score,health_tier,churn_risk_level,"
            "risk_priority_score,mrr,risk_reasons "
            "FROM marts.mart_customer_success_summary "
            "WHERE account_id=:aid ORDER BY snapshot_month DESC LIMIT :m",
            {"aid": account_id, "m": months})
        data = [{
            "month": _s(r.get("snapshot_month")),
            "health_score": _f(r.get("health_score")),
            "health_tier": _s(r.get("health_tier")),
            "churn_risk_level": _s(r.get("churn_risk_level")),
            "risk_priority_score": _f(r.get("risk_priority_score")),
            "mrr": _f(r.get("mrr")),
            "risk_reasons": _risks(r.get("risk_reasons")),
        } for r in reversed(rows)]
        if len(data) >= 2:
            trend = "improving" if data[-1]["health_score"] > data[-2]["health_score"] else "declining"
        else:
            trend = "stable"
        return {"account_id": account_id, "trend": trend, "data": data}

    def get_usage_drop_alerts(self, month_key: str | None = None, threshold: float = 0.4) -> dict[str, Any]:
        if not month_key:
            month_key = _latest(self.db, "marts.fct_account_monthly_health")
        rows = _q(self.db,
            "SELECT cur.account_id,cur.company_name,cur.plan_name,cur.mrr,"
            "cur.health_score,cur.churn_risk_level,"
            "cur.monthly_active_users AS cur_mau,prev.monthly_active_users AS prev_mau,"
            "CASE WHEN prev.monthly_active_users>0 "
            "THEN (cur.monthly_active_users-prev.monthly_active_users)::float/prev.monthly_active_users "
            "ELSE NULL END AS usage_change_pct "
            "FROM marts.fct_account_monthly_health cur "
            "JOIN marts.fct_account_monthly_health prev "
            "ON cur.account_id=prev.account_id "
            "AND prev.month_key=TO_CHAR(TO_DATE(cur.month_key,'YYYY-MM')-INTERVAL '1 month','YYYY-MM') "
            "WHERE cur.month_key=:mk "
            "AND prev.monthly_active_users>0 "
            "AND (cur.monthly_active_users-prev.monthly_active_users)::float/prev.monthly_active_users <= -:thr "
            "ORDER BY usage_change_pct ASC LIMIT 50",
            {"mk": month_key, "thr": threshold})
        data = [{
            "account_id": _s(r.get("account_id")),
            "company_name": _s(r.get("company_name")),
            "plan_name": _s(r.get("plan_name")),
            "mrr": _f(r.get("mrr")),
            "health_score": _f(r.get("health_score")),
            "churn_risk_level": _s(r.get("churn_risk_level")),
            "cur_mau": _i(r.get("cur_mau")),
            "prev_mau": _i(r.get("prev_mau")),
            "usage_change_pct": round(_f(r.get("usage_change_pct")) * 100, 1),
        } for r in rows]
        return {"month_key": month_key, "threshold_pct": threshold * 100, "alerts": data, "total": len(data)}
