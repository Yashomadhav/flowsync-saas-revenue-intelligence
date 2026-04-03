-- =============================================================================
-- Migration 005: Views and Helper Functions
-- FlowSync Revenue Intelligence
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Convenience Views (cross-schema joins for FastAPI queries)
-- ---------------------------------------------------------------------------

-- v_current_mrr_summary — Latest month executive KPI snapshot
CREATE OR REPLACE VIEW marts.v_current_mrr_summary AS
SELECT
    m.*,
    LAG(m.total_mrr) OVER (ORDER BY m.month_date) AS prev_mrr,
    LAG(m.active_accounts) OVER (ORDER BY m.month_date) AS prev_accounts,
    CASE
        WHEN LAG(m.total_mrr) OVER (ORDER BY m.month_date) > 0
        THEN (m.total_mrr - LAG(m.total_mrr) OVER (ORDER BY m.month_date))
             / LAG(m.total_mrr) OVER (ORDER BY m.month_date)
        ELSE 0
    END AS mrr_growth_rate
FROM marts.mart_exec_revenue_summary m
ORDER BY m.month_date;

COMMENT ON VIEW marts.v_current_mrr_summary IS 'Executive summary with MoM growth rates';

-- v_active_accounts_health — Current month health for all active accounts
CREATE OR REPLACE VIEW marts.v_active_accounts_health AS
SELECT
    h.*,
    s.industry,
    s.region,
    s.acquisition_channel,
    s.company_size
FROM marts.fct_account_monthly_health h
JOIN staging.stg_accounts s ON h.account_id = s.account_id
WHERE h.month_date = (
    SELECT MAX(month_date) FROM marts.fct_account_monthly_health
);

COMMENT ON VIEW marts.v_active_accounts_health IS 'Latest health scores joined with account attributes';

-- v_mrr_waterfall — Monthly MRR waterfall aggregated
CREATE OR REPLACE VIEW marts.v_mrr_waterfall AS
SELECT
    month_date,
    SUM(new_mrr)          AS new_mrr,
    SUM(expansion_mrr)    AS expansion_mrr,
    SUM(contraction_mrr)  AS contraction_mrr,
    SUM(churned_mrr)      AS churned_mrr,
    SUM(reactivation_mrr) AS reactivation_mrr,
    SUM(net_new_mrr)      AS net_new_mrr,
    SUM(CASE WHEN movement_type != 'churn' THEN ending_mrr ELSE 0 END) AS total_mrr
FROM marts.fct_mrr_movements
GROUP BY month_date
ORDER BY month_date;

COMMENT ON VIEW marts.v_mrr_waterfall IS 'Monthly MRR waterfall aggregated across all accounts';

-- v_revenue_by_plan — MRR breakdown by plan for latest month
CREATE OR REPLACE VIEW marts.v_revenue_by_plan AS
SELECT
    plan_name,
    SUM(ending_mrr) AS total_mrr,
    COUNT(DISTINCT account_id) AS account_count,
    AVG(ending_mrr) AS avg_mrr
FROM marts.fct_mrr_movements
WHERE month_date = (SELECT MAX(month_date) FROM marts.fct_mrr_movements)
  AND movement_type != 'churn'
GROUP BY plan_name
ORDER BY total_mrr DESC;

COMMENT ON VIEW marts.v_revenue_by_plan IS 'Current month MRR by plan';

-- v_revenue_by_region — MRR breakdown by region for latest month
CREATE OR REPLACE VIEW marts.v_revenue_by_region AS
SELECT
    region,
    SUM(ending_mrr) AS total_mrr,
    COUNT(DISTINCT account_id) AS account_count,
    AVG(ending_mrr) AS avg_mrr
FROM marts.fct_mrr_movements
WHERE month_date = (SELECT MAX(month_date) FROM marts.fct_mrr_movements)
  AND movement_type != 'churn'
GROUP BY region
ORDER BY total_mrr DESC;

COMMENT ON VIEW marts.v_revenue_by_region IS 'Current month MRR by region';

-- v_top_expanding_accounts — Top 10 expanding accounts this month
CREATE OR REPLACE VIEW marts.v_top_expanding_accounts AS
SELECT
    m.account_id,
    a.company_name,
    m.plan_name,
    a.region,
    a.industry,
    m.expansion_mrr,
    m.ending_mrr,
    h.health_score
FROM marts.fct_mrr_movements m
JOIN staging.stg_accounts a ON m.account_id = a.account_id
LEFT JOIN marts.fct_account_monthly_health h
    ON m.account_id = h.account_id AND m.month_date = h.month_date
WHERE m.month_date = (SELECT MAX(month_date) FROM marts.fct_mrr_movements)
  AND m.movement_type = 'expansion'
ORDER BY m.expansion_mrr DESC
LIMIT 10;

COMMENT ON VIEW marts.v_top_expanding_accounts IS 'Top 10 expanding accounts in latest month';

-- v_churn_risk_accounts — Accounts flagged as critical risk
CREATE OR REPLACE VIEW marts.v_churn_risk_accounts AS
SELECT
    h.account_id,
    h.company_name,
    h.plan_name,
    h.mrr_amount,
    h.health_score,
    h.risk_level,
    h.flag_usage_drop,
    h.flag_no_login,
    h.flag_support_overload,
    h.flag_payment_failure,
    h.flag_low_csat,
    h.flag_low_seat_util,
    a.region,
    a.industry,
    a.acquisition_channel,
    (
        CASE WHEN h.flag_usage_drop      THEN 1 ELSE 0 END +
        CASE WHEN h.flag_no_login        THEN 1 ELSE 0 END +
        CASE WHEN h.flag_support_overload THEN 1 ELSE 0 END +
        CASE WHEN h.flag_payment_failure  THEN 1 ELSE 0 END +
        CASE WHEN h.flag_low_csat        THEN 1 ELSE 0 END +
        CASE WHEN h.flag_low_seat_util   THEN 1 ELSE 0 END
    ) AS risk_flag_count
FROM marts.fct_account_monthly_health h
JOIN staging.stg_accounts a ON h.account_id = a.account_id
WHERE h.month_date = (SELECT MAX(month_date) FROM marts.fct_account_monthly_health)
  AND h.risk_level IN ('at_risk', 'critical')
ORDER BY h.health_score ASC, h.mrr_amount DESC;

COMMENT ON VIEW marts.v_churn_risk_accounts IS 'At-risk and critical accounts with risk flag details';

-- v_funnel_summary — Lead-to-paid conversion funnel summary
CREATE OR REPLACE VIEW marts.v_funnel_summary AS
SELECT
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE trial_start_date IS NOT NULL) AS trial_starts,
    COUNT(*) FILTER (WHERE is_converted = TRUE) AS paid_conversions,
    ROUND(
        COUNT(*) FILTER (WHERE trial_start_date IS NOT NULL)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100, 2
    ) AS lead_to_trial_rate,
    ROUND(
        COUNT(*) FILTER (WHERE is_converted = TRUE)::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE trial_start_date IS NOT NULL), 0) * 100, 2
    ) AS trial_to_paid_rate,
    ROUND(
        COUNT(*) FILTER (WHERE is_converted = TRUE)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100, 2
    ) AS overall_conversion_rate,
    ROUND(AVG(days_to_convert) FILTER (WHERE is_converted = TRUE), 1) AS avg_days_to_convert
FROM marts.fct_sales_conversion;

COMMENT ON VIEW marts.v_funnel_summary IS 'Overall lead-to-paid conversion funnel metrics';

-- ---------------------------------------------------------------------------
-- Helper Functions
-- ---------------------------------------------------------------------------

-- fn_get_mrr_for_month — Get total MRR for a specific month
CREATE OR REPLACE FUNCTION marts.fn_get_mrr_for_month(p_month DATE)
RETURNS NUMERIC AS $$
    SELECT COALESCE(SUM(ending_mrr), 0)
    FROM marts.fct_mrr_movements
    WHERE month_date = DATE_TRUNC('month', p_month)::DATE
      AND movement_type != 'churn';
$$ LANGUAGE SQL STABLE;

-- fn_compute_nrr — Compute NRR for a given month
CREATE OR REPLACE FUNCTION marts.fn_compute_nrr(p_month DATE)
RETURNS NUMERIC AS $$
DECLARE
    v_starting_mrr    NUMERIC;
    v_expansion       NUMERIC;
    v_reactivation    NUMERIC;
    v_contraction     NUMERIC;
    v_churn           NUMERIC;
BEGIN
    SELECT
        COALESCE(SUM(starting_mrr), 0),
        COALESCE(SUM(expansion_mrr), 0),
        COALESCE(SUM(reactivation_mrr), 0),
        COALESCE(SUM(contraction_mrr), 0),
        COALESCE(SUM(churned_mrr), 0)
    INTO v_starting_mrr, v_expansion, v_reactivation, v_contraction, v_churn
    FROM marts.fct_mrr_movements
    WHERE month_date = DATE_TRUNC('month', p_month)::DATE;

    IF v_starting_mrr = 0 THEN RETURN 1.0; END IF;
    RETURN (v_starting_mrr + v_expansion + v_reactivation - v_contraction - v_churn)
           / v_starting_mrr;
END;
$$ LANGUAGE plpgsql STABLE;

-- fn_health_score_label — Convert numeric score to label
CREATE OR REPLACE FUNCTION marts.fn_health_score_label(p_score NUMERIC)
RETURNS TEXT AS $$
BEGIN
    IF p_score >= 75 THEN RETURN 'Healthy';
    ELSIF p_score >= 50 THEN RETURN 'At Risk';
    ELSE RETURN 'Critical';
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- fn_refresh_exec_summary — Recompute MoM changes in exec summary
CREATE OR REPLACE FUNCTION marts.fn_refresh_exec_summary()
RETURNS VOID AS $$
BEGIN
    UPDATE marts.mart_exec_revenue_summary m
    SET
        mrr_mom_change = CASE
            WHEN prev.total_mrr > 0
            THEN (m.total_mrr - prev.total_mrr) / prev.total_mrr
            ELSE 0
        END,
        arr_mom_change = CASE
            WHEN prev.total_arr > 0
            THEN (m.total_arr - prev.total_arr) / prev.total_arr
            ELSE 0
        END,
        accounts_mom_change = CASE
            WHEN prev.active_accounts > 0
            THEN (m.active_accounts - prev.active_accounts)::NUMERIC / prev.active_accounts
            ELSE 0
        END,
        updated_at = NOW()
    FROM (
        SELECT
            month_date,
            LAG(total_mrr) OVER (ORDER BY month_date) AS total_mrr,
            LAG(total_arr) OVER (ORDER BY month_date) AS total_arr,
            LAG(active_accounts) OVER (ORDER BY month_date) AS active_accounts
        FROM marts.mart_exec_revenue_summary
    ) prev
    WHERE m.month_date = prev.month_date;
END;
$$ LANGUAGE plpgsql;

SELECT 'Migration 005: Views and functions created' AS status;
