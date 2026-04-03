"""
FlowSync - Raw CSV to PostgreSQL Loader
Loads all generated CSV seed files into the raw (bronze) schema tables.
Handles upserts, truncate-reload, and connection pooling.
"""

from __future__ import annotations
import csv
import os
import sys
from pathlib import Path
from datetime import date

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

ROOT_DIR = Path(__file__).resolve().parent.parent
SEEDS_DIR = ROOT_DIR / "seeds"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://flowsync:flowsync@localhost:5432/flowsync_db"
)

TABLE_MAP = {
    "plans.csv":            "raw.raw_plans",
    "features.csv":         "raw.raw_features",
    "calendar.csv":         "raw.raw_calendar",
    "accounts.csv":         "raw.raw_accounts",
    "subscriptions.csv":    "raw.raw_subscriptions",
    "invoices.csv":         "raw.raw_invoices",
    "usage_events.csv":     "raw.raw_usage_events",
    "support_tickets.csv":  "raw.raw_tickets",
    "leads.csv":            "raw.raw_leads",
}

LOAD_ORDER = [
    "plans.csv",
    "features.csv",
    "calendar.csv",
    "accounts.csv",
    "subscriptions.csv",
    "invoices.csv",
    "usage_events.csv",
    "support_tickets.csv",
    "leads.csv",
]


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def ensure_raw_schema(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    conn.commit()
    print("[loader] Ensured raw schema exists")


def create_table_from_csv(conn, table_name, csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        if not columns:
            print(f"[loader] WARNING: {csv_path} has no columns, skipping")
            return

    col_defs = []
    for col in columns:
        if col.endswith("_date") or col.endswith("_at") or col == "date":
            col_defs.append(f'"{col}" DATE')
        elif col.endswith("_month") or col == "month":
            col_defs.append(f'"{col}" DATE')
        elif col.endswith("_id") and col != "csat_score":
            col_defs.append(f'"{col}" TEXT')
        elif col in ("is_weekend", "is_escalated", "is_converted", "is_lost",
                     "seat_based", "is_annual", "payment_succeeded", "is_dunning"):
            col_defs.append(f'"{col}" BOOLEAN')
        elif col in ("monthly_price", "annual_price", "price_per_seat", "mrr",
                     "amount", "mrr_at_conversion", "health_score_at_event",
                     "health_score_at_open", "health_score_baseline",
                     "seat_utilization_pct", "trial_engagement_score",
                     "failure_rate_pct"):
            col_defs.append(f'"{col}" NUMERIC(12,4)')
        elif col in ("min_seats", "max_seats", "seats", "seats_purchased",
                     "active_users_this_month", "session_duration_minutes",
                     "dunning_count", "resolution_days", "days_to_convert",
                     "months_to_churn", "csat_score", "tier"):
            col_defs.append(f'"{col}" INTEGER')
        else:
            col_defs.append(f'"{col}" TEXT')

    schema, tbl = table_name.split(".")
    col_defs_str = ", ".join(col_defs)
    ddl = "CREATE TABLE IF NOT EXISTS " + table_name + " (" + col_defs_str + ");"
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("[loader] Ensured table " + table_name)


def truncate_table(conn, table_name):
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {table_name};")
    conn.commit()


def load_csv_to_table(conn, table_name, csv_path, batch_size=500):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        if not columns:
            return 0

        quoted_cols = [f'"{c}"' for c in columns]
        placeholders = ["%s"] * len(columns)
        insert_sql = (
            f"INSERT INTO {table_name} ({', '.join(quoted_cols)}) "
            f"VALUES ({', '.join(placeholders)})"
        )

        total = 0
        batch = []

        for row in reader:
            values = []
            for col in columns:
                val = row.get(col)
                if val == "" or val is None or val == "None":
                    values.append(None)
                elif val in ("True", "true"):
                    values.append(True)
                elif val in ("False", "false"):
                    values.append(False)
                else:
                    values.append(val)
            batch.append(tuple(values))

            if len(batch) >= batch_size:
                with conn.cursor() as cur:
                    psycopg2.extras.execute_batch(cur, insert_sql, batch)
                conn.commit()
                total += len(batch)
                batch = []

        if batch:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, insert_sql, batch)
            conn.commit()
            total += len(batch)

    return total


def load_all(seeds_dir=SEEDS_DIR, truncate=True):
    print(f"[loader] Connecting to {DATABASE_URL[:40]}...")
    conn = get_connection()
    ensure_raw_schema(conn)

    for filename in LOAD_ORDER:
        csv_path = seeds_dir / filename
        if not csv_path.exists():
            print(f"[loader] SKIP {filename} (not found)")
            continue

        table_name = TABLE_MAP[filename]
        create_table_from_csv(conn, table_name, csv_path)

        if truncate:
            truncate_table(conn, table_name)
            print(f"[loader] Truncated {table_name}")

        n = load_csv_to_table(conn, table_name, csv_path)
        print(f"[loader] Loaded {n:,} rows into {table_name}")

    conn.close()
    print("[loader] All tables loaded successfully")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load FlowSync seed CSVs into PostgreSQL")
    parser.add_argument("--seeds-dir", default=str(SEEDS_DIR), help="Path to seeds directory")
    parser.add_argument("--no-truncate", action="store_true", help="Skip truncation before load")
    parser.add_argument("--db-url", default=None, help="Override DATABASE_URL")
    args = parser.parse_args()

    if args.db_url:
        DATABASE_URL = args.db_url

    load_all(
        seeds_dir=Path(args.seeds_dir),
        truncate=not args.no_truncate,
    )
