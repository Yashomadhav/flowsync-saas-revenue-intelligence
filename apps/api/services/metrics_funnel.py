"""Funnel and growth queries."""
from .metrics_helpers import _q, _div, _f, _i, _s


class FunnelMixin:
    def get_funnel_overview(self, months=12):
        rows = _q(self.db,
            "SELECT COUNT(*) AS total_leads,"
            "COUNT(*) FILTER (WHERE funnel_stage IN ('trial','paid')) AS trial_starts,"
            "COUNT(*) FILTER (WHERE is_paid_conversion=TRUE) AS paid_conversions,"
            "AVG(days_lead_to_paid) FILTER (WHERE is_paid_conversion=TRUE) AS avg_days_to_paid,"
            "AVG(converted_mrr) FILTER (WHERE is_paid_conversion=TRUE) AS avg_first_month_mrr,"
            "SUM(converted_mrr) FILTER (WHERE is_paid_conversion=TRUE) AS total_converted_mrr "
            "FROM marts.fct_sales_conversion "
            "WHERE lead_created_month >= (NOW() - INTERVAL '1 month' * :m)::date",
            {"m": months})
        if not rows:
            return {}
        r = rows[0]
        total = _i(r.get("total_leads"))
        trials = _i(r.get("trial_starts"))
        paid = _i(r.get("paid_conversions"))
        return {
            "period_months": months,
            "total_leads": total,
            "trial_starts": trials,
            "paid_conversions": paid,
            "lead_to_trial_rate": round(_div(trials, total) * 100, 2),
            "trial_to_paid_rate": round(_div(paid, trials) * 100, 2),
            "overall_conversion_rate": round(_div(paid, total) * 100, 2),
            "avg_days_to_paid": round(_f(r.get("avg_days_to_paid")), 1),
            "avg_first_month_mrr": round(_f(r.get("avg_first_month_mrr")), 2),
            "total_converted_mrr": round(_f(r.get("total_converted_mrr")), 2),
        }

    def get_conversion_by_channel(self, months=12):
        rows = _q(self.db,
            "SELECT acquisition_channel AS channel,"
            "COUNT(*) AS total_leads,"
            "COUNT(*) FILTER (WHERE funnel_stage IN ('trial','paid')) AS trial_starts,"
            "COUNT(*) FILTER (WHERE is_paid_conversion=TRUE) AS paid_conversions,"
            "AVG(days_lead_to_paid) FILTER (WHERE is_paid_conversion=TRUE) AS avg_days_to_convert,"
            "AVG(converted_mrr) FILTER (WHERE is_paid_conversion=TRUE) AS avg_first_month_mrr,"
            "SUM(converted_mrr) FILTER (WHERE is_paid_conversion=TRUE) AS total_converted_mrr "
            "FROM marts.fct_sales_conversion "
            "WHERE lead_created_month >= (NOW() - INTERVAL '1 month' * :m)::date "
            "GROUP BY acquisition_channel ORDER BY paid_conversions DESC",
            {"m": months})
        total_leads = sum(_i(r.get("total_leads")) for r in rows)
        total_conv = sum(_i(r.get("paid_conversions")) for r in rows)
        data = []
        for r in rows:
            leads = _i(r.get("total_leads"))
            trials = _i(r.get("trial_starts"))
            paid = _i(r.get("paid_conversions"))
            data.append({
                "channel": _s(r.get("channel")),
                "total_leads": leads,
                "trial_starts": trials,
                "paid_conversions": paid,
                "trial_to_paid_rate": round(_div(paid, trials) * 100, 2),
                "overall_conversion_rate": round(_div(paid, leads) * 100, 2),
                "avg_days_to_convert": round(_f(r.get("avg_days_to_convert")), 1),
                "avg_first_month_mrr": round(_f(r.get("avg_first_month_mrr")), 2),
                "total_converted_mrr": round(_f(r.get("total_converted_mrr")), 2),
                "pct_of_total_leads": round(_div(leads, total_leads) * 100, 2),
                "pct_of_total_conversions": round(_div(paid, total_conv) * 100, 2),
            })
        best_conv = max(data, key=lambda x: x["overall_conversion_rate"])["channel"] if data else None
        best_mrr = max(data, key=lambda x: x["avg_first_month_mrr"])["channel"] if data else None
        return {
            "period_months": months,
            "total_leads": total_leads,
            "total_conversions": total_conv,
            "data": data,
            "best_channel_by_conversion": best_conv,
            "best_channel_by_mrr": best_mrr,
        }

    def get_sales_cycle(self, months=12):
        # Note: fct_sales_conversion has no plan_name column — group by channel only
        rows = _q(self.db,
            "SELECT acquisition_channel AS channel,"
            "AVG(days_lead_to_paid) AS avg_days,"
            "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_lead_to_paid) AS median_days,"
            "MIN(days_lead_to_paid) AS min_days,MAX(days_lead_to_paid) AS max_days,"
            "COUNT(*) AS conversions,AVG(converted_mrr) AS avg_mrr "
            "FROM marts.fct_sales_conversion "
            "WHERE is_paid_conversion=TRUE "
            "AND lead_created_month >= (NOW() - INTERVAL '1 month' * :m)::date "
            "GROUP BY acquisition_channel ORDER BY avg_days ASC",
            {"m": months})
        data = [{
            "channel": _s(r.get("channel")),
            "avg_days": round(_f(r.get("avg_days")), 1),
            "median_days": round(_f(r.get("median_days")), 1),
            "min_days": round(_f(r.get("min_days")), 1),
            "max_days": round(_f(r.get("max_days")), 1),
            "conversions": _i(r.get("conversions")),
            "avg_mrr": round(_f(r.get("avg_mrr")), 2),
        } for r in rows]
        all_days = [d["avg_days"] for d in data if d["avg_days"] > 0]
        overall_avg = round(_div(sum(all_days), len(all_days)), 1) if all_days else 0
        sorted_d = sorted(all_days)
        overall_median = sorted_d[len(sorted_d) // 2] if sorted_d else 0
        return {"period_months": months, "data": data, "overall_avg_days": overall_avg, "overall_median_days": overall_median}

    def get_trial_usage(self, months=12):
        rows = _q(self.db,
            "SELECT "
            "COUNT(*) FILTER (WHERE funnel_stage IN ('trial','paid')) AS trial_accounts,"
            "COUNT(*) FILTER (WHERE is_paid_conversion=TRUE) AS paid_conversions,"
            "AVG(converted_mrr) FILTER (WHERE is_paid_conversion=TRUE) AS avg_converted_mrr,"
            "AVG(days_lead_to_paid) FILTER (WHERE is_paid_conversion=TRUE) AS avg_days_to_convert "
            "FROM marts.fct_sales_conversion "
            "WHERE lead_created_month >= (NOW() - INTERVAL '1 month' * :m)::date",
            {"m": months})
        if not rows:
            return {"period_months": months, "trial_accounts": 0, "paid_conversions": 0, "trial_to_paid_rate": 0.0}
        r = rows[0]
        trial_accounts = _i(r.get("trial_accounts"))
        paid_conversions = _i(r.get("paid_conversions"))
        return {
            "period_months": months,
            "trial_accounts": trial_accounts,
            "paid_conversions": paid_conversions,
            "trial_to_paid_rate": round(_div(paid_conversions, trial_accounts) * 100, 2),
            "avg_converted_mrr": round(_f(r.get("avg_converted_mrr")), 2),
            "avg_days_to_convert": round(_f(r.get("avg_days_to_convert")), 1),
        }

    def get_expansion_by_segment_funnel(self, months=12):
        rows = _q(self.db,
            "SELECT s.company_size,s.acquisition_channel,f.plan_name,"
            "SUM(f.expansion_mrr) AS total_expansion_mrr,"
            "COUNT(DISTINCT CASE WHEN f.expansion_mrr>0 THEN f.account_id END) AS expanding_accounts "
            "FROM marts.fct_mrr_movements f "
            "JOIN marts.mart_customer_success_summary s ON f.account_id=s.account_id "
            "WHERE f.expansion_mrr>0 "
            "AND f.month_key >= (NOW() - INTERVAL '1 month' * :m)::date "
            "GROUP BY s.company_size,s.acquisition_channel,f.plan_name "
            "ORDER BY total_expansion_mrr DESC LIMIT 50",
            {"m": months})
        total_exp = sum(_f(r.get("total_expansion_mrr")) for r in rows)
        data = []
        for r in rows:
            exp_mrr = _f(r.get("total_expansion_mrr"))
            exp_accts = _i(r.get("expanding_accounts"))
            data.append({
                "company_size": _s(r.get("company_size")),
                "acquisition_channel": _s(r.get("acquisition_channel")),
                "plan_name": _s(r.get("plan_name")),
                "total_expansion_mrr": exp_mrr,
                "expanding_accounts": exp_accts,
                "avg_expansion_per_account": round(_div(exp_mrr, exp_accts), 2),
                "pct_of_total_expansion": round(_div(exp_mrr, total_exp) * 100, 2),
            })
        top_seg = data[0]["company_size"] if data else None
        return {
            "period_months": months,
            "total_expansion_mrr": total_exp,
            "total_expanding_accounts": sum(d["expanding_accounts"] for d in data),
            "data": data,
            "top_expansion_segment": top_seg,
        }
