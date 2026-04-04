"""Customer health and churn risk queries."""
from .metrics_helpers import _q, _div, _f, _i, _s, _risks, _latest


class HealthMixin:
    def get_health_distribution(self, month_key=None):
        if not month_key:
            month_key = _latest(self.db, "marts.mart_customer_success_summary", "snapshot_month")
        rows = _q(self.db,
            "SELECT health_tier,COUNT(*) AS account_count,SUM(mrr) AS total_mrr,"
            "AVG(health_score) AS avg_health_score,AVG(mrr) AS avg_mrr "
            "FROM marts.mart_customer_success_summary WHERE snapshot_month=:mk "
            "GROUP BY health_tier ORDER BY avg_health_score DESC",
            {"mk": month_key})
        total_accts = sum(_i(r.get("account_count")) for r in rows)
        total_mrr = sum(_f(r.get("total_mrr")) for r in rows)
        data = [{
            "health_tier": _s(r.get("health_tier")),
            "account_count": _i(r.get("account_count")),
            "total_mrr": _f(r.get("total_mrr")),
            "avg_health_score": round(_f(r.get("avg_health_score")), 1),
            "avg_mrr": round(_f(r.get("avg_mrr")), 2),
            "pct_of_accounts": round(_div(_i(r.get("account_count")), total_accts) * 100, 2),
            "pct_of_mrr": round(_div(_f(r.get("total_mrr")), total_mrr) * 100, 2),
        } for r in rows]
        return {"month_key": month_key, "total_accounts": total_accts, "total_mrr": total_mrr, "data": data}

    def get_churn_risk_quadrant(self, month_key=None):
        if not month_key:
            month_key = _latest(self.db, "marts.mart_customer_success_summary", "snapshot_month")
        rows = _q(self.db,
            "SELECT account_id,company_name,plan_name,region,industry,company_size,"
            "mrr,arr,health_score,churn_risk_level,risk_priority_score,"
            "risk_reasons,health_trend,health_tier "
            "FROM marts.mart_customer_success_summary WHERE snapshot_month=:mk "
            "ORDER BY risk_priority_score DESC NULLS LAST LIMIT 200",
            {"mk": month_key})
        data = [{
            "account_id": _s(r.get("account_id")),
            "company_name": _s(r.get("company_name")),
            "plan_name": _s(r.get("plan_name")),
            "region": _s(r.get("region")),
            "industry": _s(r.get("industry")),
            "company_size": _s(r.get("company_size")),
            "mrr": _f(r.get("mrr")),
            "arr": _f(r.get("arr")),
            "health_score": _f(r.get("health_score")),
            "churn_risk_level": _s(r.get("churn_risk_level")),
            "risk_priority_score": _f(r.get("risk_priority_score")),
            "risk_reasons": _risks(r.get("risk_reasons")),
            "health_trend": _s(r.get("health_trend")),
            "health_tier": _s(r.get("health_tier")),
        } for r in rows]
        return {"month_key": month_key, "data": data, "total": len(data)}

    def get_risky_accounts(self, month_key=None, risk_level=None, plan_name=None, page=1, page_size=25):
        if not month_key:
            month_key = _latest(self.db, "marts.mart_customer_success_summary", "snapshot_month")
        filters = ["snapshot_month=:mk", "churn_risk_level IN ('high','critical')"]
        params = {"mk": month_key, "ps": page_size, "off": (page - 1) * page_size}
        if risk_level:
            filters.append("churn_risk_level=:rl")
            params["rl"] = risk_level
        if plan_name:
            filters.append("plan_name=:pn")
            params["pn"] = plan_name
        where = " AND ".join(filters)
        cnt = _q(self.db, f"SELECT COUNT(*) AS c FROM marts.mart_customer_success_summary WHERE {where}", params)
        total = _i(cnt[0]["c"]) if cnt else 0
        rows = _q(self.db,
            f"SELECT account_id,company_name,plan_name,region,industry,company_size,"
            f"mrr,arr,health_score,health_tier,churn_risk_level,risk_priority_score,risk_reasons,health_trend "
            f"FROM marts.mart_customer_success_summary WHERE {where} "
            f"ORDER BY risk_priority_score DESC NULLS LAST LIMIT :ps OFFSET :off", params)
        data = [{
            "account_id": _s(r.get("account_id")),
            "company_name": _s(r.get("company_name")),
            "plan_name": _s(r.get("plan_name")),
            "region": _s(r.get("region")),
            "industry": _s(r.get("industry")),
            "company_size": _s(r.get("company_size")),
            "mrr": _f(r.get("mrr")),
            "arr": _f(r.get("arr")),
            "health_score": _f(r.get("health_score")),
            "health_tier": _s(r.get("health_tier")),
            "churn_risk_level": _s(r.get("churn_risk_level")),
            "risk_priority_score": _f(r.get("risk_priority_score")),
            "risk_reasons": _risks(r.get("risk_reasons")),
            "health_trend": _s(r.get("health_trend")),
        } for r in rows]
        return {"month_key": month_key, "total_count": total, "page": page, "page_size": page_size, "data": data}

    def get_support_burden(self, month_key=None, limit=20):
        if not month_key:
            month_key = _latest(self.db, "marts.mart_customer_success_summary", "snapshot_month")
        rows = _q(self.db,
            "SELECT s.account_id,s.company_name,s.plan_name,s.mrr,s.health_score,s.churn_risk_level,"
            "COUNT(t.ticket_id) AS total_tickets,"
            "SUM(CASE WHEN t.priority='high' THEN 1 ELSE 0 END) AS high_priority_tickets,"
            "SUM(CASE WHEN t.status='open' THEN 1 ELSE 0 END) AS open_tickets,"
            "AVG(CASE WHEN t.resolved_at IS NOT NULL THEN "
            "  EXTRACT(EPOCH FROM (t.resolved_at - t.created_at))/3600 END) AS avg_resolution_hours,"
            "AVG(t.csat_score) AS avg_csat "
            "FROM marts.mart_customer_success_summary s "
            "LEFT JOIN staging.stg_support_tickets t ON s.account_id::text=t.account_id::text "
            "AND DATE_TRUNC('month', t.created_at)=CAST(:mk AS date) "
            "WHERE s.snapshot_month=CAST(:mk AS date) "
            "GROUP BY s.account_id,s.company_name,s.plan_name,s.mrr,s.health_score,s.churn_risk_level "
            "ORDER BY total_tickets DESC NULLS LAST LIMIT :lim",
            {"mk": month_key, "lim": limit})
        data = [{
            "account_id": _s(r.get("account_id")),
            "company_name": _s(r.get("company_name")),
            "plan_name": _s(r.get("plan_name")),
            "mrr": _f(r.get("mrr")),
            "health_score": _f(r.get("health_score")),
            "churn_risk_level": _s(r.get("churn_risk_level")),
            "total_tickets": _i(r.get("total_tickets")),
            "high_priority_tickets": _i(r.get("high_priority_tickets")),
            "open_tickets": _i(r.get("open_tickets")),
            "avg_resolution_hours": round(_f(r.get("avg_resolution_hours")), 1),
            "avg_csat": round(_f(r.get("avg_csat")), 2),
        } for r in rows]
        return {"month_key": month_key, "data": data}
