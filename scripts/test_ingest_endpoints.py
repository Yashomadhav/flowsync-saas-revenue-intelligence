"""Test ingest and webhook endpoints."""
import urllib.request
import urllib.error
import json

BASE = "http://localhost:8000/api/v1"
KEY_WRITE = "fs_live_demo_production_key_k9mX"
KEY_READ  = "fs_test_demo_staging_key_p2nQ"
KEY_WHK   = "fs_whk_demo_webhook_key_r7vL"


def req(method, path, data=None, key=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


results = []

# 1. GET /ingest/status with read key → 200
s, b = req("GET", "/ingest/status", key=KEY_READ)
results.append(("GET /ingest/status (read key)", s, str(b.get("status", b))[:60]))

# 2. GET /ingest/status with no key → 401 (missing_api_key — correct security behavior)
s, b = req("GET", "/ingest/status")
results.append(("GET /ingest/status (no key)", s, str(b.get("detail", b))[:60]))

# 3. POST /ingest/accounts
payload = {"records": [{"account_id": "test-acc-001", "company_name": "Acme Corp",
    "industry": "SaaS", "company_size": "mid_market", "region": "North America",
    "acquisition_channel": "inbound", "created_at": "2024-01-15T00:00:00Z"}]}
s, b = req("POST", "/ingest/accounts", data=payload, key=KEY_WRITE)
results.append(("POST /ingest/accounts", s, str(b)[:80]))

# 4. POST /ingest/subscriptions — plan_name is required
payload = {"records": [{"subscription_id": "sub-test-001", "account_id": "test-acc-001",
    "plan_name": "Starter", "plan_id": "plan-starter", "status": "active", "mrr": 299.0,
    "billing_interval": "monthly", "started_at": "2024-01-15T00:00:00Z"}]}
s, b = req("POST", "/ingest/subscriptions", data=payload, key=KEY_WRITE)
results.append(("POST /ingest/subscriptions", s, str(b)[:80]))

# 5. POST /ingest/invoices
payload = {"records": [{"invoice_id": "inv-test-001", "account_id": "test-acc-001",
    "subscription_id": "sub-test-001", "amount": 299.0, "status": "paid",
    "invoice_date": "2024-01-15T00:00:00Z"}]}
s, b = req("POST", "/ingest/invoices", data=payload, key=KEY_WRITE)
results.append(("POST /ingest/invoices", s, str(b)[:80]))

# 6. POST /ingest/usage-events — feature_name + occurred_at are required
payload = {"records": [{"event_id": "evt-test-001", "account_id": "test-acc-001",
    "feature_name": "workflow_run", "event_type": "login",
    "event_count": 1, "occurred_at": "2024-01-20T10:00:00Z"}]}
s, b = req("POST", "/ingest/usage-events", data=payload, key=KEY_WRITE)
results.append(("POST /ingest/usage-events", s, str(b)[:80]))

# 7. POST /ingest/tickets
payload = {"records": [{"ticket_id": "tkt-test-001", "account_id": "test-acc-001",
    "subject": "Test ticket", "status": "open", "priority": "medium",
    "created_at": "2024-01-22T09:00:00Z"}]}
s, b = req("POST", "/ingest/tickets", data=payload, key=KEY_WRITE)
results.append(("POST /ingest/tickets", s, str(b)[:80]))

# 8. POST /ingest/leads
payload = {"records": [{"lead_id": "lead-test-001", "company_name": "Beta Inc",
    "acquisition_channel": "outbound", "funnel_stage": "lead",
    "created_at": "2024-02-01T00:00:00Z"}]}
s, b = req("POST", "/ingest/leads", data=payload, key=KEY_WRITE)
results.append(("POST /ingest/leads", s, str(b)[:80]))

# 9. POST /ingest/accounts with wrong key → 403 (insufficient_scope — correct security behavior)
s, b = req("POST", "/ingest/accounts", data={"records": []}, key=KEY_WHK)
results.append(("POST /ingest/accounts (wrong key)", s, str(b.get("detail", b))[:60]))

# 10. POST /webhooks/test (dev echo)
payload = {"event": "test.ping", "data": {"msg": "hello"}}
s, b = req("POST", "/webhooks/test", data=payload, key=KEY_WHK)
results.append(("POST /webhooks/test", s, str(b)[:80]))

# 11. POST /webhooks/stripe (no sig verification in dev)
payload = {
    "type": "customer.subscription.created",
    "data": {"object": {"id": "sub_test", "customer": "cus_test", "status": "active",
        "items": {"data": [{"price": {"unit_amount": 9900,
            "recurring": {"interval": "month"}}}]}}}
}
s, b = req("POST", "/webhooks/stripe", data=payload, key=KEY_WHK)
results.append(("POST /webhooks/stripe", s, str(b)[:80]))

# 12. POST /webhooks/chargebee
payload = {"event_type": "subscription_created",
    "content": {"subscription": {"id": "sub_cb_test", "customer_id": "cus_cb_test",
        "status": "active", "plan_id": "starter", "plan_amount": 29900}}}
s, b = req("POST", "/webhooks/chargebee", data=payload, key=KEY_WHK)
results.append(("POST /webhooks/chargebee", s, str(b)[:80]))

# Expected status codes per test (security failures are correct behavior)
EXPECTED = {
    "GET /ingest/status (read key)":      [200],
    "GET /ingest/status (no key)":        [401],        # missing key → 401 is correct
    "POST /ingest/accounts":              [200, 201],
    "POST /ingest/subscriptions":         [200, 201],
    "POST /ingest/invoices":              [200, 201],
    "POST /ingest/usage-events":          [200, 201],
    "POST /ingest/tickets":               [200, 201],
    "POST /ingest/leads":                 [200, 201],
    "POST /ingest/accounts (wrong key)":  [403],        # wrong scope → 403 is correct
    "POST /webhooks/test":                [200],
    "POST /webhooks/stripe":              [200],
    "POST /webhooks/chargebee":           [200],
}

# Print results
print()
print("=" * 72)
print("{:<42} {:<8} RESULT".format("ENDPOINT", "STATUS"))
print("=" * 72)
for name, status, result in results:
    expected = EXPECTED.get(name, [200, 201])
    ok = "OK  " if status in expected else "FAIL"
    print("{:<42} {:<8} [{}] {}".format(name, status, ok, result))
print("=" * 72)
passed = sum(1 for name, s, _ in results if s in EXPECTED.get(name, [200, 201]))
print("PASSED: {}/{}".format(passed, len(results)))
print()
