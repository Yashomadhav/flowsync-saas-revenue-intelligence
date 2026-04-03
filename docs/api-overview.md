# FlowSync SaaS Revenue Intelligence — API Overview

## Base
- **Base URL:** `/api/v1`
- **Format:** JSON
- **Auth:** Demo mode (public/internal portfolio). For production demo, add token/JWT gateway.
- **Health endpoint:** `/health` (service/container health checks)

---

## 1) Executive Endpoints

### `GET /api/v1/executive/summary`
Returns top-line KPI summary for selected period.

**Query params**
- `month` (optional, `YYYY-MM`)

**Response highlights**
- `total_mrr`, `arr`, `new_mrr`, `expansion_mrr`, `contraction_mrr`, `churned_mrr`, `reactivation_mrr`
- `net_new_mrr`, `active_accounts`, `arpa`, `logo_churn_rate`, `revenue_churn_rate`, `nrr`, `grr`

---

### `GET /api/v1/executive/mrr-trend`
MRR and retention trend series.

**Query params**
- `months` (optional, default 24)

**Response**
Array of month points:
- `month`, `total_mrr`, `arr`, `net_new_mrr`, `new_mrr`, `expansion_mrr`, `contraction_mrr`, `churned_mrr`, `reactivation_mrr`, `nrr`, `arpa`

---

### `GET /api/v1/executive/waterfall`
Current-period MRR movement bridge.

**Response**
- `month`
- `waterfall[]` (`start`, `positive`, `negative`, `end`)
- `net_new_mrr`

---

### `GET /api/v1/executive/by-plan`
MRR distribution by subscription plan.

### `GET /api/v1/executive/by-region`
MRR distribution by region.

### `GET /api/v1/executive/top-expanding`
Top expansion accounts.

**Query params**
- `limit` (optional, default 10)
- `month` (optional)

### `GET /api/v1/executive/top-churn-risk`
Top risk accounts by health/risk model.

**Query params**
- `limit` (optional, default 10)

---

## 2) Revenue Endpoints

### `GET /api/v1/revenue/mrr-bridge`
Monthly bridge over time.

**Query params**
- `months` (optional, default 12)

### `GET /api/v1/revenue/account-movements`
Detailed account-level movement table.

**Query params**
- `month` (optional)
- `limit` (optional)
- `offset` (optional)

**Response**
- `total`
- `data[]` with movement details and deltas

### `GET /api/v1/revenue/new-mrr-by-channel`
Channel contribution to new MRR.

### `GET /api/v1/revenue/payment-trends`
Invoice payment and failure trend.

---

## 3) Cohort Endpoints

### `GET /api/v1/cohorts/customer-retention`
Customer retention cohort matrix rows.

**Query params**
- `cohort_months` (optional, default 12)

### `GET /api/v1/cohorts/revenue-retention`
Revenue retention (NRR) cohort rows.

### `GET /api/v1/cohorts/logo-churn-trend`
Monthly logo/revenue churn trend.

### `GET /api/v1/cohorts/retention-by-plan`
Segmented retention summary by plan.

### `GET /api/v1/cohorts/retention-by-size`
Segmented retention summary by company size.

---

## 4) Health Endpoints

### `GET /api/v1/health/score-distribution`
Health score bucket distribution.

### `GET /api/v1/health/risk-quadrant`
Risk quadrant points (usage vs health, MRR bubble).

### `GET /api/v1/health/support-burden`
Support burden table.

**Query params**
- `limit` (optional)

### `GET /api/v1/health/risky-accounts`
Risk-filtered account list.

**Query params**
- `risk_level` (`at_risk` / `critical`, optional)
- `limit` (optional)

### `GET /api/v1/health/summary-stats`
Portfolio-level health summary.

---

## 5) Funnel Endpoints

### `GET /api/v1/funnel/conversion`
Top funnel conversion metrics.

### `GET /api/v1/funnel/by-channel`
Channel-level conversion and quality.

### `GET /api/v1/funnel/sales-cycle`
Sales cycle metrics by channel/plan.

### `GET /api/v1/funnel/expansion-by-segment`
Expansion MRR by company size/channel/plan.

---

## 6) Suggested Extended Endpoints (Drill-through & Filters)

For richer interactivity, add/enable:

### `GET /api/v1/accounts/{account_id}`
Detailed account profile payload:
- profile
- current MRR
- revenue history
- plan history
- seat utilization
- active users trend
- usage trend
- feature adoption
- support tickets timeline
- CSAT trend
- risk reasons
- payment/invoice history

### Filter metadata
- `GET /api/v1/filters/regions`
- `GET /api/v1/filters/plans`
- `GET /api/v1/filters/industries`
- `GET /api/v1/filters/channels`
- `GET /api/v1/filters/company-sizes`

---

## Error & Status Model

Recommended response model:
```json
{
  "data": {},
  "meta": { "request_id": "uuid", "duration_ms": 12 },
  "error": null
}
```

For errors:
```json
{
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid month format; expected YYYY-MM"
  }
}
```

---

## CORS & Production Notes

- Restrict `ALLOWED_ORIGINS` to deployed frontend domains only.
- Keep API under HTTPS behind platform TLS.
- Do not expose admin/debug endpoints publicly.
- Add rate limiting for public demo routes.

---

## Testing Recommendations

### Critical-path
- Summary/trend endpoints
- Account movement table endpoint with pagination
- Health risky accounts endpoint
- Funnel conversion endpoints

### Thorough
- All query parameter combinations
- Empty datasets
- Invalid parameters
- High offset/limit
- Service degraded scenarios (DB unavailable)
