"""
FlowSync SaaS Revenue Intelligence — Database Seeder
=====================================================
Generates synthetic data and loads it into PostgreSQL.
Also computes and populates the Gold layer (MRR movements, health scores, etc.)

Usage:
    python scripts/seed_db.py
    python scripts/seed_db.py --accounts 500 --months 36 --reset
"""

import sys
import os
import argparse
import uuid
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    from psycopg2.extras import execute_values, RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

from data.generators.generate_data import generate_all, add_months, first_of_month, months_between

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://flowsync:flowsync_secret_change_me@localhost:5432/flowsync_bi"
)

NUM_ACCOUNTS = int(os.getenv("SEED_ACCOUNTS", "200"))
NUM_MONTHS = int(os.getenv("SEED_MONTHS", "24"))
RANDOM_SEED = int(os.getenv("SEED_RANDOM_SEED", "42"))

random.seed(RANDOM_SEED)

# ─────────────────────────────────────────────────────────────────────────────
# Database connection
# ─────────────────────────────────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# ─────────────────────────────────────────────────────────────────────────────
# Bronze Layer Loaders
# ─────────────────────────────────────────────────────────────────────────────

def load_raw_accounts(conn, accounts: List[Dict]):
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw_accounts (_id, account_id, company_name, industry, region, country,
                company_size, employee_count, founded_year, website, acquisition_channel,
                created_at, updated_at)
            VALUES %s ON CONFLICT DO NOTHING
        """, [(
            a["_id"], a["account_id"], a["company_name"], a["industry"], a["region"],
            a["country"], a["company_size"], a["employee_count"], a["founded_year"],
            a["website"], a["acquisition_channel"], a["created_at"], a["updated_at"]
        ) for a in accounts])
    conn.commit()
    print(f"   ✓ Loaded {len(accounts)} raw_accounts")

def load_raw_subscriptions(conn, subscriptions: List[Dict]):
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw_subscriptions (_id, subscription_id, account_id, plan_id, plan_name,
                status, mrr_amount, arr_amount, billing_cycle, seats_licensed, seats_used,
                trial_start_date, trial_end_date, start_date, end_date, cancelled_at,
                created_at, updated_at)
            VALUES %s ON CONFLICT DO NOTHING
        """, [(
            s["_id"], s["subscription_id"], s["account_id"], s["plan_id"], s["plan_name"],
            s["status"], s["mrr_amount"], s["arr_amount"], s["billing_cycle"],
            s["seats_licensed"], s["seats_used"], s["trial_start_date"], s["trial_end_date"],
            s["start_date"], s["end_date"], s["cancelled_at"], s["created_at"], s["updated_at"]
        ) for s in subscriptions])
    conn.commit()
    print(f"   ✓ Loaded {len(subscriptions)} raw_subscriptions")

def load_raw_invoices(conn, invoices: List[Dict]):
    batch_size = 1000
    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(invoices), batch_size):
            batch = invoices[i:i+batch_size]
            execute_values(cur, """
                INSERT INTO raw_invoices (_id, invoice_id, account_id, subscription_id,
                    amount, currency, status, due_date, paid_date, failed_date,
                    failure_reason, invoice_date, created_at)
                VALUES %s ON CONFLICT DO NOTHING
            """, [(
                inv["_id"], inv["invoice_id"], inv["account_id"], inv["subscription_id"],
                inv["amount"], inv["currency"], inv["status"], inv["due_date"],
                inv["paid_date"], inv["failed_date"], inv["failure_reason"],
                inv["invoice_date"], inv["created_at"]
            ) for inv in batch])
            total += len(batch)
    conn.commit()
    print(f"   ✓ Loaded {total} raw_invoices")

def load_raw_usage_events(conn, events: List[Dict]):
    batch_size = 2000
    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(events), batch_size):
            batch = events[i:i+batch_size]
            execute_values(cur, """
                INSERT INTO raw_usage_events (_id, event_id, account_id, user_id,
                    feature_name, event_type, session_id, duration_seconds, event_date, created_at)
                VALUES %s ON CONFLICT DO NOTHING
            """, [(
                e["_id"], e["event_id"], e["account_id"], e["user_id"],
                e["feature_name"], e["event_type"], e["session_id"],
                e["duration_seconds"], e["event_date"], e["created_at"]
            ) for e in batch])
            total += len(batch)
    conn.commit()
    print(f"   ✓ Loaded {total} raw_usage_events")

def load_raw_tickets(conn, tickets: List[Dict]):
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw_tickets (_id, ticket_id, account_id, user_id, subject,
                category, priority, status, csat_score, created_at, resolved_at, first_response_at)
            VALUES %s ON CONFLICT DO NOTHING
        """, [(
            t["_id"], t["ticket_id"], t["account_id"], t["user_id"], t["subject"],
            t["category"], t["priority"], t["status"], t["csat_score"] or None,
            t["created_at"], t["resolved_at"] or None, t["first_response_at"] or None
        ) for t in tickets])
    conn.commit()
    print(f"   ✓ Loaded {len(tickets)} raw_tickets")

def load_raw_leads(conn, leads: List[Dict]):
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO raw_leads (_id, lead_id, company_name, contact_name, contact_email,
                industry, company_size, acquisition_channel, lead_source, status,
                trial_start_date, trial_end_date, converted_at, account_id,
                estimated_mrr, created_at, updated_at)
            VALUES %s ON CONFLICT DO NOTHING
        """, [(
            l["_id"], l["lead_id"], l["company_name"], l["contact_name"], l["contact_email"],
            l["industry"], l["company_size"], l["acquisition_channel"], l["lead_source"],
            l["status"], l["trial_start_date"] or None, l["trial_end_date"] or None,
            l["converted_at"] or None, l["account_id"] or None,
            l["estimated_mrr"], l["created_at"], l["updated_at"]
        ) for l in leads])
    conn.commit()
    print(f"   ✓ Loaded {len(leads)} raw_leads")

# ─────────────────────────────────────────────────────────────────────────────
# Silver Layer — Transform raw → staging
# ─────────────────────────────────────────────────────────────────────────────

def transform_to_silver(conn):
    print("\n🔄 Transforming Bronze → Silver...")
    with conn.cursor() as cur:
        # stg_accounts
        cur.execute("""
            INSERT INTO stg_accounts (account_id, company_name, industry, region, country,
                company_size, employee_count, founded_year, website, acquisition_channel,
                created_at, updated_at)
            SELECT
                account_id::uuid,
                company_name,
                industry,
                region,
                country,
                company_size,
                NULLIF(employee_count, '')::integer,
                NULLIF(founded_year, '')::integer,
                website,
                acquisition_channel,
                NULLIF(created_at, '')::timestamptz,
                NULLIF(updated_at, '')::timestamptz
            FROM raw_accounts
            ON CONFLICT (account_id) DO NOTHING
        """)
        print(f"   ✓ stg_accounts: {cur.rowcount} rows")

        # stg_subscriptions
        cur.execute("""
            INSERT INTO stg_subscriptions (subscription_id, account_id, plan_id, plan_name,
                status, mrr_amount, arr_amount, billing_cycle, seats_licensed, seats_used,
                trial_start_date, trial_end_date, start_date, end_date, cancelled_at,
                created_at, updated_at)
            SELECT
                subscription_id::uuid,
                account_id::uuid,
                plan_id,
                plan_name,
                status,
                NULLIF(mrr_amount, '')::numeric,
                NULLIF(arr_amount, '')::numeric,
                billing_cycle,
                NULLIF(seats_licensed, '')::integer,
                NULLIF(seats_used, '')::integer,
                NULLIF(trial_start_date, '')::date,
                NULLIF(trial_end_date, '')::date,
                NULLIF(start_date, '')::date,
                NULLIF(end_date, '')::date,
                NULLIF(cancelled_at, '')::timestamptz,
                NULLIF(created_at, '')::timestamptz,
                NULLIF(updated_at, '')::timestamptz
            FROM raw_subscriptions
            WHERE account_id IN (SELECT account_id::text FROM stg_accounts)
            ON CONFLICT (subscription_id) DO NOTHING
        """)
        print(f"   ✓ stg_subscriptions: {cur.rowcount} rows")

        # stg_invoices
        cur.execute("""
            INSERT INTO stg_invoices (invoice_id, account_id, subscription_id, amount,
                currency, status, due_date, paid_date, failed_date, failure_reason,
                invoice_date, created_at)
            SELECT
                invoice_id::uuid,
                account_id::uuid,
                subscription_id::uuid,
                NULLIF(amount, '')::numeric,
                COALESCE(NULLIF(currency, ''), 'USD'),
                status,
                NULLIF(due_date, '')::date,
                NULLIF(paid_date, '')::date,
                NULLIF(failed_date, '')::date,
                NULLIF(failure_reason, ''),
                NULLIF(invoice_date, '')::date,
                NULLIF(created_at, '')::timestamptz
            FROM raw_invoices
            WHERE account_id IN (SELECT account_id::text FROM stg_accounts)
            ON CONFLICT (invoice_id) DO NOTHING
        """)
        print(f"   ✓ stg_invoices: {cur.rowcount} rows")

        # stg_usage_events
        cur.execute("""
            INSERT INTO stg_usage_events (event_id, account_id, user_id, feature_name,
                event_type, session_id, duration_seconds, event_date, created_at)
            SELECT
                event_id::uuid,
                account_id::uuid,
                user_id::uuid,
                feature_name,
                event_type,
                session_id::uuid,
                NULLIF(duration_seconds, '')::integer,
                NULLIF(event_date, '')::date,
                NULLIF(created_at, '')::timestamptz
            FROM raw_usage_events
            WHERE account_id IN (SELECT account_id::text FROM stg_accounts)
            ON CONFLICT (event_id) DO NOTHING
        """)
        print(f"   ✓ stg_usage_events: {cur.rowcount} rows")

        # stg_tickets
        cur.execute("""
            INSERT INTO stg_tickets (ticket_id, account_id, user_id, subject, category,
                priority, status, csat_score, created_at, resolved_at, first_response_at)
            SELECT
                ticket_id::uuid,
                account_id::uuid,
                user_id::uuid,
                subject,
                category,
                priority,
                status,
                NULLIF(csat_score, '')::numeric,
                NULLIF(created_at, '')::timestamptz,
                NULLIF(resolved_at, '')::timestamptz,
                NULLIF(first_response_at, '')::timestamptz
            FROM raw_tickets
            WHERE account_id IN (SELECT account_id::text FROM stg_accounts)
            ON CONFLICT (ticket_id) DO NOTHING
        """)
        print(f"   ✓ stg_tickets: {cur.rowcount} rows")

        # stg_leads
        cur.execute("""
            INSERT INTO stg_leads (lead_id, company_name, contact_name, contact_email,
                industry, company_size, acquisition_channel, lead_source, status,
                trial_start_date, trial_end_date, converted_at, account_id,
                estimated_mrr, created_at, updated_at)
            SELECT
                lead_id::uuid,
                company_name,
                contact_name,
                contact_email,
                industry,
                company_size,
                acquisition_channel,
                lead_source,
                status,
                NULLIF(trial_start_date, '')::date,
                NULLIF(trial_end_date, '')::date,
                NULLIF(converted_at, '')::timestamptz,
                NULLIF(account_id, '')::uuid,
                NULLIF(estimated_mrr, '')::numeric,
                NULLIF(created_at, '')::timestamptz,
                NULLIF(updated_at, '')::timestamptz
            FROM raw_leads
            ON CONFLICT (lead_id) DO NOTHING
        """)
        print(f"   ✓ stg_leads: {cur.rowcount} rows")

    conn.commit()

# ─────────────────────────────────────────────────────────────────────────────
# Gold Layer — Compute MRR Movements
# ─────────────────────────────────────────────────────────────────────────────

def compute_mrr_movements(conn):
    print("\n💰 Computing MRR movements (Gold layer)...")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                s.account_id,
                a.region,
                a.industry,
                a.company_size,
                a.acquisition_channel,
                s.plan_id,
                s.plan_name,
                s.mrr_amount,
                s.start_date,
                s.end_date,
                s.cancelled_at,
                s.status
            FROM stg_subscriptions s
            JOIN stg_accounts a ON s.account_id = a.account_id
            WHERE s.start_date IS NOT NULL
        """)
        subscriptions = cur.fetchall()

    end_date = date.today().replace(day=1)
    start_date = add_months(end_date, -NUM_MONTHS)

    movements = []
    prev_mrr = {}  # account_id -> mrr last month

    current_month = start_date
    while current_month < end_date:
        next_month = add_months(current_month, 1)

        for sub in subscriptions:
            account_id = str(sub["account_id"])
            sub_start = sub["start_date"]
            sub_end = sub["end_date"]
            mrr = float(sub["mrr_amount"] or 0)

            is_active_this_month = (
                sub_start <= current_month and
                (sub_end is None or sub_end > current_month)
            )
            was_active_last_month = account_id in prev_mrr

            if is_active_this_month and not was_active_last_month:
                movement_type = "reactivation" if random.random() < 0.05 else "new"
                new_mrr = mrr
                expansion = contraction = churn = reactivation = 0
                if movement_type == "reactivation":
                    reactivation = mrr
                    new_mrr = 0
            elif is_active_this_month and was_active_last_month:
                prev = prev_mrr[account_id]
                diff = mrr - prev
                if diff > 5:
                    movement_type = "expansion"
                    expansion = diff
                    contraction = churn = new_mrr = reactivation = 0
                elif diff < -5:
                    movement_type = "contraction"
                    contraction = abs(diff)
                    expansion = churn = new_mrr = reactivation = 0
                else:
                    movement_type = "retained"
                    expansion = contraction = churn = new_mrr = reactivation = 0
            elif not is_active_this_month and was_active_last_month:
                movement_type = "churn"
                churn = prev_mrr[account_id]
                expansion = contraction = new_mrr = reactivation = 0
                mrr = 0
            else:
                continue

            starting_mrr = prev_mrr.get(account_id, 0)
            net_new = new_mrr + expansion + reactivation - contraction - churn

            movements.append({
                "month_date": current_month,
                "account_id": account_id,
                "plan_id": sub["plan_id"],
                "plan_name": sub["plan_name"],
                "region": sub["region"],
                "industry": sub["industry"],
                "company_size": sub["company_size"],
                "acquisition_channel": sub["acquisition_channel"],
                "movement_type": movement_type,
                "starting_mrr": starting_mrr,
                "ending_mrr": mrr,
                "new_mrr": new_mrr,
                "expansion_mrr": expansion,
                "contraction_mrr": contraction,
                "churned_mrr": churn,
                "reactivation_mrr": reactivation,
                "net_new_mrr": net_new,
            })

        # Update prev_mrr for next month
        for sub in subscriptions:
            account_id = str(sub["account_id"])
            sub_start = sub["start_date"]
            sub_end = sub["end_date"]
            mrr = float(sub["mrr_amount"] or 0)
            is_active = (
                sub_start <= current_month and
                (sub_end is None or sub_end > current_month)
            )
            if is_active:
                prev_mrr[account_id] = mrr
            elif account_id in prev_mrr and not is_active:
                del prev_mrr[account_id]

        current_month = next_month

    # Insert movements
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO fct_mrr_movements (month_date, account_id, plan_id, plan_name,
                region, industry, company_size, acquisition_channel, movement_type,
                starting_mrr, ending_mrr, new_mrr, expansion_mrr, contraction_mrr,
                churned_mrr, reactivation_mrr, net_new_mrr)
            VALUES %s
            ON CONFLICT (month_date, account_id) DO NOTHING
        """, [(
            m["month_date"], m["account_id"], m["plan_id"], m["plan_name"],
            m["region"], m["industry"], m["company_size"], m["acquisition_channel"],
            m["movement_type"], m["starting_mrr"], m["ending_mrr"],
            m["new_mrr"], m["expansion_mrr"], m["contraction_mrr"],
            m["churned_mrr"], m["reactivation_mrr"], m["net_new_mrr"]
        ) for m in movements])
    conn.commit()
    print(f"   ✓ fct_mrr_movements: {len(movements)} rows")

# ─────────────────────────────────────────────────────────────────────────────
# Gold Layer — Compute Executive Summary
# ─────────────────────────────────────────────────────────────────────────────

def compute_exec_summary(conn):
    print("\n📊 Computing executive summary mart...")
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO mart_exec_revenue_summary (
                month_date, total_mrr, total_arr, new_mrr, expansion_mrr,
                contraction_mrr, churned_mrr, reactivation_mrr, net_new_mrr,
                nrr, grr, logo_churn_rate, revenue_churn_rate,
                active_accounts, new_accounts, churned_accounts, arpa,
                mrr_mom_change, arr_mom_change, accounts_mom_change
            )
            WITH monthly AS (
                SELECT
                    month_date,
                    SUM(CASE WHEN movement_type != 'churn' THEN ending_mrr ELSE 0 END) AS total_mrr,
                    SUM(new_mrr) AS new_mrr,
                    SUM(expansion_mrr) AS expansion_mrr,
                    SUM(contraction_mrr) AS contraction_mrr,
                    SUM(churned_mrr) AS churned_mrr,
                    SUM(reactivation_mrr) AS reactivation_mrr,
                    SUM(net_new_mrr) AS net_new_mrr,
                    SUM(starting_mrr) AS total_starting_mrr,
                    COUNT(DISTINCT CASE WHEN movement_type != 'churn' THEN account_id END) AS active_accounts,
                    COUNT(DISTINCT CASE WHEN movement_type = 'new' THEN account_id END) AS new_accounts,
                    COUNT(DISTINCT CASE WHEN movement_type = 'churn' THEN account_id END) AS churned_accounts,
                    COUNT(DISTINCT CASE WHEN movement_type IN ('retained','expansion','contraction') THEN account_id END) AS starting_accounts
                FROM fct_mrr_movements
                GROUP BY month_date
            )
            SELECT
                month_date,
                total_mrr,
                total_mrr * 12 AS total_arr,
                new_mrr,
                expansion_mrr,
                contraction_mrr,
                churned_mrr,
                reactivation_mrr,
                net_new_mrr,
                CASE WHEN total_starting_mrr > 0
                    THEN (total_starting_mrr + expansion_mrr + reactivation_mrr - contraction_mrr - churned_mrr) / total_starting_mrr
                    ELSE 1.0 END AS nrr,
                CASE WHEN total_starting_mrr > 0
                    THEN (total_starting_mrr - contraction_mrr - churned_mrr) / total_starting_mrr
                    ELSE 1.0 END AS grr,
                CASE WHEN starting_accounts > 0
                    THEN churned_accounts::numeric / starting_accounts
                    ELSE 0 END AS logo_churn_rate,
                CASE WHEN total_starting_mrr > 0
                    THEN (churned_mrr + contraction_mrr) / total_starting_mrr
                    ELSE 0 END AS revenue_churn_rate,
                active_accounts,
                new_accounts,
                churned_accounts,
                CASE WHEN active_accounts > 0 THEN total_mrr / active_accounts ELSE 0 END AS arpa,
                0 AS mrr_mom_change,
                0 AS arr_mom_change,
                0 AS accounts_mom_change
            FROM monthly
            ON CONFLICT (month_date) DO NOTHING
        """)
        conn.commit()
        print(f"   ✓ mart_exec_revenue_summary: {cur.rowcount} rows")

# ─────────────────────────────────────────────────────────────────────────────
# Gold Layer — Compute Health Scores
# ─────────────────────────────────────────────────────────────────────────────

def compute_health_scores(conn):
    print("\n🏥 Computing account health scores...")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                a.account_id, a.company_name,
                s.plan_name, s.mrr_amount, s.seats_licensed, s.start_date, s.end_date
            FROM stg_accounts a
            JOIN stg_subscriptions s ON a.account_id = s.account_id
            WHERE s.status = 'active' OR (s.end_date IS NOT NULL AND s.end_date > CURRENT_DATE - INTERVAL '6 months')
        """)
        accounts = cur.fetchall()

    end_date = date.today().replace(day=1)
    start_date = add_months(end_date, -NUM_MONTHS)
    health_records = []

    for account in accounts:
        account_id = str(account["account_id"])
        sub_start = account["start_date"] or start_date
        sub_end = account["end_date"] or end_date
        tenure_months = months_between(sub_start, end_date)

        current_month = max(sub_start.replace(day=1), start_date)
        while current_month < min(sub_end, end_date):
            # Simulate health metrics
            base_usage = random.randint(20, 200)
            usage_trend = random.uniform(-0.3, 0.2)
            monthly_sessions = max(0, int(base_usage * (1 + usage_trend * months_between(sub_start, current_month) / 12)))

            seats = int(account["seats_licensed"] or 5)
            active_users = max(1, int(seats * random.uniform(0.2, 0.95)))
            features_used = random.randint(2, 12)
            open_tickets = random.randint(0, 5)
            avg_csat = round(random.uniform(2.5, 5.0), 1)
            days_since_login = random.randint(0, 30)
            payment_failures = random.randint(0, 2)

            # Score components (0-100)
            usage_score = min(100, (monthly_sessions / 100) * 100)
            seat_util_score = (active_users / seats) * 100
            feature_score = (features_used / 12) * 100
            support_score = max(0, 100 - (open_tickets * 20))
            csat_norm = ((avg_csat - 1) / 4) * 100
            payment_score = max(0, 100 - (payment_failures * 40))
            tenure_score = min(100, (tenure_months / 24) * 100)

            # Weighted health score
            health_score = round(
                usage_score * 0.25 +
                seat_util_score * 0.20 +
                feature_score * 0.15 +
                support_score * 0.15 +
                csat_norm * 0.10 +
                payment_score * 0.10 +
                tenure_score * 0.05,
                2
            )

            # Risk flags
            flag_usage_drop = usage_trend < -0.40
            flag_no_login = days_since_login > 14
            flag_support_overload = open_tickets >= 2
            flag_payment_failure = payment_failures > 0
            flag_low_csat = avg_csat < 3.0
            flag_low_seat_util = (active_users / seats) < 0.25

            # Risk level
            if health_score >= 75:
                risk_level = "healthy"
            elif health_score >= 50:
                risk_level = "at_risk"
            else:
                risk_level = "critical"

            health_records.append((
                current_month, account_id, account["company_name"],
                account["plan_name"], float(account["mrr_amount"] or 0),
                health_score, usage_score, seat_util_score, feature_score,
                support_score, csat_norm, payment_score, tenure_score,
                risk_level, flag_usage_drop, flag_no_login, flag_support_overload,
                flag_payment_failure, flag_low_csat, flag_low_seat_util,
                monthly_sessions, active_users, seats, features_used,
                open_tickets, avg_csat, days_since_login, tenure_months
            ))

            current_month = add_months(current_month, 1)

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO fct_account_monthly_health (
                month_date, account_id, company_name, plan_name, mrr_amount,
                health_score, usage_score, seat_utilization_score, feature_adoption_score,
                support_score, csat_score_normalized, payment_score, tenure_score,
                risk_level, flag_usage_drop, flag_no_login, flag_support_overload,
                flag_payment_failure, flag_low_csat, flag_low_seat_util,
                monthly_sessions, active_users, seats_licensed, features_used,
                open_tickets, avg_csat, days_since_login, tenure_months
            ) VALUES %s
            ON CONFLICT (month_date, account_id) DO NOTHING
        """, health_records)
    conn.commit()
    print(f"   ✓ fct_account_monthly_health: {len(health_records)} rows")

# ─────────────────────────────────────────────────────────────────────────────
# Gold Layer — Compute Cohort Retention
# ─────────────────────────────────────────────────────────────────────────────

def compute_cohorts(conn):
    print("\n📅 Computing cohort retention...")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                s.account_id,
                a.acquisition_channel,
                a.company_size,
                s.plan_name,
                s.mrr_amount,
                s.start_date,
                s.end_date
            FROM stg_subscriptions s
            JOIN stg_accounts a ON s.account_id = a.account_id
            WHERE s.start_date IS NOT NULL
        """)
