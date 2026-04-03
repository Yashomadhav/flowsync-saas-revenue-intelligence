"""
FlowSync Revenue Intelligence - CSV Ingestion Pipeline
=======================================================
Loads CSV files from data/output/ into the raw schema,
then transforms to staging and marts via SQL.

Usage:
    python scripts/ingest/ingest_pipeline.py
    python scripts/ingest/ingest_pipeline.py --stage raw
    python scripts/ingest/ingest_pipeline.py --stage all --truncate
"""

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest_pipeline")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "output"

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def get_connection():
    """Creates a psycopg2 connection from environment variables."""
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=os.environ.get("POSTGRES_DB", "flowsync_bi"),
            user=os.environ.get("POSTGRES_USER", "flowsync"),
            password=os.environ.get("POSTGRES_PASSWORD", "flowsync_secret_change_me"),
        )
    conn.autocommit = False
    return conn


# ---------------------------------------------------------------------------
# CSV → raw schema loader
# ---------------------------------------------------------------------------

RAW_TABLE_MAP = {
    "plans.csv": {
        "table": "raw.raw_plans",
        "columns": [
            "plan_id", "plan_name", "monthly_price", "annual_price",
            "max_seats", "max_workflows", "tier", "is_active",
        ],
    },
    "features.csv": {
        "table": "raw.raw_features",
        "columns": [
            "feature_id", "feature_name", "feature_category",
            "plan_tier_required", "is_core",
        ],
    },
    "calendar.csv": {
        "table": "raw.raw_calendar",
        "columns": [
            "date_id", "full_date", "year", "quarter", "month",
            "month_name", "week", "day_of_week", "day_name",
            "is_weekend", "is_month_start", "is_month_end",
        ],
    },
    "accounts.csv": {
        "table": "raw.raw_accounts",
        "columns": [
            "account_id", "company_name", "industry", "company_size",
            "region", "country", "acquisition_channel", "account_owner",
            "created_at", "website", "annual_revenue_usd", "employee_count",
        ],
    },
    "subscriptions.csv": {
        "table": "raw.raw_subscriptions",
        "columns": [
            "subscription_id", "account_id", "plan_id", "status",
            "billing_cycle", "mrr", "arr", "seats", "start_date",
            "end_date", "trial_start", "trial_end", "cancelled_at",
            "cancellation_reason", "discount_pct",
        ],
    },
    "invoices.csv": {
        "table": "raw.raw_invoices",
        "columns": [
            "invoice_id", "account_id", "subscription_id", "invoice_date",
            "due_date", "amount", "currency", "status", "payment_method",
            "paid_at", "failure_reason", "retry_count",
        ],
    },
    "usage_events.csv": {
        "table": "raw.raw_usage_events",
        "columns": [
            "event_id", "account_id", "user_id", "feature_id",
            "event_type", "event_date", "session_duration_min", "actions_count",
        ],
    },
    "support_tickets.csv": {
        "table": "raw.raw_tickets",
        "columns": [
            "ticket_id", "account_id", "subject", "category",
            "priority", "status", "created_at", "resolved_at",
            "csat_score", "agent_id",
        ],
    },
    "leads.csv": {
        "table": "raw.raw_leads",
        "columns": [
            "lead_id", "company_name", "industry", "company_size",
            "region", "acquisition_channel", "lead_source", "lead_date",
            "trial_start_date", "trial_end_date", "converted_at",
            "account_id", "plan_id", "first_mrr", "lost_reason",
        ],
    },
}


def load_csv_to_raw(conn, csv_file: str, table: str, columns: list,
                    truncate: bool = False, batch_size: int = 1000) -> int:
    """
    Loads a CSV file into a raw schema table using COPY-style batch inserts.
    Returns the number of rows inserted.
    """
    csv_path = DATA_DIR / csv_file
    if not csv_path.exists():
        logger.warning("CSV not found, skipping: %s", csv_path)
        return 0

    source_file = str(csv_path.name)
    col_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = (
        "INSERT INTO " + table + " (" + col_list + ", _source_file) "
        "VALUES (" + placeholders + ", %s)"
    )

    total_rows = 0
    start_time = time.monotonic()

    with conn.cursor() as cur:
        if truncate:
            logger.info("Truncating %s...", table)
            cur.execute("TRUNCATE TABLE " + table + " RESTART IDENTITY")

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch = []

            for row in reader:
                values = []
                for col in columns:
                    val = row.get(col, None)
                    if val == "" or val is None:
                        values.append(None)
                    else:
                        values.append(val)
                values.append(source_file)
                batch.append(tuple(values))

                if len(batch) >= batch_size:
                    psycopg2.extras.execute_batch(cur, insert_sql, batch, page_size=batch_size)
                    total_rows += len(batch)
                    batch = []

            if batch:
                psycopg2.extras.execute_batch(cur, insert_sql, batch, page_size=batch_size)
                total_rows += len(batch)

    elapsed = round(time.monotonic() - start_time, 2)
    logger.info("Loaded %d rows into %s in %.2fs", total_rows, table, elapsed)
    return total_rows


# ---------------------------------------------------------------------------
# raw → staging transformations
# ---------------------------------------------------------------------------

STAGING_TRANSFORMS = [
    # Plans
    """
    INSERT INTO staging.stg_plans (
        plan_id, plan_name, monthly_price, annual_price,
        max_seats, max_workflows, tier, is_active
    )
    SELECT DISTINCT ON (plan_id)
        plan_id,
        plan_name,
        NULLIF(monthly_price, '')::NUMERIC,
        NULLIF(annual_price, '')::NUMERIC,
        NULLIF(max_seats, '')::INTEGER,
        NULLIF(max_workflows, '')::INTEGER,
        tier,
        COALESCE(NULLIF(is_active, '')::BOOLEAN, TRUE)
    FROM raw.raw_plans
    WHERE plan_id IS NOT NULL
    ORDER BY plan_id, _loaded_at DESC
    ON CONFLICT (plan_id) DO UPDATE SET
        plan_name = EXCLUDED.plan_name,
        monthly_price = EXCLUDED.monthly_price,
        annual_price = EXCLUDED.annual_price,
        max_seats = EXCLUDED.max_seats,
        max_workflows = EXCLUDED.max_workflows,
        tier = EXCLUDED.tier,
        is_active = EXCLUDED.is_active,
        _loaded_at = NOW()
    """,

    # Features
    """
    INSERT INTO staging.stg_features (
        feature_id, feature_name, feature_category, plan_tier_required, is_core
    )
    SELECT DISTINCT ON (feature_id)
        feature_id,
        feature_name,
        feature_category,
        plan_tier_required,
        COALESCE(NULLIF(is_core, '')::BOOLEAN, FALSE)
    FROM raw.raw_features
    WHERE feature_id IS NOT NULL
    ORDER BY feature_id, _loaded_at DESC
    ON CONFLICT (feature_id) DO UPDATE SET
        feature_name = EXCLUDED.feature_name,
        feature_category = EXCLUDED.feature_category,
        plan_tier_required = EXCLUDED.plan_tier_required,
        is_core = EXCLUDED.is_core,
        _loaded_at = NOW()
    """,

    # Calendar
    """
    INSERT INTO staging.stg_calendar (
        date_id, full_date, year, quarter, month, month_name,
        week, day_of_week, day_name, is_weekend, is_month_start, is_month_end
    )
    SELECT DISTINCT ON (date_id)
        NULLIF(date_id, '')::INTEGER,
        NULLIF(full_date, '')::DATE,
        NULLIF(year, '')::INTEGER,
        NULLIF(quarter, '')::INTEGER,
        NULLIF(month, '')::INTEGER,
        month_name,
        NULLIF(week, '')::INTEGER,
        NULLIF(day_of_week, '')::INTEGER,
        day_name,
        COALESCE(NULLIF(is_weekend, '')::BOOLEAN, FALSE),
        COALESCE(NULLIF(is_month_start, '')::BOOLEAN, FALSE),
        COALESCE(NULLIF(is_month_end, '')::BOOLEAN, FALSE)
    FROM raw.raw_calendar
    WHERE date_id IS NOT NULL
    ORDER BY date_id, _loaded_at DESC
    ON CONFLICT (date_id) DO NOTHING
    """,

    # Accounts
    """
    INSERT INTO staging.stg_accounts (
        account_id, company_name, industry, company_size, region, country,
        acquisition_channel, account_owner, created_at, website,
        annual_revenue_usd, employee_count
    )
    SELECT DISTINCT ON (account_id)
        NULLIF(account_id, '')::UUID,
        company_name,
        industry,
        company_size,
        region,
        country,
        acquisition_channel,
        account_owner,
        NULLIF(created_at, '')::TIMESTAMPTZ,
        website,
        NULLIF(annual_revenue_usd, '')::NUMERIC,
        NULLIF(employee_count, '')::INTEGER
    FROM raw.raw_accounts
    WHERE account_id IS NOT NULL
    ORDER BY account_id, _loaded_at DESC
    ON CONFLICT (account_id) DO UPDATE SET
        company_name = EXCLUDED.company_name,
        industry = EXCLUDED.industry,
        company_size = EXCLUDED.company_size,
        region = EXCLUDED.region,
        country = EXCLUDED.country,
        acquisition_channel = EXCLUDED.acquisition_channel,
        account_owner = EXCLUDED.account_owner,
        created_at = EXCLUDED.created_at,
        website = EXCLUDED.website,
        annual_revenue_usd = EXCLUDED.annual_revenue_usd,
        employee_count = EXCLUDED.employee_count,
        _loaded_at = NOW()
    """,

    # Subscriptions
    """
    INSERT INTO staging.stg_subscriptions (
        subscription_id, account_id, plan_id, status, billing_cycle,
        mrr, arr, seats, start_date, end_date, trial_start, trial_end,
        cancelled_at, cancellation_reason, discount_pct
    )
    SELECT DISTINCT ON (subscription_id)
        NULLIF(subscription_id, '')::UUID,
        NULLIF(account_id, '')::UUID,
        plan_id,
        status,
        billing_cycle,
        NULLIF(mrr, '')::NUMERIC,
        NULLIF(arr, '')::NUMERIC,
        NULLIF(seats, '')::INTEGER,
        NULLIF(start_date, '')::DATE,
        NULLIF(end_date, '')::DATE,
        NULLIF(trial_start, '')::DATE,
        NULLIF(trial_end, '')::DATE,
        NULLIF(cancelled_at, '')::TIMESTAMPTZ,
        cancellation_reason,
        NULLIF(discount_pct, '')::NUMERIC
    FROM raw.raw_subscriptions
    WHERE subscription_id IS NOT NULL
    ORDER BY subscription_id, _loaded_at DESC
    ON CONFLICT (subscription_id) DO UPDATE SET
        status = EXCLUDED.status,
        mrr = EXCLUDED.mrr,
        arr = EXCLUDED.arr,
        seats = EXCLUDED.seats,
        end_date = EXCLUDED.end_date,
        cancelled_at = EXCLUDED.cancelled_at,
        cancellation_reason = EXCLUDED.cancellation_reason,
        _loaded_at = NOW()
    """,

    # Invoices
    """
    INSERT INTO staging.stg_invoices (
        invoice_id, account_id, subscription_id, invoice_date, due_date,
        amount, currency, status, payment_method, paid_at,
        failure_reason, retry_count
    )
    SELECT DISTINCT ON (invoice_id)
        NULLIF(invoice_id, '')::UUID,
        NULLIF(account_id, '')::UUID,
        NULLIF(subscription_id, '')::UUID,
        NULLIF(invoice_date, '')::DATE,
        NULLIF(due_date, '')::DATE,
        NULLIF(amount, '')::NUMERIC,
        COALESCE(NULLIF(currency, ''), 'USD'),
        status,
        payment_method,
        NULLIF(paid_at, '')::TIMESTAMPTZ,
        failure_reason,
        COALESCE(NULLIF(retry_count, '')::INTEGER, 0)
    FROM raw.raw_invoices
    WHERE invoice_id IS NOT NULL
    ORDER BY invoice_id, _loaded_at DESC
    ON CONFLICT (invoice_id) DO UPDATE SET
        status = EXCLUDED.status,
        paid_at = EXCLUDED.paid_at,
        failure_reason = EXCLUDED.failure_reason,
        retry_count = EXCLUDED.retry_count,
        _loaded_at = NOW()
    """,

    # Usage events
    """
    INSERT INTO staging.stg_usage_events (
        event_id, account_id, user_id, feature_id, event_type,
        event_date, session_duration_min, actions_count
    )
    SELECT DISTINCT ON (event_id)
        NULLIF(event_id, '')::UUID,
        NULLIF(account_id, '')::UUID,
        user_id,
        feature_id,
        event_type,
        NULLIF(event_date, '')::DATE,
        NULLIF(session_duration_min, '')::INTEGER,
        NULLIF(actions_count, '')::INTEGER
    FROM raw.raw_usage_events
    WHERE event_id IS NOT NULL
    ORDER BY event_id, _loaded_at DESC
    ON CONFLICT (event_id) DO NOTHING
    """,

    # Tickets
    """
    INSERT INTO staging.stg_tickets (
        ticket_id, account_id, subject, category, priority,
        status, created_at, resolved_at, csat_score, agent_id
    )
    SELECT DISTINCT ON (ticket_id)
        NULLIF(ticket_id, '')::UUID,
        NULLIF(account_id, '')::UUID,
        subject,
        category,
        priority,
        status,
        NULLIF(created_at, '')::TIMESTAMPTZ,
        NULLIF(resolved_at, '')::TIMESTAMPTZ,
        NULLIF(csat_score, '')::NUMERIC,
        agent_id
    FROM raw.raw_tickets
    WHERE ticket_id IS NOT NULL
    ORDER BY ticket_id, _loaded_at DESC
    ON CONFLICT (ticket_id) DO UPDATE SET
        status = EXCLUDED.status,
        resolved_at = EXCLUDED.resolved_at,
        csat_score = EXCLUDED.csat_score,
        _loaded_at = NOW()
    """,

    # Leads
    """
    INSERT INTO staging.stg_leads (
        lead_id, company_name, industry, company_size, region,
        acquisition_channel, lead_source, lead_date, trial_start_date,
        trial_end_date, converted_at, account_id, plan_id,
        first_mrr, lost_reason
    )
    SELECT DISTINCT ON (lead_id)
        NULLIF(lead_id, '')::UUID,
        company_name,
        industry,
        company_size,
        region,
        acquisition_channel,
        lead_source,
        NULLIF(lead_date, '')::DATE,
        NULLIF(trial_start_date, '')::DATE,
        NULLIF(trial_end_date, '')::DATE,
        NULLIF(converted_at, '')::TIMESTAMPTZ,
        NULLIF(account_id, '')::UUID,
        plan_id,
        NULLIF(first_mrr, '')::NUMERIC,
        lost_reason
    FROM raw.raw_leads
    WHERE lead_id IS NOT NULL
    ORDER BY lead_id, _loaded_at DESC
    ON CONFLICT (lead_id) DO UPDATE SET
        converted_at = EXCLUDED.converted_at,
        account_id = EXCLUDED.account_id,
        plan_id = EXCLUDED.plan_id,
        first_mrr = EXCLUDED.first_mrr,
        lost_reason = EXCLUDED.lost_reason,
        _loaded_at = NOW()
    """,
]


# ---------------------------------------------------------------------------
# staging → marts transformations
# ---------------------------------------------------------------------------

MARTS_TRANSFORMS = [
    # MRR movements fact table
    """
    INSERT INTO marts.fct_mrr_movements (
        month_date, account_id, company_name, plan_id, plan_name,
        region, industry, company_size, acquisition_channel,
        starting_mrr, ending_mrr, new_mrr, expansion_mrr,
        contraction_mrr, churned_mrr, reactivation_mrr, net_new_mrr, movement_type
    )
    WITH monthly_subs AS (
        SELECT
            DATE_TRUNC('month', d.full_date)::DATE AS month_date,
            s.account_id,
            a.company_name,
            s.plan_id,
            p.plan_name,
            a.region,
            a.industry,
            a.company_size,
            a.acquisition_channel,
            COALESCE(s.mrr, 0) AS mrr,
            s.status,
            s.start_date,
            s.end_date,
            s.cancelled_at
        FROM staging.stg_subscriptions s
        JOIN staging.stg_accounts a ON s.account_id = a.account_id
        JOIN staging.stg_plans p ON s.plan_id = p.plan_id
        CROSS JOIN (
            SELECT DISTINCT DATE_TRUNC('month', full_date)::DATE AS full_date
            FROM staging.stg_calendar
        ) d
        WHERE s.start_date <= (d.full_date + INTERVAL '1 month - 1 day')::DATE
          AND (s.end_date IS NULL OR s.end_date >= d.full_date)
          AND s.status NOT IN ('trial', 'pending')
    ),
    prev_month AS (
        SELECT
            month_date,
            account_id,
            mrr AS current_mrr,
            LAG(mrr) OVER (PARTITION BY account_id ORDER BY month_date) AS prev_mrr,
            LAG(status) OVER (PARTITION BY account_id ORDER BY month_date) AS prev_status
        FROM monthly_subs
    )
    SELECT
        pm.month_date,
        pm.account_id,
        ms.company_name,
        ms.plan_id,
        ms.plan_name,
        ms.region,
        ms.industry,
        ms.company_size,
        ms.acquisition_channel,
        COALESCE(pm.prev_mrr, 0) AS starting_mrr,
        pm.current_mrr AS ending_mrr,
        CASE WHEN pm.prev_mrr IS NULL THEN pm.current_mrr ELSE 0 END AS new_mrr,
        CASE WHEN pm.prev_mrr IS NOT NULL AND pm.current_mrr > pm.prev_mrr
             THEN pm.current_mrr - pm.prev_mrr ELSE 0 END AS expansion_mrr,
        CASE WHEN pm.prev_mrr IS NOT NULL AND pm.current_mrr < pm.prev_mrr AND pm.current_mrr > 0
             THEN pm.prev_mrr - pm.current_mrr ELSE 0 END AS contraction_mrr,
        0 AS churned_mrr,
        0 AS reactivation_mrr,
        pm.current_mrr - COALESCE(pm.prev_mrr, 0) AS net_new_mrr,
        CASE
            WHEN pm.prev_mrr IS NULL THEN 'new'
            WHEN pm.current_mrr > pm.prev_mrr THEN 'expansion'
            WHEN pm.current_mrr < pm.prev_mrr AND pm.current_mrr > 0 THEN 'contraction'
            ELSE 'retained'
        END AS movement_type
    FROM prev_month pm
    JOIN monthly_subs ms ON pm.month_date = ms.month_date AND pm.account_id = ms.account_id
    ON CONFLICT (month_date, account_id) DO UPDATE SET
        ending_mrr = EXCLUDED.ending_mrr,
        new_mrr = EXCLUDED.new_mrr,
        expansion_mrr = EXCLUDED.expansion_mrr,
        contraction_mrr = EXCLUDED.contraction_mrr,
        net_new_mrr = EXCLUDED.net_new_mrr,
        movement_type = EXCLUDED.movement_type,
        _loaded_at = NOW()
    """,

    # Executive revenue summary
    """
    INSERT INTO marts.mart_exec_revenue_summary (
        month_date, total_mrr, total_arr, active_accounts,
        new_mrr, expansion_mrr, contraction_mrr, churned_mrr,
        reactivation_mrr, net_new_mrr,
        logo_churn_rate, revenue_churn_rate, nrr, grr, arpa
    )
    SELECT
        month_date,
        SUM(ending_mrr) AS total_mrr,
        SUM(ending_mrr) * 12 AS total_arr,
        COUNT(DISTINCT account_id) AS active_accounts,
        SUM(new_mrr) AS new_mrr,
        SUM(expansion_mrr) AS expansion_mrr,
        SUM(contraction_mrr) AS contraction_mrr,
        SUM(churned_mrr) AS churned_mrr,
        SUM(reactivation_mrr) AS reactivation_mrr,
        SUM(net_new_mrr) AS net_new_mrr,
        CASE WHEN SUM(starting_mrr) > 0
             THEN ROUND(SUM(churned_mrr) / NULLIF(SUM(starting_mrr), 0), 4)
             ELSE 0 END AS logo_churn_rate,
        CASE WHEN SUM(starting_mrr) > 0
             THEN ROUND((SUM(churned_mrr) + SUM(contraction_mrr)) / NULLIF(SUM(starting_mrr), 0), 4)
             ELSE 0 END AS revenue_churn_rate,
        CASE WHEN SUM(starting_mrr) > 0
             THEN ROUND((SUM(starting_mrr) + SUM(expansion_mrr) + SUM(reactivation_mrr)
                         - SUM(contraction_mrr) - SUM(churned_mrr)) / NULLIF(SUM(starting_mrr), 0), 4)
             ELSE 1 END AS nrr,
        CASE WHEN SUM(starting_mrr) > 0
             THEN ROUND((SUM(starting_mrr) - SUM(contraction_mrr) - SUM(churned_mrr))
                        / NULLIF(SUM(starting_mrr), 0), 4)
             ELSE 1 END AS grr,
        CASE WHEN COUNT(DISTINCT account_id) > 0
             THEN ROUND(SUM(ending_mrr) / NULLIF(COUNT(DISTINCT account_id), 0), 2)
             ELSE 0 END AS arpa
    FROM marts.fct_mrr_movements
    GROUP BY month_date
    ON CONFLICT (month_date) DO UPDATE SET
        total_mrr = EXCLUDED.total_mrr,
        total_arr = EXCLUDED.total_arr,
        active_accounts = EXCLUDED.active_accounts,
        new_mrr = EXCLUDED.new_mrr,
        expansion_mrr = EXCLUDED.expansion_mrr,
        contraction_mrr = EXCLUDED.contraction_mrr,
        churned_mrr = EXCLUDED.churned_mrr,
        reactivation_mrr = EXCLUDED.reactivation_mrr,
        net_new_mrr = EXCLUDED.net_new_mrr,
        logo_churn_rate = EXCLUDED.logo_churn_rate,
        revenue_churn_rate = EXCLUDED.revenue_churn_rate,
        nrr = EXCLUDED.nrr,
        grr = EXCLUDED.grr,
        arpa = EXCLUDED.arpa,
        _loaded_at = NOW()
    """,

    # Sales conversion fact
    """
    INSERT INTO marts.fct_sales_conversion (
        lead_id, lead_date, trial_start_date, converted_at,
        acquisition_channel, lead_source, company_size, industry, region,
        plan_id, plan_name, first_mrr, had_trial, converted, lost_reason,
        days_lead_to_trial, days_trial_to_paid, days_lead_to_paid
    )
    SELECT
        l.lead_id,
        l.lead_date,
        l.trial_start_date,
        l.converted_at,
        l.acquisition_channel,
        l.lead_source,
        l.company_size,
        l.industry,
        l.region,
        l.plan_id,
        p.plan_name,
        l.first_mrr,
        l.trial_start_date IS NOT NULL AS had_trial,
        l.converted_at IS NOT NULL AS converted,
        l.lost_reason,
        CASE WHEN l.trial_start_date IS NOT NULL
             THEN (l.trial_start_date - l.lead_date)
             ELSE NULL END AS days_lead_to_trial,
        CASE WHEN l.converted_at IS NOT NULL AND l.trial_start_date IS NOT NULL
             THEN (l.converted_at::DATE - l.trial_start_date)
             ELSE NULL END AS days_trial_to_paid,
        CASE WHEN l.converted_at IS NOT NULL
             THEN (l.converted_at::DATE - l.lead_date)
             ELSE NULL END AS days_lead_to_paid
    FROM staging.stg_leads l
    LEFT JOIN staging.stg_plans p ON l.plan_id = p.plan_id
    ON CONFLICT DO NOTHING
    """,
]


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_raw_stage(conn, truncate: bool = False) -> dict:
    """Loads all CSVs into raw schema tables."""
    logger.info("=== Stage: raw (Bronze) ===")
    results = {}
    for csv_file, config in RAW_TABLE_MAP.items():
        rows = load_csv_to_raw(
            conn,
            csv_file=csv_file,
            table=config["table"],
            columns=config["columns"],
            truncate=truncate,
        )
        results[config["table"]] = rows
    conn.commit()
    logger.info("Raw stage complete. Tables loaded: %d", len(results))
    return results


def run_staging_stage(conn, truncate: bool = False) -> int:
    """Transforms raw → staging (Silver layer)."""
    logger.info("=== Stage: staging (Silver) ===")
    if truncate:
        with conn.cursor() as cur:
            staging_tables = [
                "staging.stg_leads", "staging.stg_tickets",
                "staging.stg_usage_events", "staging.stg_invoices",
                "staging.stg_subscriptions", "staging.stg_accounts",
                "staging.stg_calendar", "staging.stg_features", "staging.stg_plans",
            ]
            for tbl in staging_tables:
                cur.execute("TRUNCATE TABLE " + tbl + " CASCADE")
            logger.info("Truncated all staging tables.")

    total = 0
    for i, sql in enumerate(STAGING_TRANSFORMS, 1):
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.rowcount
            total += max(rows, 0)
            logger.info("Staging transform %d/%d: %d rows affected", i, len(STAGING_TRANSFORMS), rows)
    conn.commit()
    logger.info("Staging stage complete. Total rows: %d", total)
    return total


def run_marts_stage(conn, truncate: bool = False) -> int:
    """Transforms staging → marts (Gold layer)."""
    logger.info("=== Stage: marts (Gold) ===")
    if truncate:
        with conn.cursor() as cur:
            marts_tables = [
                "marts.mart_customer_success_summary",
                "marts.mart_exec_revenue_summary",
                "marts.fct_sales_conversion",
                "marts.fct_customer_cohorts",
                "marts.fct_account_monthly_health",
                "marts.fct_mrr_movements",
            ]
            for tbl in marts_tables:
                cur.execute("TRUNCATE TABLE " + tbl + " CASCADE")
            logger.info("Truncated all marts tables.")

    total = 0
    for i, sql in enumerate(MARTS_TRANSFORMS, 1):
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.rowcount
            total += max(rows, 0)
            logger.info("Marts transform %d/%d: %d rows affected", i, len(MARTS_TRANSFORMS), rows)
    conn.commit()
    logger.info("Marts stage complete. Total rows: %d", total)
    return total


def run_pipeline(stage: str = "all", truncate: bool = False):
    """Main pipeline entry point."""
    logger.info("FlowSync Ingestion Pipeline starting (stage=%s, truncate=%s)", stage, truncate)
    start = time.monotonic()

    conn = get_connection()
    try:
        if stage in ("raw", "all"):
            run_raw_stage(conn, truncate=truncate)

        if stage in ("staging", "all"):
            run_staging_stage(conn, truncate=truncate)

        if stage in ("marts", "all"):
            run_marts_stage(conn, truncate=truncate)

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        conn.rollback()
        raise
    finally:
        conn.close()

    elapsed = round(time.monotonic() - start, 2)
    logger.info("Pipeline complete in %.2fs", elapsed)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FlowSync CSV Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python ingest_pipeline.py\n"
            "  python ingest_pipeline.py --stage raw\n"
            "  python ingest_pipeline.py --stage all --truncate\n"
        ),
    )
    parser.add_argument(
        "--stage",
        choices=["raw", "staging", "marts", "all"],
        default="all",
        help="Which pipeline stage to run (default: all)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        default=False,
        help="Truncate target tables before loading (full reload)",
    )
    args = parser.parse_args()
    run_pipeline(stage=args.stage, truncate=args.truncate)


if __name__ == "__main__":
    main()
