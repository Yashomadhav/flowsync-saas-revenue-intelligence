# FlowSync SaaS Revenue Intelligence — Data Dictionary

## Overview
This dictionary documents core entities across the medallion architecture:
- **Raw (`raw.*`)**: ingestion-friendly text-first source tables
- **Staging (`staging.*`)**: typed, cleaned, conformed tables
- **Marts (`marts.*`)**: analytics-ready facts and summaries

---

## 1) Accounts

### `raw.raw_accounts`
Source account records as ingested from generated/source files.

| Column | Type | Description |
|---|---|---|
| account_id | text | Source account identifier |
| company_name | text | Company legal/display name |
| industry | text | Industry segment |
| region | text | Geographic region |
| company_size | text | Segment bucket (e.g., SMB, Mid, Enterprise) |
| acquisition_channel | text | Initial acquisition source |
| created_at | text | Account creation timestamp |
| _row_id | bigserial | Ingestion surrogate row id |
| _loaded_at | timestamptz | Ingestion load timestamp |
| _source_file | text | Source file path/name |

### `staging.stg_accounts`
Typed and cleaned account dimension.

| Column | Type | Description |
|---|---|---|
| account_id | uuid | Canonical account key |
| company_name | text | Cleaned company name |
| industry | text | Normalized industry |
| region | text | Normalized region |
| company_size | text | Normalized size bucket |
| acquisition_channel | text | Normalized acquisition source |
| created_at | timestamptz | Account creation timestamp |

---

## 2) Plans

### `raw.raw_plans`
| Column | Type | Description |
|---|---|---|
| plan_id | text | Source plan id |
| plan_name | text | Plan name (Starter/Growth/Pro/Enterprise) |
| monthly_price | text | Monthly list price |
| annual_price | text | Annual list price |
| _loaded_at | timestamptz | Ingestion timestamp |

### `staging.stg_plans`
| Column | Type | Description |
|---|---|---|
| plan_id | uuid | Canonical plan id |
| plan_name | text | Plan name |
| monthly_price | numeric | Monthly recurring price |
| annual_price | numeric | Annual recurring price |

---

## 3) Subscriptions

### `raw.raw_subscriptions`
| Column | Type | Description |
|---|---|---|
| subscription_id | text | Source subscription id |
| account_id | text | Source account reference |
| plan_id | text | Source plan reference |
| status | text | Active/Trial/Churned/etc |
| start_date | text | Subscription start date |
| end_date | text | Subscription end date |
| mrr | text | Monthly recurring amount |
| seats | text | Purchased seats |
| _loaded_at | timestamptz | Ingestion timestamp |

### `staging.stg_subscriptions`
| Column | Type | Description |
|---|---|---|
| subscription_id | uuid | Canonical subscription id |
| account_id | uuid | Account FK |
| plan_id | uuid | Plan FK |
| status | text | Normalized lifecycle status |
| start_date | date | Start date |
| end_date | date | End/cancel date |
| mrr | numeric | Normalized monthly recurring amount |
| seats | integer | Seat count |

---

## 4) Invoices & Payments

### `raw.raw_invoices`
| Column | Type | Description |
|---|---|---|
| invoice_id | text | Source invoice id |
| account_id | text | Source account reference |
| amount | text | Invoice amount |
| status | text | Paid/Failed/Open/Voided |
| invoice_date | text | Invoice date |
| due_date | text | Due date |
| paid_at | text | Payment timestamp |
| _loaded_at | timestamptz | Ingestion timestamp |

### `staging.stg_invoices`
| Column | Type | Description |
|---|---|---|
| invoice_id | uuid | Canonical invoice id |
| account_id | uuid | Account FK |
| amount | numeric | Invoice amount |
| status | text | Normalized payment status |
| invoice_date | date | Invoice date |
| due_date | date | Due date |
| paid_at | timestamptz | Paid timestamp |

---

## 5) Usage Events

### `raw.raw_usage_events`
| Column | Type | Description |
|---|---|---|
| event_id | text | Source event id |
| account_id | text | Source account reference |
| user_id | text | User id |
| event_name | text | Feature/action event |
| event_ts | text | Event timestamp |
| feature_name | text | Feature associated with event |
| _loaded_at | timestamptz | Ingestion timestamp |

### `staging.stg_usage_events`
| Column | Type | Description |
|---|---|---|
| event_id | uuid | Canonical event id |
| account_id | uuid | Account FK |
| user_id | uuid | User key |
| event_name | text | Normalized event |
| event_ts | timestamptz | Event timestamp |
| event_date | date | Event date |
| feature_name | text | Feature used |

---

## 6) Support Tickets

### `raw.raw_tickets`
| Column | Type | Description |
|---|---|---|
| ticket_id | text | Source ticket id |
| account_id | text | Source account reference |
| priority | text | Low/Medium/High/Critical |
| status | text | Open/Resolved/Closed |
| created_at | text | Ticket created timestamp |
| resolved_at | text | Resolution timestamp |
| csat | text | CSAT rating |
| _loaded_at | timestamptz | Ingestion timestamp |

### `staging.stg_tickets`
| Column | Type | Description |
|---|---|---|
| ticket_id | uuid | Canonical ticket id |
| account_id | uuid | Account FK |
| priority | text | Normalized priority |
| status | text | Normalized status |
| created_at | timestamptz | Created timestamp |
| resolved_at | timestamptz | Resolved timestamp |
| csat | numeric | Satisfaction score |

---

## 7) Leads / Funnel

### `raw.raw_leads`
| Column | Type | Description |
|---|---|---|
| lead_id | text | Source lead id |
| account_id | text | Account reference |
| channel | text | Acquisition channel |
| created_at | text | Lead created timestamp |
| trial_started_at | text | Trial start timestamp |
| converted_at | text | Paid conversion timestamp |
| _loaded_at | timestamptz | Ingestion timestamp |

### `staging.stg_leads`
| Column | Type | Description |
|---|---|---|
| lead_id | uuid | Canonical lead id |
| account_id | uuid | Account FK |
| channel | text | Normalized source channel |
| created_at | timestamptz | Lead created timestamp |
| trial_started_at | timestamptz | Trial start |
| converted_at | timestamptz | Paid conversion |

---

## 8) Core Marts

### `marts.fct_mrr_movements`
Account-month revenue movement fact.

| Column | Type | Description |
|---|---|---|
| month | date | Snapshot month |
| account_id | uuid | Account key |
| starting_mrr | numeric | Opening MRR |
| new_mrr | numeric | New MRR in period |
| expansion_mrr | numeric | Expansion in period |
| contraction_mrr | numeric | Contraction in period |
| churned_mrr | numeric | Churned amount |
| reactivation_mrr | numeric | Reactivated MRR |
| ending_mrr | numeric | Closing MRR |
| net_new_mrr | numeric | Net movement |

### `marts.fct_account_monthly_health`
Health/risk fact at account-month grain.

| Column | Type | Description |
|---|---|---|
| month | date | Snapshot month |
| account_id | uuid | Account key |
| health_score | numeric | Composite 0–100 score |
| usage_score | numeric | Usage component |
| seat_utilization_score | numeric | Seat utilization component |
| feature_adoption_score | numeric | Feature breadth component |
| support_score | numeric | Support burden component |
| csat_score | numeric | CSAT component |
| payment_score | numeric | Payment reliability component |
| risk_level | text | healthy / at_risk / critical |
| risk_flag_count | integer | Number of active risk flags |

### `marts.fct_customer_cohorts`
Cohort retention fact.

| Column | Type | Description |
|---|---|---|
| cohort_month | date | Cohort start month |
| period_number | integer | Month offset from cohort start |
| cohort_size | integer | Accounts/users in cohort |
| active_customers | integer | Retained customers |
| customer_retention_rate | numeric | Customer retention % |
| active_mrr | numeric | Active retained MRR |
| revenue_retention_rate | numeric | Revenue retention % |
| nrr | numeric | Net revenue retention % |

### `marts.fct_sales_conversion`
Lead-to-paid funnel fact.

| Column | Type | Description |
|---|---|---|
| month | date | Snapshot month |
| channel | text | Acquisition channel |
| total_leads | integer | Leads created |
| trial_starts | integer | Trial starts |
| paid_conversions | integer | Paid conversions |
| lead_to_trial_rate | numeric | Conversion % |
| trial_to_paid_rate | numeric | Conversion % |
| overall_conversion_rate | numeric | End-to-end % |
| avg_days_to_convert | numeric | Average cycle days |

### `marts.mart_exec_revenue_summary`
Executive monthly summary mart.

| Column | Type | Description |
|---|---|---|
| month | date | Reporting month |
| total_mrr | numeric | Total MRR |
| arr | numeric | ARR |
| active_accounts | integer | Active paying accounts |
| arpa | numeric | Average revenue per account |
| logo_churn_rate | numeric | Logo churn % |
| revenue_churn_rate | numeric | Revenue churn % |
| nrr | numeric | Net revenue retention % |
| grr | numeric | Gross revenue retention % |

### `marts.mart_customer_success_summary`
Customer success rollup mart.

| Column | Type | Description |
|---|---|---|
| month | date | Reporting month |
| healthy_accounts | integer | Accounts classified healthy |
| at_risk_accounts | integer | Accounts at risk |
| critical_accounts | integer | Critical-risk accounts |
| avg_health_score | numeric | Portfolio average health |
| support_ticket_volume | integer | Ticket volume |
| avg_csat | numeric | Average CSAT |

---

## Notes
- Source-to-staging casting rules, constraints, and accepted values are enforced through dbt tests and staging model logic.
- Field naming in marts is intentionally business-readable for dashboard and API compatibility.
