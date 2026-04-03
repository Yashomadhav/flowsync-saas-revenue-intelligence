"""
FlowSync Revenue Intelligence - Row Count Validation
=====================================================
Validates that all pipeline stages have expected row counts
and that data quality checks pass after ingestion.

Usage:
    python scripts/ingest/validate_counts.py
    python scripts/ingest/validate_counts.py --fail-fast
    python scripts/ingest/validate_counts.py --output json
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("validate_counts")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "output"


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def get_connection():
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "flowsync_bi"),
        user=os.environ.get("POSTGRES_USER", "flowsync"),
        password=os.environ.get("POSTGRES_PASSWORD", "flowsync_secret_change_me"),
    )


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

SCHEMA_TABLE_CHECKS = [
    # Raw schema
    ("raw", "raw_plans",         "plan_id IS NOT NULL",         4,    20),
    ("raw", "raw_features",      "feature_id IS NOT NULL",      10,   100),
    ("raw", "raw_calendar",      "full_date IS NOT NULL",       700,  1000),
    ("raw", "raw_accounts",      "account_id IS NOT NULL",      200,  500),
    ("raw", "raw_subscriptions", "subscription_id IS NOT NULL", 200,  600),
    ("raw", "raw_invoices",      "invoice_id IS NOT NULL",      1000, 10000),
    ("raw", "raw_usage_events",  "event_id IS NOT NULL",        5000, 100000),
    ("raw", "raw_tickets",       "ticket_id IS NOT NULL",       500,  5000),
    ("raw", "raw_leads",         "lead_id IS NOT NULL",         500,  3000),

    # Staging schema
    ("staging", "stg_plans",         "plan_id IS NOT NULL",         4,    20),
    ("staging", "stg_features",      "feature_id IS NOT NULL",      10,   100),
    ("staging", "stg_calendar",      "full_date IS NOT NULL",       700,  1000),
    ("staging", "stg_accounts",      "account_id IS NOT NULL",      200,  500),
    ("staging", "stg_subscriptions", "subscription_id IS NOT NULL", 200,  600),
    ("staging", "stg_invoices",      "invoice_id IS NOT NULL",      1000, 10000),
    ("staging", "stg_usage_events",  "event_id IS NOT NULL",        5000, 100000),
    ("staging", "stg_tickets",       "ticket_id IS NOT NULL",       500,  5000),
    ("staging", "stg_leads",         "lead_id IS NOT NULL",         500,  3000),

    # Marts schema
    ("marts", "fct_mrr_movements",         "month_date IS NOT NULL",  500,  10000),
    ("marts", "mart_exec_revenue_summary", "month_date IS NOT NULL",  12,   36),
    ("marts", "fct_sales_conversion",      "lead_id IS NOT NULL",     500,  3000),
]

DATA_QUALITY_CHECKS = [
    # No null account_ids in staging subscriptions
    (
        "staging.stg_subscriptions: no null account_id",
        "SELECT COUNT(*) FROM staging.stg_subscriptions WHERE account_id IS NULL",
        "eq", 0,
    ),
    # No negative MRR
    (
        "staging.stg_subscriptions: no negative MRR",
        "SELECT COUNT(*) FROM staging.stg_subscriptions WHERE mrr < 0",
        "eq", 0,
    ),
    # All subscriptions reference valid accounts
    (
        "staging.stg_subscriptions: all accounts exist",
        """
        SELECT COUNT(*) FROM staging.stg_subscriptions s
        WHERE NOT EXISTS (
            SELECT 1 FROM staging.stg_accounts a WHERE a.account_id = s.account_id
        )
        """,
        "eq", 0,
    ),
    # All subscriptions reference valid plans
    (
        "staging.stg_subscriptions: all plans exist",
        """
        SELECT COUNT(*) FROM staging.stg_subscriptions s
        WHERE s.plan_id IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM staging.stg_plans p WHERE p.plan_id = s.plan_id
        )
        """,
        "eq", 0,
    ),
    # MRR movements: no duplicate month+account combos
    (
        "marts.fct_mrr_movements: no duplicate month+account",
        """
        SELECT COUNT(*) FROM (
            SELECT month_date, account_id, COUNT(*) AS cnt
            FROM marts.fct_mrr_movements
            GROUP BY month_date, account_id
            HAVING COUNT(*) > 1
        ) dups
        """,
        "eq", 0,
    ),
    # Executive summary: MRR > 0 for all months
    (
        "marts.mart_exec_revenue_summary: total_mrr > 0",
        "SELECT COUNT(*) FROM marts.mart_exec_revenue_summary WHERE total_mrr <= 0",
        "eq", 0,
    ),
    # NRR should be between 0.5 and 2.0 (50% to 200%)
    (
        "marts.mart_exec_revenue_summary: NRR in valid range",
        "SELECT COUNT(*) FROM marts.mart_exec_revenue_summary WHERE nrr < 0.5 OR nrr > 2.0",
        "eq", 0,
    ),
    # CSAT scores should be between 1 and 5
    (
        "staging.stg_tickets: CSAT in valid range",
        "SELECT COUNT(*) FROM staging.stg_tickets WHERE csat_score IS NOT NULL AND (csat_score < 1 OR csat_score > 5)",
        "eq", 0,
    ),
    # Invoices: no future invoice dates beyond 1 year
    (
        "staging.stg_invoices: no far-future dates",
        "SELECT COUNT(*) FROM staging.stg_invoices WHERE invoice_date > CURRENT_DATE + INTERVAL '365 days'",
        "eq", 0,
    ),
    # Leads: conversion rate sanity (converted leads have account_id)
    (
        "staging.stg_leads: converted leads have account_id",
        "SELECT COUNT(*) FROM staging.stg_leads WHERE converted_at IS NOT NULL AND account_id IS NULL",
        "eq", 0,
    ),
]


def check_table_count(cur, schema: str, table: str, where_clause: str,
                      min_rows: int, max_rows: int) -> dict:
    """Checks that a table has row count within expected range."""
    full_table = schema + "." + table
    sql = "SELECT COUNT(*) FROM " + full_table + " WHERE " + where_clause
    try:
        cur.execute(sql)
        count = cur.fetchone()[0]
        passed = min_rows <= count <= max_rows
        status = "PASS" if passed else "FAIL"
        msg = (
            full_table + ": " + str(count) + " rows "
            "(expected " + str(min_rows) + "-" + str(max_rows) + ")"
        )
        return {
            "check": "row_count",
            "table": full_table,
            "status": status,
            "count": count,
            "min_expected": min_rows,
            "max_expected": max_rows,
            "message": msg,
        }
    except Exception as exc:
        return {
            "check": "row_count",
            "table": full_table,
            "status": "ERROR",
            "count": -1,
            "min_expected": min_rows,
            "max_expected": max_rows,
            "message": str(exc),
        }


def check_data_quality(cur, name: str, sql: str, operator: str, expected) -> dict:
    """Runs a data quality SQL check and compares result to expected value."""
    try:
        cur.execute(sql)
        result = cur.fetchone()[0]
        if operator == "eq":
            passed = result == expected
        elif operator == "gt":
            passed = result > expected
        elif operator == "lt":
            passed = result < expected
        elif operator == "gte":
            passed = result >= expected
        elif operator == "lte":
            passed = result <= expected
        else:
            passed = False

        status = "PASS" if passed else "FAIL"
        msg = name + ": result=" + str(result) + " (expected " + operator + " " + str(expected) + ")"
        return {
            "check": "data_quality",
            "name": name,
            "status": status,
            "result": result,
            "expected": expected,
            "operator": operator,
            "message": msg,
        }
    except Exception as exc:
        return {
            "check": "data_quality",
            "name": name,
            "status": "ERROR",
            "result": None,
            "expected": expected,
            "operator": operator,
            "message": str(exc),
        }


def get_csv_counts() -> dict:
    """Returns row counts from CSV files in data/output/."""
    csv_counts = {}
    csv_files = [
        "plans.csv", "features.csv", "calendar.csv", "accounts.csv",
        "subscriptions.csv", "invoices.csv", "usage_events.csv",
        "support_tickets.csv", "leads.csv",
    ]
    for fname in csv_files:
        fpath = DATA_DIR / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                lines = sum(1 for _ in f)
            csv_counts[fname] = max(0, lines - 1)
        else:
            csv_counts[fname] = -1
    return csv_counts


def run_validation(fail_fast: bool = False, output_format: str = "text") -> dict:
    """
    Runs all validation checks and returns a summary report.
    """
    start = time.monotonic()
    results = []
    errors = 0
    warnings = 0

    logger.info("Starting FlowSync data validation...")

    # CSV file counts
    logger.info("Checking CSV source files...")
    csv_counts = get_csv_counts()
    for fname, count in csv_counts.items():
        if count < 0:
            logger.warning("CSV not found: %s", fname)
            warnings += 1
        else:
            logger.info("  %s: %d rows", fname, count)

    # Database checks
    conn = get_connection()
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            # Row count checks
            logger.info("Running row count checks (%d tables)...", len(SCHEMA_TABLE_CHECKS))
            for schema, table, where, min_r, max_r in SCHEMA_TABLE_CHECKS:
                result = check_table_count(cur, schema, table, where, min_r, max_r)
                results.append(result)
                if result["status"] == "PASS":
                    logger.info("  PASS  %s", result["message"])
                elif result["status"] == "FAIL":
                    logger.warning("  FAIL  %s", result["message"])
                    errors += 1
                    if fail_fast:
                        break
                else:
                    logger.error("  ERROR %s", result["message"])
                    errors += 1
                    if fail_fast:
                        break

            # Data quality checks
            if not (fail_fast and errors > 0):
                logger.info("Running data quality checks (%d checks)...", len(DATA_QUALITY_CHECKS))
                for name, sql, op, expected in DATA_QUALITY_CHECKS:
                    result = check_data_quality(cur, name, sql, op, expected)
                    results.append(result)
                    if result["status"] == "PASS":
                        logger.info("  PASS  %s", result["message"])
                    elif result["status"] == "FAIL":
                        logger.warning("  FAIL  %s", result["message"])
                        errors += 1
                        if fail_fast:
                            break
                    else:
                        logger.error("  ERROR %s", result["message"])
                        errors += 1
                        if fail_fast:
                            break

    finally:
        conn.close()

    elapsed = round(time.monotonic() - start, 2)
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errored = sum(1 for r in results if r["status"] == "ERROR")

    summary = {
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "errors": errored,
        "warnings": warnings,
        "elapsed_seconds": elapsed,
        "overall_status": "PASS" if errors == 0 else "FAIL",
        "csv_counts": csv_counts,
        "checks": results,
    }

    logger.info(
        "Validation complete in %.2fs: %d/%d passed, %d failed, %d errors",
        elapsed, passed, total, failed, errored,
    )

    if output_format == "json":
        print(json.dumps(summary, indent=2, default=str))
    else:
        print("\n" + "=" * 60)
        print("FlowSync Data Validation Summary")
        print("=" * 60)
        print("Total checks : " + str(total))
        print("Passed       : " + str(passed))
        print("Failed       : " + str(failed))
        print("Errors       : " + str(errored))
        print("Elapsed      : " + str(elapsed) + "s")
        print("Status       : " + summary["overall_status"])
        print("=" * 60)

        if failed > 0 or errored > 0:
            print("\nFailed checks:")
            for r in results:
                if r["status"] in ("FAIL", "ERROR"):
                    print("  [" + r["status"] + "] " + r["message"])

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="FlowSync Data Validation — Row counts and quality checks",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        default=False,
        help="Stop on first failure",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    summary = run_validation(fail_fast=args.fail_fast, output_format=args.output)
    sys.exit(0 if summary["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
