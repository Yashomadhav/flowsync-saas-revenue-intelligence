# Data Ingestion Guide

**FlowSync Revenue Intelligence Platform**  
Version 1.0 · API prefix: `/api/v1`

---

## Overview

The FlowSync ingestion layer provides two mechanisms for loading data into the platform:

| Mechanism | Use Case | Auth |
|-----------|----------|------|
| **REST Ingest API** | Batch upserts from your CRM, billing system, or ETL pipeline | `X-API-Key` header |
| **Webhook Receivers** | Real-time event push from Stripe or Chargebee | `X-API-Key` + optional HMAC signature |

All endpoints write to the `raw.*` schema. Data flows through `staging.*` → `marts.*` via dbt transformations.

---

## Authentication

Include your API key in every request:

```http
X-API-Key: fs_live_demo_production_key_k9mX
```

### Key Scopes

| Key | Scope | Allowed Operations |
|-----|-------|--------------------|
| `fs_live_demo_production_key_k9mX` | `INGEST_WRITE`, `INGEST_READ` | All ingest endpoints |
| `fs_test_demo_staging_key_p2nQ` | `INGEST_WRITE`, `INGEST_READ` | All ingest endpoints (staging) |
| `fs_whk_demo_webhook_key_r7vL` | `WEBHOOK` | Webhook receivers only |
| `fs_live_admin_master_key_ADMIN` | `ADMIN`, `INGEST_WRITE`, `INGEST_READ`, `WEBHOOK` | All operations |

### Error Responses

| HTTP | Error Code | Meaning |
|------|-----------|---------|
| 401 | `missing_api_key` | No `X-API-Key` header provided |
| 403 | `insufficient_scope` | Key exists but lacks required permission |

---

## Ingest Status

```http
GET /api/v1/ingest/status
X-API-Key: <read-or-write-key>
```

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "endpoints": ["accounts", "subscriptions", "invoices", "usage-events", "tickets", "leads"],
  "timestamp": "2024-03-01T12:00:00Z"
}
```

---

## Batch Ingest Endpoints

All batch endpoints accept a `records` array and return a processing summary. Records that fail validation are counted in `error_count` but do not block the rest of the batch.

### POST /api/v1/ingest/accounts

Upsert company accounts. Matches on `account_id`.

```http
POST /api/v1/ingest/accounts
X-API-Key: <write-key>
Content-Type: application/json
```

**Request body:**
```json
{
  "records": [
    {
      "account_id": "acc-001",
      "company_name": "Acme Corp",
      "industry": "SaaS",
      "company_size": "mid_market",
      "region": "North America",
      "country": "US",
      "acquisition_channel": "inbound",
      "account_owner": "Jane Smith",
      "website": "https://acme.com",
      "created_at": "2024-01-15T00:00:00Z",
      "updated_at": "2024-03-01T00:00:00Z"
    }
  ]
}
```

**Field reference:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `account_id` | string | ✅ | Primary key, used for upsert |
| `company_name` | string | ✅ | |
| `industry` | string | | e.g. `SaaS`, `FinTech`, `Healthcare` |
| `company_size` | string | | `smb`, `mid_market`, `enterprise` |
| `region` | string | | e.g. `North America`, `EMEA`, `APAC` |
| `country` | string | | ISO 2-letter code |
| `acquisition_channel` | string | | `inbound`, `outbound`, `partner`, `self_serve` |
| `account_owner` | string | | CSM or AE name |
| `website` | string | | |
| `created_at` | ISO 8601 | | Defaults to now |
| `updated_at` | ISO 8601 | | Defaults to now |

---

### POST /api/v1/ingest/subscriptions

Upsert subscription records. Matches on `subscription_id`.

```json
{
  "records": [
    {
      "subscription_id": "sub-001",
      "account_id": "acc-001",
      "plan_name": "Professional",
      "plan_id": "plan-pro",
      "mrr": 999.0,
      "arr": 11988.0,
      "status": "active",
      "billing_interval": "monthly",
      "seats": 10,
      "started_at": "2024-01-15T00:00:00Z",
      "trial_started_at": null,
      "trial_ended_at": null,
      "canceled_at": null,
      "updated_at": "2024-03-01T00:00:00Z"
    }
  ]
}
```

**Field reference:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `subscription_id` | string | ✅ | Primary key |
| `account_id` | string | ✅ | FK to accounts |
| `plan_name` | string | ✅ | Human-readable plan name |
| `plan_id` | string | | Internal plan identifier |
| `mrr` | float | | Monthly recurring revenue |
| `arr` | float | | Annual recurring revenue (auto-calc if omitted) |
| `status` | string | | `active`, `trialing`, `canceled`, `paused` |
| `billing_interval` | string | | `monthly`, `annual` |
| `seats` | int | | Licensed seat count |
| `started_at` | ISO 8601 | | Subscription start date |
| `trial_started_at` | ISO 8601 | | |
| `trial_ended_at` | ISO 8601 | | |
| `canceled_at` | ISO 8601 | | Set when churned |
| `updated_at` | ISO 8601 | | |

---

### POST /api/v1/ingest/invoices

Upsert invoice records. Matches on `invoice_id`.

```json
{
  "records": [
    {
      "invoice_id": "inv-001",
      "account_id": "acc-001",
      "subscription_id": "sub-001",
      "amount": 999.0,
      "currency": "USD",
      "status": "paid",
      "payment_method": "card",
      "invoice_date": "2024-03-01T00:00:00Z",
      "due_date": "2024-03-15T00:00:00Z",
      "paid_at": "2024-03-02T00:00:00Z",
      "failed_at": null,
      "failure_reason": null,
      "attempt_count": 1,
      "created_at": "2024-03-01T00:00:00Z"
    }
  ]
}
```

**Field reference:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `invoice_id` | string | ✅ | Primary key |
| `account_id` | string | ✅ | FK to accounts |
| `subscription_id` | string | | FK to subscriptions |
| `amount` | float | ✅ | Invoice amount |
| `currency` | string | | Default `USD` |
| `status` | string | | `paid`, `open`, `failed`, `void` |
| `payment_method` | string | | `card`, `ach`, `wire` |
| `invoice_date` | ISO 8601 | | |
| `due_date` | ISO 8601 | | |
| `paid_at` | ISO 8601 | | |
| `failed_at` | ISO 8601 | | Set on payment failure |
| `failure_reason` | string | | e.g. `card_declined` |
| `attempt_count` | int | | Number of payment attempts |

---

### POST /api/v1/ingest/usage-events

Ingest product usage events. Matches on `event_id`.

```json
{
  "records": [
    {
      "event_id": "evt-001",
      "account_id": "acc-001",
      "feature_name": "workflow_run",
      "event_type": "feature_used",
      "event_count": 5,
      "session_duration_seconds": 300,
      "occurred_at": "2024-03-01T10:00:00Z",
      "properties": {"workflow_type": "approval", "steps": 3}
    }
  ]
}
```

**Field reference:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `event_id` | string | ✅ | Primary key |
| `account_id` | string | ✅ | FK to accounts |
| `feature_name` | string | ✅ | Feature identifier (e.g. `workflow_run`, `api_call`) |
| `event_type` | string | | `login`, `feature_used`, `export`, `api_call` |
| `event_count` | int | | Number of events in batch (default 1) |
| `session_duration_seconds` | int | | Session length |
| `occurred_at` | ISO 8601 | ✅ | Event timestamp |
| `properties` | object | | Arbitrary JSON metadata |

---

### POST /api/v1/ingest/tickets

Upsert support tickets. Matches on `ticket_id`.

```json
{
  "records": [
    {
      "ticket_id": "tkt-001",
      "account_id": "acc-001",
      "subject": "Cannot connect integration",
      "status": "open",
      "priority": "high",
      "category": "integration",
      "csat_score": null,
      "created_at": "2024-03-01T09:00:00Z",
      "resolved_at": null,
      "updated_at": "2024-03-01T09:00:00Z"
    }
  ]
}
```

**Field reference:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `ticket_id` | string | ✅ | Primary key |
| `account_id` | string | ✅ | FK to accounts |
| `subject` | string | ✅ | Ticket title |
| `status` | string | | `open`, `pending`, `resolved`, `closed` |
| `priority` | string | | `low`, `medium`, `high`, `critical` |
| `category` | string | | `billing`, `integration`, `bug`, `feature_request` |
| `csat_score` | float | | 1–5 customer satisfaction score |
| `created_at` | ISO 8601 | ✅ | |
| `resolved_at` | ISO 8601 | | |
| `updated_at` | ISO 8601 | | |

---

### POST /api/v1/ingest/leads

Upsert sales leads / opportunities. Matches on `lead_id`.

```json
{
  "records": [
    {
      "lead_id": "lead-001",
      "company_name": "Beta Inc",
      "acquisition_channel": "outbound",
      "funnel_stage": "trial",
      "converted_mrr": 499.0,
      "days_to_close": 21,
      "closed_at": null,
      "created_at": "2024-02-01T00:00:00Z",
      "updated_at": "2024-03-01T00:00:00Z"
    }
  ]
}
```

**Field reference:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `lead_id` | string | ✅ | Primary key |
| `company_name` | string | ✅ | |
| `acquisition_channel` | string | ✅ | `inbound`, `outbound`, `partner`, `self_serve` |
| `funnel_stage` | string | ✅ | `lead`, `mql`, `sql`, `trial`, `paid`, `lost` |
| `converted_mrr` | float | | MRR if converted to paid |
| `days_to_close` | int | | Sales cycle length in days |
| `closed_at` | ISO 8601 | | Date won or lost |
| `created_at` | ISO 8601 | ✅ | Lead creation date |
| `updated_at` | ISO 8601 | | |

---

## Response Format

All batch ingest endpoints return the same response shape:

```json
{
  "inserted": 1,
  "updated": 0,
  "error_count": 0,
  "message": "Processed 1 accounts: 1 inserted, 0 updated, 0 errors"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `inserted` | int | New records created |
| `updated` | int | Existing records updated (upsert) |
| `error_count` | int | Records that failed validation or DB write |
| `message` | string | Human-readable summary |

> **Note:** `error_count > 0` does not cause a non-200 response. The batch is partially processed. Check your source data for the failing records.

---

## Webhook Receivers

### POST /api/v1/webhooks/test

Echo endpoint for connectivity testing. No signature verification.

```http
POST /api/v1/webhooks/test
X-API-Key: <webhook-key>
Content-Type: application/json

{"event": "test.ping", "data": {"msg": "hello"}}
```

---

### POST /api/v1/webhooks/stripe

Receives Stripe webhook events. Supported event types:

| Stripe Event | Action |
|-------------|--------|
| `customer.subscription.created` | Creates subscription record |
| `customer.subscription.updated` | Updates subscription MRR/status |
| `customer.subscription.deleted` | Marks subscription canceled |
| `invoice.payment_succeeded` | Records paid invoice |
| `invoice.payment_failed` | Records failed invoice |

**Stripe Dashboard Setup:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-api.com/api/v1/webhooks/stripe`
3. Select events listed above
4. Copy the signing secret to `STRIPE_WEBHOOK_SECRET` env var

**Signature verification** is enabled in production (`ENVIRONMENT=production`). In development it is bypassed automatically.

```http
POST /api/v1/webhooks/stripe
X-API-Key: <webhook-key>
Stripe-Signature: t=...,v1=...
Content-Type: application/json
```

---

### POST /api/v1/webhooks/chargebee

Receives Chargebee webhook events. Supported event types:

| Chargebee Event | Action |
|----------------|--------|
| `subscription_created` | Creates subscription record |
| `subscription_changed` | Updates subscription |
| `subscription_cancelled` | Marks subscription canceled |
| `payment_succeeded` | Records paid invoice |
| `payment_failed` | Records failed invoice |

**Chargebee Setup:**
1. Go to Chargebee → Settings → API Keys & Webhooks
2. Add webhook URL: `https://your-api.com/api/v1/webhooks/chargebee`
3. Copy the webhook password to `CHARGEBEE_WEBHOOK_SECRET` env var

---

## Environment Variables

```bash
# Webhook signature verification
STRIPE_WEBHOOK_SECRET=whsec_...
CHARGEBEE_WEBHOOK_SECRET=...
WEBHOOK_VERIFY_SIGNATURES=true   # set to "false" in development
ENVIRONMENT=production            # "development" disables sig verification
```

---

## Data Flow Architecture

```
External Systems
      │
      ▼
┌─────────────────────────────────────┐
│  Ingest API  /api/v1/ingest/*       │  ← Batch REST upserts
│  Webhooks    /api/v1/webhooks/*     │  ← Real-time push events
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  raw.*  (Bronze Layer)              │
│  raw_accounts, raw_subscriptions,   │
│  raw_invoices, raw_usage_events,    │
│  raw_tickets, raw_leads             │
└─────────────────────────────────────┘
      │  dbt run
      ▼
┌─────────────────────────────────────┐
│  staging.*  (Silver Layer)          │
│  stg_accounts, stg_subscriptions,   │
│  stg_invoices, stg_usage_events,    │
│  stg_support_tickets, stg_leads     │
└─────────────────────────────────────┘
      │  dbt run
      ▼
┌─────────────────────────────────────┐
│  marts.*  (Gold Layer)              │
│  fct_mrr_movements                  │
│  fct_account_monthly_health         │
│  fct_customer_cohorts               │
│  fct_sales_conversion               │
│  mart_exec_revenue_summary          │
│  mart_customer_success_summary      │
└─────────────────────────────────────┘
      │
      ▼
  Dashboard API  /api/v1/executive/*
                 /api/v1/revenue/*
                 /api/v1/cohorts/*
                 /api/v1/health/*
                 /api/v1/funnel/*
```

---

## Running dbt After Ingestion

After loading data via the ingest API, trigger dbt to transform raw → staging → marts:

```bash
# Via Docker Compose
docker-compose --profile dbt run dbt

# Or exec into the dbt container
docker-compose exec dbt dbt run --profiles-dir /app/dbt_project

# Run only specific models
docker-compose exec dbt dbt run --select marts.*
```

---

## Rate Limits

| Tier | Requests/min | Max batch size |
|------|-------------|----------------|
| Production key | 1,000 | 1,000 records |
| Staging key | 100 | 100 records |
| Webhook | Unlimited | N/A (single event) |

---

## Error Handling Best Practices

1. **Retry on 5xx** — Use exponential backoff (1s, 2s, 4s, max 30s)
2. **Don't retry on 4xx** — Fix the payload before retrying
3. **Check `error_count`** — A 200 response with `error_count > 0` means partial failure; log the message for debugging
4. **Idempotency** — All endpoints are idempotent on their primary key; safe to re-send the same record
5. **Ordering** — Ingest accounts before subscriptions/invoices (FK dependency)

---

## Quick Start Example (Python)

```python
import requests

API_BASE = "http://localhost:8000/api/v1"
API_KEY  = "fs_live_demo_production_key_k9mX"
HEADERS  = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# 1. Ingest an account
resp = requests.post(f"{API_BASE}/ingest/accounts", headers=HEADERS, json={
    "records": [{
        "account_id": "acc-acme-001",
        "company_name": "Acme Corp",
        "industry": "SaaS",
        "company_size": "mid_market",
        "region": "North America",
        "acquisition_channel": "inbound",
        "created_at": "2024-01-15T00:00:00Z"
    }]
})
print(resp.json())  # {'inserted': 1, 'updated': 0, 'error_count': 0, ...}

# 2. Ingest a subscription
resp = requests.post(f"{API_BASE}/ingest/subscriptions", headers=HEADERS, json={
    "records": [{
        "subscription_id": "sub-acme-001",
        "account_id": "acc-acme-001",
        "plan_name": "Professional",
        "mrr": 999.0,
        "status": "active",
        "billing_interval": "monthly",
        "started_at": "2024-01-15T00:00:00Z"
    }]
})
print(resp.json())  # {'inserted': 1, 'updated': 0, 'error_count': 0, ...}
```

---

*For dashboard API documentation, see [api-overview.md](./api-overview.md)*  
*For metric definitions, see [kpi-definitions.md](./kpi-definitions.md)*  
*For data schema reference, see [data-dictionary.md](./data-dictionary.md)*
