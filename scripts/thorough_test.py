#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlowSync Revenue Intelligence - Thorough API Test Suite
Tests all 39 endpoints: health + 27 dashboard + 12 ingest/webhook + edge cases
ASCII-only output for Windows cp1252 compatibility.
"""
import io
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime

# Force UTF-8 stdout on Windows to avoid cp1252 encode errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"
API  = f"{BASE}/api/v1"

WRITE_KEY   = "fs_live_demo_production_key_k9mX"
READ_KEY    = "fs_test_demo_staging_key_p2nQ"
WEBHOOK_KEY = "fs_whk_demo_webhook_key_r7vL"
BAD_KEY     = "invalid_key_xyz"

PASSED = 0
FAILED = 0
RESULTS = []

def req(method, url, headers=None, body=None, expected=200, label=""):
    global PASSED, FAILED
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body else None
    try:
        r = urllib.request.Request(url, data=data, headers=h, method=method)
        with urllib.request.urlopen(r, timeout=10) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8", errors="replace")
    except Exception as ex:
        status = 0
        raw = str(ex)

    ok = (status == expected)
    icon = "PASS" if ok else "FAIL"
    if ok:
        PASSED += 1
    else:
        FAILED += 1
    preview = raw[:100].replace("\n", " ") if raw else ""
    line = f"[{icon}] [{status}/{expected}] {method} {url.replace(BASE, '')} | {label} | {preview}"
    RESULTS.append((ok, line))
    print(line)
    return status, raw

def auth(key):
    return {"X-API-Key": key}

SEP = "=" * 80
print(SEP)
print(f"FlowSync Thorough API Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

# ---------------------------------------------------------------------------
# 1. HEALTH
# ---------------------------------------------------------------------------
print("\n--- 1. Health ---")
req("GET", f"{BASE}/health", label="root health check")
req("GET", f"{API}/health",  label="versioned health", expected=200)

# ---------------------------------------------------------------------------
# 2. EXECUTIVE (9 endpoints)
# ---------------------------------------------------------------------------
print("\n--- 2. Executive ---")
req("GET", f"{API}/executive/summary",         label="exec summary")
req("GET", f"{API}/executive/mrr-trend",       label="mrr trend")
req("GET", f"{API}/executive/waterfall",       label="revenue waterfall")
req("GET", f"{API}/executive/by-plan",         label="by plan")
req("GET", f"{API}/executive/by-region",       label="by region")
req("GET", f"{API}/executive/by-industry",     label="by industry")
req("GET", f"{API}/executive/by-company-size", label="by company size")
req("GET", f"{API}/executive/top-expanding",   label="top expanding")
req("GET", f"{API}/executive/top-churn-risk",  label="top churn risk")

# ---------------------------------------------------------------------------
# 3. REVENUE (6 endpoints)
# ---------------------------------------------------------------------------
print("\n--- 3. Revenue ---")
req("GET", f"{API}/revenue/mrr-bridge",           label="mrr bridge")
req("GET", f"{API}/revenue/account-movements",    label="account movements")
req("GET", f"{API}/revenue/new-mrr-by-channel",   label="new mrr by channel")
req("GET", f"{API}/revenue/expansion-by-segment", label="expansion by segment")
req("GET", f"{API}/revenue/churned-by-plan",      label="churned by plan")
req("GET", f"{API}/revenue/payment-trend",        label="payment trend")

# ---------------------------------------------------------------------------
# 4. COHORTS (4 endpoints)
# ---------------------------------------------------------------------------
print("\n--- 4. Cohorts ---")
req("GET", f"{API}/cohorts/heatmap",              label="cohort heatmap")
req("GET", f"{API}/cohorts/logo-churn-trend",     label="logo churn trend")
req("GET", f"{API}/cohorts/nrr-by-cohort",        label="nrr by cohort")
req("GET", f"{API}/cohorts/retention-by-segment", label="retention by segment")

# ---------------------------------------------------------------------------
# 5. CUSTOMER HEALTH (4 endpoints)
# ---------------------------------------------------------------------------
print("\n--- 5. Customer Health ---")
req("GET", f"{API}/health/distribution",        label="health distribution")
req("GET", f"{API}/health/churn-risk-quadrant", label="churn risk quadrant")
req("GET", f"{API}/health/risky-accounts",      label="risky accounts")
req("GET", f"{API}/health/support-burden",      label="support burden")

# ---------------------------------------------------------------------------
# 6. FUNNEL (5 endpoints)
# ---------------------------------------------------------------------------
print("\n--- 6. Funnel ---")
req("GET", f"{API}/funnel/overview",              label="funnel overview")
req("GET", f"{API}/funnel/conversion-by-channel", label="conversion by channel")
req("GET", f"{API}/funnel/sales-cycle",           label="sales cycle")
req("GET", f"{API}/funnel/trial-usage",           label="trial usage")
req("GET", f"{API}/funnel/expansion-by-segment",  label="expansion by segment")

# ---------------------------------------------------------------------------
# 7. INGEST AUTH
# ---------------------------------------------------------------------------
print("\n--- 7. Ingest Auth ---")
req("GET", f"{API}/ingest/status", headers=auth(WRITE_KEY), label="write key -> 200", expected=200)
req("GET", f"{API}/ingest/status", headers=auth(READ_KEY),  label="read key -> 200",  expected=200)
req("GET", f"{API}/ingest/status",                          label="no key -> 401",    expected=401)
req("GET", f"{API}/ingest/status", headers=auth(BAD_KEY),   label="bad key -> 401",   expected=401)

# ---------------------------------------------------------------------------
# 8. INGEST BATCH
# ---------------------------------------------------------------------------
print("\n--- 8. Ingest Batch ---")
req("POST", f"{API}/ingest/accounts", headers=auth(WRITE_KEY),
    body={"records": [{"account_id": "test-acc-001", "company_name": "Test Corp",
                        "industry": "SaaS", "company_size": "smb", "region": "North America",
                        "acquisition_channel": "inbound", "created_at": "2024-01-01T00:00:00Z"}]},
    label="accounts")

req("POST", f"{API}/ingest/subscriptions", headers=auth(WRITE_KEY),
    body={"records": [{"subscription_id": "test-sub-001", "account_id": "test-acc-001",
                        "plan_name": "Starter", "mrr": 99.0, "status": "active",
                        "billing_interval": "monthly", "started_at": "2024-01-01T00:00:00Z"}]},
    label="subscriptions")

req("POST", f"{API}/ingest/invoices", headers=auth(WRITE_KEY),
    body={"records": [{"invoice_id": "test-inv-001", "account_id": "test-acc-001",
                        "amount": 99.0, "currency": "USD", "status": "paid",
                        "invoice_date": "2024-01-01T00:00:00Z", "created_at": "2024-01-01T00:00:00Z"}]},
    label="invoices")

req("POST", f"{API}/ingest/usage-events", headers=auth(WRITE_KEY),
    body={"records": [{"event_id": "test-evt-001", "account_id": "test-acc-001",
                        "feature_name": "workflow_run", "event_type": "feature_used",
                        "event_count": 3, "occurred_at": "2024-01-15T10:00:00Z"}]},
    label="usage events")

req("POST", f"{API}/ingest/tickets", headers=auth(WRITE_KEY),
    body={"records": [{"ticket_id": "test-tkt-001", "account_id": "test-acc-001",
                        "subject": "Test ticket", "status": "open", "priority": "medium",
                        "created_at": "2024-01-10T00:00:00Z"}]},
    label="tickets")

req("POST", f"{API}/ingest/leads", headers=auth(WRITE_KEY),
    body={"records": [{"lead_id": "test-lead-001", "company_name": "Lead Corp",
                        "acquisition_channel": "inbound", "funnel_stage": "trial",
                        "created_at": "2024-01-05T00:00:00Z"}]},
    label="leads")

# ---------------------------------------------------------------------------
# 9. INGEST SECURITY
# ---------------------------------------------------------------------------
print("\n--- 9. Ingest Security ---")
req("POST", f"{API}/ingest/accounts", headers=auth(BAD_KEY),
    body={"records": []}, label="bad key -> 401", expected=401)
req("POST", f"{API}/ingest/accounts", headers=auth(WEBHOOK_KEY),
    body={"records": []}, label="webhook key on ingest -> 403", expected=403)

# ---------------------------------------------------------------------------
# 10. WEBHOOKS
# ---------------------------------------------------------------------------
print("\n--- 10. Webhooks ---")
req("POST", f"{API}/webhooks/test", headers=auth(WEBHOOK_KEY),
    body={"event": "test.ping", "data": {"msg": "hello"}},
    label="webhook test echo")

req("POST", f"{API}/webhooks/stripe", headers=auth(WEBHOOK_KEY),
    body={"type": "invoice.payment_succeeded",
          "data": {"object": {"id": "in_test", "customer": "cus_test",
                               "subscription": "sub_test", "amount_paid": 9900,
                               "currency": "usd", "status": "paid"}}},
    label="stripe payment_succeeded")

req("POST", f"{API}/webhooks/chargebee", headers=auth(WEBHOOK_KEY),
    body={"event_type": "payment_succeeded",
          "content": {"invoice": {"id": "inv_test", "customer_id": "cus_test",
                                   "subscription_id": "sub_test", "amount_paid": 9900,
                                   "currency_code": "USD", "status": "paid"}}},
    label="chargebee payment_succeeded")

# ---------------------------------------------------------------------------
# 11. EDGE CASES
# ---------------------------------------------------------------------------
print("\n--- 11. Edge Cases ---")
req("POST", f"{API}/ingest/accounts", headers=auth(WRITE_KEY),
    body={"records": []}, label="empty batch -> 422", expected=422)

req("POST", f"{API}/ingest/accounts", headers=auth(WRITE_KEY),
    body={"records": [{"account_id": "bad-001"}]},
    label="missing company_name -> 422", expected=422)

req("GET", f"{API}/executive/nonexistent",
    label="unknown route -> 404", expected=404)

# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
total = PASSED + FAILED
print(f"\n{SEP}")
print(f"RESULTS: {PASSED}/{total} PASSED  |  {FAILED} FAILED")
print(SEP)

if FAILED > 0:
    print("\nFAILED TESTS:")
    for ok, line in RESULTS:
        if not ok:
            print(f"  {line}")
    sys.exit(1)
else:
    print("\nALL TESTS PASSED")
    sys.exit(0)
