-- ============================================================
-- FlowSync — Aggregation SQL (run after Python inserts raw data)
-- ============================================================

-- 1. mart_exec_revenue_summary
INSERT INTO marts.mart_exec_revenue_summary
    (month_key, total_mrr, total_arr, active_accounts, arpa,
     new_mrr, expansion_mrr, contraction_mrr, churned_mrr,
     reactivation_mrr, net_new_mrr, nrr, grr,
     logo_churn_rate, revenue_churn_rate, mrr_mom_pct,
     churned_accounts, starting_accounts, starting_mrr)
WITH monthly AS (
    SELECT
        month_key,
        SUM(CASE WHEN mrr_movement_type != 'churn' THEN mrr ELSE 0 END)   AS total_mrr,
        SUM(new_mrr)                                                        AS new_mrr,
        SUM(expansion_mrr)                                                  AS expansion_mrr,
        SUM(contraction_mrr)                                                AS contraction_mrr,
        SUM(churned_mrr)                                                    AS churned_mrr,
        SUM(reactivation_mrr)                                               AS reactivation_mrr,
        SUM(net_mrr_contribution)                                           AS net_new_mrr,
        COUNT(DISTINCT CASE WHEN mrr_movement_type != 'churn' THEN account_id END) AS active_accounts,
        COUNT(DISTINCT CASE WHEN mrr_movement_type = 'churn'  THEN account_id END) AS churned_accounts,
        COUNT(DISTINCT CASE WHEN mrr_movement_type IN ('retained','expansion','contraction')
                            THEN account_id END)                            AS starting_accounts,
        SUM(CASE WHEN mrr_movement_type IN ('retained','expansion','contraction')
                 THEN mrr ELSE 0 END)                                       AS starting_mrr
    FROM marts.fct_mrr_movements
    GROUP BY month_key
),
with_lag AS (
    SELECT *, LAG(total_mrr) OVER (ORDER BY month_key) AS prev_mrr
    FROM monthly
)
SELECT
    month_key,
    total_mrr,
    total_mrr * 12                                                          AS total_arr,
    active_accounts,
    CASE WHEN active_accounts > 0 THEN total_mrr / active_accounts ELSE 0 END AS arpa,
    new_mrr, expansion_mrr, contraction_mrr, churned_mrr, reactivation_mrr, net_new_mrr,
    CASE WHEN starting_mrr > 0
         THEN (starting_mrr + expansion_mrr + reactivation_mrr - contraction_mrr - churned_mrr) / starting_mrr
         ELSE 1.0 END                                                       AS nrr,
    CASE WHEN starting_mrr > 0
         THEN (starting_mrr - contraction_mrr - churned_mrr) / starting_mrr
         ELSE 1.0 END                                                       AS grr,
    CASE WHEN starting_accounts > 0
         THEN churned_accounts::numeric / starting_accounts ELSE 0 END     AS logo_churn_rate,
    CASE WHEN starting_mrr > 0
         THEN (churned_mrr + contraction_mrr) / starting_mrr ELSE 0 END   AS revenue_churn_rate,
    CASE WHEN prev_mrr IS NOT NULL AND prev_mrr > 0
         THEN (total_mrr - prev_mrr) / prev_mrr ELSE 0 END                AS mrr_mom_pct,
    churned_accounts, starting_accounts, starting_mrr
FROM with_lag
ON CONFLICT (month_key) DO NOTHING;

-- 2. fct_customer_cohorts
INSERT INTO marts.fct_customer_cohorts
    (cohort_month, months_since_created, cohort_size, active_accounts,
     logo_retention_rate, cohort_mrr, starting_mrr,
     revenue_retention_rate, nrr, grr, cohort_health,
     plan_name, company_size, acquisition_channel)
WITH cohort_base AS (
    SELECT
        a.account_id,
        DATE_TRUNC('month', a.created_at)::date AS cohort_month,
        s.plan_name,
        a.company_size,
        a.acquisition_channel
    FROM staging.stg_accounts a
    JOIN staging.stg_subscriptions s ON a.account_id = s.account_id
),
cohort_months AS (
    SELECT
        cb.account_id,
        cb.cohort_month,
        cb.plan_name,
        cb.company_size,
        cb.acquisition_channel,
        m.month_key,
        (EXTRACT(YEAR FROM m.month_key) - EXTRACT(YEAR FROM cb.cohort_month)) * 12
        + (EXTRACT(MONTH FROM m.month_key) - EXTRACT(MONTH FROM cb.cohort_month)) AS months_since_created,
        m.mrr,
        m.mrr_movement_type
    FROM cohort_base cb
    JOIN marts.fct_mrr_movements m ON cb.account_id = m.account_id
),
cohort_start AS (
    SELECT cohort_month, COUNT(DISTINCT account_id) AS cohort_size,
           SUM(mrr) AS starting_mrr
    FROM cohort_months WHERE months_since_created = 0
    GROUP BY cohort_month
),
cohort_period AS (
    SELECT
        cm.cohort_month,
        cm.months_since_created,
        cm.plan_name,
        cm.company_size,
        cm.acquisition_channel,
        COUNT(DISTINCT CASE WHEN cm.mrr_movement_type != 'churn' THEN cm.account_id END) AS active_accounts,
        SUM(CASE WHEN cm.mrr_movement_type != 'churn' THEN cm.mrr ELSE 0 END)            AS cohort_mrr,
        SUM(cm.mrr)                                                                        AS total_mrr_incl_churn
    FROM cohort_months cm
    GROUP BY cm.cohort_month, cm.months_since_created, cm.plan_name, cm.company_size, cm.acquisition_channel
)
SELECT
    cp.cohort_month,
    cp.months_since_created,
    cs.cohort_size,
    cp.active_accounts,
    CASE WHEN cs.cohort_size > 0 THEN cp.active_accounts::numeric / cs.cohort_size ELSE 0 END AS logo_retention_rate,
    cp.cohort_mrr,
    cs.starting_mrr,
    CASE WHEN cs.starting_mrr > 0 THEN cp.cohort_mrr / cs.starting_mrr ELSE 0 END            AS revenue_retention_rate,
    CASE WHEN cs.starting_mrr > 0 THEN cp.cohort_mrr / cs.starting_mrr ELSE 0 END            AS nrr,
    CASE WHEN cs.starting_mrr > 0 THEN LEAST(cp.cohort_mrr / cs.starting_mrr, 1.0) ELSE 0 END AS grr,
    CASE
        WHEN cs.cohort_size > 0 AND cp.active_accounts::numeric / cs.cohort_size >= 0.85 THEN 'healthy'
        WHEN cs.cohort_size > 0 AND cp.active_accounts::numeric / cs.cohort_size >= 0.65 THEN 'at_risk'
        ELSE 'churning'
    END                                                                                        AS cohort_health,
    cp.plan_name,
    cp.company_size,
    cp.acquisition_channel
FROM cohort_period cp
JOIN cohort_start cs ON cp.cohort_month = cs.cohort_month
WHERE cp.months_since_created <= 12
ON CONFLICT (cohort_month, months_since_created) DO NOTHING;

-- 3. mart_customer_success_summary (latest month snapshot)
INSERT INTO marts.mart_customer_success_summary
    (account_id, snapshot_month, company_name, health_score, health_tier,
     churn_risk_level, risk_priority_score, mrr, arr, plan_name,
     company_size, region, industry, risk_reasons, health_trend, acquisition_channel)
SELECT DISTINCT ON (h.account_id)
    h.account_id,
    h.month_key                                                             AS snapshot_month,
    h.company_name,
    h.health_score,
    h.health_tier,
    h.churn_risk_level,
    h.churn_risk_score                                                      AS risk_priority_score,
    h.mrr,
    h.mrr * 12                                                              AS arr,
    h.plan_name,
    h.company_size,
    h.region,
    h.industry,
    h.risk_reasons,
    CASE
        WHEN h.health_score >= 70 THEN 'improving'
        WHEN h.health_score >= 50 THEN 'stable'
        ELSE 'declining'
    END                                                                     AS health_trend,
    h.acquisition_channel
FROM marts.fct_account_monthly_health h
ORDER BY h.account_id, h.month_key DESC
ON CONFLICT (account_id, snapshot_month) DO NOTHING;

-- Done
SELECT 'Aggregation complete' AS status;
