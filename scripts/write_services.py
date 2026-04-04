"""Write all API service files programmatically to avoid tool truncation."""
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'services')
os.makedirs(BASE, exist_ok=True)

# ── metrics_helpers.py ────────────────────────────────────────────────────────
helpers = '''\
"""Shared helpers for MetricsService."""
from __future__ import annotations
import json, logging
from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def _q(db, sql, params=None):
    try:
        r = db.execute(text(sql), params or {})
        cols = list(r.keys())
        return [dict(zip(cols, row)) for row in r.fetchall()]
    except Exception as exc:
        logger.error("Query failed: %s | %s", sql[:80], exc); raise

def _div(n, d, default=0.0): return n / d if d else default
def _pct(v): return round(float(v or 0) * 100, 2)
def _f(v): return float(v or 0)
def _i(v): return int(v or 0)
def _s(v): return str(v or "")
def _risks(v):
    if not v: return []
    if isinstance(v, list): return v
    try: return json.loads(v)
    except: return [str(v)]
def _latest(db, table="marts.mart_exec_revenue_summary", col="month_key"):
    rows = _q(db, f"SELECT MAX({col}) AS mk FROM {table}")
    return rows[0]["mk"] if rows else None
'''

# ── metrics_exec.py ───────────────────────────────────────────────────────────
exec_svc = '''\
"""Executive overview queries."""
from .metrics_helpers import _q, _div, _pct, _f, _i, _s, _risks, _latest

class ExecMixin:
    def get_latest_exec_kpi(self, month_key=None):
        rows = _q(self.db, "SELECT * FROM marts.mart_exec_revenue_summary WHERE month_key=:mk LIMIT 1", {"mk": month_key}) if month_key else _q(self.db, "SELECT * FROM marts.mart_exec_revenue_summary ORDER BY month_key DESC LIMIT 1")
        if not rows: return {}
        cur = dict(rows[0])
        p = (_q(self.db, "SELECT total_mrr,nrr,logo_churn_rate FROM marts.mart_exec_revenue_summary WHERE month_key<:mk ORDER BY month_key DESC LIMIT 1", {"mk": cur["month_key"]}) or [{}])[0]
        for k in ("nrr","grr"): cur[k] = _pct(cur.get(k, 1.0))
        for k in ("logo_churn_rate","revenue_churn_rate","mrr_mom_pct"): cur[k] = _pct(cur.get(k, 0))
        if p:
            cur["prev_month_mrr"] = _f(p.get("total_mrr")); cur["prev_month_nrr"] = _pct(p.get("nrr",1.0)); cur["prev_month_logo_churn"] = _pct(p.get("logo_churn_rate"))
        return cur

    def get_mrr_trend(self, months=24):
        rows = _q(self.db, "SELECT month_key,total_mrr,total_arr,new_mrr,expansion_mrr,contraction_mrr,churned_mrr,reactivation_mrr,net_new_mrr,active_accounts,nrr,grr,logo_churn_rate,mrr_mom_pct FROM marts.mart_exec_revenue_summary ORDER BY month_key DESC LIMIT :m", {"m": months})
        data = []
        for r in reversed(rows):
            d = dict(r); d["nrr"]=_pct(d.get("nrr",1.0)); d["grr"]=_pct(d.get("grr",1.0)); d["logo_churn_rate"]=_pct(d.get("logo_churn_rate")); d["mrr_mom_pct"]=_pct(d.get("mrr_mom_pct")); data.append(d)
        return {"data": data, "months": len(data)}

    def get_waterfall(self, month_key=None):
        rows = _q(self.db, "SELECT * FROM marts.mart_exec_revenue_summary WHERE month_key=:mk", {"mk": month_key}) if month_key else _q(self.db, "SELECT * FROM marts.mart_exec_revenue_summary ORDER BY month_key DESC LIMIT 1")
        if not rows: return {}
        r = rows[0]; new_m=_f(r.get("new_mrr")); exp=_f(r.get("expansion_mrr")); react=_f(r.get("reactivation_mrr")); cont=_f(r.get("contraction_mrr")); churn=_f(r.get("churned_mrr")); end=_f(r.get("total_mrr")); start=end-_f(r.get("net_new_mrr")); c=start
        items=[{"label":"Starting MRR","value":start,"cumulative":c,"type":"start","color":"#6366f1"}]
        c+=new_m; items.append({"label":"New","value":new_m,"cumulative":c,"type":"positive","color":"#22c55e"})
        c+=exp; items.append({"label":"Expansion","value":exp,"cumulative":c,"type":"positive","color":"#10b981"})
        c+=react; items.append({"label":"Reactivation","value":react,"cumulative":c,"type":"positive","color":"#06b6d4"})
        c-=cont; items.append({"label":"Contraction","value":cont,"cumulative":c,"type":"negative","color":"#f59e0b"})
        c-=churn; items.append({"label":"Churn","value":churn,"cumulative":c,"type":"negative","color":"#ef4444"})
        items.append({"label":"Ending MRR","value":end,"cumulative":end,"type":"end","color":"#6366f1"})
        return {"month_key":r["month_key"],"items":items,"starting_mrr":start,"ending_mrr":end,"net_change":end-start}

    def get_revenue_by_dimension(self, dimension, month_key=None):
        if dimension not in {"plan_name","region","industry","company_size"}: raise ValueError(f"Bad dim: {dimension}")
        if not month_key: month_key = _latest(self.db)
        sql = ("SELECT {d} AS value,SUM(mrr) AS mrr,SUM(mrr*12) AS arr,COUNT(DISTINCT account_id) AS account_count,SUM(mrr)/NULLIF(COUNT(DISTINCT account_id),0) AS arpa FROM marts.fct_mrr_movements WHERE mrr>0 AND month_key=:mk GROUP BY {d} ORDER BY mrr DESC").format(d=dimension)
        rows = _q(self.db, sql, {"mk": month_key}); total = sum(_f(r.get("mrr")) for r in rows)
        items = [{"dimension":dimension,"value":_s(r.get("value")),"mrr":_f(r.get("mrr")),"arr":_f(r.get("arr")),"account_count":_i(r.get("account_count")),"arpa":_f(r.get("arpa")),"pct_of_total":round(_div(_f(r.get("mrr")),total)*100,2)} for r in rows]
        return {"month_key":month_key,"dimension":dimension,"total_mrr":total,"items":items}

    def get_top_accounts(self, sort_by="churn_risk", limit=10, month_key=None):
        if not month_key: month_key = _latest(self.db, "marts.mart_customer_success_summary", "snapshot_month")
        order = "risk_priority_score DESC NULLS LAST" if sort_by=="churn_risk" else "mrr DESC NULLS LAST"
        extra = "AND churn_risk_level IN (\'high\',\'critical\')" if sort_by=="churn_risk" else ""
        rows = _q(self.db, "SELECT account_id,company_name,plan_name,region,industry,company_size,mrr,arr,health_score,health_tier,churn_risk_level,risk_priority_score,risk_reasons,health_trend FROM marts.mart_customer_success_summary WHERE snapshot_month=:mk "+extra+" ORDER BY "+order+" LIMIT :lim", {"mk":month_key,"lim":limit})
        accounts = [{"account_id":_s(r.get("account_id")),"company_name":_s(r.get("company_name")),"plan_name":_s(r.get("plan_name")),"region":_s(r.get("region")),"industry":_s(r.get("industry")),"company_size":_s(r.get("company_size")),"mrr":_f(r.get("mrr")),"arr":_f(r.get("arr")),"health_score":_f(r.get("health_score")),"health_tier":_s(r.get("health_tier")),"churn_risk_level":_s(r.get("churn_risk_level")),"risk_reasons":_risks(r.get("risk_reasons"))} for r in rows]
        return {"month_key":month_key,"sort_by":sort_by,"limit":limit,"accounts":accounts}
'''

# ── metrics_revenue.py ────────────────────────────────────────────────────────
revenue_svc = '''\
"""Revenue movement queries."""
from .metrics_helpers import _q, _div, _pct, _f, _i, _s, _risks, _latest

class RevenueMixin:
    def get_mrr_bridge(self, months=12):
        rows = _q(self.db, "SELECT month_key,LAG(total_mrr) OVER (ORDER BY month_key) AS starting_mrr,new_mrr,expansion_mrr,contraction_mrr,churned_mrr,reactivation_mrr,net_new_mrr,total_mrr AS ending_mrr FROM marts.mart_exec_revenue_summary ORDER BY month_key DESC LIMIT :m", {"m":months})
        data = [{"month_key":r["month_key"],"starting_mrr":_f(r.get("starting_mrr")),"new_mrr":_f(r.get("new_mrr")),"expansion_mrr":_f(r.get("expansion_mrr")),"contraction_mrr":_f(r.get("contraction_mrr")),"churned_mrr":_f(r.get("churned_mrr")),"reactivation_mrr":_f(r.get("reactivation_mrr")),"net_new_mrr":_f(r.get("net_new_mrr")),"ending_mrr":_f(r.get("ending_mrr"))} for r in reversed(rows)]
        return {"data":data,"months":len(data)}

    def get_account_movements(self, month_key=None, movement_type=None, page=1, page_size=50):
        if not month_key: month_key = _latest(self.db, "marts.fct_mrr_movements")
        tf = "AND f.mrr_movement_type=:mtype" if movement_type else ""
        off = (page-1)*page_size; params = {"mk":month_key,"ps":page_size,"off":off}
        if movement_type: params["mtype"] = movement_type
        cnt = _q(self.db, "SELECT COUNT(*) AS c FROM marts.fct_mrr_movements f JOIN marts.mart_customer_success_summary s ON f.account_id=s.account_id WHERE f.month_key=:mk "+tf, params)
        total = _i(cnt[0]["c"]) if cnt else 0
        rows = _q(self.db, "SELECT f.account_id,s.company_name,f.plan_name,s.region,s.industry,s.company_size,f.month_key,f.mrr,f.mrr_movement_type,f.new_mrr,f.expansion_mrr,f.contraction_mrr,f.churned_mrr,f.reactivation_mrr,f.net_mrr_contribution,s.acquisition_channel FROM marts.fct_mrr_movements f JOIN marts.mart_customer_success_summary s ON f.account_id=s.account_id WHERE f.month_key=:mk "+tf+" ORDER BY ABS(f.net_mrr_contribution) DESC LIMIT :ps OFFSET :off", params)
        return {"month_key":month_key,"total_count":total,"page":page,"page_size":page_size,"data":[dict(r) for r in rows]}

    def get_new_mrr_by_channel(self, month_key=None):
        if not month_key: month_key = _latest(self.db, "marts.fct_mrr_movements")
        rows = _q(self.db, "SELECT s.acquisition_channel AS channel,f.month_key,SUM(f.new_mrr) AS new_mrr,COUNT(DISTINCT CASE WHEN f.new_mrr>0 THEN f.account_id END) AS new_accounts FROM marts.fct_mrr_movements f JOIN marts.mart_customer_success_summary s ON f.account_id=s.account_id WHERE f.month_key=:mk AND f.new_mrr>0 GROUP BY s.acquisition_channel,f.month_key ORDER BY new_mrr DESC", {"mk":month_key})
        total = sum(_f(r.get("new_mrr")) for r in rows)
        data = [{"channel":_s(r.get("channel")),"month_key":month_key,"new_mrr":_f(r.get("new_mrr")),"new_accounts":_i(r.get("new_accounts")),"avg_mrr_per_account":round(_div(_f(r.get("new_mrr")),_i(r.get("new_accounts"))),2),"pct_of_total_new_mrr":round(_div(_f(r.get("new_mrr")),total)*100,2)} for r in rows]
        return {"month_key":month_key,"total_new_mrr":total,"data":data}

    def get_expansion_by_segment(self, dimension="company_size", month_key=None):
        if dimension not in {"company_size","plan_name","region"}: raise ValueError("Bad dim")
        if not month_key: month_key = _latest(self.db, "marts.fct_mrr_movements")
        sql = ("SELECT s.{d} AS segment,f.month_key,SUM(f.expansion_mrr) AS expansion_mrr,COUNT(DISTINCT CASE WHEN f.expansion_mrr>0 THEN f.account_id END) AS expanding_accounts FROM marts.fct_mrr_movements f JOIN marts.mart_customer_success_summary s ON f.account_id=s.account_id WHERE f.month_key=:mk AND f.expansion_mrr>0 GROUP BY s.{d},f.month_key ORDER BY expansion_mrr DESC").format(d=dimension)
        rows = _q(self.db, sql, {"mk":month_key}); total = sum(_f(r.get("expansion_mrr")) for r in rows)
        data = [{"segment":_s(r.get("segment")),"month_key":month_key,"expansion_mrr":_f(r.get("expansion_mrr")),"expanding_accounts":_i(r.get("expanding_accounts")),"avg_expansion_per_account":round(_div(_f(r.get("expansion_mrr")),_i(r.get("expanding_accounts"))),2),"pct_of_total_expansion":round(_div(_f(r.get("expansion_mrr")),total)*100,2)} for r in rows]
        return {"month_key":month_key,"dimension":dimension,"total_expansion_mrr":total,"data":data}

    def get_churned_by_plan(self, month_key=None):
        if not month_key: month_key = _latest(self.db, "marts.fct_mrr_movements")
        rows = _q(self.db, "SELECT plan_name,month_key,SUM(churned_mrr) AS churned_mrr,COUNT(DISTINCT CASE WHEN churned_mrr>0 THEN account_id END) AS churned_accounts FROM marts.fct_mrr_movements WHERE month_key=:mk AND churned_mrr>0 GROUP BY plan_name,month_key ORDER BY churned_mrr DESC", {"mk":month_key})
        total = sum(_f(r.get("churned_mrr")) for r in rows)
        data = [{"plan_name":_s(r.get("plan_name")),"month_key":month_key,"churned_mrr":_f(r.get("churned_mrr")),"churned_accounts":_i(r.get("churned_accounts")),"avg_churned_mrr":round(_div(_f(r.get("churned_mrr")),_i(r.get("churned_accounts"))),2),"pct_of_total_churned":round(_div(_f(r.get("churned_mrr")),total)*100,2)} for r in rows]
        return {"month_key":month_key,"total_churned_mrr":total,"data":data}

    def get_payment_trend(self, months=12):
        rows = _q(self.db, "SELECT TO_CHAR(invoice_date,\'YYYY-MM\') AS month_key,COUNT(*) AS total_invoices,COUNT(*) FILTER (WHERE status=\'paid\') AS paid_invoices,COUNT(*) FILTER (WHERE status=\'failed\') AS failed_invoices,COUNT(*) FILTER (WHERE status=\'pending\') AS pending_invoices,SUM(amount) AS total_invoice_amount,SUM(amount) FILTER (WHERE status=\'paid\') AS collected_amount,SUM(amount) FILTER (WHERE status=\'failed\') AS failed_amount,AVG(EXTRACT(EPOCH FROM (paid_at-invoice_date))/86400) FILTER (WHERE status=\'paid\' AND paid_at IS NOT NULL) AS avg_days_to_pay FROM staging.stg_invoices GROUP BY TO_CHAR(invoice_date,\'YYYY-MM\') ORDER BY month_key DESC LIMIT :m", {"m":months})
        data = []
        for r in reversed(rows):
            t=_i(r.get("total_invoices")); p=_i(r.get("paid_invoices"))
            data.append({"month_key":r["month_key"],"total_invoices":t,"paid_invoices":p,"failed_invoices":_i(r.get("failed_invoices")),"pending_invoices":_i(r.get("pending_invoices")),"payment_success_rate":round(_div(p,t)*100,2),"total_invoice_amount":_f(r.get("total_invoice_amount")),"collected_amount":_f(r.get("collected_amount")),"failed_amount":_f(r.get("failed_amount")),"avg_days_to_pay":round(_f(r.get("avg_days_to_pay")),1)})
