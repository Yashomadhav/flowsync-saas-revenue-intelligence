"""
FlowSync - Support Tickets Generator
Outputs: data/seeds/support_tickets.csv -> raw_tickets (bronze)
Generates support tickets correlated with account health and churn patterns.
High-priority tickets cluster before churn events.
"""

from __future__ import annotations
import calendar
import csv
import uuid
import random
from datetime import date, timedelta
from pathlib import Path

from config import (
    RANDOM_SEED, OUTPUT_DIR, SIM_START_DATE, SIM_END_DATE,
    TICKET_PRIORITIES, TICKET_CATEGORIES, TICKET_STATUSES,
    add_months, month_start, clamp,
)

random.seed(RANDOM_SEED + 3)

PRIORITY_WEIGHTS_HEALTHY = [40, 35, 20, 5]
PRIORITY_WEIGHTS_AT_RISK = [15, 30, 40, 15]
PRIORITY_WEIGHTS_CHURNING = [5, 20, 45, 30]

CATEGORY_WEIGHTS = [10, 25, 15, 15, 12, 10, 5, 8]

BASE_TICKETS_PER_MONTH = {
    1: (0.3, 1.2),
    2: (0.5, 2.0),
    3: (0.8, 3.0),
    4: (1.0, 4.5),
}

RESOLUTION_DAYS = {
    "low": (3, 14),
    "medium": (1, 7),
    "high": (0, 3),
    "critical": (0, 1),
}

CSAT_WEIGHTS_BY_priority = {
    "low": [5, 10, 20, 35, 30],
    "medium": [8, 12, 25, 30, 25],
    "high": [15, 20, 30, 25, 10],
    "critical": [25, 30, 25, 15, 5],
}


def _ticket_count(plan_tier, health_score, months_to_churn):
    lo, hi = BASE_TICKETS_PER_MONTH[plan_tier]
    base_rate = random.uniform(lo, hi)
    health_mod = clamp(1.5 - health_score / 100, 0.3, 2.0)
    rate = base_rate * health_mod
    if months_to_churn is not None and months_to_churn <= 2:
        rate *= random.uniform(1.5, 2.5)
    count = int(rate)
    if random.random() < (rate - count):
        count += 1
    return count


def _priority_weights(health_score, months_to_churn):
    if months_to_churn is not None and months_to_churn <= 1:
        return PRIORITY_WEIGHTS_CHURNING
    if health_score < 50:
        return PRIORITY_WEIGHTS_AT_RISK
    return PRIORITY_WEIGHTS_HEALTHY


def _resolution_date(open_date, priority, status):
    if status in ("open", "in_progress"):
        return None
    lo, hi = RESOLUTION_DAYS[priority]
    days = random.randint(lo, hi)
    resolved = open_date + timedelta(days=days)
    if resolved > SIM_END_DATE:
        return None
    return resolved


def _rand_day_in_month(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, random.randint(1, last_day))


def generate_support_tickets(accounts, subscriptions):
    sub_by_account = {}
    for s in subscriptions:
        aid = s["account_id"]
        if aid not in sub_by_account:
            sub_by_account[aid] = []
        sub_by_account[aid].append(s)

    for aid in sub_by_account:
        sub_by_account[aid].sort(key=lambda x: x.get("start_date") or "")

    rows = []

    for acct in accounts:
        account_id = acct["account_id"]
        health_base = float(acct["health_score_baseline"])
        acct_created = date.fromisoformat(acct["created_at"])
        plan_id = acct.get("initial_plan_id", "plan_starter")
        plan_tier_map = {"plan_starter": 1, "plan_growth": 2, "plan_pro": 3, "plan_enterprise": 4}
        plan_tier = plan_tier_map.get(plan_id, 1)

        acct_subs = sub_by_account.get(account_id, [])
        churned_subs = [s for s in acct_subs if s.get("churned_at")]
        churn_date = date.fromisoformat(churned_subs[0]["churned_at"]) if churned_subs else None

        cursor = month_start(max(acct_created, SIM_START_DATE))

        while cursor <= SIM_END_DATE:
            if churn_date and cursor > churn_date:
                break

            health_score = clamp(health_base + random.uniform(-5, 5), 10, 100)

            months_to_churn = None
            if churn_date:
                diff = (churn_date.year - cursor.year) * 12 + (churn_date.month - cursor.month)
                months_to_churn = diff if diff >= 0 else None

            n_tickets = _ticket_count(plan_tier, health_score, months_to_churn)
            pw = _priority_weights(health_score, months_to_churn)

            for _ in range(n_tickets):
                priority = random.choices(TICKET_PRIORITIES, weights=pw, k=1)[0]
                category = random.choices(TICKET_CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]
                open_date = _rand_day_in_month(cursor.year, cursor.month)

                if months_to_churn is not None and months_to_churn <= 1:
                    status_weights = [30, 25, 30, 15]
                else:
                    status_weights = [10, 15, 45, 30]
                status = random.choices(TICKET_STATUSES, weights=status_weights, k=1)[0]

                resolved_date = _resolution_date(open_date, priority, status)
                resolution_days = None
                if resolved_date:
                    resolution_days = (resolved_date - open_date).days

                csat_weights = CSAT_WEIGHTS_BY_priority.get(priority, [20, 20, 20, 20, 20])
                csat = random.choices([1, 2, 3, 4, 5], weights=csat_weights, k=1)[0]
                if status in ("open", "in_progress"):
                    csat = None

                rows.append(dict(
                    ticket_id="tkt_" + uuid.uuid4().hex[:12],
                    account_id=account_id,
                    plan_id=plan_id,
                    open_date=open_date.isoformat(),
                    open_month=cursor.isoformat(),
                    resolved_date=resolved_date.isoformat() if resolved_date else None,
                    resolution_days=resolution_days,
                    priority=priority,
                    category=category,
                    status=status,
                    csat_score=csat,
                    health_score_at_open=round(health_score, 1),
                    months_to_churn=months_to_churn,
                    is_escalated=priority in ("high", "critical") and random.random() < 0.3,
                ))

            cursor = add_months(cursor, 1)

    rows.sort(key=lambda r: r["open_date"])
    print(f"[support_tickets] Generated {len(rows)} ticket records")
    return rows


def save_support_tickets(rows, out_dir=OUTPUT_DIR):
    path = out_dir / "support_tickets.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        print(f"[support_tickets] Wrote {len(rows)} rows -> {path}")
    return path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generate_accounts import generate_accounts
    from generate_subscriptions import generate_subscriptions
    accts = generate_accounts()
    subs = generate_subscriptions(accts)
    data = generate_support_tickets(accts, subs)
    save_support_tickets(data)
