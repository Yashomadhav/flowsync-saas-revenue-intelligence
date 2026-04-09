"""Cohort retention queries."""
from .metrics_helpers import _q, _div, _pct, _f, _i, _s


class CohortsMixin:
    def get_cohort_heatmap(self, metric="logo_retention"):
        rows = _q(self.db,
            "SELECT cohort_month,months_since_created,cohort_size,active_accounts,"
            "logo_retention_rate,revenue_retention_rate,nrr,grr,cohort_mrr,starting_mrr,cohort_health "
            "FROM marts.fct_customer_cohorts ORDER BY cohort_month,months_since_created")
        cohorts = sorted(set(_s(r["cohort_month"]) for r in rows))
        max_p = max((_i(r["months_since_created"]) for r in rows), default=0)
        data = [{
            "cohort_month": _s(r["cohort_month"]),
            "months_since_created": _i(r["months_since_created"]),
            "cohort_size": _i(r.get("cohort_size")),
            "active_accounts": _i(r.get("active_accounts")),
            "logo_retention_rate": _f(r.get("logo_retention_rate")),
            "revenue_retention_rate": _f(r.get("revenue_retention_rate")),
            "nrr": _f(r.get("nrr")),
            "grr": _f(r.get("grr")),
            "cohort_mrr": _f(r.get("cohort_mrr")),
            "starting_mrr": _f(r.get("starting_mrr")),
            "cohort_health": _s(r.get("cohort_health")),
        } for r in rows]
        return {"metric": metric, "cohorts": cohorts, "max_period": max_p, "data": data, "total_rows": len(data)}

    def get_logo_churn_trend(self, months=24):
        rows = _q(self.db,
            "SELECT month_key,logo_churn_rate,churned_accounts,starting_accounts,active_accounts "
            "FROM marts.mart_exec_revenue_summary ORDER BY month_key DESC LIMIT :m", {"m": months})
        data = [{
            "month_key": r["month_key"],
            "logo_churn_rate": _pct(r.get("logo_churn_rate")),
            "churned_accounts": _i(r.get("churned_accounts")),
            "starting_accounts": _i(r.get("starting_accounts")),
            "active_accounts": _i(r.get("active_accounts")),
        } for r in reversed(rows)]
        avg_churn = round(_div(sum(d["logo_churn_rate"] for d in data), len(data)), 2) if data else 0
        return {"data": data, "months": len(data), "avg_logo_churn_rate": avg_churn}

    def get_nrr_by_cohort(self, period_months=12):
        # period_months = how many months_since_created to filter on (e.g. 12 = 12-month cohort view)
        rows = _q(self.db,
            "SELECT cohort_month,nrr,grr,logo_retention_rate,revenue_retention_rate,"
            "cohort_size,active_accounts,cohort_mrr,starting_mrr,cohort_health "
            "FROM marts.fct_customer_cohorts WHERE months_since_created=:p "
            "ORDER BY cohort_month DESC LIMIT 24", {"p": period_months})
        data = [{
            "cohort_month": _s(r["cohort_month"]),
            "nrr": _f(r.get("nrr")),
            "grr": _f(r.get("grr")),
            "logo_retention_rate": _f(r.get("logo_retention_rate")),
            "revenue_retention_rate": _f(r.get("revenue_retention_rate")),
            "cohort_size": _i(r.get("cohort_size")),
            "active_accounts": _i(r.get("active_accounts")),
            "cohort_mrr": _f(r.get("cohort_mrr")),
            "starting_mrr": _f(r.get("starting_mrr")),
            "cohort_health": _s(r.get("cohort_health")),
        } for r in reversed(rows)]
        avg_nrr = round(_div(sum(d["nrr"] for d in data), len(data)), 2) if data else 0
        avg_grr = round(_div(sum(d["grr"] for d in data), len(data)), 2) if data else 0
        return {"period_months": period_months, "data": data, "avg_nrr": avg_nrr, "avg_grr": avg_grr}

    def get_retention_by_segment(self, dimension="plan_name", period_months=12):
        if dimension not in {"plan_name", "company_size", "region"}:
            raise ValueError("dimension must be one of plan_name, company_size, region")
        # Query account-level health data grouped by segment dimension.
        # fct_customer_cohorts is cohort-level (no account_id), so we use
        # fct_account_monthly_health which has both segment columns and monthly data.
        sql = (
            "SELECT h.{d} AS segment_value,"
            "AVG(h.health_score) AS avg_health_score,"
            "COUNT(DISTINCT h.account_id) AS account_count,"
            "AVG(h.mrr) AS avg_mrr,"
            "SUM(h.mrr) AS total_mrr,"
            "AVG(CASE WHEN h.churn_risk_level='high' THEN 1.0 ELSE 0.0 END)*100 AS pct_high_risk "
            "FROM marts.fct_account_monthly_health h "
            "WHERE h.month_key >= (CURRENT_DATE - INTERVAL '1 month' * :p)::date "
            "GROUP BY h.{d} ORDER BY avg_health_score DESC NULLS LAST"
        ).format(d=dimension)
        rows = _q(self.db, sql, {"p": period_months})
        data = [{
            "segment_value": _s(r.get("segment_value")),
            "avg_health_score": _f(r.get("avg_health_score")),
            "account_count": _i(r.get("account_count")),
            "avg_mrr": _f(r.get("avg_mrr")),
            "total_mrr": _f(r.get("total_mrr")),
            "pct_high_risk": _f(r.get("pct_high_risk")),
        } for r in rows]
        return {"dimension": dimension, "period_months": period_months, "data": data}
